import pandas as pd
import yaml
import glob
import numpy as np
import pathlib
import pandas as pd


def read_data(fnames):
    df = pd.DataFrame()
    for fname in fnames:
        with open(fname, "r") as file:
            data = yaml.safe_load(file)

        xsub = data["independent_variables"][0]["values"]
        y = 0.0
        Qsub = data["independent_variables"][1]["values"]
        Gsub = data["dependent_variables"][0]["values"]

        for i in range(len(xsub)):
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        {
                            "x": [xsub[i]["value"]],
                            "y": [y],
                            "Q2": [Qsub[i]["value"]],
                            "G": [Gsub[i]["value"]],
                            "stat": [Gsub[i]["errors"][0]["symerror"]],
                            "sys_1": [Gsub[i]["errors"][1]["symerror"]],
                            "sys_2": [Gsub[i]["errors"][2]["symerror"]],
                            "sys_3": [Gsub[i]["errors"][3]["symerror"]],
                        }
                    ),
                ],
                ignore_index=True,
            )

    return df


def read_corrmatrix(nb_datapoints: int = 15) -> np.ndarray:
    """Load the correlation Matrix in Table 22."""
    file = pathlib.Path("./rawdata/HEPData-ins726689-v1-Table_22.yaml")
    loaded_file = yaml.safe_load(file.read_text())

    corrs = loaded_file['dependent_variables'][0]['values']
    df_corrs = pd.DataFrame(corrs)

    return df_corrs.value.values.reshape((nb_datapoints, nb_datapoints))


def compute_covmat(corrmat: np.ndarray, error: list, ndata: int) -> None:
    pass


def write_data(df):
    data_central = []
    for i in range(len(df["G"])):
        data_central.append(float(df.loc[i, "G"]))

    data_central_yaml = {"data_central": data_central}
    with open("data.yaml", "w") as file:
        yaml.dump(data_central_yaml, file, sort_keys=False)

    # Write kin file
    kin = []
    for i in range(len(df["G"])):
        kin_value = {
            "x": {"min": None, "mid": float(df.loc[i, "x"]), "max": None},
            "Q2": {"min": None, "mid": float(df.loc[i, "Q2"]), "max": None},
            "y": {"min": None, "mid": float(df.loc[i, "y"]), "max": None},
        }
        kin.append(kin_value)

    kinematics_yaml = {"bins": kin}

    with open("kinematics.yaml", "w") as file:
        yaml.dump(kinematics_yaml, file, sort_keys=False)

    # Write unc file
    error = []
    for i in range(len(df)):
        e = {
            "stat": float(df.loc[i, "stat"]),
            "sys_1": float(df.loc[i, "sys_1"]),
            "sys_2": float(df.loc[i, "sys_2"]),
        }
        error.append(e)

    # Extract the correlation matrix and compute artificial systematics
    ndata_points = len(data_central)
    corrmatrix = read_corrmatrix(nb_datapoints=ndata_points)
    # Compute the covariance matrix
    compute_covmat(corrmatrix, error, ndata_points)

    error_definition = {
        "stat": {
            "description": "statistical uncertainty",
            "treatment": "ADD",
            "type": "UNCORR",
        },
        "sys_1": {
            "description": "systematic uncertainty",
            "treatment": "ADD",
            "type": "UNCORR",
        },
        "sys_2": {
            "description": "systematic uncertainty",
            "treatment": "ADD",
            "type": "UNCORR",
        },
    }

    uncertainties_yaml = {"definitions": error_definition, "bins": error}

    with open("uncertainties.yaml", "w") as file:
        yaml.dump(uncertainties_yaml, file, sort_keys=False)


if __name__ == "__main__":
    fnames = glob.glob("./rawdata/Table13.yaml")
    df = read_data(fnames)
    write_data(df)
