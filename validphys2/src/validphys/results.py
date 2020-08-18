# -*- coding: utf-8 -*-
"""
results.py

Tools to obtain theory predictions and basic statistical estimators.
"""
from __future__ import generator_stop

from collections import OrderedDict, namedtuple
from collections.abc import Sequence
import itertools
import logging

import numpy as np
import pandas as pd

from NNPDF import ThPredictions, CommonData, Experiment
from reportengine.checks import require_one, remove_outer, check_not_empty
from reportengine.table import table
from reportengine import collect

from validphys.checks import (
    check_cuts_considered,
    check_pdf_is_montecarlo,
    check_speclabels_different,
    check_two_dataspecs,
)

from validphys.core import DataSetSpec, PDF, DataGroupSpec, cut_mask
from validphys.calcutils import (
    all_chi2, central_chi2, calc_chi2, calc_phi, bootstrap_values
)

log = logging.getLogger(__name__)



class Result: pass


#TODO: Eventually,only one of (NNPDFDataResult, StatsResult) should survive
class NNPDFDataResult(Result):
    """A result fills its values from a libnnpf data object"""
    def __init__(self, dataobj):
        self._central_value = dataobj.get_cv()

    @property
    def central_value(self):
        return self._central_value

    def __len__(self):
        return len(self.central_value)

class StatsResult(Result):
    def __init__(self, stats):
        self.stats = stats

    @property
    def central_value(self):
        return self.stats.central_value()

    @property
    def std_error(self):
        return self.stats.std_error()

class DataResult(NNPDFDataResult):

    def __init__(self, dataobj, covmat, sqrtcovmat):
        super().__init__(dataobj)
        self._covmat = covmat
        self._sqrtcovmat = sqrtcovmat


    @property
    def label(self):
        return "Data"

    @property
    def std_error(self):
        return np.sqrt(np.diag(self.covmat))

    @property
    def covmat(self):
        return self._covmat

    @property
    def sqrtcovmat(self):
        """Lower part of the Cholesky decomposition"""
        return self._sqrtcovmat


class ThPredictionsResult(NNPDFDataResult):

    def __init__(self, dataobj, stats_class, label=None):
        self.stats_class = stats_class
        self.label = label
        self._std_error = dataobj.get_error()
        self._rawdata = dataobj.get_data()
        super().__init__(dataobj)

    @property
    def std_error(self):
        return self._std_error

    @staticmethod
    def make_label(pdf, dataset):
        """Deduce a reasonsble label for the result based on pdf and dataspec"""
        th = dataset.thspec
        if hasattr(pdf,'label'):
            if hasattr(th, 'label'):
                label = ' '.join((pdf.label, th.label))
            else:
                label = pdf.label
        elif hasattr(th, 'label'):
            label = th.label
        else:
            label = ('%s@<Theory %s>' % (pdf, th.id))
        return label


    @classmethod
    def from_convolution(cls, pdf, dataset, loaded_pdf=None, loaded_data=None):
        if loaded_pdf  is None:
            loaded_pdf = pdf.load()
        if loaded_data is None:
            loaded_data = dataset.load()
        th_predictions = ThPredictions(loaded_pdf, loaded_data)


        label = cls.make_label(pdf, dataset)


        return cls(th_predictions, pdf.stats_class, label)

class PositivityResult(StatsResult):
    @classmethod
    def from_convolution(cls, pdf, posset):
        loaded_pdf = pdf.load()
        loaded_pos = posset.load()
        data = loaded_pos.GetPredictions(loaded_pdf)
        stats = pdf.stats_class(data.T)
        return cls(stats)

    @property
    def rawdata(self):
        return self.stats.data

#TODO: finish deprecating all dependencies on this index largely in theorycovmat module
groups_data = collect("data", ("group_dataset_inputs_by_metadata",))

experiments_data = collect("data", ("group_dataset_inputs_by_experiment",))

def groups_index(groups_data):
    """Return a pandas.MultiIndex with levels for group, dataset and point
    respectively, the group is determined by a key in the dataset metadata, and
    controlled by `metadata_group` key in the runcard.

    Example
    -------
    TODO: add example

    """
    records = []
    for group in groups_data:
        for dataset in group.datasets:
            if dataset.cuts:
                data_id = dataset.cuts.load()
            else:
                #No cuts - use all data
                data_id = np.arange(dataset.commondata.ndata, dtype=int)
            for idat in data_id:
                records.append(
                    dict(
                        [('group', str(group.name)),
                         ('dataset', str(dataset.name)),
                         ('id', idat),]))

    columns = ['group', 'dataset', 'id']
    df = pd.DataFrame(records, columns=columns)
    df.set_index(columns, inplace=True)
    return df.index

def experiments_index(experiments_data):
    return groups_index(experiments_data)

def groups_data_values(group_result_table):
    """Returns list of data values for the input groups."""
    data_central_values = group_result_table["data_central"]
    return data_central_values

groups_results = collect(
    "dataset_inputs_results", ("group_dataset_inputs_by_metadata",))

