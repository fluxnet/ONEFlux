import numpy as np
from typing import Tuple


import math
from typing import Tuple, Dict

import numpy as np
from typing import Tuple, Dict

def initValues() -> Tuple[float, float, Dict[str, float], Dict[str, float]]:
    """
    Initialize values analogous to the MATLAB function initValues.

    Returns
    -------
    Cp2 : float
        Initialized to NaN.
    Cp3 : float
        Initialized to NaN.
    s2 : dict
        Dictionary representing the 's2' struct with each field set to NaN.
    s3 : dict
        Copy of the 's2' dictionary.
    """
    # Assign NaN to Cp2 and Cp3
    Cp2, Cp3 = np.nan, np.nan

    # Initialize s2 as a dictionary with all fields set to NaN
    s2 = {
        "n": np.nan,
        "Cp": np.nan,
        "Fmax": np.nan,
        "p": np.nan,
        "b0": np.nan,
        "b1": np.nan,
        "b2": np.nan,
        "c2": np.nan,
        "cib0": np.nan,
        "cib1": np.nan,
        "cic2": np.nan,
    }

    # Copy s2 to s3
    s3 = s2.copy()

    return Cp2, Cp3, s2, s3


def removeNans(xx: np.ndarray, yy: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reshape input vectors into column vectors and remove NaNs pairwise.

    Parameters
    ----------
    xx : np.ndarray
        Input vector (1D array, row or column).
    yy : np.ndarray
        Input vector (1D array, row or column).

    Returns
    -------
    x : np.ndarray
        Column vector with NaNs removed.
    y : np.ndarray
        Column vector with NaNs removed (corresponding rows to x).

    Example
    -------
    >>> xx = np.array([1, 2, np.nan, 4])
    >>> yy = np.array([10, np.nan, 30, 40])
    >>> x, y = remove_nans(xx, yy)
    >>> print(x)  # [1. 4.]
    >>> print(y)  # [10. 40.]
    """
    # Reshape xx and yy into column vectors
    x = xx.reshape(-1, 1).copy()
    y = yy.reshape(-1, 1).copy()

    # Find indices where either x or y are NaN
    isnan_mask = np.isnan(x + y).flatten()

    # Remove those entries
    x = x[~isnan_mask]
    y = y[~isnan_mask]

    return x, y


def removeOutliers(x: np.ndarray, y: np.ndarray, n: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fits a simple linear model to (x, y), computes residuals, and removes
    outliers beyond four standard deviations from the mean residual.

    Parameters
    ----------
    x : np.ndarray
        Independent variable (1D array of shape (n,) or (n, 1)).
    y : np.ndarray
        Dependent variable (1D array of shape (n,) or (n, 1)).
    n : int
        Number of data points.

    Returns
    -------
    x_filtered : np.ndarray
        Shallow copy of x with outlier entries removed.
    y_filtered : np.ndarray
        Shallow copy of y with outlier entries removed (corresponding to x_filtered).
    """

    # Make shallow copies so as not to modify the original arrays
    x_copy = x.copy()
    y_copy = y.copy()

    # Ensure x_copy and y_copy are 1D to match MATLAB's usage of (n,1) -> flatten
    x_copy = x_copy.reshape(-1)
    y_copy = y_copy.reshape(-1)

    # Perform linear regression: A = [ones(n,1), x], solve A * a = y
    A = np.column_stack((np.ones(n), x_copy))
    a, _, _, _ = np.linalg.lstsq(A, y_copy, rcond=None)

    # Predicted values from the linear model
    y_hat = a[0] + a[1] * x_copy

    # Residuals
    dy = y_copy - y_hat

    # Mean and std of residuals (sample std to match MATLAB default)
    mdy = np.mean(dy)
    sdy = np.std(dy, ddof=1)  # ddof=1 gives sample standard deviation (MATLAB-like)

    # Number of std-dev multiples to define an outlier
    ns = 4

    # Indices of outliers
    i_out = np.where(np.abs(dy - mdy) > ns * sdy)[0]

    # Remove outliers from x_copy and y_copy
    x_filtered = np.delete(x_copy, i_out)
    y_filtered = np.delete(y_copy, i_out)

    return x_filtered, y_filtered



def computeReducedModels(x: np.ndarray, 
                           y: np.ndarray, 
                           n: int) -> Tuple[float, np.ndarray, np.ndarray, float]:
    """
    Compute statistics of reduced (null hypothesis) models for later testing 
    of Cp2 and Cp3 significance.

    Parameters
    ----------
    x : np.ndarray
        Independent variable (1D array).
    y : np.ndarray
        Dependent variable (1D array).
    n : int
        Number of data points.

    Returns
    -------
    SSERed2 : float
        Sum of squared errors for reduced model (only intercept).
    a : np.ndarray
        Linear regression coefficients [intercept, slope].
    yHat3 : np.ndarray
        Predicted values from the linear model a[0] + a[1]*x.
    SSERed3 : float
        Sum of squared errors for the reduced model with intercept & slope.

    Notes
    -----
    1) Reduced model with only the mean (intercept):
       yHat2   = mean(y)
       SSERed2 = sum((y - yHat2)^2)

    2) Reduced model with intercept + slope:
       A = [ones(n), x]
       a = A \ y
       yHat3   = a[0] + a[1]*x
       SSERed3 = sum((y - yHat3)^2)
    """
    # 1) Reduced model with only mean (intercept)
    x = x.copy()
    y = y.copy()
    yHat2 = np.mean(y)
    SSERed2 = np.sum((y - yHat2)**2)

    # 2) Reduced model with intercept + slope
    A = np.column_stack((np.ones(n), x))
    a, _, _, _ = np.linalg.lstsq(A, y, rcond=None) # Unequivalent line to matlab code: a = A \ y .ie. mldivide
    yHat3 = a[0] + a[1] * x
    SSERed3 = np.sum((y - yHat3)**2)

    return SSERed2, SSERed3
