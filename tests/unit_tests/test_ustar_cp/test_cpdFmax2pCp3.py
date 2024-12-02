import pytest
import numpy as np
import matlab.engine
from oneflux_steps.ustar_cp_python.cpdFmax2pCp3 import cpdFmax2pCp3, calculate_p_high, calculate_p_low, interpolate_FmaxCritical

testcases = [
        # Fmax = NaN
        (np.nan, 52, np.nan),
        # n = NaN
        (42, np.nan, np.nan),
        # n < 10
        (3.14159265358979323, 9, np.nan),
        # Fmax Below f-critical(1)
        (5, 20, 0.4393355161666135),
        (5.45204127574611, 52, 0.384643400326067), 
        # Fmax Above f-critical(3)
        (30, 1000, 2.7278340575698223e-05),
        (17, 53, 0.005441758015001),
        # Between f-critical(1) and f-critical(3)
        (10, 52, 0.0761404222166437),
        # fmax = 0
        (0, 55, 1.0),
        # fmax = fcritical(1)
        (1.6301, 52, 1.0),
        # Nominal
        (2.37324492970613, 55, 1.0),
        (10.3567400792636, 54, 0.0657053181314848)
]
@pytest.mark.parametrize("fmax, n, expected_p3", testcases)
def test_cpdFmax2pCp3_matlab(ustar_cp, fmax, n, expected_p3):
    """
    Test the cpdFmax2pCp3 MATLAB function for cases where `nan` is returned.
    """
    # Handle NaN inputs for MATLAB
    Fmax_matlab = matlab.double([Fmax]) if not np.isnan(Fmax) else matlab.double([float('nan')])
    n_matlab = matlab.double([n]) if not np.isnan(n) else matlab.double([float('nan')])

    # Call the MATLAB function
    result = ustar_cp.cpdFmax2pCp3(Fmax_matlab, n_matlab)

    assert type(result) == type(expected), f"Result should be a {type(expected)}, got {type(result)}"

@pytest.mark.parametrize("fmax, n, expected_p3", testcases)
def test_cpdFmax2pCp3(fmax, n, expected_p3):

    output_p3 = cpdFmax2pCp3(fmax, n)

    assert type(output_p3) == type(expected_p3), f"Result should be a {type(expected_p3)}, got {type(output_p3)}"
    assert np.isclose(output_p3, expected_p3, equal_nan=True), f"Expected p3 value of {expected_p3}, but got {output_p3}."

def test_cpdFmax2pCp3_return_numeric(ustar_cp, Fmax, n, expected):
    """
    Test the cpdFmax2pCp3 MATLAB function for cases where numeric values are returned.
    """
    # Handle NaN inputs for MATLAB
    Fmax_matlab = matlab.double([Fmax]) if not np.isnan(Fmax) else matlab.double([float('nan')])
    n_matlab = matlab.double([n]) if not np.isnan(n) else matlab.double([float('nan')])

    # Call the MATLAB function
    result = ustar_cp.cpdFmax2pCp3(Fmax_matlab, n_matlab)

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

def test_calculate_p_high_return_numeric_matlab(ustar_cp, Fmax, FmaxCritical_high, n, expected_p):
    """
    Test the cpdFmax2pCp3 MATLAB function for cases where numeric values are returned.
    """
    # Handle NaN inputs for MATLAB
    Fmax_matlab = matlab.double([Fmax]) if not np.isnan(Fmax) else matlab.double([float('nan')])
    FmaxCritical_high_matlab = matlab.double([FmaxCritical_high]) if not np.isnan(FmaxCritical_high) else matlab.double([float('nan')])
    n_matlab = matlab.double([n]) if not np.isnan(n) else matlab.double([float('nan')])

    # Call the MATLAB function
    result = ustar_cp.calculate_p_high(Fmax_matlab, FmaxCritical_high_matlab, n_matlab)

    assert result == expected_p, f"Result should be {expected_p}. Instead {result} was returned."
    assert np.allclose(np.array(result), np.array(expected_p))

@pytest.mark.parametrize(
"Fmax, FmaxCritical_high, n, expected_p",
[
    (20, 15, 50, 0.0018068999227986993),
    (15, 15, 50, 0.010000000000000009),
    (15.1, 15, 50, 0.00965419741276663),
    (30, 15, 100, 4.4960217949308046e-05),
],
)

def test_calculate_p_high_return_numeric(Fmax, FmaxCritical_high, n, expected_p):

    result = calculate_p_high(Fmax, FmaxCritical_high, n)

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

