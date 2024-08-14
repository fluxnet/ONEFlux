# test_cpdFmax2pCp3.py

import pytest
import matlab

def test_cpdFmax2pCp3_with_valid_data(matlab_engine):
    """
    Test cpdFmax2pCp3 with typical valid data.
    """
    Fmax = 12.0
    n = 100

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp3(Fmax, n)

    # Check that the output is within the expected range
    assert 0 <= p <= 1, "The output probability p should be between 0 and 1"

def test_cpdFmax2pCp3_with_edge_case_Fmax_below_range(matlab_engine):
    """
    Test cpdFmax2pCp3 with Fmax below the table's range.
    """
    Fmax = 5.0  # Below the lowest Fmax in the table
    n = 100

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp3(Fmax, n)

    # Check that the output is valid and within the expected range
    assert 0 <= p <= 1, "The output probability p should be between 0 and 1 even for low Fmax"

def test_cpdFmax2pCp3_with_edge_case_Fmax_above_range(matlab_engine):
    """
    Test cpdFmax2pCp3 with Fmax above the table's range.
    """
    Fmax = 30.0  # Above the highest Fmax in the table
    n = 100

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp3(Fmax, n)

    # Check that the output is valid and within the expected range
    assert 0 <= p <= 1, "The output probability p should be between 0 and 1 even for high Fmax"

def test_cpdFmax2pCp3_with_small_sample_size(matlab_engine):
    """
    Test cpdFmax2pCp3 with a small sample size (n).
    """
    Fmax = 12.0
    n = 5  # Below the minimum valid n in the table

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp3(Fmax, n)

    # Since n is less than 10, the function should return NaN
    assert p != p, "The output probability p should be NaN when n is less than 10"

def test_cpdFmax2pCp3_with_NaN_values(matlab_engine):
    """
    Test cpdFmax2pCp3 with NaN values for Fmax and n.
    """
    Fmax = float('nan')
    n = 100

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp3(Fmax, n)

    # Since Fmax is NaN, the function should return NaN
    assert p != p, "The output probability p should be NaN when Fmax is NaN"

    Fmax = 12.0
    n = float('nan')

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp3(Fmax, n)

    # Since n is NaN, the function should return NaN
    assert p != p, "The output probability p should be NaN when n is NaN"

def test_cpdFmax2pCp3_interpolation(matlab_engine):
    """
    Test cpdFmax2pCp3 for correct interpolation between values.
    """
    Fmax = 14.0  # Value that requires interpolation
    n = 100

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp3(Fmax, n)

    # Check that the output is within the expected range
    assert 0 <= p <= 1, "The output probability p should be between 0 and 1"

def test_cpdFmax2pCp3_extrapolation_low_Fmax(matlab_engine):
    """
    Test cpdFmax2pCp3 for extrapolation when Fmax is below the table's range.
    """
    Fmax = 2.0  # Value significantly below the table's range
    n = 100

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp3(Fmax, n)

    # Check that the output is within the expected range and tends toward 1
    assert p > 0.99, "The output probability p should be close to 1 for low Fmax values"

def test_cpdFmax2pCp3_extrapolation_high_Fmax(matlab_engine):
    """
    Test cpdFmax2pCp3 for extrapolation when Fmax is above the table's range.
    """
    Fmax = 35.0  # Value significantly above the table's range
    n = 100

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp3(Fmax, n)

    # Check that the output is within the expected range and tends toward 0
    assert p < 0.01, "The output probability p should be close to 0 for high Fmax values"
