"""
Filter for CMS_2JET_7TEV

Created on Mar  2023

@author: Mark N. Costantini
"""

from filter_utils import (
    JEC_error_matrix,
    bin_by_bin_covmat,
    correlation_to_covariance,
    dat_file_to_df,
    decompose_covmat,
    get_corr_dat_file,
    get_data_values,
    get_kinematics,
    get_stat_uncertainties,
    lumi_covmat,
    unfolding_error_matrix,
)
import numpy as np
import pandas as pd
from scipy.linalg import block_diag
import yaml


def filter_CMS_2JET_7TEV_data_kinetic():
    """
    writes kinetic and data central values
    to kinematics.yaml and data.yaml files
    respectively
    """

    with open('metadata.yaml', 'r') as file:
        metadata = yaml.safe_load(file)

    version = metadata['hepdata']['version']
    tables = metadata['hepdata']['tables']

    # get kinematics from hepdata tables
    kin = get_kinematics(tables, version)

    # get central values from hepdata tables
    data_central = get_data_values(tables, version)

    data_central_yaml = {'data_central': data_central}
    kinematics_yaml = {'bins': kin}

    # write central values and kinematics to yaml file
    with open('data.yaml', 'w') as file:
        yaml.dump(data_central_yaml, file, sort_keys=False)

    with open('kinematics.yaml', 'w') as file:
        yaml.dump(kinematics_yaml, file, sort_keys=False)


def filterCMS_2JET_7TEV_uncertainties():
    """
    writes uncertainties to uncertainties.yaml file
    """
    # read metadata file
    with open('metadata.yaml', 'r') as file:
        metadata = yaml.safe_load(file)

    tables = metadata['hepdata']['tables']
    version = metadata['hepdata']['version']

    # generate block diagonal statistical covariance matrix
    # Statistical uncertainty correlated between the mass bins in
    # the same rapidity range

    # get correlation matrix for statistical uncertainties
    corr_matrices = get_corr_dat_file('rawdata/dijet_corr.dat')
    # get statistical uncertainties from each HEPData table
    stat_uncertainties = get_stat_uncertainties()

    stat_cov_mats = []

    for i, table in enumerate(tables):
        if corr_matrices[i].shape[0] != np.array(stat_uncertainties[table]).shape[0]:
            raise ("Shapes of correlation matrix and uncertainties array are not compatible")
        # convert correlation matrices to covariance matrices
        stat_cov_mats.append(correlation_to_covariance(corr_matrices[i], stat_uncertainties[table]))

    # build block diagonal stat covmat
    BD_stat = stat_cov_mats[0]
    for i in range(1, len(stat_cov_mats)):
        stat = stat_cov_mats[i]
        BD_stat = block_diag(BD_stat, stat)

    # dataframe of uncertainties
    dfs = dat_file_to_df()
    df_uncertainties = pd.concat(dfs, axis=0)
    cv = get_data_values(tables, version)
    cv = np.array(cv)

    # get Luminosity Covmat CMSLUMI11
    lumi_cov = lumi_covmat()
    A_lum = df_uncertainties["Lumi+"].multiply(cv, axis=0).to_numpy()

    # Get JEC covmat, CORR
    jec_error_matrix = JEC_error_matrix()

    # get unfolding covmat, CORR
    unfold_error_matrix = unfolding_error_matrix()

    # get bin-by-bin covmat, UNCORR
    bin_cov = bin_by_bin_covmat()
    A_bin = df_uncertainties["Bin-by-bin-"].multiply(cv, axis=0).to_numpy()

    # generate artificial systematics
    A_art_sys_corr = decompose_covmat(covmat=BD_stat)

    # error definition
    error_definition = {
        f"art_sys_corr_{i}": {
            "description": f"artificial systematic originating from correlated statistical uncertainties",
            "treatment": "ADD",
            "type": "CORR",
        }
        for i in range(1, A_art_sys_corr.shape[0] + 1)
    }

    for col in jec_error_matrix.columns:
        error_definition[f"{col}"] = {
            "description": f"JEC uncertainty, {col}",
            "treatment": "MULT",
            "type": "CORR",
        }

    for col in unfold_error_matrix.columns:
        error_definition[f"{col}"] = {
            "description": f"Unfolding uncertainty, {col}",
            "treatment": "MULT",
            "type": "CORR",
        }

    error_definition["luminosity_uncertainty"] = {
        "description": "luminosity uncertainty",
        "treatment": "MULT",
        "type": "CMSLUMI11",
    }

    error_definition["bin_by_bin_uncertainty"] = {
        "description": "bin_by_bin_uncertainty",
        "treatment": "MULT",
        "type": "UNCORR",
    }

    # store error in dict
    error = []
    for n in range(A_art_sys_corr.shape[0]):
        error_value = {}

        for m in range(A_art_sys_corr.shape[1]):
            error_value[f"art_sys_corr_{m+1}"] = float(A_art_sys_corr[n, m])

        for col, m in zip(
            unfold_error_matrix.columns, range(unfold_error_matrix.to_numpy().shape[1])
        ):
            error_value[f"{col}"] = float(unfold_error_matrix.to_numpy()[n, m])

        for col, m in zip(jec_error_matrix.columns, range(jec_error_matrix.to_numpy().shape[1])):
            error_value[f"{col}"] = float(jec_error_matrix.to_numpy()[n, m])

        error_value["luminosity_uncertainty"] = float(A_lum[n])
        error_value["bin_by_bin_uncertainty"] = float(A_bin[n])

        error.append(error_value)

    uncertainties_yaml = {"definitions": error_definition, "bins": error}

    with open(f"uncertainties.yaml", 'w') as file:
        yaml.dump(uncertainties_yaml, file, sort_keys=False)

    # this part here is only needed to test and can be removed
    # function does not need to return anything
    covmat = (
        BD_stat
        + lumi_cov
        + (jec_error_matrix.to_numpy() @ jec_error_matrix.to_numpy().T)
        + (unfold_error_matrix.to_numpy() @ unfold_error_matrix.to_numpy().T)
        + bin_cov
    )

    return covmat


if __name__ == "__main__":
    # save data central values and kinematics
    filter_CMS_2JET_7TEV_data_kinetic()

    # save uncertainties
    filterCMS_2JET_7TEV_uncertainties()

    # only to test
    covmat = filterCMS_2JET_7TEV_uncertainties()

    from validphys.covmats import dataset_inputs_covmat_from_systematics
    from validphys.loader import Loader

    setname = "CMS_2JET_7TEV"
    l = Loader()
    cd = l.check_commondata(setname=setname).load_commondata_instance()
    dataset_input = l.check_dataset(setname, theoryid=200)
    from validphys.commondataparser import parse_commondata

    dat_file = (
        '/Users/markcostantini/codes/nnpdfgit/nnpdf/buildmaster/results/DATA_CMS_2JET_7TEV.dat'
    )
    sys_file = '/Users/markcostantini/codes/nnpdfgit/nnpdf/buildmaster/results/systypes/SYSTYPE_CMS_2JET_7TEV_DEFAULT.dat'

    cd = parse_commondata(dat_file, sys_file, setname)

    cmat = dataset_inputs_covmat_from_systematics(
        dataset_inputs_loaded_cd_with_cuts=[cd],
        data_input=[dataset_input],
        use_weights_in_covmat=False,
        norm_threshold=None,
        _list_of_central_values=None,
        _only_additive=False,
    )

    print(covmat / cmat)
    # print(np.allclose(covmat / cmat, np.ones(cmat.shape)))
    # dfs = dat_file_to_df()
    # print(dfs)
    # lumi_covmat(dfs)
