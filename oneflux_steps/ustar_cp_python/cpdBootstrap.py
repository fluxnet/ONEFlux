import numpy as np
from typing import Dict, List
from oneflux_steps.ustar_cp_python.utilities import dot, ones

def generate_stats_mt() -> Dict[str, float]:
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


def setup_stats(n_boot: int, n_seasons: int, n_strata_x: int) -> List[List[List[Dict[str, float]]]]|dict[str, float]:
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
    stats = [[[generate_stats_mt() for _ in range(n_strata_x)]
              for _ in range(n_seasons)]
             for _ in range(n_boot)]

    return stats

def setup_Cp(nSeasons=None, nStrataX=None, nBoot=None):
    # TODO: check definition, may need to use the definition in utils.py
    return dot(np.nan, np.ones(nSeasons, nStrataX, nBoot))
