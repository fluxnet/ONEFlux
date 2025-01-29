import numpy as np
from typing import Dict, List
from oneflux_steps.ustar_cp_python.utilities import dot, intersect

def cpdBootstrapUStarTh4Season20100901(*args, **kwargs):
    """
    cpdBootstrapUStarTh4Season20100901: Bootstrap the uStarTh for a season

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        None
    """
    # TODO: implement this function
    return None

def generate_statsMT() -> Dict[str, float]:
    """
    Initialize a stats structure with NaN values for predefined fields.

    Returns:
        Dict[str, float]: Initialized stats dictionary with NaN values.
    """
    fields = [
        "n", "Cp", "Fmax", "p", "b0", "b1", "b2", "c2",
        "cib0", "cib1", "cic2", "mt", "ti", "tf",
        "ruStarVsT", "puStarVsT", "mT", "ciT"
    ]

    # Initialize all fields with NaN
    stats_mt = {field: np.nan for field in fields}

    return stats_mt


def setup_Stats(n_boot: int, n_seasons: int, n_strata_x: int, **kwargs) -> List[List[List[Dict[str, float]]]]|dict[str, float]:
    """
    Initialize the Stats structure based on input dimensions.

    This function is correct where the args are all integers > 1.

    Args:
        n_boot (int): Number of bootstraps.
        n_seasons (int): Number of seasons.
        n_strata_x (int): Number of strata in X direction.

    Returns:
        List[List[List[Dict[str, float]]]]: Preallocated stats structure.
    """
    args_list = [n_boot, n_seasons, n_strata_x]
    for n in args_list:
        if n < 2:
            raise ValueError(f'Function "setup_stats" has been passed an argument \
                             with value {n}. This may lead undesired behaviour')

    # Preallocate stats array
    stats = [[[generate_statsMT() for _ in range(n_strata_x)]
              for _ in range(n_seasons)]
             for _ in range(n_boot)]

    return stats

def setup_Cp(nSeasons=None, nStrataX=None, nBoot=None):
    # TODO: check definition, may need to use the definition in utils.py
    return dot(np.nan, np.ones([nSeasons, nStrataX, nBoot]))

# TODO: rough attempt in np
def get_itNee(NEE=None, uStar=None, T=None, iNight=None):
    itNee = np.where(np.logical_not(np.isnan(NEE + uStar + T)))
    # itNee = intersect(itNee, iNight)
    return []

def get_ntN(t = None, nSeasons=None):
    # TODO
    return []

def update_uStar(x):
    # TODO
    return 0

def get_iNight(x):
    # TODO
    return 0

def get_nPerBin(x):
    # TODO
    return 0

def get_nPerDay(x):
    # TODO
    return 0