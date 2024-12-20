# Tests for fcDoy

import pytest
from tests.conftest import test_engine

# Specific state vectors
# via a parameterized test fixture
@pytest.mark.parametrize('t, expected', [
      ([367], [366])
    , ([0,365,500], [364,364,133])
    , ([0,365,500,1000], [364,364,133,268])
    , ([[0],[365],[500],[1000]], [[364],[364],[133],[268]])
    , ([1000,500,365,0.055], [268, 133, 364, 0])
])
def test_fcDoy_specific(test_engine, t, expected):
    """
    Test specific state vectors
    """
    # Call the function
    result = test_engine.fcDoy.convert(t)

    # Check the result
    assert test_engine.equal(result, test_engine.convert(expected))