def group_result_table_no_table(groups_results, groups_index):
    """Generate a table containing the data central value, the central prediction,
    and the prediction for each PDF member."""
    result_records = []
    for group_results in groups_results:
        dt, th = group_results
        for index, (dt_central, th_central) in enumerate(zip(dt.central_value, th.central_value)):
            replicas = (('rep_%05d'%(i+1), th_rep) for
                        i, th_rep in enumerate(th._rawdata[index, :]))

            result_records.append(dict([
                                 ('data_central', dt_central),
                                 ('theory_central', th_central),
                                  *replicas
                                 ]))
    if not result_records:
        log.warning("Empty records for group results")
        return pd.DataFrame()
    df =  pd.DataFrame(result_records, columns=result_records[0].keys(),
                       index=groups_index)

    return df

@table
def group_result_table(group_result_table_no_table):
    """Duplicate of group_result_table_no_table but with a table decorator."""
    return group_result_table_no_table

experiment_result_table = collect('group_result_table', ("group_dataset_inputs_by_experiment",))

@table
def group_result_table_68cl(groups_results, group_result_table_no_table: pd.DataFrame, pdf: PDF):
    """Generate a table containing the data central value, the data 68% confidence levels, the central prediction,
    and 68% confidence level bounds of the prediction.
    """
    df = group_result_table_no_table
    # replica data is every columns after central values, transpose for stats class
    replica_data = df.iloc[:, 2:].values.T
    # Use pdf stats class but reshape output to have each row as a data point
    th_unc_array = [level.reshape(-1, 1) for level in pdf.stats_class(replica_data).errorbar68()]
    # concatenate for dataframe construction
    th_unc_array_reshaped = np.concatenate(th_unc_array, axis=1)
    data_unc_array = np.concatenate([i[0].std_error for i in groups_results])
    uncertainties_array = np.c_[data_unc_array, th_unc_array_reshaped]
    df_cl = pd.DataFrame(
        uncertainties_array,
        index=df.index,
        columns=['data uncertainty', 'theory_lower', 'theory_upper'])
    res = pd.concat([df.iloc[:, :2], df_cl], axis=1)
    return res

experiments_covmat_collection = collect(
    'dataset_inputs_covariance_matrix', ("group_dataset_inputs_by_experiment",)
    )

def experiments_covmat_no_table(
    experiments_data, experiments_index, experiments_covmat_collection):
    """Makes the total experiments covariance matrix, which can then
    be reindexed appropriately by the chosen grouping. The covariance
    matrix must first be grouped by experiments to ensure correlations
    within experiments are preserved."""
    data = np.zeros((len(experiments_index), len(experiments_index)))
    df = pd.DataFrame(data, index=experiments_index, columns=experiments_index)
    for experiment, experiment_covmat in zip(
            experiments_data, experiments_covmat_collection):
        name = experiment.name
        df.loc[[name],[name]] = experiment_covmat
    return df

def groups_covmat_no_table(
       experiments_covmat_no_table, experiments_data, groups_index):
    """Export the covariance matrix for the groups. It exports the full
    (symmetric) matrix, with the 3 first rows and columns being:

        - group name

        - dataset name

        - index of the point within the dataset.
    """
    covmat = experiments_covmat_no_table
    # Sorting along dataset axis so we can apply the groups index directly
    covmat = covmat.sort_index(axis=0, level=1)
    covmat = covmat.sort_index(axis=1, level=1)
    sorted_groups_index = groups_index.sortlevel(1)[0]
    df = pd.DataFrame(covmat.values, index=sorted_groups_index, 
                                    columns=sorted_groups_index)
    # Reindexing to fit with groups_index
    df.reindex(groups_index, axis=0)
    df.reindex(groups_index, axis=1)
    return df

@table
def groups_covmat(groups_covmat_no_table):
    """Duplicate of groups_covmat_no_table but with a table decorator."""
    return groups_covmat_no_table

groups_sqrt_covmat = collect(
    'dataset_inputs_sqrt_covmat',
    ('group_dataset_inputs_by_metadata',)
)

@table
def groups_sqrtcovmat(
        groups_data, groups_index, groups_sqrt_covmat):
    """Like groups_covmat, but dump the lower triangular part of the
    Cholesky decomposition as used in the fit. The upper part indices are set
    to zero.
    """
    data = np.zeros((len(groups_index),len(groups_index)))
    df = pd.DataFrame(data, index=groups_index, columns=groups_index)
    for group, group_sqrt_covmat in zip(
            groups_data, groups_sqrt_covmat):
        name = group.name
        group_sqrt_covmat[np.triu_indices_from(group_sqrt_covmat, k=1)] = 0
        df.loc[[name],[name]] = group_sqrt_covmat
    return df

@table
def groups_invcovmat(
        groups_data, groups_index, groups_covmat_collection):
    """Compute and export the inverse covariance matrix.
    Note that this inverts the matrices with the LU method which is
    suboptimal."""
    data = np.zeros((len(groups_index),len(groups_index)))
    df = pd.DataFrame(data, index=groups_index, columns=groups_index)
    for group, group_covmat in zip(
            groups_data, groups_covmat_collection):
        name = group.name
        #Improve this inversion if this method tuns out to be important
        invcov = la.inv(group_covmat)
        df.loc[[name],[name]] = invcov
    return df


