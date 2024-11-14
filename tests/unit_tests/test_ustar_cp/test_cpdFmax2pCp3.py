import pytest
import numpy as np
import matlab.engine

@pytest.mark.parametrize(
    "Fmax, n, expected",
    [
        (np.nan, 10, np.nan),     # Test case with Fmax = NaN
        (10, np.nan, np.nan),     # Test case with n = NaN
        (10, 5, np.nan),          # Test case with n < 10
        ],
)
def test_cpdFmax2pCp3_return_nan(matlab_engine, Fmax, n, expected):
    """
    Test the cpdFmax2pCp3 MATLAB function for cases where `nan` is returned.
    """
    # Handle NaN inputs for MATLAB
    Fmax_matlab = matlab.double([Fmax]) if not np.isnan(Fmax) else matlab.double([float('nan')])
    n_matlab = matlab.double([n]) if not np.isnan(n) else matlab.double([float('nan')])

    # Call the MATLAB function
    result = matlab_engine.cpdFmax2pCp3(Fmax_matlab, n_matlab)

    assert type(result) == type(expected), f"Result should be a {type(expected)}, got {type(result)}"


@pytest.mark.parametrize(
    "Fmax, n, expected",
    [
        (5, 20, 0.4393355161666135),       # Fmax below critical value
        (30, 1000, 2.7278340575698223e-05),# Fmax above critical value
        (11.5, 100, 0.0432111321429921),   # Fmax within critical range
    ],
)

def test_cpdFmax2pCp3_return_numeric(matlab_engine, Fmax, n, expected):
    """
    Test the cpdFmax2pCp3 MATLAB function for cases where numeric values are returned.
    """
    # Handle NaN inputs for MATLAB
    Fmax_matlab = matlab.double([Fmax]) if not np.isnan(Fmax) else matlab.double([float('nan')])
    n_matlab = matlab.double([n]) if not np.isnan(n) else matlab.double([float('nan')])

    # Call the MATLAB function
    result = matlab_engine.cpdFmax2pCp3(Fmax_matlab, n_matlab)

    assert type(result) == type(expected), f"Result should be a {type(expected)}, got {type(result)}"
    assert np.allclose(np.array(result), np.array(expected))

@pytest.mark.parametrize(
"Fmax, FmaxCritical_high, n, expected_p",
[
    (20, 15, 50, 0.0018068999227986993),
    (15, 15, 50, 0.010000000000000009),
    (15.1, 15, 50, 0.00965419741276663),
    (30, 15, 100, 4.4960217949308046e-05),
],
)

def test_calculate_p_high_return_numeric(matlab_engine, Fmax, FmaxCritical_high, n, expected_p):
    """
    Test the cpdFmax2pCp3 MATLAB function for cases where numeric values are returned.
    """
    # Handle NaN inputs for MATLAB
    Fmax_matlab = matlab.double([Fmax]) if not np.isnan(Fmax) else matlab.double([float('nan')])
    FmaxCritical_high_matlab = matlab.double([FmaxCritical_high]) if not np.isnan(FmaxCritical_high) else matlab.double([float('nan')])
    n_matlab = matlab.double([n]) if not np.isnan(n) else matlab.double([float('nan')])

    # Call the MATLAB function
    result = matlab_engine.calculate_p_high(Fmax_matlab, FmaxCritical_high_matlab, n_matlab)

    assert result == expected_p, f"Result should be {expected_p}. Instead {result} was returned."
    assert np.allclose(np.array(result), np.array(expected_p))
    
@pytest.mark.parametrize(
    "Fmax, FmaxCritical_high, n, expected_p",
    [
        (np.nan, 15, 50, np.nan),
        (20, np.nan, 50, np.nan),
        (20, 15, np.nan, np.nan),
        (20, 0, 50, np.nan),
        (-20, 15, 50, np.nan),
        (20, -15, 50, np.nan),
        (20, 15, -50, np.nan),
    ],
)

def test_calculate_p_high_return_nan(matlab_engine, Fmax, FmaxCritical_high, n, expected_p):
    """
    Test the cpdFmax2pCp3 MATLAB function for cases where nan values are returned.
    """
    # Handle NaN inputs for MATLAB
    Fmax_matlab = matlab.double([Fmax]) if not np.isnan(Fmax) else matlab.double([float('nan')])
    FmaxCritical_high_matlab = matlab.double([FmaxCritical_high]) if not np.isnan(FmaxCritical_high) else matlab.double([float('nan')])
    n_matlab = matlab.double([n]) if not np.isnan(n) else matlab.double([float('nan')])

    # Call the MATLAB function
    result = matlab_engine.calculate_p_high(Fmax_matlab, FmaxCritical_high_matlab, n_matlab)

    assert type(result) == type(expected_p), f"Result should be a {type(expected_p)}, got {type(result)}"


