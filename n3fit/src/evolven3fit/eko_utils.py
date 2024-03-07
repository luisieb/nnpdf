import logging
from typing import Any, Dict, Optional

from ekobox.cards import _operator as default_op_card
import numpy as np

from eko.io import runcards
from eko.matchings import Atlas, nf_default
from eko.quantities.heavy_quarks import MatchingScales
from validphys.loader import Loader

from . import utils

_logger = logging.getLogger(__name__)

EVOLVEN3FIT_CONFIGS_DEFAULTS_TRN = {
    "ev_op_iterations": 1,
    "ev_op_max_order": (1, 0),
    "evolution_method": "truncated",
    "inversion_method": "expanded",
    "n_integration_cores": 1,
}

EVOLVEN3FIT_CONFIGS_DEFAULTS_EXA = {
    "ev_op_iterations": 30,
    "ev_op_max_order": (1, 0),
    "evolution_method": "iterate-exact",
    "inversion_method": "exact",
    "n_integration_cores": 1,
}

NFREF_DEFAULT = 5


def construct_eko_cards(
    theoryID,
    q_fin,
    q_points,
    x_grid,
    op_card_dict: Optional[Dict[str, Any]] = None,
    theory_card_dict: Optional[Dict[str, Any]] = None,
    legacy40: bool = False,
):
    """
    Return the theory and operator cards used to construct the eko.
    theoryID is the ID of the theory for which we are computing the theory and operator card.
    q_fin is the final point of the q grid while q_points is the number of points of the grid.
    x_grid is the x grid to be used.
    op_card_dict and theory_card_dict are optional updates that can be provided respectively to the
    operator card and to the theory card.
    """
    theory, thresholds = load_theory(theoryID, theory_card_dict)

    # if is eko_photon then mu0 = q_gamma
    mu0 = theory["Q0"]

    # Set nf_0 according to the fitting scale unless set explicitly
    if "nf0" not in theory:
        theory["nf0"] = find_nf(mu0, theory, thresholds)

    # The Legacy function is able to construct a theory card for eko starting from an NNPDF theory
    legacy_class = runcards.Legacy(theory, {})
    theory_card = legacy_class.new_theory

    # construct mugrid

    # Generate the q2grid, if q_fin and q_points are None, use `nf0` to select a default
    q2_grid = utils.generate_q2grid(
        mu0,
        q_fin,
        q_points,
        {
            theory["mc"]: thresholds["c"],
            theory["mb"]: thresholds["b"],
            theory["mt"]: thresholds["t"],
        },
        theory["nf0"],
        legacy40=legacy40,
    )

    masses = np.array([theory["mc"], theory["mb"], theory["mt"]]) ** 2
    thresholds_ratios = np.array([thresholds["c"], thresholds["b"], thresholds["t"]]) ** 2

    atlas = Atlas(
        matching_scales=MatchingScales(masses * thresholds_ratios), origin=(mu0**2, theory["nf0"])
    )

    # Create the eko operator q2grid
    # This is a grid which contains information on (q, nf)
    # in VFNS values at the matching scales need to be doubled so that they are considered in both sides
    ep = 1e-4
    mugrid = []
    for q2 in q2_grid:
        q = float(np.sqrt(q2))
        if nf_default(q2 + ep, atlas) != nf_default(q2 - ep, atlas):
            nf_l = int(nf_default(q2 - ep, atlas))
            nf_u = int(nf_default(q2 + ep, atlas))
            mugrid.append((q, nf_l))
            mugrid.append((q, nf_u))
        else:
            mugrid.append((q, int(nf_default(q2, atlas))))

    # construct operator card
    op_card = build_opcard(op_card_dict, theory, x_grid, mu0, mugrid)

    return theory_card, op_card


