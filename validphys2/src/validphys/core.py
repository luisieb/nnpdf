# -*- coding: utf-8 -*-
"""
Core datastructures used in the validphys data model. Some of these are inmutable
specifications representing C++ objects.
Created on Wed Mar  9 15:19:52 2016

@author: Zahari Kassabov
"""
from __future__ import generator_stop

from collections import namedtuple
import re
import enum
import functools
import inspect
import json
import logging

import numpy as np

from reportengine import namespaces
from reportengine.baseexceptions import AsInputError
from reportengine.compat import yaml

from NNPDF import (LHAPDFSet,
    CommonData,
    FKTable,
    FKSet,
    DataSet,
    Experiment,
    PositivitySet,)

#TODO: There is a bit of a circular dependency between filters.py and this.
#Maybe move the cuts logic to its own module?
from validphys import lhaindex, filters
from validphys.tableloader import parse_exp_mat
from validphys.theorydbutils import fetch_theory
from validphys.hyperoptplot import HyperoptTrial
from validphys.utils import experiments_to_dataset_inputs

log = logging.getLogger(__name__)


#TODO: Remove this eventually
#Bacward compatibility error type names
#Swig renamed these for no reason whatsoever.
try:
    LHAPDFSet.erType_ER_EIG
except AttributeError:
    import warnings
    warnings.warn("libnnpdf out of date. Setting backwards compatible names")
    LHAPDFSet.erType_ER_MC = LHAPDFSet.ER_MC
    LHAPDFSet.erType_ER_EIG = LHAPDFSet.ER_EIG
    LHAPDFSet.erType_ER_EIG90 = LHAPDFSet.ER_EIG90
    LHAPDFSet.erType_ER_SYMEIG = LHAPDFSet.ER_SYMEIG

class TupleComp:

    @classmethod
    def argnames(cls):
        return list(inspect.signature(cls.__init__).parameters.keys())[1:]

    def __init__(self, *args, **kwargs):
        self.comp_tuple = (*args, *kwargs.values())

    def __eq__(self, other):
        return self.comp_tuple == other.comp_tuple

    def __hash__(self):
        return hash(self.comp_tuple)

    def __repr__(self):
        argvals = ', '.join('%s=%r'%vals for vals in zip(self.argnames(),
                                                         self.comp_tuple))
        return '%s(%s)'%(self.__class__.__qualname__, argvals)

class PDFDoesNotExist(Exception): pass

class _PDFSETS():
    """Convenient way to access installed PDFS, by e.g. tab completing
       in ipython."""
    def __getattr__(self, attr):
        if lhaindex.isinstalled(attr):
            return PDF(attr)
        raise AttributeError()

    def __dir__(self):
        return lhaindex.expand_local_names('*')


PDFSETS = _PDFSETS()