@pytest.mark.parametrize(
    "Fmax, FmaxCritical, pTable, expected_p, description",
    [
        (10, [5, 15], [0.1, 0.05], None, "Fmax between FmaxCritical[0] and FmaxCritical[1]"),
        (15, [10, 15, 20], [0.1, 0.05, 0.01], 0.95, "Fmax equal to FmaxCritical[1]"),
        
        # Test case 3: Interpolation within FmaxCritical
        # Testing interpolation where Fmax is between FmaxCritical[0] and FmaxCritical[1]
        (17, [15, 20], [0.05, 0.01], None, "Fmax between FmaxCritical[0] and FmaxCritical[1], interpolate p"),
        
        # Test case 4: Fmax less than minimum FmaxCritical
        # Testing behavior when Fmax is less than all values in FmaxCritical, expecting NaN
        (4, [5, 10, 15], [0.1, 0.05, 0.01], np.nan, "Fmax less than minimum FmaxCritical, expect NaN"),
        
        # Test case 5: Fmax greater than maximum FmaxCritical
        # Testing behavior when Fmax is greater than all values in FmaxCritical, expecting NaN
        (16, [5, 10, 15], [0.1, 0.05, 0.01], np.nan, "Fmax greater than maximum FmaxCritical, expect NaN"),
        
        # Test case 6: Fmax is NaN
        # Testing behavior when Fmax is NaN, expecting NaN as result
        (np.nan, [5, 10, 15], [0.1, 0.05, 0.01], np.nan, "Fmax is NaN, expect NaN"),
        
        # Test case 7: FmaxCritical contains NaN
        # Testing behavior when FmaxCritical contains NaN, expecting NaN as result
        (10, [5, np.nan, 15], [0.1, 0.05, 0.01], np.nan, "FmaxCritical contains NaN, expect NaN"),
        
        # Test case 8: pTable contains NaN
        # Testing behavior when pTable contains NaN, expecting NaN as result
        (10, [5, 10, 15], [0.1, np.nan, 0.01], np.nan, "pTable contains NaN, expect NaN"),
        
        # Test case 9: Empty FmaxCritical
        # Testing behavior when FmaxCritical is empty, expecting NaN as result
        (10, [], [0.1, 0.05, 0.01], np.nan, "Empty FmaxCritical, expect NaN"),
        
        # Test case 10: Empty pTable
        # Testing behavior when pTable is empty, expecting NaN as result
        (10, [5, 10, 15], [], np.nan, "Empty pTable, expect NaN"),
        
        # Test case 11: Non-monotonic FmaxCritical
        # Testing behavior when FmaxCritical is not strictly increasing, may cause error or NaN
        (10, [10, 5, 15], [0.1, 0.05, 0.01], np.nan, "Non-monotonic FmaxCritical, expect error or NaN"),
    ]
)
def test_calculate_p_interpolate(matlab_engine, Fmax, FmaxCritical, pTable, expected_p, description):
    
    """
    Test calculate_p_interpolate with various inputs.

    Parameters:
    - Fmax: The Fmax value to test.
    - FmaxCritical: Array of critical Fmax values.
    - pTable: Array of p-values corresponding to FmaxCritical.
    - expected_p: Expected result (if known).
    - description: Description of the test case.
    """
    # Convert inputs to MATLAB types
    Fmax_matlab = matlab.double([float(Fmax)]) if not np.isnan(Fmax) else matlab.double([float('nan')])
    FmaxCritical_matlab = matlab.double(FmaxCritical)
    pTable_matlab = matlab.double(pTable)

    try:
        # Call the MATLAB function
        result = matlab_engine.calculate_p_interpolate(Fmax_matlab, FmaxCritical_matlab, pTable_matlab)
        p = result  # MATLAB returns a scalar

        if np.isnan(expected_p):
            # Expecting NaN as result
            assert np.isnan(p), f"{description}: Expected NaN, got {p}"
        else:
            # Check that result is a float and within [0, 1]
            assert isinstance(p, float), f"{description}: Result should be a float, got {type(p)}"
            assert 0 <= p <= 1, f"{description}: Result {p} is not between 0 and 1"

            # If expected_p is provided, compare the result
            if expected_p is not None:
                np.testing.assert_almost_equal(
                    p, expected_p, decimal=6,
                    err_msg=f"{description}: Result {p} does not match expected {expected_p}"
                )
    except matlab.engine.MatlabExecutionError as e:
        # Handle cases where MATLAB throws an error
        if np.isnan(expected_p):
            # If we expected NaN, an error is acceptable
            pass
        else:
            pytest.fail(f"{description}: Unexpected MATLAB error: {e}")