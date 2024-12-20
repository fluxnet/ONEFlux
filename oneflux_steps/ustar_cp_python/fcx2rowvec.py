import numpy as np

def fcx2rowvec(x: np.ndarray) -> np.ndarray:
    """
    Converts an input array `x` to a 1 x n row vector using MATLAB-style column-major order.

    This function reshapes the input array into a two-dimensional array with
    a single row, preserving all elements of the original array in column-major order.

    Args:
        x (np.ndarray): Input array to be reshaped.

    Returns:
        np.ndarray: Reshaped array as a row vector.

    Example:
        >>> import numpy as np
        >>> x = np.array([[1, 2], [3, 4]])
        >>> fcx2rowvec(x)
        array([[1, 3, 2, 4]])
    """
    return np.reshape(x, (1, -1), order='F')
