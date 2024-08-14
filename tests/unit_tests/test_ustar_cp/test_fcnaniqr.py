# test_fcnaniqr.py

import matlab.engine
import pytest

def test_fcnaniqr_vector(matlab):
    # Test case for vector input
    
    X = matlab.double([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    IQR = matlab.fcnaniqr(X)
    assert IQR == pytest.approx(5.0, rel=1e-2)  # Expected IQR for the given vector

def test_fcnaniqr_2d_matrix(matlab):
    # Test case for 2D matrix input
    
    X = matlab.double([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
    IQR = matlab.fcnaniqr(X)
    expected_IQR = [5.0, 5.0, 5.0]  # Expected IQR for each column
    assert IQR == pytest.approx(expected_IQR, rel=1e-2)

def test_fcnaniqr_3d_array(matlab):
    # Test case for 3D array input
    
    X = matlab.double([
        [[1, 2], [3, 4]],
        [[5, 6], [7, 8]],
        [[9, 10], [11, 12]]
    ])
    IQR = matlab.fcnaniqr(X)
    expected_IQR = [
        [5.0, 5.0],
        [5.0, 5.0]
    ]  # Expected IQR for each 2D slice
    assert IQR == pytest.approx(expected_IQR, rel=1e-2)

def test_fcnaniqr_with_nans(matlab):
    # Test case for input with NaNs
    
    X = matlab.double([[1, 2, None], [None, 5, 6], [7, 8, None], [10, 11, 12]])
    IQR = matlab.fcnaniqr(X)
    expected_IQR = [5.0, 5.0, 6.0]  # Expected IQR for each column ignoring NaNs
    assert IQR == pytest.approx(expected_IQR, rel=1e-2)

def test_fcnaniqr_small_vector(matlab):
    # Test case for small vector input where IQR cannot be computed
    
    X = matlab.double([1, 2, None])
    IQR = matlab.fcnaniqr(X)
    assert IQR == float('nan')  # Not enough data to compute IQR
