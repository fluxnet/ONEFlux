import numpy as np

def prctile(A: np.ndarray, p: float) -> float|np.ndarray:
    """
    Compute the p-th percentile of array A using MATLAB's percentile algorithm.

    Args:
        A (np.ndarray): Input 1D array.
        p (float): Desired percentile (0 to 100).

    Returns:
        float|np.ndarray: The computed percentile value.
    """
    A = A[~np.isnan(A)]  # Remove NaNs
    n = len(A)
    if n == 0:
        return np.nan
    
    A_sorted = np.sort(A)
    
    # Define percentiles at sorted element positions
    percentiles = 100 * (np.arange(0.5, n) / n)
    
    # Linear interpolation
    return np.interp(p, percentiles, A_sorted)