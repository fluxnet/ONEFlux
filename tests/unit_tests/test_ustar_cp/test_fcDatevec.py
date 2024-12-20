# Contains tests for testing the fcDatevec function
# which converts a date string to a date vector

import pytest
from tests.conftest import test_engine

from hypothesis import given, settings
from hypothesis.strategies import floats, lists, composite

import numpy as np

# Property-based tests for fcDatevec
# The size of the input `n` determines the size of the output as `n x 6`
@given(data=lists(floats(allow_infinity=False, min_value=-10000, max_value=10000), min_size=1, max_size=100))
@settings(deadline=1000)
def test_fcDatevec_shape(test_engine, data):
    """
    Test the shape of the output of fcDatevec
    """
    # Call the function
    result = test_engine.fcDatevec(test_engine.convert(data),nargout=6)

    # Check the shape of each part of the data is of length `n`
    n = len(data) # - len(list([item for item in data if np.isnan(item)]))
    for chunk in result:
        # check if `chunk` is an instance of a list
        if isinstance(chunk, list):
            assert len(chunk) == n
        else:
            assert True

    # Reveersing the input data reverses the components of the output data
    if n > 1:
      result2 = test_engine.fcDatevec(test_engine.convert(data[::-1]),nargout=6)

      for chunk1, chunk2 in zip(list(result), list(result2)):
          part1 = chunk1[0]
          part2 = chunk2[0]

          if isinstance(part1, list):
              assert test_engine.equal(part1, part2[::-1])
          else:
              assert test_engine.equal(part1, part2)

# Specific state vectors
# via a parameterized test fixture
@pytest.mark.parametrize('t, expected', [
      ([367], (0, 12, 31, 24, 0, 0))
    , ([0,365,500], ([-1,0,1], [12,12,5], [30,29,13], [24,24,24], [0,0,0], [0,0,0]))
    , ([0,365,500,1000], ([-1,0,1,2], [12,12,5,9], [30,29,13,25], [24,24,24,24], [0,0,0,0], [0,0,0,0]))
    , ([0.055,365,500,1000], ([0,0,1,2], [0,12,5,9], [0,29,13,25], [1,24,24,24], [19,0,0,0], [12,0,0,0]))
])
def test_fcDatevec_specific(test_engine, t, expected):
    """
    Test specific state vectors
    """
    # Call the function
    result = test_engine.fcDatevec(test_engine.convert(t), nargout=6)

    # Check the result
    assert test_engine.equal(result, test_engine.convert(expected))