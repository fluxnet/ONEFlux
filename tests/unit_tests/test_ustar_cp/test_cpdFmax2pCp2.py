# test_cpdFmax2pCp2.py

import pytest
import matlab

def test_cpdFmax2pCp2_with_valid_data(matlab_engine):
    """
    Test cpdFmax2pCp2 with typical valid data.
    """
    Fmax = 5.0
    n = 50

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp2(Fmax, n)

    # Check that the output is within the expected range
    assert 0 <= p <= 1, "The output probability p should be between 0 and 1"

def test_cpdFmax2pCp2_with_edge_case_Fmax_below_range(matlab_engine):
    """
    Test cpdFmax2pCp2 with Fmax below the table's range.
    """
    Fmax = 1.0  # Below the lowest Fmax in the table
    n = 50

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp2(Fmax, n)

    # Check that the output is valid and within the expected range
    assert 0 <= p <= 1, "The output probability p should be between 0 and 1 even for low Fmax"

def test_cpdFmax2pCp2_with_edge_case_Fmax_above_range(matlab_engine):
    """
    Test cpdFmax2pCp2 with Fmax above the table's range.
    """
    Fmax = 20.0  # Above the highest Fmax in the table
    n = 50

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp2(Fmax, n)

    # Check that the output is valid and within the expected range
    assert 0 <= p <= 1, "The output probability p should be between 0 and 1 even for high Fmax"

def test_cpdFmax2pCp2_with_small_sample_size(matlab_engine):
    """
    Test cpdFmax2pCp2 with a small sample size (n).
    """
    Fmax = 5.0
    n = 5  # Below the minimum valid n in the table

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp2(Fmax, n)

    # Since n is less than 10, the function should return NaN
    assert p != p, "The output probability p should be NaN when n is less than 10"

def test_cpdFmax2pCp2_with_NaN_values(matlab_engine):
    """
    Test cpdFmax2pCp2 with NaN values for Fmax and n.
    """
    Fmax = float('nan')
    n = 50

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp2(Fmax, n)

    # Since Fmax is NaN, the function should return NaN
    assert p != p, "The output probability p should be NaN when Fmax is NaN"

    Fmax = 5.0
    n = float('nan')

    # Call the MATLAB function
    p = matlab_engine.cpdFmax2pCp2(Fmax, n)

    # Since n is NaN, the function should return NaN
    assert p != p, "The output probability p should be NaN when n is NaN"