class PDF(TupleComp):

    def __init__(self, name):
        self.name = name
        self._plotname = name
        super().__init__(name)


    def __getattr__(self, attr):
        #We don't even try to get reserved attributes from the info file
        if attr.startswith('__'):
            raise AttributeError(attr)
        try:
            return lhaindex.parse_info(self.name)[attr]
        except KeyError as e:
            raise AttributeError("'%r' has no attribute '%s'" % (type(self),
                                                                 attr)) from e
        except IOError as e:
            raise PDFDoesNotExist(self.name) from e

    @property
    def label(self):
        return self._plotname

    @label.setter
    def label(self, label):
        self._plotname = label

    @property
    def stats_class(self):
        """Return the stats calculator for this error type"""
        error = self.ErrorType
        klass = STAT_TYPES[error]
        if hasattr(self, 'ErrorConfLevel'):
            klass = functools.partial(klass, rescale_factor=self.rescale_factor)
        return klass

    #TODO: Make this a proper Path
    @property
    def infopath(self):
        return lhaindex.infofilename(self.name)

    @property
    def isinstalled(self):
        try:
            self.infopath
        except FileNotFoundError:
            return False
        else:
            return True


    @property
    def rescale_factor(self):
        #This is imported here for performance reasons.
        import scipy.stats
        if hasattr(self, "ErrorConfLevel"):
            if self.ErrorType == 'replicas':
                raise ValueError("Attribute at %s 'ErrorConfLevel' doesn't "
                "make sense with 'replicas' error type" % self.infopath)
            val = scipy.stats.norm.isf((1 - 0.01*self.ErrorConfLevel)/2)
            if np.isnan(val):
                raise ValueError("Invalid 'ErrorConfLevel' of PDF %s: %s" %
                                 (self, val))
            return val
        else:
            return 1

    @functools.lru_cache(maxsize=16)
    def load(self):
        return LHAPDFSet(self.name, self.nnpdf_error)

    @functools.lru_cache(maxsize=2)
    def load_t0(self):
        """Load the PDF as a t0 set"""
        return LHAPDFSet(self.name, LHAPDFSet.erType_ER_MCT0)


    def __str__(self):
        return self.label

    def __len__(self):
        return self.NumMembers



    @property
    def nnpdf_error(self):
        """Return the NNPDF error tag, used to build the `LHAPDFSet` objeect"""
        error = self.ErrorType
        if error == "replicas":
            return LHAPDFSet.erType_ER_MC
        if error == "hessian":
            if hasattr(self, 'ErrorConfLevel'):
                cl = self.ErrorConfLevel
                if cl == 90:
                    return LHAPDFSet.erType_ER_EIG90
                elif cl == 68:
                    return LHAPDFSet.erType_ER_EIG
                else:
                    raise NotImplementedError("No hessian errors with confidence"
                                              " interval %s" % (cl,) )
            else:
                return LHAPDFSet.erType_ER_EIG

        if error == "symmhessian":
            if hasattr(self, 'ErrorConfLevel'):
                cl = self.ErrorConfLevel
                if cl == 68:
                    return LHAPDFSet.erType_ER_SYMEIG
                else:
                    raise NotImplementedError("No symmetric hessian errors "
                                              "with confidence"
                                              " interval %s" % (cl,) )
            else:
                return LHAPDFSet.erType_ER_SYMEIG

        raise NotImplementedError("Error type for %s: '%s' is not implemented" %
                                  (self.name, error))

    @property
    def grid_values_index(self):
        """A range object describing which members are selected in a
        ``pdf.load().grid_values`` operation.  This is ``range(1,
        len(pdf))`` for Monte Carlo sets, because replica 0 is not selected
        and ``range(0, len(pdf))`` for hessian sets.


        Returns
        -------
        index : range
            A range object describing the proper indexing.

        Notes
        -----
        The range object can be used efficiently as a Pandas index.
        """
        err = self.nnpdf_error
        if err is LHAPDFSet.erType_ER_MC:
            return range(1, len(self))
        elif err in (LHAPDFSet.erType_ER_SYMEIG, LHAPDFSet.erType_ER_EIG, LHAPDFSet.erType_ER_EIG90):
            return range(0, len(self))
        else:
            raise RuntimeError("Unknown error type")

    def get_members(self):
        """Return the number of members selected in ``pdf.load().grid_values``
        operation. See :py:meth:`PDF.grid_values_index` for details on differences
        between types of PDF sets.
        """
        return len(self.grid_values_index)



kinlabels_latex = CommonData.kinLabel_latex.asdict()
_kinlabels_keys = sorted(kinlabels_latex, key=len, reverse=True)



def get_plot_kinlabels(commondata):
    """Return the LaTex kinematic labels for a given Commondata"""
    key = commondata.process_type

    return kinlabels_latex[key]

def get_kinlabel_key(process_label):
    #Since there is no 1:1 correspondence between latex keys and GetProc,
    #we match the longest key such that the proc label starts with it.
    l = process_label
    try:
        return next(k for k in _kinlabels_keys if l.startswith(k))
    except StopIteration as e:
        raise ValueError("Could not find a set of kinematic "
                         "variables matching  the process %s Check the "
                         "labels defined in commondata.cc. " % (l)) from e

CommonDataMetadata = namedtuple('CommonDataMetadata', ('name', 'nsys', 'ndata', 'process_type'))

def peek_commondata_metadata(commondatafilename):
    """Check some basic properties commondata object without going though the
    trouble of processing it on the C++ side"""
    with open(commondatafilename) as f:
        try:
            l = f.readline()
            name, nsys_str, ndata_str = l.split()
            l = f.readline()
            process_type_str = l.split()[1]
        except Exception:
            log.error(f"Error processing {commondatafilename}")
            raise

    return CommonDataMetadata(name, int(nsys_str), int(ndata_str),
                              get_kinlabel_key(process_type_str))


