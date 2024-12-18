import pytest
import numpy as np
from tests.conftest

@pytest.mark.parametrize(
    "input_data, expected",
    [
        # Case 1: 1D Row Vector
        ([1, 2, 3], [1, 2, 3]),

        # Case 2: 1D Column Vector
        ([[1], [2], [3]], [1, 2, 3]),

        # Case 3: 2D Matrix (3x2)
        ([[1, 2], [3, 4], [5, 6]], [1, 3, 5, 2, 4, 6]),  # MATLAB is column-major!

        # Case 4: 3D Array (2x2x2)
        (
            [[[1, 2], [3, 4]], [[5, 6], [7, 8]]],
            [1, 5, 3, 7, 2, 6, 4, 8],  # MATLAB flattens column-major first!
        ),

        # Case 5: Empty Array (Expect float if MATLAB returns scalar)
        ([], []),

        # Case 6: Single Element
        ([5], [5]),

        # Case 7: Large Matrix
        (
            np.arange(1, 101).reshape(10, 10).tolist(),
            list(np.arange(1, 101).reshape(10, 10, order="F").flatten()),
        ),

        # Case 8: NaN Data
        (
            [[float('nan'), 2], [3, float('nan')]],
            [float('nan'), 3, 2, float('nan')],
        ),
    ],
)
def test_fcx2rowvec(test_engine, input_data, expected):
    """
    Test fcx2rowvec function with various matrices and arrays, verifying reshaping.
    """
    result = test_engine.fcx2rowvec(test_engine.convert(input_data))
    assert test_engine.equal(result, expected)