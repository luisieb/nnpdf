"""This script provides the common filer to the jet and dijet STAR 2009 datasets.
Files need to be parsed all together as there are correlations provided.
"""

import pathlib

import numpy as np
import pandas as pd
import yaml

from nnpdf_data.filter_utils.correlations import compute_covmat

TOPOPLOGY_LIST = ["I", "SS", "OS", "A", "B", "C"]
POL_UNC = 0.065
LUMI_UNC = 0.0005
HERE = pathlib.Path(__file__).parents[2]


def read_1jet_data():
    df3 = pd.DataFrame()
    df4 = pd.DataFrame()

    fnames = [
        "../../new_commondata/STAR_2009_1JET_200GEV/rawdata/Table_3_ALL.csv",
        "../../new_commondata/STAR_2009_1JET_200GEV/rawdata/Table_3_pT.csv",
        "../../new_commondata/STAR_2009_1JET_200GEV/rawdata/Table_4_ALL.csv",
        "../../new_commondata/STAR_2009_1JET_200GEV/rawdata/Table_4_pT.csv",
        "../../new_commondata/STAR_2009_1JET_200GEV/rawdata/Table_5.csv",
    ]

    for fname in fnames:
        if "3" in fname:
            dfi = pd.read_csv(fname)
            if "pT" in fname:
                df3["pT"] = dfi["Parton Jet $p_T$ [GeV/c]"]

            elif "ALL" in fname:
                df3["ALL"] = dfi["$A_{LL}$"]
                df3["stat_min"] = dfi["stat -"]
                df3["stat_max"] = dfi["stat +"]
                df3["sys_min"] = dfi["sys -"]
                df3["sys_max"] = dfi["sys +"]

            df3["abs_eta_min"] = 0.0
            df3["abs_eta_max"] = 0.5
            df3["abs_eta"] = (df3["abs_eta_min"] + df3["abs_eta_max"]) / 2
            df3["sqrts"] = 200

        elif "4" in fname:
            dfi = pd.read_csv(fname)
            if "pT" in fname:
                df4["pT"] = dfi["Parton Jet $p_T$ [GeV/c]"]

            if "ALL" in fname:
                df4["ALL"] = dfi["$A_{LL}$"]
                df3["stat_min"] = dfi["stat -"]
                df3["stat_max"] = dfi["stat +"]
                df3["sys_min"] = dfi["sys -"]
                df3["sys_max"] = dfi["sys +"]

            df4["abs_eta_min"] = 0.5
            df4["abs_eta_max"] = 1.0
            df4["sqrts"] = 200

        elif "5" in fname:
            dfc_col = pd.read_csv(fname)

            dfc = pd.DataFrame()
            biny = 1
            for i in range(len(dfc_col)):
                if dfc_col.loc[i, "binx"] == "-":
                    biny = float(dfc_col.loc[i, "val"])
                else:
                    binx = float(dfc_col.loc[i, "binx"])
                    dfc.loc[binx, biny] = dfc_col.loc[i, "val"]

            dfc = dfc.astype("float")

        else:
            print("ERROR: Unknown table number detected! Check input files.")

    df = pd.concat([df3, df4], ignore_index=True)

    for i in range(len(df)):
        df.loc[i, "stat"] = df.loc[i, "stat_max"]
        df.loc[i, "sys"] = df.loc[i, "sys_max"]
    return df, dfc


def read_2jet_data(topology):
    fname = f"../../new_commondata/STAR_2009_2JET_{topology}_200GEV/rawdata/Table.yaml"
    df = pd.DataFrame()
    with open(fname, "r") as file:
        data = yaml.safe_load(file)

    if topology in ["A", "B", "C"]:
        Msub = data["independent_variables"][0]["values"]
        Gsub = data["dependent_variables"][0]["values"]

        for i in range(len(Msub)):

            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        {
                            "m_low": [Msub[i]["low"]],
                            "m_high": [Msub[i]["high"]],
                            "ALL": [Gsub[i]["value"]],
                            "stat": [Gsub[i]["errors"][0]["symerror"]],
                            "sys": [Gsub[i]["errors"][1]["symerror"]],
                        }
                    ),
                ],
                ignore_index=True,
            )

        df["m"] = (df["m_low"] + df["m_high"]) / 2
        df["sqrts"] = 200

    else:
        Msub = data["dependent_variables"][0]["values"]
        Gsub = data["dependent_variables"][1]["values"]

        for i in range(len(Msub)):

            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        {
                            "m": [Msub[i]["value"]],
                            "ALL": [Gsub[i]["value"]],
                            "stat": [Gsub[i]["errors"][0]["symerror"]],
                            "sys": [Gsub[i]["errors"][1]["symerror"]],
                            "pol": [POL_UNC * Gsub[i]["value"]],
                        }
                    ),
                ],
                ignore_index=True,
            )
        df["sqrts"] = 200

    return df


