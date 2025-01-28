import pytest
import numpy as np
from oneflux_steps.ustar_cp_python.utilities import prctile

TEST_CASES = [
    ["Empty array", np.array([]), 50, np.nan],
    ["Single element", np.array([5]), 50, 5],
    ["Two elements, lower percentile", np.array([1, 9]), 10, 1],
    ["Two elements, upper percentile", np.array([1, 9]), 90, 9],
    ["Three elements, median", np.array([1, 5, 9]), 50, 5],
    ["Four elements, lower quartile", np.array([1, 2, 3, 4]), 25, 1.5],
    ["Four elements, upper quartile", np.array([1, 2, 3, 4]), 75, 3.5],
    ["With NaNs, ignore them", np.array([1, np.nan, 3, 5, np.nan]), 50, 3],
    ["All identical elements", np.array([4, 4, 4, 4]), 25, 4],
    ["Negative values", np.array([-5, -2, -1, 0]), 25, -3.5],
    ["Mixed values", np.array([3, 7, 2, 5, 1]), 40, 2.5],
    ["Bounds lower", np.array([2, 8, 10]), 0, 2],
    ["Bounds upper", np.array([2, 8, 10]), 100, 10]
]

@pytest.mark.parametrize("description, A, p, expected", TEST_CASES)
def test_prctile(description, A, p, expected):
    result = prctile(A, p)
    
    assert np.allclose(result, expected, equal_nan=True)