class CommonDataSpec(TupleComp):
    def __init__(self, datafile, sysfile, plotfiles, name=None, metadata=None):
        self.datafile = datafile
        self.sysfile = sysfile
        self.plotfiles = tuple(plotfiles)
        self._name=name
        self._metadata = metadata
        super().__init__(datafile, sysfile, self.plotfiles)

    @property
    def name(self):
        return self.metadata.name

    @property
    def nsys(self):
        return self.metadata.nsys

    @property
    def ndata(self):
        return self.metadata.ndata

    @property
    def process_type(self):
        return self.metadata.process_type

    @property
    def metadata(self):
        if self._metadata is None:
            self._metadata = peek_commondata_metadata(self.datafile)
        return self._metadata

    def __str__(self):
        return self.name

    def __iter__(self):
        return iter((self.datafile, self.sysfile, self.plotfiles))

    @functools.lru_cache()
    def load(self)->CommonData:
        #TODO: Use better path handling in python 3.6
        return CommonData.ReadFile(str(self.datafile), str(self.sysfile))

    @property
    def plot_kinlabels(self):
        return get_plot_kinlabels(self)


class DataSetInput(TupleComp):
    """Represents whatever the user enters in the YAML to specidy a
    dataset."""
    def __init__(self, *, name, sys, cfac, frac, weight, custom_group):
        self.name=name
        self.sys=sys
        self.cfac = cfac
        self.frac = frac
        self.weight = weight
        self.custom_group = custom_group
        super().__init__(name, sys, cfac, frac, weight, custom_group)

    def __str__(self):
        return self.name

class ExperimentInput(TupleComp):
    def __init__(self, *, name, datasets):
        self.name = name
        self.datasets = datasets
        super().__init__(name, datasets)

    def as_dict(self):
        return {'experiment':self.name, 'datasets':self.datasets}

    def __str__(self):
        return self.name

class CutsPolicy(enum.Enum):
    INTERNAL = "internal"
    NOCUTS = "nocuts"
    FROMFIT = "fromfit"
    FROM_CUT_INTERSECTION_NAMESPACE = "fromintersection"
    FROM_SIMILAR_PREDICTIONS_NAMESPACE = "fromsimilarpredictions"


class Cuts(TupleComp):
    def __init__(self, name, path):
        """Represents a file containing cuts for a given dataset"""
        self.name = name
        self.path = path
        super().__init__(name, path)

    def load(self):
        log.debug("Loading cuts for %s", self.name)
        return np.atleast_1d(np.loadtxt(self.path, dtype=int))

class InternalCutsWrapper(TupleComp):
    def __init__(self, commondata, rules):
        self.rules = rules
        self.commondata = commondata
        super().__init__(commondata, tuple(rules))

    def load(self):
        return np.atleast_1d(
            np.asarray(
                filters.get_cuts_for_dataset(self.commondata, self.rules),
                dtype=int))

class MatchedCuts(TupleComp):
    def __init__(self, othercuts, ndata):
        self.othercuts = tuple(othercuts)
        self.ndata = ndata
        super().__init__(self.othercuts, self.ndata)

    def load(self):
        loaded =  [c.load() for c in self.othercuts if c]
        if loaded:
            return functools.reduce(np.intersect1d, loaded)
        self._full = True
        return np.arange(self.ndata)

class SimilarCuts(TupleComp):
    def __init__(self, inputs, threshold):
        if len(inputs) != 2:
            raise ValueError("Expecting two input tuples")
        firstcuts, secondcuts = inputs[0][0].cuts, inputs[1][0].cuts
        if firstcuts != secondcuts:
            raise ValueError("Expecting cuts to be the same for all datasets")
        self.inputs = inputs
        self.threshold = threshold
        super().__init__(self.inputs, self.threshold)

    @functools.lru_cache()
    def load(self):
        # TODO: Update this when a suitable interace becomes available
        from validphys.convolution import central_predictions
        from validphys.commondataparser import load_commondata
        from validphys.covmats import covmat_from_systematics

        first, second = self.inputs
        first_ds = first[0]
        exp_err = np.sqrt(
            np.diag(
                covmat_from_systematics(
                    load_commondata(first_ds.commondata).with_cuts(first_ds.cuts),
                    first_ds, # DataSetSpec has weight attr
                    use_weights_in_covmat=False, # Don't weight covmat
                )
            )
        )
        # Compute matched predictions
        delta = np.abs(
            (central_predictions(*first) - central_predictions(*second)).squeeze(axis=1)
        )
        ratio = delta / exp_err
        passed = ratio < self.threshold
        return passed[passed].index


