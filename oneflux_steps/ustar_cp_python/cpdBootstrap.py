import numpy as np
from typing import Dict, List

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

    Args:
        n_boot (int): Number of bootstraps.
        n_seasons (int): Number of seasons.
        n_strata_x (int): Number of strata in X direction.

    Returns:
        List[List[List[Dict[str, float]]]]: Preallocated stats structure.
    """
    stats_mt = generate_stats_mt()

    def has_zero(*args: int) -> bool:
        """Check if any input argument is zero."""
        return any(arg == 0 for arg in args)

    if has_zero(n_boot, n_seasons, n_strata_x):
        return stats_mt

    # Preallocate stats array
    stats = [[[stats_mt.copy() for _ in range(n_strata_x)]
              for _ in range(n_seasons)]
             for _ in range(n_boot)]

    return stats