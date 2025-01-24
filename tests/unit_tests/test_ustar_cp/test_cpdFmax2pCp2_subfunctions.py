# test_cpdFmax2pCp2.py
import pytest
from tests.conftest import test_engine


def test_cpdFmax2pCp2_with_valid_data(test_engine):
    """
    Test cpdFmax2pCp2 with typical valid data.
    """
    Fmax = test_engine.convert(5.0)
    n = test_engine.convert(50)

    # Call the MATLAB function
    p = test_engine.cpdFmax2pCp2(Fmax, n)

    # Check that the output is within the expected range
    assert 0 <= p <= 1, "The output probability p should be between 0 and 1"

def test_cpdFmax2pCp2_with_edge_case_Fmax_below_range(test_engine):
    """
    Test cpdFmax2pCp2 with Fmax below the table's range.
    """
    Fmax = test_engine.convert(1.0)  # Below the lowest Fmax in the table
    n = test_engine.convert(50)

    # Call the MATLAB function
    p = test_engine.cpdFmax2pCp2(Fmax, n)

    # Check that the output is valid and within the expected range
    assert 0 <= p <= 1, "The output probability p should be between 0 and 1 even for low Fmax"

def test_cpdFmax2pCp2_with_edge_case_Fmax_above_range(test_engine):
    """
    Test cpdFmax2pCp2 with Fmax above the table's range.
    """
    Fmax = test_engine.convert(20.0)  # Above the highest Fmax in the table
    n = test_engine.convert(50)

    # Call the MATLAB function
    p = test_engine.cpdFmax2pCp2(Fmax, n)

    # Check that the output is valid and within the expected range
    assert 0 <= p <= 1, "The output probability p should be between 0 and 1 even for high Fmax"

def test_cpdFmax2pCp2_with_small_sample_size(test_engine):
    """
    Test cpdFmax2pCp2 with a small sample size (n).
    """
    Fmax = test_engine.convert(5.0)
    n = test_engine.convert(5)  # Below the minimum valid n in the table

    # Call the MATLAB function
    p = test_engine.cpdFmax2pCp2(Fmax, n)

    # Since n is less than 10, the function should return NaN
    assert p != p, "The output probability p should be NaN when n is less than 10"

def test_cpdFmax2pCp2_with_NaN_values(test_engine):
    """
    Test cpdFmax2pCp2 with NaN values for Fmax and n.
    """
    Fmax = float('nan')
    n = test_engine.convert(50)

    # Call the MATLAB function
    p = test_engine.cpdFmax2pCp2(Fmax, n)

    # Since Fmax is NaN, the function should return NaN
    assert p != p, "The output probability p should be NaN when Fmax is NaN"

    Fmax = test_engine.convert(5.0)
    n = float('nan')

    # Call the MATLAB function
    p = test_engine.cpdFmax2pCp2(Fmax, n)

    # Since n is NaN, the function should return NaN
    assert p != p, "The output probability p should be NaN when n is NaN"

def test_cpdFmax2pCp2_interpolation(test_engine):
    """
    Test cpdFmax2pCp2 for correct interpolation between values.
    """
    Fmax = test_engine.convert(6.0)  # Value that requires interpolation
    n = test_engine.convert(70)

    # Call the MATLAB function
    p = test_engine.cpdFmax2pCp2(Fmax, n)

    # Check that the output is within the expected range
    assert 0 <= p <= 1, "The output probability p should be between 0 and 1"

def test_cpdFmax2pCp2_extrapolation_low_Fmax(test_engine):
    """
    Test cpdFmax2pCp2 for extrapolation when Fmax is below the table's range.
    """
    Fmax = test_engine.convert(0.5)  # Value significantly below the table's range
    n = test_engine.convert(50)

    # Call the MATLAB function
    p = test_engine.cpdFmax2pCp2(Fmax, n)

    # Check that the output is within the expected range and tends toward 1
    assert p > 0.99, "The output probability p should be close to 1 for low Fmax values"

def test_cpdFmax2pCp2_extrapolation_high_Fmax(test_engine):
    """
    Test cpdFmax2pCp2 for extrapolation when Fmax is above the table's range.
    """
    Fmax = test_engine.convert(25.0)  # Value significantly above the table's range
    n = test_engine.convert(50)

    # Call the MATLAB function
    p = test_engine.cpdFmax2pCp2(Fmax, n)

    # Check that the output is within the expected range and tends toward 0
    assert p < 0.01, "The output probability p should be close to 0 for high Fmax values"
