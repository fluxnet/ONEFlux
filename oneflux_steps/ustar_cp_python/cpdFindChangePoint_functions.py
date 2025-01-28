import numpy as np
from typing import Tuple, List, Dict, Callable
from scipy.stats import t
from oneflux_steps.ustar_cp_python.cpdFmax2pCp3 import cpdFmax2pCp3
from oneflux_steps.ustar_cp_python.cpdFmax2pCp2 import cpdFmax2pCp2


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
    # x_copy = x_copy.reshape(-1, 1)
    # y_copy = y_copy.reshape(-1, 1)

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
    i_out = np.where(np.abs(dy - mdy) > ns * sdy)[0] #Check this line indexing

    # Remove outliers from x_copy and y_copy
    x_filtered = np.delete(x_copy, i_out).reshape(-1, 1) # Recheck this shape issue line
    y_filtered = np.delete(y_copy, i_out).reshape(-1, 1)

    return x_filtered, y_filtered # Try reshaping



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


def computeNEndPts(n: int) -> int:
    """
    Compute the number of endpoints for a dataset.

    Sets minimum number of endpoints, then uses a fraction (5%)
    of n to determine nEndPts, ensuring it does not fall below
    a specified floor.

    Parameters:
    -----------
    n : int
        Number of elements in the dataset

    Returns:
    --------
    int
        Computed number of endpoints, floored at 5% of n,
        not falling below nEndPtsN
    """
    # Hard-coded minimum number of endpoints
    n_end_pts_n: int = 3
    
    # Compute 5% of n, then floor
    n_end_pts: int = int(0.05 * n)
    
    # Enforce a minimum value of nEndPtsN
    if n_end_pts < n_end_pts_n:
        n_end_pts = n_end_pts_n
    
    return n_end_pts


def fitOperational2ParamModel(
    i: int, 
    n: int, 
    x: np.ndarray, 
    y: np.ndarray, 
    SSERed2: float, 
    Fc2: List[float]
) -> Tuple[np.ndarray, float]:
    """
    Fit a 2-parameter model with zero slope above Cp2 (i.e., 2 connected line segments).
    
    Segment 1: slope = a2(2)
    Segment 2: slope = 0 for x > x(i)
    
    Parameters:
    -----------
    i : int
        Index at which the second segment (flat) starts
    n : int
        Total number of points
    x : np.ndarray
        Data vector of x coordinates
    y : np.ndarray
        Data vector of y coordinates
    SSERed2 : float
        SSE for reduced model (for comparison)
    Fc2 : List[float]
        F-statistic array to be updated
    
    Returns:
    --------
    Tuple[np.ndarray, float]
        iAbv: Indices above i
        Fc2[i]: F-statistic for testing improvement of this model vs. reduced model
    """
    # print('i')
    # print(i)
    # print(type(i))
    # print('n')
    # print(n)
    # print('x')
    # print(x)
    # print(type(x))
    # print(x.dtype)
    # print(x.shape)
    # print(y)
    # print(type(y))
    # print(Fc2)
    # print(type(Fc2))
    # Number of parameters in the 'full' model
    nFull2 = 2
    
    # Indices above i
    iAbv = np.arange(i+1, n)
    
    # Create modified x (x1) by setting x(iAbv) to x(i)
    x1 = x.copy()
    x1[iAbv] = x[i]
    
    # Prepare design matrix for linear regression
    error = (np.ones(n), x1)
    print(error)
    X = np.column_stack((np.ones(n), x1))
    
    # Fit the model: a2[0] is intercept, a2[1] is slope for segment 1
    a2 = np.linalg.lstsq(X, y, rcond=None)[0]
    
    # Predicted values
    yHat2 = a2[0] + a2[1] * x1
    
    # SSE for the 'full' 2-parameter model
    SSEFull2 = np.sum((y - yHat2)**2)
    
    # Compute the F-statistic
    Fc2[i] = (SSERed2 - SSEFull2) / (SSEFull2 / (n - nFull2))
    
    return iAbv, Fc2


