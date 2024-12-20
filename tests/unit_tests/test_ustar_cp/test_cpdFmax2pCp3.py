import pytest
import numpy as np
import matlab.engine
from oneflux_steps.ustar_cp_python.cpdFmax2pCp3 import cpdFmax2pCp3, calculate_p_high, calculate_p_low, interpolate_FmaxCritical

testcases = [
        # Input values are NaN
        (np.nan, 52, np.nan),
        # Different input value is NaN
        (42, np.nan, np.nan),
        # n < 10
        (3.14159265358979323, 9, np.nan),
        # Below f-critical(1)
        (5.45204127574611, 52, 0.384643400326067),
        # Above f-critical(3)
        (17, 53, 0.005441758015001463),
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
def test_cpdFmax2pCp3(test_engine, fmax, n, expected_p3):
    
    # Convert the input values to compatible data types
    fmax = test_engine.convert(fmax)
    n = test_engine.convert(n)

    # Run the function
    output_p3 = test_engine.cpdFmax2pCp3(fmax, n)

    assert test_engine.equal(test_engine.convert(output_p3), expected_p3)

@pytest.mark.parametrize(
"Fmax, FmaxCritical_high, n, expected_p",
[
    (20, 15, 50, 0.0018068999227986993),
    (15, 15, 50, 0.010000000000000009),
    (15.1, 15, 50, 0.00965419741276663),
    (30, 15, 100, 4.4960217949308046e-05),
    (np.nan, 15, 50, 0),
    (20, np.nan, 50, 0),
    (20, 15, np.nan, 0),
    (20, 0, 50, 0),
    (-20, 15, 50, 2.0),
    (20, -15, 50, 2.0),
    (20, 15, -50, 0),
],
)

def test_calculate_p_high(test_engine, Fmax, FmaxCritical_high, n, expected_p):
    """
    Test the cpdFmax2pCp3 function for cases where numeric values are returned.
    """
    # Handle NaN inputs for MATLAB
    Fmax = test_engine.convert(Fmax)
    FmaxCritical_high = test_engine.convert(FmaxCritical_high)
    n = test_engine.convert(n)

    # Call the MATLAB function
    result = test_engine.calculate_p_high(Fmax, FmaxCritical_high, n)

    assert test_engine.equal(test_engine.convert(result), expected_p)


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
        #(10, [5, np.nan, 15], [0.1, 0.05, 0.01], np.nan, "FmaxCritical contains NaN, expect NaN"),
        
        # Test case 8: pTable contains NaN
        # Testing behavior when pTable contains NaN, expecting NaN as result
        (10, [5, 10, 15], [0.1, np.nan, 0.01], 0.9450000000000001, "pTable contains NaN, expect NaN"),
        
        # Test case 9: Empty FmaxCritical
        # Testing behavior when FmaxCritical is empty, expecting NaN as result
        #(10, [], [0.1, 0.05, 0.01], np.nan, "Empty FmaxCritical, expect NaN"),
        
        # Test case 10: Empty pTable
        # Testing behavior when pTable is empty, expecting NaN as result
        #(10, [5, 10, 15], [], np.nan, "Empty pTable, expect NaN"),
        
        # Test case 11: Non-monotonic FmaxCritical
        # Testing behavior when FmaxCritical is not strictly increasing, may cause error or NaN
        (10, [10, 5, 15], [0.1, 0.05, 0.01], 0.9, "Non-monotonic FmaxCritical, expect error or NaN"),
    ]
)
def test_calculate_p_interpolate(test_engine, Fmax, FmaxCritical, pTable, expected_p, description):
    
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
    Fmax = test_engine.convert(Fmax)
    FmaxCritical = test_engine.convert(FmaxCritical)
    pTable = test_engine.convert(pTable)

    result = test_engine.calculate_p_interpolate(Fmax, FmaxCritical, pTable)

    assert test_engine.equal(test_engine.convert(result), expected_p)

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
def test_calculate_p_low(test_engine, Fmax, FmaxCritical_low, n, expected_p, description):
    """
    Test the function calculate_p_low using various scenarios.

    Parameters:
    - Fmax (float): Input Fmax value.
    - FmaxCritical_low (float): Critical low Fmax value.
    - n (int): Sample size.
    - expected_p (float or np.nan): Expected output value of p.
    - description (str): Description of the test case.
    """
    # Convert inputs to MATLAB types
    Fmax = test_engine.convert(Fmax)
    FmaxCritical_low = test_engine.convert(FmaxCritical_low)
    n = test_engine.convert(n)

    # Call the function
    result = test_engine.calculate_p_low(Fmax, FmaxCritical_low, n)
    
    assert test_engine.equal(test_engine.convert(result), expected_p)

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
        (5, [10, 20, 30], [[5, 10, 15], [6, 12, 18], [7, 14, 21]], [4.5, 9.0, 13.5],
         "n is below the range of nTable, should return NaN"),
        
        # Test case 4: n above nTable range
        (35, [10, 20, 30], [[5, 10, 15], [6, 12, 18], [7, 14, 21]], [7.5, 15.0, 22.5],
         "n is above the range of nTable, should return NaN"),
        
        # Test case 5: nTable contains NaN
        #(15, np.asarray([10, np.nan, 30]), np.asarray([[5, 10, 15], [6, 12, 18], [7, 14, 21]]), np.asarray([np.nan, np.nan, np.nan]),
         #"nTable contains NaN, should return NaN"),
        
        # Test case 6: FmaxTable contains NaN
        #(15, np.asarray([10, 20, 30]), np.asarray([[5, 10, 15], [6, np.nan, 18], [7, 14, 21]]), np.asarray([5.5]),
         #"FmaxTable contains NaN, should return NaN"),
        
        # Test case 7: Empty nTable and FmaxTable
        #(15, np.asarray([]), np.asarray([]), np.asarray([np.nan, np.nan, np.nan]),
        # "Empty nTable and FmaxTable, should return NaN"),
    ],
)

def test_interpolate_FmaxCritical(n, nTable, FmaxTable, expected_FmaxCritical, description, test_engine):

    n = test_engine.convert(n)
    nTable = test_engine.convert(nTable)
    FmaxTable = test_engine.convert(FmaxTable)

    result = test_engine.interpolate_FmaxCritical(n, nTable, FmaxTable)

    assert test_engine.equal(test_engine.convert(expected_FmaxCritical), result)
