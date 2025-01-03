import numpy as np
from typing import Optional
from scipy.stats import f
from scipy.interpolate import PchipInterpolator

def cpdFmax2pCp3(Fmax: float, n: int) -> Optional[float]:
    """
    Calculates the probability `p` that the 3-parameter diagnostic change-point model fit is significant.

    Args:
        Fmax: The Fmax value to be evaluated.
        n: Sample size or degrees of freedom.

    Returns:
        The calculated probability `p`, or `NaN` if inputs are invalid.
    """

    # Validate inputs
    if not validate_inputs(Fmax, n):
        return np.nan

    # Get data tables
    pTable = get_pTable()
    nTable = get_nTable()
    FmaxTable = get_FmaxTable()

    # Interpolate critical Fmax values
    FmaxCritical = interpolate_FmaxCritical(n, nTable, FmaxTable)

    # Calculate p based on Fmax comparison
    if Fmax < FmaxCritical[0]:
        return float(calculate_p_low(Fmax, FmaxCritical[0], n))
    elif Fmax > FmaxCritical[2]:
        return float(calculate_p_high(Fmax, FmaxCritical[2], n))
    else:
        return float(calculate_p_interpolate(Fmax, FmaxCritical, pTable))


def calculate_p_high(Fmax: float, FmaxCritical_high: float, n: float) -> float:
    """
    Calculate p when Fmax is above the highest critical value.
    
    Parameters:
        Fmax: The Fmax value.
        FmaxCritical_high: The critical value for Fmax.
        n: Degrees of freedom.
    
    Returns:
        The calculated p-value or NaN if inputs are invalid.
    """
    # Handle invalid inputs
    if (
        np.isnan(Fmax) or np.isnan(FmaxCritical_high) or np.isnan(n) or
        n <= 0
    ):
        return 0

    # Compute the adjusted F statistic
    fAdj = f.ppf(0.995, 3, n) * Fmax / FmaxCritical_high
    
    # Compute p-value
    p = 2 * (1 - f.cdf(fAdj, 3, n))
    
    # Ensure p is non-negative
    return max(p, 0)

def calculate_p_interpolate(Fmax: float, FmaxCritical: np.ndarray, pTable: np.ndarray) -> float:
    """
    Calculate p using piecewise cubic Hermite interpolation (PCHIP). Extrapolation is set to `True`.
    
    Parameters:
        Fmax: The Fmax value.
        FmaxCritical: Array of critical Fmax values.
        pTable: Array of probabilities corresponding to FmaxCritical.
    
    Returns:
        The interpolated p-value or NaN if invalid inputs are provided.
    """


    try:
        interpolator = PchipInterpolator(FmaxCritical, 1 - pTable, extrapolate=True)
        return interpolator(Fmax)
    except ValueError:
        return np.nan
    
def calculate_p_low(Fmax: float, FmaxCritical_low: float, n: float) -> float:
    """
    Calculate p when Fmax is below the lowest critical value.
    
    Parameters:
        Fmax: The Fmax value.
        FmaxCritical_low: The critical value for Fmax.
        n: Degrees of freedom.
    
    Returns:
        The calculated p-value or NaN if inputs are invalid.
    """

    # Compute the adjusted F statistic
    fAdj = f.ppf(0.95, 3, n) * Fmax / FmaxCritical_low
    
    # Compute p-value
    p = 2 * (1 - f.cdf(fAdj, 3, n))
    
    # Ensure p is at most 1
    if np.isnan(p):
        return 1.0
    else:
        return min(p, 1)

def get_FmaxTable() -> np.ndarray:
    """
    Return the critical F-max values as a NumPy array.
    
    Returns:
        A 2D NumPy array containing critical F-max values.
    """
    return np.array([
        [11.646, 15.559, 28.412],
        [9.651, 11.948, 18.043],
        [9.379, 11.396, 16.249],
        [9.261, 11.148, 15.750],
        [9.269, 11.068, 15.237],
        [9.296, 11.072, 15.252],
        [9.296, 11.059, 14.985],
        [9.341, 11.072, 15.013],
        [9.397, 11.080, 14.891],
        [9.398, 11.085, 14.874],
        [9.506, 11.127, 14.828],
        [9.694, 11.208, 14.898],
        [9.691, 11.310, 14.975],
        [9.790, 11.406, 14.998],
        [9.794, 11.392, 15.044],
        [9.840, 11.416, 14.980],
        [9.872, 11.474, 15.072],
        [9.929, 11.537, 15.115],
        [9.955, 11.552, 15.086],
        [9.995, 11.549, 15.164],
        [10.102, 11.673, 15.292],
        [10.169, 11.749, 15.154],
        [10.478, 12.064, 15.519]
    ])

def get_nTable() -> np.ndarray:
    """
    Return the sample sizes as a NumPy array.
    
    Returns:
        A 1D NumPy array containing sample sizes.
    """
    return np.concatenate([
        np.arange(10, 101, 10),  # 10, 20, ..., 100
        np.arange(150, 601, 50),  # 150, 200, ..., 600
        [800, 1000, 2500]  # 800, 1000, 2500
    ])

def get_pTable() -> np.ndarray:
    """
    Return the significance levels as a NumPy array.
    
    Returns:
        A 1D NumPy array containing significance levels.
    """
    return np.array([0.90, 0.95, 0.99])

def interpolate_FmaxCritical(n: float, nTable: np.ndarray, FmaxTable: np.ndarray) -> np.ndarray:
    """
    Interpolate critical Fmax values for the given sample size (n).
    
    Parameters:
        n: The sample size for which to interpolate Fmax values.
        nTable: Array of sample sizes.
        FmaxTable: 2D array of critical Fmax values, where each column corresponds to a significance level.
    
    Returns:
        A 1D NumPy array containing the interpolated Fmax values for the given n.
    """
    if np.any(np.isnan(nTable)) or nTable.size == 0:
        return np.array([np.nan,np.nan,np.nan])

    FmaxCritical = np.zeros(3)
    for ip in range(3):
        interpolator = PchipInterpolator(nTable, FmaxTable[:, ip])
        FmaxCritical[ip] = interpolator(n)
    return FmaxCritical


def validate_inputs(Fmax: float, n: float) -> bool:
    """
    Check if Fmax and n are valid inputs.
    
    Parameters:
        Fmax: The Fmax value.
        n: The sample size.
    
    Returns:
        True if inputs are valid, otherwise False.
    """
    return not (np.isnan(Fmax) or np.isnan(n) or n < 10)