@table
def groups_normcovmat(groups_covmat, groups_data_values):
    """Calculates the grouped experimental covariance matrix normalised to data."""
    df = groups_covmat
    groups_data_array = np.array(groups_data_values)
    mat = df/np.outer(groups_data_array, groups_data_array)
    return mat

@table
def groups_corrmat(groups_covmat):
    """Generates the grouped experimental correlation matrix with groups_covmat as input"""
    df = groups_covmat
    covmat = df.values
    diag_minus_half = (np.diagonal(covmat))**(-0.5)
    mat = diag_minus_half[:,np.newaxis]*df*diag_minus_half
    return mat

@table
def closure_pseudodata_replicas(experiments, pdf, nclosure:int,
                                experiments_index, nnoisy:int=0):
    """Generate closure pseudodata replicas from the given pdf.

    nclosure: Number of Level 1 pseudodata replicas.

    nnoisy:   Number of Level 2 replicas generated out of each pseudodata replica.

    The columns of the table are of the form (clos_0, noise_0_n0 ..., clos_1, ...)
    """

    #TODO: Do this somewhere else
    from NNPDF import RandomGenerator
    RandomGenerator.InitRNG(0,0)
    data = np.zeros((len(experiments_index), nclosure*(1+nnoisy)))

    cols = []
    for i in range(nclosure):
        cols += ['clos_%04d'%i, *['noise_%04d_%04d'%(i,j) for j in range(nnoisy)]]


    loaded_pdf = pdf.load()

    for exp in experiments:
        #Since we are going to modify the experiments, we copy them
        #(and work on the copies) to avoid all
        #sorts of weirdness with other providers. We don't want this to interact
        #with DataGroupSpec at all, because it could do funny things with the
        #cache when calling load(). We need to copy this yet again, for each
        # of the noisy replicas.
        closure_exp = Experiment(exp.load())

        #TODO: This is probably computed somewhere else... All this code is
        #very error prone.
        #The predictions are for the unmodified experiment.
        predictions = [ThPredictions(loaded_pdf, d.load()) for d in exp]


        exp_location = experiments_index.get_loc(closure_exp.GetExpName())

        index = itertools.count()
        for i in range(nclosure):
            #Generate predictions with experimental noise, a different for
            #each closure set.
            closure_exp.MakeClosure(predictions, True)
            data[exp_location, next(index)] = closure_exp.get_cv()
            for j in range(nnoisy):
                #If we don't copy, we generate noise on top of the noise,
                #which is not what we want.
                replica_exp = Experiment(closure_exp)
                replica_exp.MakeReplica()

                data[exp_location, next(index)] = replica_exp.get_cv()


    df = pd.DataFrame(data, index=experiments_index,
                      columns=cols)

    return df


def results(
        dataset:(DataSetSpec),
        pdf:PDF,
        covariance_matrix,
        sqrt_covmat
    ):
    """Tuple of data and theory results for a single pdf. The data will have an associated
    covariance matrix, which can include a contribution from the theory covariance matrix which
    is constructed from scale variation. The inclusion of this covariance matrix by default is used
    where available, however this behaviour can be modified with the flag `use_theorycovmat`.

    The theory is specified as part of the dataset.
    A group of datasets is also allowed.
    (as a result of the C++ code layout)."""
    data = dataset.load()
    return (DataResult(data, covariance_matrix, sqrt_covmat),
            ThPredictionsResult.from_convolution(pdf, dataset, loaded_data=data))

def get_shifted_results(results, commondata, cutlist):
    """Returns the theory results shifted according to correlated experimental uncertainties.

    Parameters
    ----------
    results: tuple 
        A tuple of data and theory results where the theory results' central values are 
        shifted according to the paper: arXiv:1709.04922. These shifts encapsulates the 
        impact of correlated experimental uncertainties.
    commondata : ``CommonDataSpec``
        The specification corresponfing to the commondata to be plotted.
    cutlist : list
        The list of ``CutSpecs`` or ``None`` corresponding to the cuts for each
        result.

    Returns
    -------
    results: tuple 
        A tuple of data and theory results where the theory results' central values are 
        shifted according to the paper: arXiv:1709.04922. These shifts encapsulates the 
        impact of correlated experimental uncertainties.
    shifted: list 
        A list of booleans indicating which datasets have been shifted. Note: the datasets with 
        uncorrelated uncertainties doesn't include the correlated shifts."""

    shifted = []

    cd = commondata.load()

    ## fill uncertainties
    Ndat, Nsys = cd.GetNData(), cd.GetNSys()

    # square root of sum of uncorrelated uncertainties
    uncorrE = np.zeros(Ndat)
    corrE = np.zeros((Ndat, Nsys))  # table of all the correlated uncertainties

    for idat in range(Ndat):
        uncorrE[idat] = cd.GetUncE(idat)
        for isys in range(Nsys):
            if cd.GetSys(idat, isys).name != "UNCORR":
                corrE[idat, isys] = cd.GetSys(idat, isys).add

    mask = cut_mask(cutlist[0])
    uncorrE = uncorrE[mask]
    corrE = corrE[mask]
    data = results[0].central_value

    for i, result in enumerate(results):
        if i == 0:
            continue

        lambda_sys = np.zeros(Nsys)  # nuisance parameters
        theory = results[i].central_value

        ## isys is equivalent to alpha index and lsys to delta in eq.85
        if np.any(uncorrE == 0):
            temp_shifts = np.zeros(Ndat)
            shifted.append(False)
        else:
            f1 = (data - theory)/uncorrE  # first part of eq.85
            A = np.eye(Nsys) + \
                np.einsum('ik,il,i->kl', corrE, corrE, 1./uncorrE**2)  # eq.86
            f2 = np.einsum('kl,il,i->ik', np.linalg.inv(A),
                           corrE, 1./uncorrE)  # second part of eq.85
            lambda_sys = np.einsum('i,ik->k', f1, f2)  # nuisance parameter
            shifts = np.einsum('ik,k->i', corrE, lambda_sys)  # the shift

            results[i]._central_value += shifts
            shifted.append(True)

    #now that theory is shifted, take only the uncorr component of the uncertainty in the data
    if any(shifted):
        results[0].covmat[np.diag_indices_from(results[0].covmat)] = uncorrE**2

    return results, shifted

