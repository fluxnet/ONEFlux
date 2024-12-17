from typing import List, Tuple, Sequence, Dict, Union
import numpy as np



def reorder_and_preprocess_data(
    t: np.ndarray, 
    T: np.ndarray, 
    u_star: np.ndarray, 
    NEE: np.ndarray, 
    f_night: np.ndarray, 
    end_doy: int, 
    m: np.ndarray, 
    nt: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
    """
    Reorder and preprocess data based on specified conditions.

    Parameters:
        t (np.ndarray): Time array.
        T (np.ndarray): Temperature array.
        u_star (np.ndarray): Friction velocity array.
        NEE (np.ndarray): Net ecosystem exchange array.
        f_night (np.ndarray): Flag for nighttime data.
        end_doy (int): Last day of the year in day-of-year format.
        m (np.ndarray): Array of month indices.
        nt (int): Total number of data points.

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
            - Updated time array.
            - Updated temperature array.
            - Updated friction velocity array.
            - Updated net ecosystem exchange array.
            - Updated nighttime flag array.
            - Indices of annual data.
            - Number of annual data points.
    """
    # Find indices where month equals December (12)
    it_d = np.where(m == 12)[0]

    # Determine reordering indices
    min_it_d = np.min(it_d)
    it_reorder = np.concatenate((np.arange(min_it_d, nt), np.arange(0, min_it_d)))

    # Adjust time for December and reorder arrays
    t[it_d] -= end_doy
    t = t[it_reorder]
    T = T[it_reorder]
    u_star = u_star[it_reorder]
    NEE = NEE[it_reorder]
    f_night = f_night[it_reorder]

    # Find valid annual data indices and their count
    it_annual = np.where((f_night == 1) & ~np.isnan(NEE + u_star + T))[0]
    nt_annual = len(it_annual)

    return t, T, u_star, NEE, f_night, it_annual, nt_annual


def filter_invalid_points(
    u_star: np.ndarray,
    f_night: np.ndarray,
    nee: np.ndarray,
    t: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Filter invalid points from u_star and determine annual indices based on conditions.

    Parameters:
    u_star (np.ndarray): Array of u_star values.
    f_night (np.ndarray): Binary array indicating nighttime periods (1 for night, 0 for day).
    nee (np.ndarray): Array of net ecosystem exchange (NEE) values.
    t (np.ndarray): Array of time values.

    Returns:
    Tuple[np.ndarray, np.ndarray, int]:
        - Filtered u_star array with invalid values replaced by NaN.
        - Indices of valid annual points satisfying the conditions.
        - Number of valid annual points.
    """
    # Identify and filter invalid points in u_star (values outside the range [0, 3])
    invalid_indices = np.where((u_star < 0) | (u_star > 3))
    u_star[invalid_indices] = np.nan

    # Find valid annual indices satisfying the given conditions
    valid_annual_indices = np.where((f_night == 1) & ~np.isnan(nee + u_star + t))[0]
    num_valid_annual = len(valid_annual_indices)

    return u_star, valid_annual_indices, num_valid_annual

# Function from https://github.com/numpy/numpy/issues/6620
def matlab_percentile(in_data, percentiles):
    """
    Calculate percentiles in the way IDL and Matlab do it.

    By using interpolation between the lowest an highest rank and the
    minimum and maximum outside.

    Parameters
    ----------
    in_data: numpy.ndarray
        input data
    percentiles: numpy.ndarray
        percentiles at which to calculate the values

    Returns
    -------
    perc: numpy.ndarray
        values of the percentiles
    """

    data = np.sort(in_data)
    p_rank = 100.0 * (np.arange(data.size) + 0.5) / data.size
    perc = np.interp(percentiles, p_rank, data, left=data[0], right=data[-1])
    return perc


def addStatisticsFields(
    stats: Dict[str, float],
    t: np.ndarray, 
    T: np.ndarray, 
    r: np.ndarray, 
    p: np.ndarray, 
    itStrata: np.ndarray
) -> Dict[str, float]:
    """
    Calculate various expected values based on input arrays and indices.

    Parameters
    ----------
    t : np.ndarray
        One-dimensional array of values,  representing time.
    T : np.ndarray
        One-dimensional array of values, representing temperature.
    r : np.ndarray
        Two-dimensional array from which values for `expected_ruStarVsT` are extracted.
    p : np.ndarray
        Two-dimensional array from which values for `expected_puStarVsT` are extracted.
    itStrata : Sequence[int]
        Sequence of indices used to subset arrays `t` and `T`.


    Returns
    -------
    Dict[str, float]
        A dictionary containing:
        - "expected_mt": Mean of `t[itStrata]`
        - "expected_ti": The first element of `t[itStrata]`
        - "expected_tf": The last element of `t[itStrata]`
        - "expected_ruStarVsT": Extracted scalar value from `r[1][0]`
        - "expected_puStarVsT": Extracted scalar value from `p[1][0]`
        - "expected_mT": Mean of `T[itStrata]`
        - "expected_ciT": Half the difference between the 2.5th and 97.5th percentiles of `T[itStrata]`

    Notes
    -----
    The `matlab_percentile` function should be defined externally and is used to reproduce the behavior
    of MATLAB's percentile function, as it differs from NumPy's `np.percentile`.
    """

    expected_mt = float(np.mean(t[itStrata]))
    expected_ti = float(t[itStrata[0]])
    expected_tf = float(t[itStrata[-1]])
    expected_ruStarVsT = float(r[1][0])
    expected_puStarVsT = float(p[1][0])
    expected_mT = float(np.mean(T[itStrata]))
    ciT_vals = matlab_percentile(T[itStrata], [2.5, 97.5])
    expected_ciT = 0.5 * float(np.diff(ciT_vals)[0])

    stats.update({
        "expected_mt": expected_mt,
        "expected_ti": expected_ti,
        "expected_tf": expected_tf,
        "expected_ruStarVsT": expected_ruStarVsT,
        "expected_puStarVsT": expected_puStarVsT,
        "expected_mT": expected_mT,
        "expected_ciT": expected_ciT
    })
    return stats


def findStratumIndices(
    T: np.ndarray, 
    itSeason: Union[np.ndarray, np.ndarray],
    TTh: np.ndarray,
    iStrata: int
) -> np.ndarray:
    """
    Determine the indices within a specified range of T, and then intersect them with
    a given seasonal index set.

    The function first creates a boolean mask selecting the elements of T that lie between
    TTh[iStrata] and TTh[iStrata + 1]. It then extracts the indices of these elements, and
    intersects them with `itSeason` to produce the final set of indices.

    Parameters
    ----------
    T : np.ndarray
        A one-dimensional array of values (e.g., times, temperatures).
    TTh : np.ndarray
        A one-dimensional array of threshold values, used to define intervals in T.
    iStrata : int
        Index specifying which interval in TTh to use. The interval is defined as 
        [TTh[iStrata], TTh[iStrata + 1]].
    itSeason : Sequence[int] or np.ndarray
        A set of indices representing a particular season or subset of T.

    Returns
    -------
    np.ndarray
        An array of indices within the specified interval and season.

    Notes
    -----
    - The interval is inclusive of the endpoints.
    - `itSeason` is expected to be a set or list of valid indices for T.
    """

    # Create a boolean mask to select elements of T in the given interval
    mask = (T >= TTh[iStrata]) & (T <= TTh[iStrata + 1])

    # Extract indices where the condition is true
    itStrata_indices = mask.nonzero()

    # Intersect the selected indices with itSeason
    expected_itStrata = np.intersect1d(itStrata_indices, itSeason)

    return expected_itStrata


def computeStrataCount(nt_season: int, 
                         n_bins: int, 
                         n_per_bin: int, 
                         n_strata_n: int, 
                         n_strata_x: int) -> int:
    """
    Compute the number of strata for a given season length and bin configuration.

    The computation is based on dividing the total number of time steps (nt_season) 
    by the product of the number of bins (n_bins) and the number of time steps per bin (n_per_bin).
    The resulting number of strata is then constrained between minimum (n_strata_n) 
    and maximum (n_strata_x) values.

    Parameters
    ----------
    nt_season : int
        Total number of time steps in a season.
    n_bins : int
        Number of bins used for stratification.
    n_per_bin : int
        Number of time steps per bin.
    n_strata_n : int
        Minimum allowable number of strata.
    n_strata_x : int
        Maximum allowable number of strata.

    Returns
    -------
    int
        The computed number of strata, ensuring it falls within the specified bounds.
    """
    n_strata = nt_season // (n_bins * n_per_bin)
    n_strata = max(n_strata, n_strata_n)
    n_strata = min(n_strata, n_strata_x)
    return n_strata


def computeSeasonIndices(i_season: int, 
                           n_seasons: int, 
                           n_per_season: int, 
                           nt_annual: int) -> range:
    """
    Compute the time indices for a given season within an annual cycle.

    The year is divided into `n_seasons` seasons, each ideally consisting of 
    `n_per_season` time steps. The function returns the indices for the 
    `i_season`-th season. For the last season, if the total annual length (`nt_annual`)
    is not perfectly divisible by `n_seasons`, it extends to the end of the year.

    Parameters
    ----------
    i_season : int
        The season index for which to compute the indices (1-based).
    n_seasons : int
        The total number of seasons in a year.
    n_per_season : int
        The number of time steps per season, ideally. Note that if the total 
        (`nt_annual`) is not divisible by `n_seasons`, the last season will 
        include the remainder.
    nt_annual : int
        The total number of time steps in a year.

    Returns
    -------
    range
        A range object representing the indices for the specified season.
    """
    n_per_season = int(n_per_season)
    if i_season == 1:
        # First season
        return range(1, n_per_season + 1)
    elif i_season == n_seasons:
        # Last season, possibly extended to cover the remainder
        start = (n_seasons - 1) * n_per_season + 1
        return range(start, nt_annual + 1)
    else:
        # Intermediate seasons
        start = (i_season - 1) * n_per_season + 1
        end = i_season * n_per_season
        return range(start, end + 1)
