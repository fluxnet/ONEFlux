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