def fitOperational3ParamModel(
    i: int,
    iAbv: np.ndarray,
    n: int,
    x: np.ndarray,
    y: np.ndarray,
    SSERed3: float,
    Fc3: np.ndarray
) -> np.ndarray:
    """
    Fit a 3-parameter model representing two connected line segments:
      Segment 1: slope = a3(2)
      Segment 2: slope = a3(2) + a3(3), but zero shift until x > x(i).
    
    This function directly uses variable names from the original MATLAB snippet.

    Parameters
    ----------
    i : int
        The "pivot" index (1-based) for the second segment start (flat until x > x(i)).
    iAbv : np.ndarray
        A 1D array of indices above i (e.g., i+1:n in MATLAB, also 1-based).
    n : int
        Total number of data points.
    x : np.ndarray
        Independent variable data (1D or (n,1) array).
    y : np.ndarray
        Dependent variable data (1D or (n,1) array).
    SSERed3 : float
        SSE for the reduced (2-parameter) model, for comparison.
    Fc3 : np.ndarray
        Array in which the F-statistic for each i will be stored. This function
        writes into Fc3(i) (MATLAB-style), so in Python, `Fc3[i-1]` is modified.

    Returns
    -------
    Fc3_copy : np.ndarray
        A shallow copy of the Fc3 array with the updated F-statistic at position i-1.

    Notes
    -----
    - In MATLAB, the function signature is:

          function [Fc3] = fitOperational3ParamModel(i, iAbv, n, x, y, SSERed3, Fc3)

      and the docstrings mention extra internal variables (zAbv, x1, x2, a3, etc.),
      which are computed here but not returned. Only the updated Fc3 is returned.
    - We assume i and iAbv are 1-based indices, matching MATLAB.
    - A 3-parameter linear model is fit via

          [1, x1, x2] * a3 = y

      where x2 is zero until x > x(i), and then continues with the same slope increment.
    """
    print('i', i)
    # Make shallow copies to avoid modifying the original arrays in-place
    x_copy = x.copy()
    y_copy = y.copy()
    Fc3_copy = Fc3.copy()

    # Number of parameters in the "full" 3-parameter model
    nFull3 = 3

    # Create a zero/one indicator for points above x(i)
    zAbv = np.zeros(n).reshape(-1, 1)
    zAbv[iAbv] = 1.0

    # Define x1 and x2 for the segmented model
    x1 = x_copy
    # x2 is zero until x > x(i), then x - x(i)
    x2 = (x_copy - x_copy[i]) * zAbv

    # Fit the 3-parameter model: a3(1) = intercept, a3(2) = slope, a3(3) = slope increment
    # A = np.column_stack((np.ones(n), x1, x2)) # Matlab mldivide sets the third column to zero then calculates the coefficients using least squares
    # Therefore to mimic the same behaviour, we will set the third column to zero and calculate the coefficients using least squares
    # A = np.column_stack((np.ones(n), x1, np.zeros(n)))
    A = np.column_stack((np.ones(n), x1, x2))
    a3, _, _, _ = np.linalg.lstsq(A, y_copy, rcond=None)

    # Predicted values
    yHat3 = a3[0] + a3[1] * x1 + a3[2] * x2

    # Full model SSE
    SSEFull3 = np.sum((y_copy - yHat3)**2)

    # Compute F-statistic and store in Fc3
    Fc3_copy[i] = (SSERed3 - SSEFull3) / (SSEFull3 / (n - nFull3))
    # Fc3_copy = a3
    return Fc3_copy


