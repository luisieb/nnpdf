"""
    Custom hyperopt trial object for persistent file storage
    in the form of json and pickle files within the nnfit folder
"""
import pickle
import json
import logging
from numpy.random._generator import Generator
from validphys.hyperoptplot import HyperoptTrial
from hyperopt import Trials, space_eval

log = logging.getLogger(__name__)

# Note: the plan would be to do a PR in hyperopt's main repository
# because these are things generic and useful enough that should be
# in hyperopt by default. But for now it will stay here.


def space_eval_trial(space, trial):
    """
    This function is a wrapper around hyperopt's space eval in order to add
    to the json a dictionary containing the human-readable values.
    i.e., the standard json would say: "optimizer = [5]" and we want it to say optimizer = "Adam"
    But all this function does before calling hyperopt's space_eval is to "unlist" the items.
    If you think space_eval should do that by itself, you are not alone
    https://github.com/hyperopt/hyperopt/issues/383#issuecomment-378561408

    # Arguments:
        - `space`: the dictionary containing the hyperopt space samplers we pass
                   to the hyperparametrizable function
        - `trial`: trial dictionary. This is a dictionary containing (among other things)
                   the list of parameters that were tried for this iteration of hyperopt

    # Returns:
        A dictionary containing the values of all the parameters in a human-readable format
    """
    for_eval = {}
    for key, values in trial["misc"]["vals"].items():
        if values:
            for_eval[key] = values[0]
        else:
            for_eval[key] = None
    ret = space_eval(space, for_eval)
    # If the result includes a trial, expand it
    if isinstance(ret.get("parameters"), HyperoptTrial):
        used_trial = ret.pop("parameters")
        ret = dict(ret, **used_trial.params)
    return ret


class FileTrials(Trials):
    """
    Stores trial results on the fly inside the nnfit replica folder

    Parameters
    ----------
        replica_path: path
            Replica folder as generated by n3fit
        parameters: dict
            Dictionary of parameters on which we are doing hyperoptimization
    """

    def __init__(self, replica_path, parameters=None, **kwargs):
        self._store_trial = False
        self._json_file = "{0}/tries.json".format(replica_path)
        self.pkl_file = "{0}/tries.pkl".format(replica_path)
        self._parameters = parameters
        self._rstate = None
        super().__init__(**kwargs)

    @property
    def rstate(self) -> Generator:
        """
        Returs the rstate attribute.

        Notes:
            Rstate stores a `numpy.random.Generator` which is important to make
            hyperopt restarts reproducible in the hyperparameter space. It can
            be passed later as the `rstate` parameters of `hyperopt.fmin`.
        """
        return self._rstate

    @rstate.setter
    def rstate(self, random_generator: Generator) -> None:
        """
        Sets the rstate attribute.

        Example:
            >>> trials = FileTrials(replica_path_set, parameters=parameters)
            >>> trials.rstate = np.random.default_rng(42)
        """
        self._rstate = random_generator

    def refresh(self):
        """
        This is the "flushing" method which is called at the end of every trial to
        save things in the database. We are are overloading it in order to also write
        to a json file with every single trial.
        """
        super().refresh()

        # write json to disk
        if self._store_trial:
            log.info("Storing scan in %s", self._json_file)
            local_trials = []
            for idx, t in enumerate(self._dynamic_trials):
                local_trials.append(t)
                local_trials[idx]["misc"]["space_vals"] = space_eval_trial(self._parameters, t)

            all_to_str = json.dumps(local_trials, default=str)
            with open(self._json_file, "w") as f:
                f.write(all_to_str)

    # The two methods below are just a stupid overloading to avoid writing to the
    # database twice
    def new_trial_ids(self, n):
        self._store_trial = False
        return super().new_trial_ids(n)

    def new_trial_docs(self, tids, specs, results, miscs):
        self._store_trial = True
        return super().new_trial_docs(tids, specs, results, miscs)

    def to_pkl(self):
        """Dump `FileTrials` object into a pickle file."""
        with open(self.pkl_file, "wb") as file:
            pickle.dump(self, file)

    @classmethod
    def from_pkl(cls, pickle_filepath):
        """Load and return an instance of `FileTrials` from a pickle file.

        If a pickle file from previous run is present this method can be used
            to instantiate an initial `FileTrials` object to restart.
        """
        try:
            with open(pickle_filepath, "rb") as file:
                return pickle.load(file)
        except FileNotFoundError as err:
            log.error("Failed to open pickle file: %s", err)
