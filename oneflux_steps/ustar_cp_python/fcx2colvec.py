import numpy as np

def fcx2colvec(x: np.ndarray) -> np.ndarray:
    """
    Converts an input array `x` to an n x 1 column vector using column-major ordering.

    This function reshapes the input array into a two-dimensional array with
    a single column, preserving all elements of the original array using
    column-major order.

    Args:
        x (np.ndarray): Input array to be reshaped.

    Returns:
        np.ndarray: Reshaped array as a column vector.

    Example:
        >>> import numpy as np
        >>> x = np.array([[1, 2], [3, 4]])
        >>> fcx2colvec(x)
        array([[1],
               [3],
               [2],
               [4]])
    """
    return np.reshape(x, (-1, 1), order='F')
