import pytest
import matlab.engine
from tests.conftest import to_matlab_type, compare_matlab_arrays

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
def test_fcx2colvec(test_engine, input_data, expected):
    """
    Test MATLAB's fcx2colvec function with various inputs and expected results.
    """
    # Call MATLAB function
    result = test_engine.fcx2colvec(input_data)
    assert compare_matlab_arrays(result, to_matlab_type(expected))
