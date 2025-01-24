import numpy as np
from typing import Optional
from scipy.stats import f
from scipy.interpolate import PchipInterpolator

# This module provides the core of the change-point model
# but abstracted for both 2-parameter and 3-parameter diagnostics

def cpdFmax2pCore(Fmax : float, n: int, k : int
                , pTable : np.ndarray , nTable : np.ndarray
                , FmaxTable : np.ndarray
                , lowerP : float) -> Optional[float]:
  """
  Calculates the probability `p` that the k-parameter diagnostic
  change-point model fit is significant.

  Based on the method implemented by Alan Barr in 2010 in Matlab.

  It interpolates within a Table pTable, generated
  for the k-parameter model by Wang (2003).

  Args:
      Fmax: The Fmax value to be evaluated.
      n: Sample size or degrees of freedom.
      k: Number of parameters in the model.
      pTable: The table of p values.
      nTable: The table of n values.
      FmaxTable: The table of Fmax values.
      lowerP: lower tail probability for the percept point function
  """

  # Validate inputs
  if not validate_inputs(Fmax, n):
      return np.nan

  # Interpolate critical Fmax values
  FmaxCritical = interpolate_FmaxCritical(n, len(pTable), nTable, FmaxTable)

  # Calculate p based on Fmax comparison
  if Fmax < FmaxCritical[0]:
      return float(calculate_p_low(lowerP, Fmax, FmaxCritical[0], n))
  elif Fmax > FmaxCritical[2]:
      return float(calculate_p_high(Fmax, FmaxCritical[2], n))
  else:
      return float(calculate_p_interpolate(Fmax, FmaxCritical, pTable))

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

def calculate_p_low(lowerP : float, Fmax: float, FmaxCritical_low: float, n: float) -> float:
    """
    Calculate p when Fmax is below the lowest critical value.
    
    Parameters:
        lowerP: lower tail probability
        Fmax: The Fmax value.
        FmaxCritical_low: The critical value for Fmax.
        n: Degrees of freedom.
    
    Returns:
        The calculated p-value or NaN if inputs are invalid.
    """

    # Compute the adjusted F statistic
    fAdj = f.ppf(lowerP, 3, n) * Fmax / FmaxCritical_low
    
    # Compute p-value
    p = 2 * (1 - f.cdf(fAdj, 3, n))
    
    # Ensure p is at most 1
    if np.isnan(p):
        return 1.0
    else:
        return min(p, 1)

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

def interpolate_FmaxCritical(n: float, pTableSize : int, nTable: np.ndarray, FmaxTable: np.ndarray) -> np.ndarray:
    """
    Interpolate critical Fmax values for the given sample size (n).
    
    Parameters:
        n: The sample size for which to interpolate Fmax values.
        pTableSize: Size of significance levels array
        nTable: Array of sample sizes.
        FmaxTable: 2D array of critical Fmax values, where each column corresponds to a significance level.
    
    Returns:
        A 1D NumPy array containing the interpolated Fmax values for the given n.
    """
    if np.any(np.isnan(nTable)) or nTable.size == 0:
        return np.array([np.nan,np.nan,np.nan])

    FmaxCritical = np.zeros(pTableSize)
    for ip in range(pTableSize):
        interpolator = PchipInterpolator(nTable, FmaxTable[:, ip])
        FmaxCritical[ip] = interpolator(n)
    return FmaxCritical