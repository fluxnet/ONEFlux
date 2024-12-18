import pytest
import matlab.engine
from tests.conftest import to_matlab_type, compare_matlab_arrays
from oneflux_steps.ustar_cp_python.fcx2colvec import fcx2colvec
import numpy as np

@pytest.mark.parametrize(
    "input_data, expected",
    [
        # Case 1: 1D Row Vector
        ([1, 2, 3], [[1], [2], [3]]),

        # Case 2: 1D Column Vector
        ([[1], [2], [3]], [[1], [2], [3]]),

        # Case 3: 2D Matrix (3x2)
        ([[1, 2], [3, 4], [5, 6]], [[1], [3], [5], [2], [4], [6]]),  # Column-major!

        # Case 4: 3D Array (2x2x2)
        (
            [[[1, 2], [3, 4]], [[5, 6], [7, 8]]],
            [[1], [5], [3], [7], [2], [6], [4], [8]],  # Column-major flattening
        ),

        # Case 5: Empty Array
        ([], []),

        # Case 6: Single Element
        ([5], [[5]]),

        # Case 7: NaN Data
        (
            [[float('nan'), 2], [3, float('nan')]],
            [[float('nan')], [3], [2], [float('nan')]],
        ),
    ],
)
def test_fcx2colvec(test_engine, input_data, expected):
    """
    Test fcx2colvec function with various inputs and expected results.
    """
    result = test_engine.fcx2colvec(test_engine.convert(input_data))

    # Test outcomes
    assert test_engine.equal(result, test_engine.convert(expected))