def write_1jet_data(df, art_sys):
    STORE_PATH = "../../new_commondata/STAR_2009_1JET_200GEV/"

    # Write central data
    data_central_yaml = {"data_central": list(df["ALL"])}
    with open(STORE_PATH + "data.yaml", "w", encoding="utf-8") as file:
        yaml.dump(data_central_yaml, file)

    # Write kin file
    kin = []
    for i in range(len(df)):
        kin_value = {
            "pT": {"min": None, "mid": float(df.loc[i, "pT"]), "max": None},
            "sqrts": {"min": None, "mid": float(df.loc[i, "sqrts"]), "max": None},
            "eta_abs": {
                "min": float(df.loc[i, "abs_eta_min"]),
                "mid": float(df.loc[i, "abs_eta"]),
                "max": float(df.loc[i, "abs_eta_max"]),
            },
        }
        kin.append(kin_value)
    kinematics_yaml = {"bins": kin}
    with open(STORE_PATH + "kinematics.yaml", "w", encoding="utf-8") as file:
        yaml.dump(kinematics_yaml, file)

    # Write unc file
    error = []
    error_definition = {}
    # loop on data points
    for i, sys_i in enumerate(art_sys):
        e = {}
        # loop on art sys
        for j, val in enumerate(sys_i):
            e[f"sys_{j}"] = val
        error.append(e)
        if i == 0:
            error_definition.update(
                {
                    f"sys_{j}": {
                        "description": f"{j} artificial correlated statistical + systematics uncertainty",
                        "treatment": "ADD",
                        "type": f"STAR2009JETunc{j}",
                    }
                    for j in range(len(sys_i))
                }
            )

    uncertainties_yaml = {"definitions": error_definition, "bins": error}
    with open(STORE_PATH + "uncertainties.yaml", "w", encoding="utf-8") as file:
        yaml.dump(uncertainties_yaml, file, sort_keys=False)


def write_2jet_data(df, topology, art_sys):
    STORE_PATH = f"../../new_commondata/STAR_2009_2JET_{topology}_200GEV/"
    # Write central data
    data_central_yaml = {"data_central": list(df["ALL"])}
    with open(STORE_PATH + "data.yaml", "w", encoding="utf-8") as file:
        yaml.dump(data_central_yaml, file)

    # Write kin file
    kin = []
    for i in range(len(df)):
        try:
            kin_value = {
                "m_jj": {
                    "min": float(df.loc[i, "m_low"]),
                    "mid": float(df.loc[i, "m"]),
                    "max": float(df.loc[i, "m_high"]),
                },
                "sqrts": {"min": None, "mid": float(df.loc[i, "sqrts"]), "max": None},
            }
        except:
            kin_value = {
                "m_jj": {"min": None, "mid": float(df.loc[i, "m"]), "max": None},
                "sqrts": {"min": None, "mid": float(df.loc[i, "sqrts"]), "max": None},
            }
        kin.append(kin_value)
    kinematics_yaml = {"bins": kin}
    with open(STORE_PATH + "kinematics.yaml", "w", encoding="utf-8") as file:
        yaml.dump(kinematics_yaml, file)

    # Write unc file
    error = []
    if topology in ["A", "B", "C"]:
        error_definition = {
            "stat": {"description": "statistical uncertainty", "treatment": "ADD", "type": "UNCORR"}
        }
        # loop on data points
        for i, sys_i in enumerate(art_sys):
            e = {"stat": float(df.loc[i, "stat"])}
            # loop on art sys
            for j, val in enumerate(sys_i):
                e[f"sys_{j}"] = val
            error.append(e)

            if i == 0:
                error_definition.update(
                    {
                        f"sys_{j}": {
                            "description": f"{j} artificial correlated systematics uncertainty",
                            "treatment": "ADD",
                            "type": f"STAR2009JETunc{j}",
                        }
                        for j in range(len(sys_i))
                    }
                )
    else:
        error_definition = {
            "stat": {
                "description": "statistical uncertainty",
                "treatment": "ADD",
                "type": "UNCORR",
            },
            "pol": {
                "description": "polarization uncertainty",
                "treatment": "MULT",
                "type": f"STAR2009POL",
            },
        }
        # loop on data points
        for i, sys_i in enumerate(art_sys):
            e = {"stat": float(df.loc[i, "stat"]), "pol": float(df.loc[i, "pol"])}
            # loop on art sys
            for j, val in enumerate(sys_i):
                e[f"sys_{j}"] = val
            error.append(e)

            if i == 0:
                error_definition.update(
                    {
                        f"sys_{j}": {
                            "description": f"{j} artificial correlated systematics uncertainty",
                            "treatment": "ADD",
                            "type": f"STAR2009JETunc{j}",
                        }
                        for j in range(len(sys_i))
                    }
                )

    uncertainties_yaml = {"definitions": error_definition, "bins": error}
    with open(STORE_PATH + "uncertainties.yaml", "w", encoding="utf-8") as file:
        yaml.dump(uncertainties_yaml, file, sort_keys=False)


if __name__ == "__main__":
    # load all the data
    df, dfc = read_1jet_data()
    dfs = {"I": df}
    for topo in TOPOPLOGY_LIST[1:]:
        dfs[topo] = read_2jet_data(topo)

    # load correlations
    ndata_dict = {a: len(b) for a, b in dfs.items()}
    correlation_df = pd.read_csv(
        "../../new_commondata/STAR_2009_1JET_200GEV/rawdata/correlation.csv", index_col=0
    )
    # from the paper we understand that stat dijet is not correlated
    #    I-I (stat + sys) | I-D (stat + sys)
    #    D-I (stat + sys) | D-D (sys)
    correlated_unc = np.sqrt(dfs["I"]["sys"] ** 2 + dfs["I"]["stat"] ** 2).values.tolist()
    for a in TOPOPLOGY_LIST[1:]:
        correlated_unc.extend(dfs[a]["sys"].values)
    ndata_points = np.sum((*ndata_dict.values(),))
    # decompose uncertainties
    art_sys = np.array(compute_covmat(correlation_df, correlated_unc, ndata_points))

    # write data
    cnt = 0
    for topo, df in dfs.items():
        ndata = ndata_dict[topo]
        syst = art_sys[cnt : cnt + ndata, :].tolist()
        if topo == "I":
            write_1jet_data(df, syst)
        else:
            write_2jet_data(df, topo, syst)
        cnt += ndata