def updateS2(
    a2: np.ndarray,
    a2int: np.ndarray,
    Cp2: float,
    Fmax2: float,
    p2: float,
    s2: Dict[str, float]
) -> Dict[str, float]:
    """
    Uses regression coefficients (a2, a2int) and other parameters (Cp2, Fmax2, p2)
    to compute b0, cib0, b1, cib1 and update the fields of the dictionary s2.

    This function mirrors the MATLAB snippet:

        function [s2] = updateS2(a2, a2int, Cp2, Fmax2, p2, s2)

    but uses 0-based indexing internally, as is standard in Python.

    Parameters
    ----------
    a2 : np.ndarray
        Regression coefficients vector, assumed to be of length 2:
        [intercept, slope].
    a2int : np.ndarray
        Confidence intervals for the coefficients, shape (2, 2). 
        Rows: (intercept, slope), Columns: (lower bound, upper bound).
    Cp2 : float
        Change point for the two-parameter model.
    Fmax2 : float
        Maximum F-value for the two-parameter model.
    p2 : float
        p-value corresponding to Fmax2.
    s2 : Dict[str, float]
        Dictionary representing the structure s2 to be updated.

    Returns
    -------
    s2_copy : Dict[str, float]
        A shallow copy of s2 with updated fields:
            - s2['Cp']    = Cp2
            - s2['Fmax']  = Fmax2
            - s2['p']     = p2
            - s2['b0']    = a2[0]
            - s2['b1']    = a2[1]
            - s2['b2']    = np.nan
            - s2['c2']    = np.nan
            - s2['cib0']  = half-width of intercept CI
            - s2['cib1']  = half-width of slope CI
            - s2['cic2']  = np.nan

    Notes
    -----
    - b0 = a2[0] is the intercept.
    - b1 = a2[1] is the slope.
    - cib0 = half the difference between upper and lower intercept CIs.
    - cib1 = half the difference between upper and lower slope CIs.
    - b2, c2, and cic2 are set to NaN in this two-parameter model context.
    """
    print('a2')
    print(a2)
    print('a2int')
    print(a2int)

    # Create a shallow copy of s2 to avoid in-place modifications
    s2_copy = s2.copy()

    # Intercept (b0) and half-width of its confidence interval (cib0)
    b0 = a2[0][0]
    cib0 = 0.5 * (a2int[0, 1] - a2int[0, 0])

    # Slope (b1) and half-width of its confidence interval (cib1)
    b1 = a2[1][0]
    cib1 = 0.5 * (a2int[1, 1] - a2int[1, 0])

    # Update s2_copy fields
    s2_copy["Cp"]   = Cp2
    s2_copy["Fmax"] = Fmax2
    s2_copy["p"]    = p2
    s2_copy["b0"]   = b0
    s2_copy["b1"]   = b1
    s2_copy["b2"]   = np.nan  # not used for the 2-parameter model
    s2_copy["c2"]   = np.nan
    s2_copy["cib0"] = cib0
    s2_copy["cib1"] = cib1
    s2_copy["cic2"] = np.nan

    return s2_copy