def construct_eko_photon_cards(
    theoryID,
    q_fin,
    x_grid,
    q_gamma,
    op_card_dict: Optional[Dict[str, Any]] = None,
    theory_card_dict: Optional[Dict[str, Any]] = None,
):
    """
    Return the theory and operator cards used to construct the eko_photon.
    theoryID is the ID of the theory for which we are computing the theory and operator card.
    q_fin is the final point of the q grid while q_points is the number of points of the grid.
    x_grid is the x grid to be used.
    op_card_dict and theory_card_dict are optional updates that can be provided respectively to the
    operator card and to the theory card.
    """
    theory, thresholds = load_theory(theoryID, theory_card_dict)

    # if is eko_photon then mu0 = q_gamma
    mu0 = q_gamma

    # Set nf_0 according to mu0 unless set explicitly
    if "nf0" not in theory:
        theory["nf0"] = find_nf(mu0, theory, thresholds)

    # The Legacy function is able to construct a theory card for eko starting from an NNPDF theory
    legacy_class = runcards.Legacy(theory, {})
    theory_card = legacy_class.new_theory

    q_fin = theory["Q0"]

    nf_fin = find_nf(q_fin, theory, thresholds)

    # construct mugrid
    mugrid = [(q_fin, nf_fin)]

    # construct operator card
    op_card = build_opcard(op_card_dict, theory, x_grid, mu0, mugrid)

    return theory_card, op_card


def load_theory(theoryID, theory_card_dict):
    """loads and returns the theory dictionary and the thresholds"""
    if theory_card_dict is None:
        theory_card_dict = {}
    # theory_card construction
    theory = Loader().check_theoryID(theoryID).get_description()
    theory.pop("FNS")
    theory.update(theory_card_dict)

    if "nfref" not in theory:
        theory["nfref"] = NFREF_DEFAULT

    # Prepare the thresholds according to MaxNfPdf
    thresholds = {"c": theory["kcThr"], "b": theory["kbThr"], "t": theory["ktThr"]}
    if theory["MaxNfPdf"] < 5:
        thresholds["b"] = np.inf
    if theory["MaxNfPdf"] < 6:
        thresholds["t"] = np.inf

    # Setting the thresholds in the theory card to inf if necessary
    theory.update({"kbThr": thresholds["b"], "ktThr": thresholds["t"]})

    return theory, thresholds


def build_opcard(op_card_dict, theory, x_grid, mu0, mugrid):
    """builds the opcard"""
    if op_card_dict is None:
        op_card_dict = {}

    op_card = default_op_card

    op_card.update({"mu0": mu0, "mugrid": mugrid})

    op_card["xgrid"] = x_grid
    # Specific defaults for evolven3fit evolution
    if theory["ModEv"] == "TRN":
        op_card["configs"].update(EVOLVEN3FIT_CONFIGS_DEFAULTS_TRN)
    if theory["ModEv"] == "EXA":
        op_card["configs"].update(EVOLVEN3FIT_CONFIGS_DEFAULTS_EXA)
    # User can still change the configs via op_card_dict

    # Note that every entry that is not a dictionary should not be
    # touched by the user and indeed an user cannot touch them
    for key in op_card:
        if key in op_card_dict and isinstance(op_card[key], dict):
            op_card[key].update(op_card_dict[key])
        elif key in op_card_dict:
            _logger.warning("Entry %s is not a dictionary and will be ignored", key)

    # if no -e was given, take ev_op_iterations from EVOLVEN3FIT_CONFIGS_DEFAULTS_{TRN,EXA}
    if op_card['configs']['ev_op_iterations'] is None:
        if theory["ModEv"] == "TRN":
            op_card['configs']['ev_op_iterations'] = EVOLVEN3FIT_CONFIGS_DEFAULTS_TRN[
                "ev_op_iterations"
            ]
        if theory["ModEv"] == "EXA":
            op_card['configs']['ev_op_iterations'] = EVOLVEN3FIT_CONFIGS_DEFAULTS_EXA[
                "ev_op_iterations"
            ]

    op_card = runcards.OperatorCard.from_dict(op_card)

    return op_card


def find_nf(mu, theory, thresholds):
    """compute nf for a given mu"""
    if mu < theory["mc"] * thresholds["c"]:
        nf = 3
    elif mu < theory["mb"] * thresholds["b"]:
        nf = 4
    elif mu < theory["mt"] * thresholds["t"]:
        nf = 5
    else:
        nf = 6
    return nf