def cut_mask(cuts):
    """Return an objects that will act as the cuts when applied as a slice"""
    if cuts is None:
        return slice(None)
    return cuts.load()

class DataSetSpec(TupleComp):

    def __init__(self, *, name, commondata, fkspecs, thspec, cuts,
                 frac=1, op=None, weight=1):
        self.name = name
        self.commondata = commondata

        if isinstance(fkspecs, FKTableSpec):
            fkspecs = (fkspecs,)
        self.fkspecs = tuple(fkspecs)
        self.thspec = thspec

        self.cuts = cuts
        self.frac = frac

        #Do this way (instead of setting op='NULL' in the signature)
        #so we don't have to know the default everywhere
        if op is None:
            op = 'NULL'
        self.op = op
        self.weight = weight

        super().__init__(name, commondata, fkspecs, thspec, cuts,
                         frac, op, weight)

    @functools.lru_cache()
    def load(self):
        cd = self.commondata.load()

        fktables = []
        for p in self.fkspecs:
            fktable = p.load()
            #IMPORTANT: We need to tell the python garbage collector to NOT free the
            #memory owned by the FKTable on garbage collection.
            #TODO: Do this automatically
            fktable.thisown = 0
            fktables.append(fktable)

        fkset = FKSet(FKSet.parseOperator(self.op), fktables)

        data = DataSet(cd, fkset, self.weight)


        if self.cuts is not None:
            #ugly need to convert from numpy.int64 to int, so we can pass
            #it happily to the vector to the SWIG wrapper.
            #Do not do this (or find how to enable in SWIG):
            #data = DataSet(data, list(dataset.cuts))
            loaded_cuts = self.cuts.load()
            #This is an optimization to avoid recomputing the dataset if
            #nothing is discarded
            if not (hasattr(loaded_cuts, '_full') and loaded_cuts._full):
                intmask = [int(ele) for ele in loaded_cuts]
                data = DataSet(data, intmask)
        return data

    def to_unweighted(self):
        """Return a copy of the dataset with the weight set to one."""
        return self.__class__(
            name=self.name,
            commondata=self.commondata,
            fkspecs=self.fkspecs,
            thspec=self.thspec,
            cuts=self.cuts,
            frac=self.frac,
            op=self.op,
            weight=1,
        )

    def __str__(self):
        return self.name

class FKTableSpec(TupleComp):
    def __init__(self, fkpath, cfactors):
        self.fkpath = fkpath
        self.cfactors = cfactors
        super().__init__(fkpath, cfactors)

    #NOTE: We cannot do this because Fkset owns the fktable, and trying
    #to reuse the loaded one fails after it gets deleted.
    #@functools.lru_cache()
    def load(self):
        return FKTable(str(self.fkpath), [str(factor) for factor in self.cfactors])

class PositivitySetSpec(TupleComp):
    def __init__(self, name ,commondataspec, fkspec, maxlambda, thspec):
        self.name = name
        self.commondataspec = commondataspec
        self.fkspec = fkspec
        self.maxlambda = maxlambda
        self.thspec = thspec
        super().__init__(name, commondataspec, fkspec, maxlambda, thspec)



    def __str__(self):
        return self.name

    @functools.lru_cache()
    def load(self):
        cd = self.commondataspec.load()
        fk = self.fkspec.load()
        return PositivitySet(cd, fk, self.maxlambda)



