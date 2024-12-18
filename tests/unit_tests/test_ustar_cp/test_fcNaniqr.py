import matlab
import numpy as np
import pytest


# Parameterized Test Cases
@pytest.mark.parametrize(
    "vector, expected",
    [
        # Case 1: Array is 3 and has no NaNs
        (([[1], [2], [3]]), 1.5),  # IQR of [1, 2, 3]

        # Case 2: Array >3, contains NaNs, but has >3 real numbers
        (([[1], [2], [3], [4], [np.nan], [6]]), np.nan),

        # Case 3: Array >3, contains NaNs, but has 3 or fewer real numbers
        # Note this result is erroneous!
        ([[np.nan], [2], [3] ,[np.nan]], 1.0),

        # Case 4: Array >3 and has no NaNs
        ([[1], [2], [3], [4], [5]], np.nan),
    ],
)
def test_fcnaniqr_vector_cases(test_engine, vector, expected):
    """
    Test MATLAB's fcNaniqr function with different 1D vectors, including edge cases.
    """
    
    # Call function
    result = test_engine.fcNaniqr(test_engine.convert(vector))

    # Check for None result
    assert result is not None, "Expected non-None result from MATLAB function"

    assert test_engine.equal(result, test_engine.convert(expected))

@pytest.mark.parametrize(
    "matrix, expected",
    [
        # Case 1a: No NaNs, Fully Populated, column length = 3
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]], [np.nan, np.nan, np.nan]),

        # Case 1b: No NaNs, Fully Populated, column length = 4
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], [6.0, 6.0, 6.0]),

        # Case 2a: Columns with NaNs, column length = 3
        ([[1, np.nan, 3], [4, np.nan, 6], [7, 8, 9]], [np.nan, np.nan, np.nan]),

        # Case 2b: Columns with NaNs, column length >3 (after nans ignored)
        ([[1, np.nan, 3], [4, np.nan, 6], [7, 8, 9], [10,11,12]], [6.0, np.nan, 6.0]),

        # Case 3: Columns with < 4 Real Rows
        #Note weird behaviour of IQR estimation
        ([[1, np.nan], [2, 3]], [1.5]),

        # Case 4: All NaNs
        ([[np.nan, np.nan], [np.nan, np.nan]], [np.nan, np.nan]),
    ],
)
def test_fcnaniqr_2D_cases(test_engine, matrix, expected):
    """
    Test MATLAB's fcNaniqr function with 2D matrices, including edge cases.
    """
    # Call function
    result = test_engine.fcNaniqr(test_engine.convert(matrix))

    # Verify Result
    assert result is not None, "Expected non-None result from MATLAB function"

    assert test_engine.equal(result, test_engine.convert(expected))

@pytest.mark.parametrize(
    "matrix, expected",
    [
        # Case 1a: No NaNs, Fully Populated, 2 rows (<3)
        ([[[1, 2], [4, 5]], [[7, 8], [10, 11]]], [[np.nan, np.nan]]),

        # Case 1b: No NaNs, Fully Populated, 4 rows (>3)
        ([[[1, 2], [4, 5]],[[7, 8], [10, 11]],[[13, 14], [16, 17]],[[19, 20], [22, 23]]], [[12.0, 12.0, 12.0, 12.0]]),

        # Case 1b: Single NaN, Fully Populated, 4 rows (>3)
        ([[[np.nan, 2], [4, 5]],[[7, 8], [10, 11]],[[13, 14], [16, 17]],[[19, 20], [22, 23]]], [[np.nan, 12.0, 12.0, 12.0]]),

        # Case 1c: Single Layer 3D
        ([[[1, 2, 3]], [[4, 5, 6]], [[7, 8, 9]]], [[np.nan, np.nan, np.nan]]),

        # Case 2a: Contains NaNs
        ([[[1, np.nan], [4, 5]], [[np.nan, 8], [7, np.nan]]], [[np.nan, np.nan]]),

        # Case 2b: Mixed NaNs with Real
        ([[[1, np.nan], [4, 5]], [[7, 8], [10, 11]]], [[np.nan, np.nan]]),

        # Case 3: All NaNs
        ([[[np.nan, np.nan], [np.nan, np.nan]], [[np.nan, np.nan], [np.nan, np.nan]]], [[np.nan, np.nan]]),
    ],
)
def test_fcnaniqr_3D_cases(test_engine, matrix, expected):
    """
    Test MATLAB's fcNaniqr function with 3D matrices, including edge cases.
    """
    # Call function
    result = test_engine.fcNaniqr(test_engine(matrix))

    # Verify Result
    assert result is not None, "Expected non-None result from MATLAB function"

    assert test_engine.equal(result, test_engine.convert(expected))

TEST_CASES_dims = [
    ["1D vector", [[1], [2], [3], [4]], 1],
    ["2D matrix", [[1, 2, 3], [4, 5, 6]], 2],
    ["3D matrix, shape 3,4,5", [[[1]*5]*4]*3, 3],
    ["Singleton dimensions", [[[1]]*5]*3, 2],
    ["Empty array", [], 1.0],
    ["Large array", [[[1]*3]*2000]*1000, 3],
    ["High-dimensional array", [[[[[1]*6]*5]*4]*3]*2, 5],
    ["Trailing singleton dimension", [[[1]]*4]*4, 1],
    ["Leading and trailing singleton dimensions", [[[[1]]*4]*4], 1],
    ["Fully singleton array", [[[[1]]]], 0],
    ["Mixed regular and singleton dimensions", [[[1]]*9]*10, 2],
    ["High-dimensional with many singletons", [[[[[[1]]]*10]*1]*1]*10, 1],
]