def test_calculate_p_high_return_nan_matlab(ustar_cp, Fmax, FmaxCritical_high, n, expected_p):
    """
    Test the cpdFmax2pCp3 MATLAB function for cases where nan values are returned.
    """
    # Handle NaN inputs for MATLAB
    Fmax_matlab = matlab.double([Fmax]) if not np.isnan(Fmax) else matlab.double([float('nan')])
    FmaxCritical_high_matlab = matlab.double([FmaxCritical_high]) if not np.isnan(FmaxCritical_high) else matlab.double([float('nan')])
    n_matlab = matlab.double([n]) if not np.isnan(n) else matlab.double([float('nan')])

    # Call the MATLAB function
    result = ustar_cp.calculate_p_high(Fmax_matlab, FmaxCritical_high_matlab, n_matlab)

    assert type(result) == type(expected_p), f"Result should be a {type(expected_p)}, got {type(result)}"

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

def test_calculate_p_high_return_nan(Fmax, FmaxCritical_high, n, expected_p):

    result = calculate_p_high(Fmax, FmaxCritical_high, n)

    assert type(result) == type(expected_p), f"Result should be a {type(expected_p)}, got {type(result)}"


@pytest.mark.parametrize(
    "Fmax, FmaxCritical, pTable, expected_p, description",
    [
        (10, [5, 15], [0.1, 0.05], 0.925, "Fmax between FmaxCritical[0] and FmaxCritical[1]"),
        (15, [10, 15, 20], [0.1, 0.05, 0.01], 0.95, "Fmax equal to FmaxCritical[1]"),
        
        # Test case 3: Interpolation within FmaxCritical
        # Testing interpolation where Fmax is between FmaxCritical[0] and FmaxCritical[1]
        (17, [15, 20], [0.05, 0.01], 0.966, "Fmax between FmaxCritical[0] and FmaxCritical[1], interpolate p"),
        
        # Test case 4: Fmax less than minimum FmaxCritical
        # Testing behavior when Fmax is less than all values in FmaxCritical, expecting NaN
        (4, [5, 10, 15], [0.1, 0.05, 0.01], 0.8888266666666668, "Fmax less than minimum FmaxCritical, expect NaN"),
        
        # Test case 5: Fmax greater than maximum FmaxCritical
        # Testing behavior when Fmax is greater than all values in FmaxCritical, expecting NaN
        (16, [5, 10, 15], [0.1, 0.05, 0.01], 0.9967733333333333, "Fmax greater than maximum FmaxCritical, expect NaN"),
        
        # Test case 6: Fmax is NaN
        # Testing behavior when Fmax is NaN, expecting NaN as result
        (np.nan, [5, 10, 15], [0.1, 0.05, 0.01], np.nan, "Fmax is NaN, expect NaN"),
        
        # Test case 7: FmaxCritical contains NaN
        # Testing behavior when FmaxCritical contains NaN, expecting NaN as result
        (10, [5, np.nan, 15], [0.1, 0.05, 0.01], np.nan, "FmaxCritical contains NaN, expect NaN"),
        
        # Test case 8: pTable contains NaN
        # Testing behavior when pTable contains NaN, expecting NaN as result
        (10, [5, 10, 15], [0.1, np.nan, 0.01], 0.9450000000000001, "pTable contains NaN, expect NaN"),
        
        # Test case 9: Empty FmaxCritical
        # Testing behavior when FmaxCritical is empty, expecting NaN as result
        (10, [], [0.1, 0.05, 0.01], np.nan, "Empty FmaxCritical, expect NaN"),
        
        # Test case 10: Empty pTable
        # Testing behavior when pTable is empty, expecting NaN as result
        (10, [5, 10, 15], [], np.nan, "Empty pTable, expect NaN"),
        
        # Test case 11: Non-monotonic FmaxCritical
        # Testing behavior when FmaxCritical is not strictly increasing, may cause error or NaN
        (10, [10, 5, 15], [0.1, 0.05, 0.01], 0.9, "Non-monotonic FmaxCritical, expect error or NaN"),
    ]
)
def test_calculate_p_interpolate(ustar_cp, Fmax, FmaxCritical, pTable, expected_p, description):
    
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
        result = ustar_cp.calculate_p_interpolate(Fmax_matlab, FmaxCritical_matlab, pTable_matlab)
        p = result  # MATLAB returns a scalar

        if expected_p is not None and np.isnan(expected_p):
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