#We allow to expand the experiment as a list of datasets
class DataGroupSpec(TupleComp, namespaces.NSList):

    def __init__(self, name, datasets, dsinputs=None):
        #This needs to be hashable
        datasets = tuple(datasets)

        #TODO: Find a better way for interactive usage.
        if dsinputs is not None:
            dsinputs = tuple(dsinputs)

        self.name = name
        self.datasets = datasets
        self.dsinputs = dsinputs

        #TODO: Add dsinputs to comp tuple?
        super().__init__(name, datasets)

        #TODO: Can we do  better cooperative inherece trick than this?
        namespaces.NSList.__init__(self, dsinputs, nskey='dataset_input')

    @functools.lru_cache(maxsize=32)
    def load(self):
        sets = []
        for dataset in self.datasets:
            loaded_data = dataset.load()
            sets.append(loaded_data)
        return Experiment(sets, self.name)

    @property
    def thspec(self):
        #TODO: Is this good enough? Should we explicitly pass the theory
        return self.datasets[0].thspec

    def __str__(self):
        return self.name

    #Need this so that it doesn't try to iterte over itself.
    @property
    def as_markdown(self):
        return str(self)

    def to_unweighted(self):
        """Return a copy of the group with the weights for all experiments set
        to one. Note that the results cannot be used as a namespace."""
        return self.__class__(
            name=self.name,
            datasets=[ds.to_unweighted() for ds in self.datasets],
            dsinputs=None,
        )


class FitSpec(TupleComp):
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.label = name
        super().__init__(name, path)

    def __iter__(self):
        yield self.name
        yield self.path

    @functools.lru_cache()
    def as_input(self):
        p = self.path/'filter.yml'
        log.debug('Reading input from fit configuration %s' , p)
        try:
            with p.open() as f:
                d = yaml.safe_load(f)
        except (yaml.YAMLError, FileNotFoundError) as e:
            raise AsInputError(str(e)) from e
        d['pdf'] = {'id': self.name, 'label': self.label}

        if 'experiments' in d:
            # Flatten old style experiments to dataset_inputs
            dataset_inputs = experiments_to_dataset_inputs(d['experiments'])
            d['dataset_inputs'] = dataset_inputs

        #BCH
        # backwards compatibility hack for runcards with the 'fitting' namespace
        # if a variable already exists outside 'fitting' it takes precedence
        fitting = d.get("fitting")
        if fitting is not None:
            to_take_out = ["genrep", "trvlseed", "mcseed", "nnseed", "parameters"]
            for vari in to_take_out:
                if vari in fitting and vari not in d:
                    d[vari] = fitting[vari]
        return d

    def __str__(self):
        return self.label

    __slots__ = ('label','name', 'path')


class HyperscanSpec(FitSpec):
    """The hyperscan spec is just a special case of FitSpec"""

    def __init__(self, name, path):
        super().__init__(name, path)
        self._tries_files = None

    @property
    def tries_files(self):
        """Return a dictionary with all tries.json files mapped to their replica number"""
        if self._tries_files is None:
            re_idx = re.compile(r"(?<=replica_)\d+$")
            get_idx = lambda x: int(re_idx.findall(x.as_posix())[-1])
            all_rep = map(get_idx, self.path.glob("nnfit/replica_*"))
            # Now loop over all replicas and save them when they include a tries.json file
            tries = {}
            for idx in sorted(all_rep):
                test_path = self.path / f"nnfit/replica_{idx}/tries.json"
                if test_path.exists():
                    tries[idx] = test_path
            self._tries_files = tries
        return self._tries_files

    def get_all_trials(self, base_params=None):
        """Read all trials from all tries files.
        If there are original runcard-based parameters, a reference to them can be passed
        to the trials so that a full hyperparameter dictionary can be defined

        Each hyperopt trial object will also have a reference to all trials in its own file
        """
        all_trials = []
        for trial_file in self.tries_files.values():
            with open(trial_file, "r") as tf:
                run_trials = []
                for trial in json.load(tf):
                    trial = HyperoptTrial(trial, base_params=base_params, linked_trials=run_trials)
                    run_trials.append(trial)
            all_trials += run_trials
        return all_trials

    def sample_trials(self, n=None, base_params=None, sigma=4.0):
        """Parse all trials in the hyperscan object
        and then return an array of ``n`` trials read from the ``tries.json`` files
        and sampled according to their reward.
        If ``n`` is ``None``, no sapling is performed and all trials are returned

        Returns
        -------
            Dictionary on the form {parameters: list of trials}
        """
        all_trials_raw = self.get_all_trials(base_params=base_params)
        # Drop all failing trials
        all_trials = list(filter(lambda i: i.reward, all_trials_raw))
        if n is None:
            return all_trials
        if len(all_trials) < n:
            log.warning("Asked for %d trials, only %d valid trials found", n, len(all_trials))
        # Compute weights proportionally to the reward (goes from 0 (worst) to 1 (best, loss=1))
        rewards = np.array([i.weighted_reward for i in all_trials])
        weight_raw = np.exp(sigma * rewards ** 2)
        total = np.sum(weight_raw)
        weights = weight_raw / total
        return np.random.choice(all_trials, replace=False, size=n, p=weights)


