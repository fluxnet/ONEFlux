import pytest
import matlab
import numpy as np


@pytest.mark.parametrize(
    "input_data, expected",
    [
        # Case 1: 1D Row Vector
        (matlab.double([1, 2, 3]), [1, 2, 3]),

        # Case 2: 1D Column Vector
        (matlab.double([[1], [2], [3]]), [1, 2, 3]),

        # Case 3: 2D Matrix (3x2)
        (matlab.double([[1, 2], [3, 4], [5, 6]]), [1, 3, 5, 2, 4, 6]),  # MATLAB is column-major!

        # Case 4: 3D Array (2x2x2)
        (
            matlab.double([[[1, 2], [3, 4]], [[5, 6], [7, 8]]]),
            [1, 5, 3, 7, 2, 6, 4, 8],  # MATLAB flattens column-major first!
        ),

        # Case 5: Empty Array (Expect float if MATLAB returns scalar)
        (matlab.double([]), []),

        # Case 6: Single Element
        (matlab.double([5]), [5]),

        # Case 7: Large Matrix
        (
            matlab.double(np.arange(1, 101).reshape(10, 10).tolist()),
            list(np.arange(1, 101).reshape(10, 10, order="F").flatten()),
        ),

        # Case 8: NaN Data
        (
            matlab.double([[float('nan'), 2], [3, float('nan')]]),
            [float('nan'), 3, 2, float('nan')],
        ),
    ],
)
def test_fcx2rowvec(matlab_engine, input_data, expected):
    """
    Test MATLAB's fcx2rowvec function with various matrices and arrays, verifying reshaping.
    """
    # Call MATLAB function
    result = matlab_engine.fcx2rowvec(input_data)

    # Extract values from MATLAB result
    if isinstance(result, float):  # Scalar result from MATLAB
        result_list = [result]
    elif isinstance(result, matlab.double):  # Array result from MATLAB
        result_list = list(result[0]) if len(result) > 0 else []
    else:
        raise TypeError(f"Unexpected result type: {type(result)}")

    # Compare expected and actual results
    assert len(result_list) == len(expected), "Result length mismatch"
    for idx, exp_val in enumerate(expected):
        if np.isnan(exp_val):
            assert np.isnan(result_list[idx]), f"Expected NaN, got {result_list[idx]} at index {idx}"
        else:
            assert result_list[idx] == exp_val, f"Expected {exp_val}, got {result_list[idx]} at index {idx}"
