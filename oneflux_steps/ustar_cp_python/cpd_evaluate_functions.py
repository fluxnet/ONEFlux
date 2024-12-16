from typing import List, Tuple
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