def updateS3(
    a3: np.ndarray,
    a3int: np.ndarray,
    xCp3: float,
    Fmax3: float,
    p3: float,
    s3: Dict[str, float]
) -> Dict[str, float]:
    """
    Extract parameters from a3, a3int and update the dictionary s3, mirroring
    the MATLAB 'updateS3' function but with 0-based indexing.

    Parameters
    ----------
    a3 : np.ndarray
        Regression coefficients [b0, b1, b2]. (Shape: (3,))
    a3int : np.ndarray
        Confidence intervals for these coefficients. (Shape: (3, 2))
        Each row corresponds to [lower_bound, upper_bound] for b0, b1, b2.
    xCp3 : float
        Change point for the 3-parameter model.
    Fmax3 : float
        Maximum F-value for the 3-parameter model.
    p3 : float
        p-value corresponding to Fmax3.
    s3 : Dict[str, float]
        Dictionary representing the original s3 struct to update.

    Returns
    -------
    s3_copy : Dict[str, float]
        A shallow copy of s3 with the following updated fields:
            - s3_copy['Cp']   = xCp3
            - s3_copy['Fmax'] = Fmax3
            - s3_copy['p']    = p3
            - s3_copy['b0']   = b0
            - s3_copy['b1']   = b1
            - s3_copy['b2']   = b2
            - s3_copy['c2']   = b1 + b2
            - s3_copy['cib0'] = half the width of the CI for b0
            - s3_copy['cib1'] = half the width of the CI for b1
            - s3_copy['cic2'] = half the width of the CI for b2

    Notes
    -----
    1) In MATLAB, a3(1) => b0, a3(2) => b1, a3(3) => b2, but Python arrays are 0-based:
       a3[0] => b0, a3[1] => b1, a3[2] => b2.
    2) The confidence interval half-width is computed as 0.5 * (upper - lower).
    3) c2 = b1 + b2 is the combined slope for the second segment.
    """

    # Create a shallow copy to avoid modifying the original s3 in-place
    s3_copy = s3.copy()

    # Intercept (b0) and half-width CI
    b0 = a3[0][0]
    cib0 = 0.5 * (a3int[0, 1] - a3int[0, 0])

    # First slope parameter (b1) and half-width CI
    b1 = a3[1][0]
    cib1 = 0.5 * (a3int[1, 1] - a3int[1, 0])

    # Second slope increment (b2) and half-width CI
    b2 = a3[2][0]
    cic2 = 0.5 * (a3int[2, 1] - a3int[2, 0])

    # Combined slope c2
    c2 = b1 + b2

    # Update s3_copy fields
    s3_copy["Cp"]   = xCp3
    s3_copy["Fmax"] = Fmax3
    s3_copy["p"]    = p3
    s3_copy["b0"]   = b0
    s3_copy["b1"]   = b1
    s3_copy["b2"]   = b2
    s3_copy["c2"]   = c2
    s3_copy["cib0"] = cib0
    s3_copy["cib1"] = cib1
    s3_copy["cic2"] = cic2

    return s3_copy