class TheoryIDSpec:
    def __init__(self, id, path):
        self.id = id
        self.path = path

    def __iter__(self):
        yield self.id
        yield self.path

    def get_description(self):
        dbpath = self.path.parent/'theory.db'
        return fetch_theory(dbpath, self.id)

    __slots__ = ('id', 'path')

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, path={self.path!r})"

    def __str__(self):
        return f"Theory {self.id}"

class ThCovMatSpec:
    def __init__(self, path):
        self.path = path

    # maxsize relatively low here, expect single experiments so one load per dataspec
    @functools.lru_cache(maxsize=8)
    def load(self):
        return parse_exp_mat(self.path)

    def __str__(self):
        return str(self.path)

#TODO: Decide if we want methods or properties
class Stats:

    def __init__(self, data):
        """`data `should be N_pdf*N_bins"""
        self.data = np.atleast_2d(data)

    def central_value(self):
        raise NotImplementedError()

    def error_members(self):
        raise NotImplementedError()

    def std_error(self):
        raise NotImplementedError()

    def moment(self, order):
        raise NotImplementedError()

    def sample_values(self, size):
        raise NotImplementedError()

    def std_interval(self, nsigma):
        raise NotImplementedError()

    def errorbar68(self):
        raise NotImplementedError()

    def errorbarstd(self):
        return (self.central_value() - self.std_error(),
                self.central_value() + self.std_error())

    #TODO...
    ...


class MCStats(Stats):
    """Result obtained from a Monte Carlo sample"""

    def central_value(self):
        return np.mean(self.data, axis=0)

    def std_error(self):
        return np.std(self.data, axis=0)

    def moment(self, order):
        return np.mean(np.power(self.data-self.central_value(),order), axis=0)

    def errorbar68(self):
        #Use nanpercentile here because we can have e.g. 0/0==nan normalization
        #somewhere.
        down = np.nanpercentile(self.error_members(), 15.87, axis=0)
        up =   np.nanpercentile(self.error_members(), 84.13, axis=0)
        return down, up

    def sample_values(self, size):
        return np.random.choice(self, size=size)

    def error_members(self):
        return self.data


class SymmHessianStats(Stats):
    """Compute stats in the 'assymetric' hessian format: The first index (0)
    is the
    central value. The rest of the indexes are results for each eigenvector.
    A 'rescale_factor is allowed in case the eigenvector confidence interval
    is not 68%'."""
    def __init__(self, data, rescale_factor=1):
        super().__init__(data)
        self.rescale_factor = rescale_factor

    def central_value(self):
        return self.data[0]

    def errorbar68(self):
        return self.errorbarstd()

    def error_members(self):
        return self.data[1:]

    def std_error(self):
        data = self.data
        diffsq = (data[0] - data[1:])**2
        return np.sqrt(diffsq.sum(axis=0))/self.rescale_factor

    def moment(self, order):
        data = self.data
        return np.sum(
            np.power((data[0] - data[1:])/self.rescale_factor, order), axis=0)

class HessianStats(SymmHessianStats):
    """Compute stats in the 'assymetric' hessian format: The first index (0)
    is the
    central value. The odd indexes are the
    results for lower eigenvectors and the
    even are the upper eigenvectors.A 'rescale_factor is allowed in
    case the eigenvector confidence interval
    is not 68%'."""
    def std_error(self):
        data = self.data
        diffsq = (data[1::2] - data[2::2])**2
        return np.sqrt(diffsq.sum(axis=0))/self.rescale_factor/2

    def moment(self, order):
        data = self.data
        return np.sum(
            np.power((data[1::2] - data[2::2])/self.rescale_factor/2, order), axis=0)


STAT_TYPES = dict(
                    symmhessian = SymmHessianStats,
                    hessian = HessianStats,
                    replicas   = MCStats,
                   )

class Filter:
    def __init__(self, indexes, label, **kwargs):
        self.indexes  = indexes
        self.label = label
        self.kwargs = kwargs

    def as_pair(self):
        return self.label, self.indexes

    def __str__(self):
        return '%s: %s' % (self.label, self.indexes)
