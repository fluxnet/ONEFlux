import pytest
import matlab.engine
import numpy as np


@pytest.mark.parametrize(
    "input_data, expected",
    [
        # Case 1: 1D Row Vector
        (matlab.double([1, 2, 3]), [[1], [2], [3]]),

        # Case 2: 1D Column Vector
        (matlab.double([[1], [2], [3]]), [[1], [2], [3]]),

        # Case 3: 2D Matrix (3x2)
        (matlab.double([[1, 2], [3, 4], [5, 6]]), [[1], [3], [5], [2], [4], [6]]),  # Column-major!

        # Case 4: 3D Array (2x2x2)
        (
            matlab.double([[[1, 2], [3, 4]], [[5, 6], [7, 8]]]),
            [[1], [5], [3], [7], [2], [6], [4], [8]],  # Column-major flattening
        ),

        # Case 5: Empty Array
        (matlab.double([]), []),

        # Case 6: Single Element
        (matlab.double([5]), [[5]]),

        # Case 7: NaN Data
        (
            matlab.double([[float('nan'), 2], [3, float('nan')]]),
            [[float('nan')], [3], [2], [float('nan')]],
        ),
    ],
)
def test_fcx2colvec(matlab_engine, input_data, expected):
    """
    Test MATLAB's fcx2colvec function with various inputs and expected results.
    """
    # Call MATLAB function
    result = matlab_engine.fcx2colvec(input_data)

    try:
        if isinstance(result, matlab.double):
            # Convert to a nested list structure
            result_list = [list(row) for row in result]
        elif isinstance(result, (float, int)):
            # Handle single numbers as a 1x1 list
            result_list = [[float(result)]]
        else:
            raise TypeError(f"Unexpected result type: {type(result)}")
    except Exception as e:
        pytest.fail(f"Unexpected extraction error: {e}")

    # Compare expected and actual results
    assert len(result_list) == len(expected), "Result length mismatch"
    for idx, exp_val in enumerate(expected):
        if np.isnan(exp_val[0]):
            assert np.isnan(result_list[idx][0]), f"Expected NaN, got {result_list[idx][0]} at index {idx}"
        else:
            assert result_list[idx][0] == exp_val[0], f"Expected {exp_val[0]}, got {result_list[idx][0]} at index {idx}"