def dataset_inputs_results(
        data,
        pdf:PDF,
        dataset_inputs_covariance_matrix,
        dataset_inputs_sqrt_covmat):
    """Like `results` but for a group of datasets"""
    return results(
        data,
        pdf,
        dataset_inputs_covariance_matrix,
        dataset_inputs_sqrt_covmat
        )

#It's better to duplicate a few lines than to complicate the logic of
#``results`` to support this.
#TODO: The above comment doesn't make sense after adding T0. Deprecate this
def pdf_results(
        dataset:(DataSetSpec,  DataGroupSpec),
        pdfs:Sequence,
        covariance_matrix,
        sqrt_covmat):
    """Return a list of results, the first for the data and the rest for
    each of the PDFs."""

    data = dataset.load()
    th_results = []
    for pdf in pdfs:
        th_result = ThPredictionsResult.from_convolution(pdf, dataset,
                                                         loaded_data=data)
        th_results.append(th_result)


    return (DataResult(data, covariance_matrix, sqrt_covmat), *th_results)

@require_one('pdfs', 'pdf')
@remove_outer('pdfs', 'pdf')
def one_or_more_results(dataset:(DataSetSpec, DataGroupSpec),
                        covariance_matrix,
                        sqrt_covmat,
                        pdfs:(type(None), Sequence)=None,
                        pdf:(type(None), PDF)=None):
    """Generate a list of results, where the first element is the data values,
    and the next is either the prediction for pdf or for each of the pdfs.
    Which of the two is selected intelligently depending on the namespace,
    when executing as an action."""
    if pdf:
        return results(dataset, pdf, covariance_matrix, sqrt_covmat)
    else:
        return pdf_results(dataset, pdfs, covariance_matrix, sqrt_covmat)
    raise ValueError("Either 'pdf' or 'pdfs' is required")


Chi2Data = namedtuple('Chi2Data', ('replica_result', 'central_result', 'ndata'))

def abs_chi2_data(results):
    """Return a tuple (member_chi², central_chi², numpoints) for a
    given dataset"""
    data_result, th_result = results

    chi2s = all_chi2(results)

    central_result = central_chi2(results)

    return Chi2Data(th_result.stats_class(chi2s[:, np.newaxis]),
                    central_result, len(data_result))


def dataset_inputs_abs_chi2_data(dataset_inputs_results):
    """Like `abs_chi2_data` but for a group of inputs"""
    return abs_chi2_data(dataset_inputs_results)

def phi_data(abs_chi2_data):
    """Calculate phi using values returned by `abs_chi2_data`.

    Returns tuple of (phi, numpoints)

    For more information on how phi is calculated see Eq.(24) in
    1410.8849
    """
    alldata, central, npoints = abs_chi2_data
    return (np.sqrt((alldata.data.mean() - central)/npoints), npoints)

def dataset_inputs_phi_data(dataset_inputs_abs_chi2_data):
    """Like `phi_data` but for group of datasets"""
    return phi_data(dataset_inputs_abs_chi2_data)

@check_pdf_is_montecarlo
def dataset_inputs_bootstrap_phi_data(
    dataset_inputs_results, bootstrap_samples=500
):
    """Takes the data result and theory prediction given `dataset_inputs` and
    then returns a bootstrap distribution of phi.
    By default `bootstrap_samples` is set to a sensible value (500). However
    a different value can be specified in the runcard.

    For more information on how phi is calculated see `phi_data`
    """
    dt, th = dataset_inputs_results
    diff = np.array(th._rawdata - dt.central_value[:, np.newaxis])
    phi_resample = bootstrap_values(diff, bootstrap_samples,
                                    apply_func=(lambda x, y: calc_phi(y, x)),
                                    args=[dt.sqrtcovmat])
    return phi_resample