@pytest.mark.parametrize("description, X, expected", TEST_CASES_dims)
def test_get_dims(test_engine, description, X, expected):
    """Parameterized test for various inputs with MATLAB column-major consideration."""
    # Run function

    result = test_engine.get_dims(test_engine.convert(X))

    assert test_engine.equal(result, test_engine.convert(X))



TEST_CASES = [
    ["All NaNs", [np.nan, np.nan, np.nan], np.nan],
    ["Single value", [5], 0],
    ["Two values", [1, 9], 8],
    ["Three values no NaNs", [1, 5, 9], 6.0],
    ["Three values with NaNs", [1, np.nan, 9], 8],
    ["All identical", [4, 4, 4], 0],
    ["Mixed values", [2, 8, 4, 6], np.nan], #returns default nan value due to len(X)>3 
    ["Negative values", [-5, -1, -3], 3],
    ["Zeroes and positives", [0, 1, 2], 1.5],
    ["Contains zeros and NaNs", [0, np.nan, 0, 0], 0],
]

@pytest.mark.parametrize("description, X, expected", TEST_CASES)
def test_iqr_1d_eval(test_engine, description, X, expected):
    """Parameterized test for IQR evaluation in 1D arrays."""
    matlab_array = test_engine.convert([[x] for x in X])
    result = test_engine.iqr_1D_eval(matlab_array)
    
    assert test_engine.equal(result, test_engine.convert([[x] for x in expected]))

TEST_CASES_2D = [
    ["All NaNs, column =< 3", [[np.nan, np.nan], [np.nan, np.nan]], [np.nan, np.nan]],
    ["Single column, same values", [[5], [5], [5], [5]], [0]],
    ["Single column, different values", [[5], [6], [7], [8]], [2]],
    ["Two columns, distinct values", [[1, 9], [2, 8], [3, 7], [4, 6]], [2, 2]],
    ["Mixed NaNs and values", [[1, np.nan], [2, 8], [np.nan, 7], [4, np.nan]], [np.nan, np.nan]],
    ["Identical columns", [[4, 4], [4, 4], [4, 4], [4, 4]], [0, 0]],
    ["Negative values", [[-5, -1], [-4, -2], [-3, -3], [-2, -4]], [2, 2]],
    ["Zeros and positives", [[0, 1], [1, 2], [2, 3], [3, 4]], [2, 2]],
    ["Zeros and NaNs", [[0, np.nan], [0, 0], [0, np.nan], [0, 0]], [0, np.nan]],
]

@pytest.mark.parametrize("description, X, expected", TEST_CASES_2D)
def test_iqr_2d_eval(test_engine, description, X, expected):
    """Parameterized test for IQR evaluation in 2D arrays."""
    
    result = test_engine.iqr_2d_eval(test_engine.convert(X))
    
    assert test_engine.equal(result, test_engine.convert(expected))

TEST_CASES_3D = [
    ["Single slice", [[[5, 5]], [[5, 5]], [[5, 5]], [[5, 5]]], [[0, 0]]],
    ["Two slices, distinct values", [[[1, 9], [2, 8]], [[3, 7], [4, 6]], [[5, 5], [6, 4]], [[7, 3], [8, 2]]], [[4, 4], [4, 4]]],
    ["Mixed NaNs and values", [[[1, np.nan], [2, 8]], [[np.nan, 7], [4, np.nan]], [[3, 5], [np.nan, 6]], [[7, np.nan], [8, 1]]], [[np.nan, np.nan], [np.nan, np.nan]]],
    ["Identical slices", [[[4, 4], [4, 4]], [[4, 4], [4, 4]], [[4, 4], [4, 4]], [[4, 4], [4, 4]]], [[0, 0], [0, 0]]],
    ["Negative values", [[[ -5, -1], [-4, -2]], [[ -3, -3], [-2, -4]], [[ -1, -5], [0, -6]], [[-7, -8], [-9, -10]]], [[4, 4.5], [5.5, 5]]],
    ["Zeros and positives", [[[0, 1], [1, 2]], [[2, 3], [3, 4]], [[4, 5], [5, 6]], [[6, 7], [7, 8]]], [[4, 4], [4, 4]]],
    ["Zeros and NaNs", [[[0, np.nan], [0, 0]], [[0, np.nan], [0, 0]], [[0, np.nan], [0, 0]], [[0, np.nan], [0, 0]]], [[0, np.nan], [0, 0]]],
]

@pytest.mark.parametrize("description, X, expected", TEST_CASES_3D)
def test_iqr_3d_eval(test_engine, description, X, expected):
    """Parameterized test for IQR evaluation in 3D arrays."""
    # Evaluate matlab
    # Ensure MATLAB-compatible 3D array creation
    matlab_array = matlab.double([[[float(val) for val in row] for row in slice_] for slice_ in X])
    result = test_engine.iqr_3d_eval(matlab_array)
    
    # Convert both to numpy arrays for consistent comparison
    result_np = np.asarray(result)

    expected_np = np.asarray(expected)

    # Assert comparison with NaN handling
    assert np.allclose(result_np, expected_np, equal_nan=True), (
        f"{description}: Expected {expected_np} but got {result_np}"
    )

