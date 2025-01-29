import pytest
from tests.conftest import test_engine

@pytest.mark.parametrize("Y, M, D, expected", [
    (2023, 10, 5, 739164),
    (0, 3, 1, 61),
    (-1, 12, 31, 0),
    (0, 24, 31, 731),
    (1, 24, 31, 1096),
    (6, 10, 5, 2470),
    (7, 10, 5, 2835),
    (8, 10, 5, 3201) # another leap year
])
def test_datenum(test_engine, Y, M, D, expected):
    """
    Test datenum function with various inputs.
    """
    result = test_engine.datenum(test_engine.convert(Y), test_engine.convert(M), test_engine.convert(D))
    assert test_engine.equal(test_engine.convert(result), expected), f"Expected {expected}, but got {result}"