@check_pdf_is_montecarlo
def dataset_inputs_bootstrap_chi2_central(dataset_inputs_results, bootstrap_samples=500,
                                      boot_seed=123):
    """Takes the data result and theory prediction given dataset_inputs and
    then returns a bootstrap distribution of central chi2.
    By default `bootstrap_samples` is set to a sensible value (500). However
    a different value can be specified in the runcard.
    """
    dt, th = dataset_inputs_results
    diff = np.array(th._rawdata - dt.central_value[:, np.newaxis])
    cchi2 = lambda x, y: calc_chi2(y, x.mean(axis=1))
    chi2_central_resample = bootstrap_values(diff, bootstrap_samples, boot_seed=boot_seed,
                                             apply_func=(cchi2), args=[dt.sqrtcovmat])
    return chi2_central_resample

#TODO: deprecate this function?
def chi2_breakdown_by_dataset(experiment_results, experiment, t0set,
                              prepend_total:bool=True,
                              datasets_sqrtcovmat=None) -> dict:
    """Return a dict with the central chi² of each dataset in the experiment,
    by breaking down the experiment results. If ``prepend_total`` is True.
    """
    dt, th = experiment_results
    sqrtcovmat = dt.sqrtcovmat
    central_diff = th.central_value - dt.central_value
    d = {}
    if prepend_total:
        d['Total'] = (calc_chi2(sqrtcovmat, central_diff), len(sqrtcovmat))


    #Allow lower level access useful for pseudodata and such.
    #TODO: This is a hack and we should get rid of it.
    if isinstance(experiment, Experiment):
        loaded_exp = experiment
    else:
        loaded_exp = experiment.load()

    #TODO: This is horrible. find a better way to do it.
    if t0set:
        loaded_exp = type(loaded_exp)(loaded_exp)
        loaded_exp.SetT0(t0set.load_T0())

    indmin = indmax = 0

    if datasets_sqrtcovmat is None:
        datasets_sqrtcovmat = (ds.get_sqrtcovmat() for ds in loaded_exp.DataSets())

    for ds, mat  in zip(loaded_exp.DataSets(), datasets_sqrtcovmat):
        indmax += len(ds)
        d[ds.GetSetName()] = (calc_chi2(mat, central_diff[indmin:indmax]), len(mat))
        indmin = indmax
    return d

def _chs_per_replica(chs):
    th, _, l = chs
    return th.data.ravel()/l


@table
def groups_chi2_table(groups_data, pdf, groups_chi2,
                           each_dataset_chi2):
    """Return a table with the chi² to the groups and each dataset in
    the groups."""
    dschi2 = iter(each_dataset_chi2)
    records = []
    for group, groupres in zip(groups_data, groups_chi2):
        stats = chi2_stats(groupres)
        stats['group'] = group.name
        records.append(stats)
        for dataset, dsres in zip(group, dschi2):
            stats = chi2_stats(dsres)
            stats['group'] = dataset.name
            records.append(stats)
    return pd.DataFrame(records)

experiments_chi2_table = collect('groups_chi2_table', ("group_dataset_inputs_by_experiment",))

@check_cuts_considered
@table
def closure_shifts(experiments_index, fit, use_cuts, experiments):
    """Save the differenve between the fitted data and the real commondata
    values.

    Actually shifts is what should be saved in the first place, rather than
    thi confusing fiddling with Commondata, but until we can implement this at
    the C++ level, we just dave it here.
    """
    name, fitpath = fit
    result = np.zeros(len(experiments_index))
    for experiment in experiments:
        for dataset in experiment:
            dspath = fitpath/'filter'/dataset.name
            cdpath = dspath/("DATA_" + dataset.name + ".dat")
            try:
                syspath = next( (dspath/'systypes').glob('*.dat'))
            except StopIteration as e:
                raise FileNotFoundError("No systype "
                "file found in filter folder %s" % (dspath/'systypes')) from e
            cd = CommonData.ReadFile(str(cdpath), str(syspath))
            loc = experiments_index.get_loc((experiment.name, dataset.name))
            result[loc] = cd.get_cv() - dataset.load().get_cv()
    return pd.DataFrame(result, index=experiments_index)


def positivity_predictions_data_result(pdf, posdataset):
    """Return an object containing the values of the positivuty observable."""
    return PositivityResult.from_convolution(pdf, posdataset)

positivity_predictions_for_pdfs = collect(positivity_predictions_data_result, ('pdfs',))

def count_negative_points(possets_predictions):
    """Return the number of replicas with negative predictions for each bin
    in the positivity observable."""
    return np.sum([(r.rawdata < 0).sum(axis=1) for r in possets_predictions], axis=0)


chi2_stat_labels = {
    'central_mean': r'$<\chi^2_{0}>_{data}$',
    'npoints': r'$N_{data}$',
    'perreplica_mean': r'$\left< \chi^2 \right>_{rep,data}$',
    'perreplica_std': r'$\left<std_{rep}(\chi^2)\right>_{data}$',
    'chi2_per_data': r'$\frac{\chi^2}{N_{data}}$'
}