def fitThreeParameterModel(
    Fc3: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    n: int,
    pSig: float
) -> Tuple[float, int, float, np.ndarray, np.ndarray, np.ndarray, float, float]:
    """
    Finds the maximum F-value in Fc3 (three-parameter model), identifies the change point xCp3,
    constructs model variables, performs regression with three parameters, and determines
    whether Cp3 is statistically significant.

    This Python code follows the logic of the MATLAB function:

        function [Fmax3, iCp3, xCp3, a3, a3int, yHat3, p3, Cp3] ...
            = fitThreeParameterModel(Fc3, x, y, n, pSig)

    but uses 0-based indexing internally.

    Parameters
    ----------
    Fc3 : np.ndarray
        Vector of F-values for each potential breakpoint (length n).
    x : np.ndarray
        Independent variable data (length n).
    y : np.ndarray
        Dependent variable data (length n).
    n : int
        Total number of observations (must match the length of x, y, and Fc3).
    pSig : float
        Significance threshold for p3 (e.g., 0.05).
    cpdFmax2pCp3 : Callable[[float, int], float]
        User-defined function that returns a p-value given (Fmax3, n).

    Returns
    -------
    Fmax3 : float
        Maximum value in Fc3.
    iCp3 : int
        0-based index of the maximum F-value in Fc3.
    xCp3 : float
        Value of x at iCp3 (the change point).
    a3 : np.ndarray
        Regression coefficients [intercept, slope, slope_increment].
    a3int : np.ndarray
        95% confidence intervals for each coefficient (shape: (3, 2)).
        Rows: [b0_CI, b1_CI, b2_CI], each a [lower, upper] pair.
    yHat3 : np.ndarray
        Fitted values from the 3-parameter model of size (n,).
    p3 : float
        p-value returned by cpdFmax2pCp3(Fmax3, n).
    Cp3 : float
        Final breakpoint; equals xCp3 if p3 <= pSig, otherwise np.nan.

    Notes
    -----
    - The 3-parameter model is:
         y ~ b0 + b1*x + b2*(x - xCp3)*I(x> xCp3),
      where I(...) is an indicator function (1 if x> xCp3, 0 otherwise).
    - We flatten indices and arrays to 1D for Python’s np.linalg.lstsq.
    - Confidence intervals are computed similarly to MATLAB’s `regress`, using a
      t-distribution quantile for a 95% CI.
    """

    # --- 1) Make shallow copies to avoid modifying external data in place ---
    Fc3_copy = Fc3.copy()
    x_copy = x.copy()
    y_copy = y.copy()

    # --- 2) Find max(Fc3) and its 0-based index ---
    Fmax3 = np.nanmax(Fc3_copy)
    iCp3 = int(np.nanargmax(Fc3_copy))  # 0-based index
    xCp3 = x_copy[iCp3]
    print('Fmax3')  
    print(Fmax3)
    print('iCp3')
    print(iCp3)
    # --- 3) Create indicator vector zAbv for x-values above xCp3 ---
    zAbv = np.zeros((n,1), dtype=float)
    if iCp3 < n - 1:
        zAbv[iCp3 + 1 :] = 1.0

    # --- 4) Define regression variables for the 3-parameter model ---
    x1 = x_copy
    x2 = (x_copy - xCp3) * zAbv
    print('zAbv')
    print(zAbv)
    print('x1')
    # print(x1)
    print('x2')
    # print(x2)
    # --- 5) Ordinary least squares on [1, x1, x2] to get a3 ---
    A = np.column_stack((np.ones(n), x1, x2))
    a3, residuals, rank, svals = np.linalg.lstsq(A, y_copy, rcond=None)
    yHat3 = A @ a3
    # --- 6) Compute 95% confidence intervals for a3 (mimicking MATLAB regress) ---
    # Residual sum of squares (SSE)
    SSE = np.sum((y_copy - yHat3) ** 2)
    # Degrees of freedom
    df = n - rank  
    # Mean square error
    MSE = SSE / df
    # Covariance of coefficients
    # print(A)
    print(A.shape)
    ATA_inv = np.linalg.inv(A.T @ A)
    var_a3 = np.diag(ATA_inv) * MSE
    se_a3 = np.sqrt(var_a3)

    # For a 95% two-sided CI, get t critical value
    from scipy.stats import t
    tval = t.ppf(0.975, df)
    print('tval')
    print(tval)
    print('se_a3')
    print(se_a3)
    print('a3')
    print(a3)
    # Compute lower/upper bounds
    a3_lower = a3.flatten() - tval * se_a3
    a3_upper = a3.flatten() + tval * se_a3
    # Stack them into (3, 2)
    a3int = np.column_stack((a3_lower, a3_upper))
    print('a3int')
    print(a3int)

    # --- 7) Compute p-value for Fmax3 via user-defined function ---
    p3 = cpdFmax2pCp3(Fmax3, n)

    # --- 8) Decide if Cp3 is significant ---
    if p3 > pSig:
        Cp3 = np.nan
    else:
        Cp3 = xCp3

    return Fmax3, iCp3, xCp3, a3, a3int, yHat3, p3, Cp3


