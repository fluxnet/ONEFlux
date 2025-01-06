# Tests for fcDoy

import pytest
from tests.conftest import test_engine

# Specific state vectors
# via a parameterized test fixture
@pytest.mark.parametrize('t, expected', [
      ([367], [366])
    , ([0], [364])
    #, ([5.0446049250313e-10], [364])
    , ([1], [0])
    , ([365], [364])
    , ([-1], [363])
    , ([-100], [264])
    , ([-365], [364])
    , ([0,365,500], [364,364,133])
    , ([0,365,500,1000], [364,364,133,268])
    , ([[0],[365],[500],[1000]], [[364],[364],[133],[268]])
    , ([1000,500,365,0.055], [268, 133, 364, 0])
    , ([0.055,365,500,1000], [0,364,133,268])
])
def test_fcDoy_specific(test_engine, t, expected):
    """
    Test specific state vectors
    """
    # Call the function
    result = test_engine.fcDoy(test_engine.convert(t))

    # Check the result
    assert test_engine.equal(result, test_engine.convert(expected))