def experiments_chi2_stats(total_experiments_chi2data):
    """Compute several estimators from the chi² for an
    aggregate of experiments:

     - central_mean

     - npoints

     - perreplica_mean

     - perreplica_std

     - chi2_per_data
    """
    rep_data, central_result, npoints = total_experiments_chi2data
    m = central_result.mean()
    rep_mean = rep_data.central_value().mean()
    return OrderedDict([
            ('central_mean'        ,  m),
            ('npoints'             , npoints),
            ('chi2_per_data', m/npoints),
            ('perreplica_mean', rep_mean),
            ('perreplica_std',  rep_data.std_error().mean()),
           ])

def chi2_stats(abs_chi2_data):
    """Compute several estimators from the chi²:

     - central_mean

     - npoints

     - perreplica_mean

     - perreplica_std

     - chi2_per_data
    """
    rep_data, central_result, npoints = abs_chi2_data
    m = central_result.mean()
    rep_mean = rep_data.central_value().mean()
    return OrderedDict([
            ('central_mean'        ,  m),
            ('npoints'             , npoints),
            ('chi2_per_data', m/npoints),
            ('perreplica_mean', rep_mean),
            ('perreplica_std',  rep_data.std_error().mean()),
           ])


@table
def dataset_chi2_table(chi2_stats, dataset):
    """Show the chi² estimators for a given dataset"""
    return pd.DataFrame(chi2_stats, index=[dataset.name])

groups_chi2 = collect("dataset_inputs_abs_chi2_data", ("group_dataset_inputs_by_metadata",))

fits_groups_chi2_data = collect("groups_chi2", ("fits", "fitcontext"))
fits_groups = collect(
    "groups_data", ("fits", "fitcontext",)
)


#TODO: Possibly get rid of the per_point_data parameter and have separate
#actions for absolute and relative tables.
@table
def fits_groups_chi2_table(
    fits_name_with_covmat_label,
    fits_groups,
    fits_groups_chi2_data,
    per_point_data: bool = True,
):
    """A table with the chi2 computed with the theory corresponding to each fit
    for all datasets in the fit, grouped according to a key in the metadata, the
    grouping can be controlled with `metadata_group`.

    If points_per_data is True, the chi² will be shown divided by ndata.
    Otherwise chi² values will be absolute.

    """
    dfs = []
    cols = ("ndata", r"$\chi^2/ndata$") if per_point_data else ("ndata", r"$\chi^2$")
    for label, groups, groups_chi2 in zip(
        fits_name_with_covmat_label, fits_groups, fits_groups_chi2_data
    ):
        records = []
        for group, group_chi2 in zip(groups, groups_chi2):
            mean_chi2 = group_chi2.central_result.mean()
            npoints = group_chi2.ndata
            records.append(dict(group=str(group), npoints=npoints, mean_chi2=mean_chi2))
        df = pd.DataFrame.from_records(
            records, columns=("group", "npoints", "mean_chi2"), index=("group",)
        )
        if per_point_data:
            df["mean_chi2"] /= df["npoints"]
        df.columns = pd.MultiIndex.from_product(([label], cols))
        dfs.append(df)
    res = pd.concat(dfs, axis=1)
    return res

groups_phi = collect("dataset_inputs_phi_data", ("group_dataset_inputs_by_metadata",))
fits_groups_phi = collect("groups_phi", ("fits", "fitcontext"))


@table
def fits_groups_phi_table(
    fits_name_with_covmat_label, fits_groups, fits_groups_phi
):
    """For every fit, returns phi and number of data points for each group of
    datasets, which are grouped according to a key in the metadata. The behaviour
    of the grouping can be controlled with `metadata_group` runcard key.

    """
    dfs = []
    cols = ("ndata", r"$\phi$")
    for label, groups, groups_phi in zip(
        fits_name_with_covmat_label, fits_groups, fits_groups_phi
    ):
        records = []
        for group, (group_phi, npoints) in zip(groups, groups_phi):
            records.append(dict(group=str(group), npoints=npoints, phi=group_phi))
        df = pd.DataFrame.from_records(
            records, columns=("group", "npoints", "phi"), index=("group",)
        )
        df.columns = pd.MultiIndex.from_product(([label], cols))
        dfs.append(df)
    res = pd.concat(dfs, axis=1)
    return res


@table
@check_speclabels_different
def dataspecs_groups_chi2_table(
    dataspecs_speclabel,
    dataspecs_groups,
    dataspecs_groups_chi2_data,
    per_point_data: bool = True,
):
    """Same as fits_groups_chi2_table but for an arbitrary list of dataspecs."""
    return fits_groups_chi2_table(
        dataspecs_speclabel,
        dataspecs_groups,
        dataspecs_groups_chi2_data,
        per_point_data=per_point_data,
    )

# we need this to reorder the datasets correctly, a potentially more satisfactory
# method could be to make a datasets chi2 table which gets collected and concatenated
groups_datasets_chi2_data = collect(
    "each_dataset_chi2", ("group_dataset_inputs_by_metadata",)
)
fits_datasets_chi2_data = collect("groups_datasets_chi2_data", ("fits", "fitcontext"))


