import matlab
import numpy as np
import pytest

# Parameterized Test Cases
@pytest.mark.parametrize(
    "vector, expected",
    [
        # Case 1: Array is 3 and has no NaNs
        (matlab.double([[1], [2], [3]]), 1.5),  # IQR of [1, 2, 3]

        # Case 2: Array >3, contains NaNs, but has >3 real numbers
        (matlab.double([[1], [2], [3], [4], [np.nan], [6]]), np.nan),

        # Case 3: Array >3, contains NaNs, but has 3 or fewer real numbers
        # Note this result is erroneous!
        (matlab.double([[np.nan], [2], [3] ,[np.nan]]), 1.0),

        # Case 4: Array >3 and has no NaNs
        (matlab.double([[1], [2], [3], [4], [5]]), np.nan),
    ],
)
def test_fcnaniqr_vector_cases(matlab_engine, vector, expected):
    """
    Test MATLAB's fcNaniqr function with different 1D vectors, including edge cases.
    """
    # Call MATLAB function
    result = matlab_engine.fcNaniqr(vector)

    # Check for None result
    assert result is not None, "Expected non-None result from MATLAB function"

    # Check if result is correct (accounting for NaNs)
    if np.isnan(expected):
        assert np.isnan(result), f"Expected NaN, but got {result}"
    else:
        assert np.isclose(result, expected), f"Expected {expected}, got {result}"

@pytest.mark.parametrize(
    "matrix, expected",
    [
        # Case 1a: No NaNs, Fully Populated, column length = 3
        (matlab.double([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), [np.nan, np.nan, np.nan]),

        # Case 1b: No NaNs, Fully Populated, column length = 4
        (matlab.double([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]), [6.0, 6.0, 6.0]),

        # Case 2a: Columns with NaNs, column length = 3
        (matlab.double([[1, np.nan, 3], [4, np.nan, 6], [7, 8, 9]]), [np.nan, np.nan, np.nan]),

        # Case 2b: Columns with NaNs, column length >3 (after nans ignored)
        (matlab.double([[1, np.nan, 3], [4, np.nan, 6], [7, 8, 9], [10,11,12]]), [6.0, np.nan, 6.0]),

        # Case 3: Columns with < 4 Real Rows
        #Note weird behaviour of IQR estimation
        (matlab.double([[1, np.nan], [2, 3]]), [1.5, np.nan]),

        # Case 4: All NaNs
        (matlab.double([[np.nan, np.nan], [np.nan, np.nan]]), [np.nan, np.nan]),

        # Case 5: Different Column Lengths
        (matlab.double([[1, 2], [4, np.nan], [7, 8], [10, 12]]), [6, np.nan]),
    ],
)
def test_fcnaniqr_2D_cases(matlab_engine, matrix, expected):
    """
    Test MATLAB's fcNaniqr function with 2D matrices, including edge cases.
    """
    # Call MATLAB function
    result = matlab_engine.fcNaniqr(matrix)

    # Verify Result
    assert result is not None, "Expected non-None result from MATLAB function"

    # Normalize result to ensure consistent access
    if isinstance(result, float):  # Scalar result
        result = [[result]]
    elif isinstance(result, list) and isinstance(result[0], float):  # 1D result from MATLAB
        result = [result]

    # Check each column's IQR
    for idx, exp_val in enumerate(expected):
        # Access the correct result value
        try:
            result_value = result[0][idx] if len(result[0]) > idx else np.nan
        except (IndexError, TypeError):
            result_value = np.nan

        # Perform the assertion
        if np.isnan(exp_val):
            assert np.isnan(result_value), f"Expected NaN, got {result_value} for column {idx}"
        else:
            assert np.isclose(result_value, exp_val), f"Expected {exp_val}, got {result_value} for column {idx}"

@pytest.mark.parametrize(
    "matrix, expected",
    [
        # Case 1a: No NaNs, Fully Populated, 2 rows (<3)
        (matlab.double([[[1, 2], [4, 5]], [[7, 8], [10, 11]]]), [[np.nan, np.nan]]),

        # Case 1b: No NaNs, Fully Populated, 4 rows (>3)
        (matlab.double([[[1, 2], [4, 5]],[[7, 8], [10, 11]],[[13, 14], [16, 17]],[[19, 20], [22, 23]]]), [[12.0, 12.0]]),

        # Case 1b: Single NaN, Fully Populated, 4 rows (>3)
        (matlab.double([[[np.nan, 2], [4, 5]],[[7, 8], [10, 11]],[[13, 14], [16, 17]],[[19, 20], [22, 23]]]), [[np.nan, 12.0]]),

        # Case 1c: Single Layer 3D
        (matlab.double([[[1, 2, 3]], [[4, 5, 6]], [[7, 8, 9]]]), [[np.nan, np.nan, np.nan]]),

        # Case 2a: Contains NaNs
        (matlab.double([[[1, np.nan], [4, 5]], [[np.nan, 8], [7, np.nan]]]), [[np.nan, np.nan]]),

        # Case 2b: Mixed NaNs with Real
        (matlab.double([[[1, np.nan], [4, 5]], [[7, 8], [10, 11]]]), [[np.nan, np.nan]]),

        # Case 3: All NaNs
        (matlab.double([[[np.nan, np.nan], [np.nan, np.nan]], [[np.nan, np.nan], [np.nan, np.nan]]]), [[np.nan, np.nan]]),

        # Case 5b: Different Column Lengths
        (matlab.double([[[1, 2], [4, 5]], [[7, 8], [10, 12]], [[13, 14], [16, 18]], [[19, 20], [22, 24]]]), [[12, 12]]),
    
    ],
)
def test_fcnaniqr_3D_cases(matlab_engine, matrix, expected):
    """
    Test MATLAB's fcNaniqr function with 3D matrices, including edge cases.
    """
    # Call MATLAB function
    result = matlab_engine.fcNaniqr(matrix)

    # Verify Result
    assert result is not None, "Expected non-None result from MATLAB function"

    # Normalize result to ensure consistent access
    if isinstance(result, float):  # Scalar result
        result = [[result]]
    elif isinstance(result, list) and isinstance(result[0], float):  # 1D result from MATLAB
        result = [result]

    # Check each column's IQR
    for row_idx, expected_row in enumerate(expected):
        for col_idx, exp_val in enumerate(expected_row):
            # Access the correct result value
            try:
                result_value = result[row_idx][col_idx] if len(result[row_idx]) > col_idx else np.nan
            except (IndexError, TypeError):
                result_value = np.nan

            # Perform the assertion
            if np.isnan(exp_val):
                assert np.isnan(result_value), f"Expected NaN, got {result_value} for row {row_idx}, col {col_idx}"
            else:
                assert np.isclose(result_value, exp_val), f"Expected {exp_val}, got {result_value} for row {row_idx}, col {col_idx}"