@pytest.mark.parametrize(
    "Fmax, FmaxCritical_low, n, expected_p, description",
    [
        (5.0, 10.0, 30, 0.4898436922743534, "Basic test case with Fmax < FmaxCritical_low"),
        (0.0, 10.0, 30, 1.0, "Fmax = 0"),
        (5.0, 10.0, 3, 0.239649936459168, "Small sample size"),
        (10.0, 10.0, 30, 0.09999999999999987, "Fmax = FmaxCritical_low"),
        (np.nan, 10.0, 30, 1.0, "Fmax is NaN, expecting p = 1.0"),
        (5.0, np.nan, 30, 1.0, "FmaxCritical_low is NaN, expecting p = 1.0"),
        (5.0, 10.0, 0, 1.0, "n = 0, invalid degrees of freedom, expecting p = 1.0"),
        (5.0, 0.0, 30, 0.0, "FmaxCritical_low = 0, invalid critical value, expecting p = 0.0"),
    ],
)
def test_calculate_p_low_matlab(ustar_cp, Fmax, FmaxCritical_low, n, expected_p, description):
    """
    Test the MATLAB function calculate_p_low using various scenarios.

    Parameters:
    - Fmax (float): Input Fmax value.
    - FmaxCritical_low (float): Critical low Fmax value.
    - n (int): Sample size.
    - expected_p (float or np.nan): Expected output value of p.
    - description (str): Description of the test case.
    """
    # Convert inputs to MATLAB types
    Fmax_matlab = matlab.double([float(Fmax)]) if not np.isnan(Fmax) else matlab.double([float('nan')])
    FmaxCritical_low_matlab = matlab.double([float(FmaxCritical_low)]) if not np.isnan(FmaxCritical_low) else matlab.double([float('nan')])
    n_matlab = matlab.double([float(n)]) if n > 0 else matlab.double([float('nan')])

    try:
        # Call the MATLAB function
        result = ustar_cp.calculate_p_low(Fmax_matlab, FmaxCritical_low_matlab, n_matlab)
        p = float(result)  # MATLAB returns scalar values as 1x1 arrays

        if np.isnan(expected_p):
            # Check if the result is NaN
            assert np.isnan(p), f"{description}: Expected NaN, got {p}"
        else:
            # Validate the result
            assert 0 <= p <= 1, f"{description}: p = {p} is not within [0, 1]"
            np.testing.assert_almost_equal(
                p, expected_p, decimal=3,
                err_msg=f"{description}: Result {p} does not match expected {expected_p}"
            )
    except matlab.engine.MatlabExecutionError as e:
        # If expected_p is NaN, MATLAB errors are acceptable
        if not np.isnan(expected_p):
            pytest.fail(f"{description}: Unexpected MATLAB error: {e}")

@pytest.mark.parametrize(
    "Fmax, FmaxCritical_low, n, expected_p, description",
    [
        (5.0, 10.0, 30, 0.4898436922743534, "Basic test case with Fmax < FmaxCritical_low"),
        (0.0, 10.0, 30, 1.0, "Fmax = 0"),
        (5.0, 10.0, 3, 0.239649936459168, "Small sample size"),
        (10.0, 10.0, 30, 0.09999999999999987, "Fmax = FmaxCritical_low"),
        (np.nan, 10.0, 30, 1.0, "Fmax is NaN, expecting p = 1.0"),
        (5.0, np.nan, 30, 1.0, "FmaxCritical_low is NaN, expecting p = 1.0"),
        (5.0, 10.0, 0, 1.0, "n = 0, invalid degrees of freedom, expecting p = 1.0"),
        (5.0, 0.0, 30, 0.0, "FmaxCritical_low = 0, invalid critical value, expecting p = 0.0"),
    ],
)

def test_calculate_p_low(Fmax, FmaxCritical_low, n, expected_p, description):

    result = calculate_p_low(Fmax, FmaxCritical_low, n)

    assert np.allclose(result, expected_p, equal_nan=True)