@table
def fits_datasets_chi2_table(
    fits_name_with_covmat_label,
    fits_groups,
    fits_datasets_chi2_data,
    per_point_data: bool = True,
):
    """A table with the chi2 for each included dataset in the fits, computed
    with the theory corresponding to the fit. The result are indexed in two
    levels by experiment and dataset, where experiment is the grouping of datasets according to the
    `experiment` key in the PLOTTING info file.  If points_per_data is True, the chi² will be shown
    divided by ndata. Otherwise they will be absolute."""

    cols = ("ndata", r"$\chi^2/ndata$") if per_point_data else ("ndata", r"$\chi^2$")

    dfs = []
    for label, groups, groups_dsets_chi2 in zip(
        fits_name_with_covmat_label, fits_groups, fits_datasets_chi2_data
    ):
        records = []
        for group, dsets_chi2 in zip(groups, groups_dsets_chi2):
            for dataset, chi2 in zip(group.datasets, dsets_chi2):
                ndata = chi2.ndata

                records.append(
                    dict(
                        group=str(group),
                        dataset=str(dataset),
                        npoints=ndata,
                        mean_chi2=chi2.central_result.mean(),
                    )
                )

        df = pd.DataFrame.from_records(
            records,
            columns=("group", "dataset", "npoints", "mean_chi2"),
            index=("group", "dataset"),
        )
        if per_point_data:
            df["mean_chi2"] /= df["npoints"]
        df.columns = pd.MultiIndex.from_product(([label], cols))
        dfs.append(df)
    return pd.concat(dfs, axis=1)

dataspecs_datasets_chi2_data = collect("groups_datasets_chi2_data", ("dataspecs",))


@table
@check_speclabels_different
def dataspecs_datasets_chi2_table(
    dataspecs_speclabel,
    dataspecs_groups,
    dataspecs_datasets_chi2_data,
    per_point_data: bool = True,
):
    """Same as fits_datasets_chi2_table but for arbitrary dataspecs."""
    return fits_datasets_chi2_table(
        dataspecs_speclabel,
        dataspecs_groups,
        dataspecs_datasets_chi2_data,
        per_point_data=per_point_data,
    )


fits_total_chi2_data = collect('dataset_inputs_abs_chi2_data', ('fits', 'fitcontext'))
dataspecs_total_chi2_data = collect('dataset_inputs_abs_chi2_data', ('dataspecs',))

#TODO: Decide what to do with the horrible totals code.
@table
def fits_chi2_table(
        fits_total_chi2_data,
        fits_datasets_chi2_table,
        fits_groups_chi2_table,
        show_total:bool=False):
    """Show the chi² of each and number of points of each dataset and experiment
    of each fit, where experiment is a group of datasets according to the `experiment` key in
    the PLOTTING info file, computed with the theory corresponding to the fit. Dataset that are not
    included in some fit appear as `NaN`
    """
    lvs = fits_groups_chi2_table.index
    #The explicit call to list is because pandas gets confused otherwise
    expanded_index = pd.MultiIndex.from_product((list(lvs), ["Total"]))
    edf = fits_groups_chi2_table.set_index(expanded_index)
    ddf = fits_datasets_chi2_table
    dfs = []
    #TODO: Better way to do the merge preserving the order?
    for lv in lvs:
        dfs.append(pd.concat((edf.loc[lv],ddf.loc[lv]), copy=False, axis=0))
    if show_total:
        total_points = np.array(
            [total_chi2_data.ndata for total_chi2_data in fits_total_chi2_data])
        total_chi = np.array(
            [total_chi2_data.central_result for total_chi2_data in fits_total_chi2_data])
        total_chi /= total_points
        row = np.zeros(len(total_points)*2)
        row[::2] = total_points
        row[1::2] = total_chi
        df = pd.DataFrame(np.atleast_2d(row),
                          columns=fits_groups_chi2_table.columns,
                          index=['Total'])
        dfs.append(df)
        keys = [*lvs, 'Total']
    else:
        keys = lvs

    res = pd.concat(dfs, axis=0, keys=keys)
    return res

@table
def dataspecs_chi2_table(
    dataspecs_total_chi2_data,
    dataspecs_datasets_chi2_table,
    dataspecs_groups_chi2_table,
    show_total: bool = False,
):
    """Same as fits_chi2_table but for an arbitrary list of dataspecs"""
    return fits_chi2_table(
        dataspecs_total_chi2_data,
        dataspecs_datasets_chi2_table,
        dataspecs_groups_chi2_table,
        show_total,
    )


@table
@check_two_dataspecs
def dataspecs_chi2_differences_table(dataspecs, dataspecs_chi2_table):
    """Given two dataspecs, print the chi² (using dataspecs_chi2_table)
    and the difference between the first and the second."""
    df = dataspecs_chi2_table.copy()
    #TODO: Make this mind the number of points somehow
    diff = df.iloc[:,1] - df.iloc[:,3]
    df['difference'] = diff
    return df


def dataset_inputs_chi2_per_point_data(dataset_inputs_abs_chi2_data):
    """Return the total chi²/ndata for all data, specified by dataset_inputs.
    Covariance matrix is fully correlated across datasets, with all known
    correlations.
    """
    return (
        dataset_inputs_abs_chi2_data.central_result / dataset_inputs_abs_chi2_data.ndata
    )


