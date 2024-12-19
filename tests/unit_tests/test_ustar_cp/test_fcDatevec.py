# Contains tests for testing the fcDatevec function
# which converts a date string to a date vector

import pytest
from tests.conftest import test_engine

from hypothesis import given, settings
from hypothesis.strategies import floats, lists, composite

import numpy as np

# Property-based tests

# The size of the input `n` determines the size of the output as `n x 6`
@given(data=lists(floats(allow_nan=True, allow_infinity=False), min_size=1))
def test_fcDatevec_shape(test_engine, data):
    """
    Test the shape of the output of fcDatevec
    """
    # Call the function
    result = test_engine.fcDatevec(test_engine.convert(data))

    # Check the shape as `n x 6`
    n = len(data) - len([item for item in result if np.isnan(item)])
    assert np.shape(result) == n
    for row in result:
        assert len(row) == 6

# Specific state vectors
# via a parameterized test fixture
@pytest.mark.parametrize('t, expected', [
    ([367], [0, 12, 31, 24, 0, 0])
])
def test_fcDatevec_specific(test_engine, t, expected):
    """
    Test specific state vectors
    """
    # Call the function
    result = test_engine.fcDatevec(test_engine.convert(t))

    # Check the result
    assert test_engine.equal(result, test_engine.convert(expected))