def fitTwoParameterModel(
    Fc2: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    n: int,
    pSig: float
) -> Tuple[float, int, float, np.ndarray, np.ndarray, np.ndarray, float, float]:
    """
    Finds the maximum F-value in Fc2, identifies the corresponding 0-based index (iCp2),
    constructs a two-parameter (piecewise) model with a breakpoint at x[iCp2],
    computes regression coefficients and their 95% confidence intervals, then
    tests for the significance of that breakpoint.

    Parameters
    ----------
    Fc2 : np.ndarray
        Vector of F-values for each potential breakpoint (shape (n,)).
    x : np.ndarray
        Independent variable data (shape (n,)).
    y : np.ndarray
        Dependent variable data (shape (n,)).
    n : int
        Total number of observations (should match the length of x, y, and Fc2).
    pSig : float
        Significance threshold for the p-value (e.g., 0.05).
    cpdFmax2pCp2 : callable
        A user-defined function that computes the p-value given (Fmax2, n).
        Must have signature like:  p2 = cpdFmax2pCp2(F_value, n_points).

    Returns
    -------
    Fmax2 : float
        Maximum F-value found in Fc2.
    iCp2 : int
        0-based index at which Fmax2 occurs.
    xCp2 : float
        Value of x at iCp2.
    a2 : np.ndarray
        Regression coefficients [intercept, slope] from the modified model.
    a2int : np.ndarray
        95% confidence intervals for each coefficient, shape (2, 2).
        Rows correspond to (intercept, slope), columns to (lower bound, upper bound).
    yHat2 : np.ndarray
        Fitted values for the two-parameter (piecewise) model.
    p2 : float
        p-value computed via `cpdFmax2pCp2(Fmax2, n)`.
    Cp2 : float
        Final breakpoint; set to xCp2 if p2 <= pSig; otherwise NaN.

    Notes
    -----
    1) Unlike MATLAB, this code uses **0-based** indexing, so iCp2 is a
       Python-style index into x, y, and Fc2.
    2) The two-parameter piecewise model is constructed by:
       - Keeping x unchanged up through iCp2,
       - Forcing x[i] = xCp2 for all i > iCp2,
       thus flattening the slope beyond iCp2.
    3) The regression is performed via ordinary least squares:
         A = [1, x1],  a2 = (A^T A)^{-1} A^T y
       We then estimate the 95% confidence intervals by a standard
       OLS variance-covariance approach and a two-sided t-quantile.
    """

    # --- Make shallow copies to avoid modifying external data in-place ---
    Fc2_copy = Fc2.copy()
    x_copy = x.copy()
    y_copy = y.copy()

    # --- 1) Find maximum Fc2 and 0-based index iCp2 ---
    Fmax2 = np.nanmax(Fc2_copy)
    iCp2 = int(np.nanargmax(Fc2_copy))  # 0-based index
    xCp2 = x_copy[iCp2]

    # --- 2) Create x1 by forcing all values after iCp2 to xCp2 ---
    x1 = x_copy.copy()
    if iCp2 < n - 1:
        x1[iCp2 + 1 :] = xCp2

    # --- 3) Perform linear regression on [1, x1] ---
    A = np.column_stack((np.ones(n), x1))
    a2, residuals, rank, svals = np.linalg.lstsq(A, y_copy, rcond=None)
    yHat2 = A @ a2

    # --- 4) Compute SSE, MSE, and degrees of freedom for CI calculation ---
    SSE = np.sum((y_copy - yHat2) ** 2)
    df = n - rank  # degrees of freedom based on the regression rank
    MSE = SSE / df

    # Covariance of the coefficients:
    ATA_inv = np.linalg.inv(A.T @ A)  # (X^T X)^{-1}
    var_a2 = np.diag(ATA_inv) * MSE
    se_a2 = np.sqrt(var_a2)

    # 95% confidence intervals using the two-sided t-distribution
    tval = t.ppf(0.975, df)
    a2_lower = a2.flatten() - tval * se_a2
    a2_upper = a2.flatten() + tval * se_a2
    # Combine into a (2 x 2) array, rows = [intercept, slope], cols = [lower, upper]
    a2int = np.column_stack((a2_lower, a2_upper))

    # --- 5) Compute p-value for Fmax2 using user-defined function ---
    p2 = cpdFmax2pCp2(Fmax2, n)

    # --- 6) Decide if Cp2 is significant ---
    Cp2 = xCp2 if p2 <= pSig else np.nan

    return Fmax2, iCp2, xCp2, a2, a2int, yHat2, p2, Cp2