def total_experiments_chi2(dataset_inputs_chi2_per_point_data):
    return dataset_inputs_chi2_per_point_data


@table
@check_not_empty("groups_data")
def perreplica_chi2_table(groups_data, groups_chi2, dataset_inputs_abs_chi2_data):
    """Chi² per point for each replica for each group.
    Also outputs the total chi² per replica.
    The columns come in two levels: The first is the name of the group,
    and the second is the number of points."""

    chs = groups_chi2
    total_chis = np.zeros(
        (len(groups_data) + 1, 1 + len(chs[0].replica_result.error_members()))
    )
    ls = []
    for i, ch in enumerate(chs, 1):
        th, central, l = ch
        total_chis[i] = [central, *th.error_members()]
        ls.append(l)
    total_rep, total_central, total_n = dataset_inputs_abs_chi2_data
    total_chis[0] = [total_central, *total_rep.error_members()]
    total_chis[0] /= total_n
    total_chis[1:, :] /= np.array(ls)[:, np.newaxis]

    columns = pd.MultiIndex.from_arrays(
        (["Total", *[str(exp) for exp in groups_data]], [total_n, *ls]),
        names=["name", "npoints"],
    )
    return pd.DataFrame(total_chis.T, columns=columns)


@table
def theory_description(theoryid):
    """A table with the theory settings."""
    return pd.DataFrame(pd.Series(theoryid.get_description()), columns=[theoryid])

def groups_central_values_no_table(group_result_table_no_table):
    """Returns a theoryid-dependent list of central theory predictions
    for a given group."""
    central_theory_values = group_result_table_no_table["theory_central"]
    return central_theory_values

@table
def groups_central_values(group_result_table):
    """Duplicate of groups_central_values_no_table but takes
    group_result_table rather than groups_central_values_no_table,
    and has a table decorator."""
    central_theory_values = group_result_table["theory_central"]
    return central_theory_values

dataspecs_each_dataset_chi2 = collect("each_dataset_chi2", ("dataspecs",))
each_dataset = collect("dataset", ("data",))
dataspecs_each_dataset = collect("each_dataset", ("dataspecs",))

@table
@check_speclabels_different
def dataspecs_dataset_chi2_difference_table(
    dataspecs_each_dataset, dataspecs_each_dataset_chi2, dataspecs_speclabel):
    r"""Returns a table with difference between the chi2 and the expected chi2
    in units of the expected chi2 standard deviation, given by

        chi2_diff = (\chi2 - N)/sqrt(2N)

    for each dataset for each dataspec.

    """
    dfs = []
    cols = [r"$(\chi^2 - N)/\sqrt{2N}$"]
    for label, datasets, chi2s in zip(
        dataspecs_speclabel, dataspecs_each_dataset, dataspecs_each_dataset_chi2):
        records = []
        for dataset, chi2 in zip(datasets, chi2s):
            ndata = chi2.ndata

            records.append(dict(
                dataset=str(dataset),
                chi2_stat = (chi2.central_result.mean() - ndata)/np.sqrt(2*ndata)
            ))


        df = pd.DataFrame.from_records(records,
                columns=("dataset", "chi2_stat"),
                index = ("dataset",)
            )
        df.columns = pd.MultiIndex.from_product(([label], cols))
        dfs.append(df)
    return pd.concat(dfs, axis=1)

each_dataset_chi2 = collect(abs_chi2_data, ('data',))

pdfs_total_chi2 = collect(dataset_inputs_chi2_per_point_data, ('pdfs',))

#These are convenient ways to iterate and extract varios data from fits
fits_chi2_data = collect(abs_chi2_data, ('fits', 'fitcontext', 'dataset_inputs'))

fits_total_chi2 = collect('dataset_inputs_chi2_per_point_data', ('fits', 'fitcontext'))

fits_total_chi2_for_groups = collect('dataset_inputs_chi2_per_point_data',
                                          ('fits', 'fittheoryandpdf'))

fits_pdf = collect('pdf', ('fits', 'fitpdf'))


groups_data_phi = collect(dataset_inputs_phi_data, ('group_dataset_inputs_by_metadata',))
groups_bootstrap_phi = collect(dataset_inputs_bootstrap_phi_data, ("group_dataset_inputs_by_metadata",))

#Dataspec is so
dataspecs_groups = collect("groups_data", ("dataspecs",))
dataspecs_groups_chi2_data = collect("groups_chi2", ("dataspecs",))
dataspecs_groups_bootstrap_phi = collect('groups_bootstrap_phi', ('dataspecs',))
dataspecs_results = collect('results', ('dataspecs',))
dataspecs_total_chi2 = collect('dataset_inputs_chi2_per_point_data', ('dataspecs',))

dataspecs_speclabel = collect('speclabel', ('dataspecs',), element_default=None)
dataspecs_cuts = collect('cuts', ('dataspecs',))
dataspecs_experiments = collect('experiments', ('dataspecs',))
dataspecs_dataset = collect('dataset', ('dataspecs',))
dataspecs_commondata = collect('commondata', ('dataspecs',))
dataspecs_pdf = collect('pdf', ('dataspecs',))
dataspecs_fit = collect('fit', ('dataspecs',))