@pytest.mark.parametrize(
    "n, nTable, FmaxTable, expected_FmaxCritical, description",
    [
        # Test case 1: Interpolation within range
        (15, [10, 20, 30], [[5, 10, 15], [6, 12, 18], [7, 14, 21]], [5.5, 11, 16.5],
         "n is within the range of nTable, interpolating FmaxCritical"),
        
        # Test case 2: Exact match in nTable
        (10, [10, 20, 30], [[5, 10, 15], [6, 12, 18], [7, 14, 21]], [5, 10, 15],
         "n matches the first value in nTable, no interpolation needed"),
        
        # Test case 3: n below nTable range
        (5, [10, 20, 30], [[5, 10, 15], [6, 12, 18], [7, 14, 21]], [4.5],
         "n is below the range of nTable, should return NaN"),
        
        # Test case 4: n above nTable range
        (35, [10, 20, 30], [[5, 10, 15], [6, 12, 18], [7, 14, 21]], [7.5],
         "n is above the range of nTable, should return NaN"),
        
        # Test case 5: nTable contains NaN
        (15, [10, np.nan, 30], [[5, 10, 15], [6, 12, 18], [7, 14, 21]], [np.nan, np.nan, np.nan],
         "nTable contains NaN, should return NaN"),
        
        # Test case 6: FmaxTable contains NaN
        (15, [10, 20, 30], [[5, 10, 15], [6, np.nan, 18], [7, 14, 21]], [5.5],
         "FmaxTable contains NaN, should return NaN"),
        
        # Test case 7: Empty nTable and FmaxTable
        (15, [], [], [np.nan, np.nan, np.nan],
         "Empty nTable and FmaxTable, should return NaN"),
    ],
)
def test_interpolate_FmaxCritical_matlab(ustar_cp, n, nTable, FmaxTable, expected_FmaxCritical, description):
    """
    Test the MATLAB function interpolate_FmaxCritical using various scenarios.

    Parameters:
    - n (float): Input n value for interpolation.
    - nTable (list): Table of n values corresponding to rows in FmaxTable.
    - FmaxTable (list of lists): Critical Fmax values for different parameters.
    - expected_FmaxCritical (list): Expected interpolated FmaxCritical values.
    - description (str): Description of the test case.
    """
    # Convert inputs to MATLAB types
    n_matlab = matlab.double([float(n)])
    nTable_matlab = matlab.double(nTable) if len(nTable) > 0 else matlab.double([])
    FmaxTable_matlab = matlab.double(FmaxTable) if len(FmaxTable) > 0 else matlab.double([])

    try:
        # Call the MATLAB function
        result = ustar_cp.interpolate_FmaxCritical(n_matlab, nTable_matlab, FmaxTable_matlab)
        FmaxCritical = np.array(result).flatten()  # Convert MATLAB result to a flat NumPy array

        # Validate the results
        for actual, expected in zip(FmaxCritical, expected_FmaxCritical):
            if np.isnan(expected):
                assert np.isnan(actual), f"{description}: Expected NaN, got {actual}"
            else:
                np.testing.assert_almost_equal(
                    actual, expected, decimal=3,
                    err_msg=f"{description}: Expected {expected}, got {actual}"
                )
    except matlab.engine.MatlabExecutionError as e:
        # Handle MATLAB errors
        if not any(np.isnan(expected) for expected in expected_FmaxCritical):
            pytest.fail(f"{description}: Unexpected MATLAB error: {e}")

@pytest.mark.parametrize(
    "n, nTable, FmaxTable, expected_FmaxCritical, description",
    [
        # Test case 1: Interpolation within range
        (15, np.asarray([10, 20, 30]), np.asarray([[5, 10, 15], [6, 12, 18], [7, 14, 21]]), np.asarray([5.5, 11, 16.5]),
         "n is within the range of nTable, interpolating FmaxCritical"),
        
        # Test case 2: Exact match in nTable
        (10, np.asarray([10, 20, 30]), np.asarray([[5, 10, 15], [6, 12, 18], [7, 14, 21]]), np.asarray([5, 10, 15]),
         "n matches the first value in nTable, no interpolation needed"),
        
        # Test case 3: n below nTable range
        (5, np.asarray([10, 20, 30]), np.asarray([[5, 10, 15], [6, 12, 18], [7, 14, 21]]), np.asarray([4.5, 9.0, 13.5]),
         "n is below the range of nTable, should return NaN"),
        
        # Test case 4: n above nTable range
        (35, np.asarray([10, 20, 30]), np.asarray([[5, 10, 15], [6, 12, 18], [7, 14, 21]]), np.asarray([7.5, 15.0, 22.5]),
         "n is above the range of nTable, should return NaN"),
        
        # Test case 5: nTable contains NaN
        (15, np.asarray([10, np.nan, 30]), np.asarray([[5, 10, 15], [6, 12, 18], [7, 14, 21]]), np.asarray([np.nan, np.nan, np.nan]),
         "nTable contains NaN, should return NaN"),
        
        # Test case 6: FmaxTable contains NaN
        (15, np.asarray([10, 20, 30]), np.asarray([[5, 10, 15], [6, np.nan, 18], [7, 14, 21]]), np.asarray([5.5]),
         "FmaxTable contains NaN, should return NaN"),
        
        # Test case 7: Empty nTable and FmaxTable
        (15, np.asarray([]), np.asarray([]), np.asarray([np.nan, np.nan, np.nan]),
         "Empty nTable and FmaxTable, should return NaN"),
    ],
)

def test_interpolate_FmaxCritical(n, nTable, FmaxTable, expected_FmaxCritical, description):

    result = interpolate_FmaxCritical(n, nTable, FmaxTable)

    assert np.allclose(result, expected_FmaxCritical, equal_nan=True)
