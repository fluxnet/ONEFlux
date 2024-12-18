import numpy as np
from typing import Union
from oneflux_steps.ustar_cp_python.utilities import prctile

def get_dims(X: np.ndarray) -> int:
    """Return the number of non-singleton dimensions in X."""

    # np.squeeze to remove singleton dims
    shape = np.squeeze(X).shape

    unique_dims = np.unique(shape)

    return len(unique_dims)

def iqr_1D_eval(X: np.ndarray) -> Union[float, np.ndarray]:
    """Evaluate IQR for a 1D array, ignoring NaNs."""
    valid_values = X[~np.isnan(X)]
    if len(valid_values) <= 3:
        return prctile(valid_values, 75) - prctile(valid_values, 25)
    return np.nan

def iqr_2d_eval(X: np.ndarray) -> np.ndarray:
    """
    Compute the interquartile range (IQR) for each column in a 2D array, ignoring NaNs.

    Args:
        X (np.ndarray): 2D input array.

    Returns:
        np.ndarray: 1D array of IQR values for each column.
    """

    IQR = np.full(X.shape[1], np.nan)
    
    for ic in range(X.shape[1]):
        column = X[:, ic]
        valid_values = column[~np.isnan(column)]
        if len(valid_values) >= 4:
            q25 = prctile(valid_values, 25)
            q75 = prctile(valid_values, 75)
            IQR[ic] = q75 - q25
        else:
            IQR[ic] = np.nan  # Ensure consistent behavior with MATLAB
    
    return IQR

def iqr_3d_eval(X: np.ndarray) -> np.ndarray:
    """
    Evaluate IQR for a 3D array along the first non-singleton dimension, ignoring NaNs.

    Args:
        X (np.ndarray): 3D input array.

    Returns:
        np.ndarray: 2D array of IQR values for each slice.
    """

    nc, nq = X.shape[1], X.shape[2]  # Correcting to MATLAB-like ordering
    IQR = np.full((nc, nq), np.nan)  # Ensure a 2D array of correct shape

    for ic in range(nc):
        for iq in range(nq):
            column = X[:, ic, iq]
            valid_values = column[~np.isnan(column)]

            if valid_values.size >3:  # Ensure 4+ valid values
                q25 = prctile(valid_values, 25)
                q75 = prctile(valid_values, 75)
                IQR[ic, iq] = q75 - q25
            else:
                IQR[ic, iq] = np.nan

    return IQR


def fcNaniqr(X: np.ndarray) -> Union[float, np.ndarray]:
    """
    Compute the interquartile range (IQR) of the values in X, ignoring NaNs.

    This function is a simplified version of MATLAB's IQR function, supporting up to
    3-dimensional arrays. It computes the IQR along the first non-singleton dimension
    of X, treating NaNs as missing values.

    - For 1D input, IQR is returned as a scalar.
    - For 2D input, IQR is computed along columns, returning a row vector.
    - For 3D input, IQR is computed along the first non-singleton dimension, returning
      a 2D array.

    The IQR is a robust measure of data spread, unaffected by changes in the top or
    bottom 25% of data points.

    Args:
        X (np.ndarray): Input array of up to 3 dimensions.

    Returns:
        Union[float, np.ndarray]: IQR of X computed along the first non-singleton dimension.

    Raises:
        ValueError: If X has more than 3 dimensions.
    """
    if X.ndim > 3:
        raise ValueError("X cannot exceed 3 dimensions.")

    nd = get_dims(X)

    return {
        1: lambda: iqr_1D_eval(X),
        2: lambda: iqr_2d_eval(X),
        3: lambda: iqr_3d_eval(X)
    }.get(nd, lambda: np.nan)()
