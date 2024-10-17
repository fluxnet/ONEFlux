"""Test module for the cpdBootstrapUStarTh4Season20100901 matlab function.

This module contains the unit tests for the cpdBootstrapUStarTh4Season20100901. 
These tests cover basic behaviour, edge cases and errors.
"""

import pytest
import matlab.engine
import numpy as np
import json
import os
from tests.conftest import to_matlab_type, read_file, mat2list, parse_testcase, compare_matlab_arrays

@pytest.fixture(scope="module")
def mock_data(nt=300, tspan=(0, 1), uStar_pars=(0.1, 3.5), T_pars=(-10, 30), fNight=None):
    """
    Fixture to generate mock time series data for testing purposes. This fixture 
    creates a set of synthetic data corresponding to cpdBootstap* function arguments, 
    such as Net Ecosystem Exchange (NEE), uStar values, temperature, and day/night flags.

    Args:
        nt (int, optional): Number of time points to generate in the series. 
                            Defaults to 300.
        tspan (tuple, optional): Start and end time for the time vector. 
                                 Defaults to (0, 1).
        uStar_pars (tuple, optional): Minimum and maximum values for the random 
                                      generation of u* values. Defaults to (0.1, 3.5).
        T_pars (tuple, optional): Minimum and maximum values for the random 
                                  generation of temperature values. Defaults to (-10, 30).
        fNight (array-like or None, optional): Binary values indicating day (0) or 
                                               night (1). If None, a random assignment 
                                               is made. Defaults to None.

    Returns:
        tuple: A tuple containing:
            - t (np.ndarray): Time vector of length `nt`.
            - NEE (np.ndarray): Randomly generated Net Ecosystem Exchange values.
            - uStar (np.ndarray): Randomly generated u* values.
            - T (np.ndarray): Randomly generated temperature values.
            - fNight (np.ndarray): Array indicating day (0) or night (1) conditions.
    """
    t = np.linspace(*tspan, nt)  # Generate time vector
    NEE = np.piecewise(t, [t < 100, (t >= 100) & (t < 200), t >= 200],
                       [lambda x: 2 * x + 1, lambda x: -x + 300, lambda x: 0.5 * x + 100])
    uStar = np.random.uniform(*uStar_pars, size=nt)  # u* values between typical ranges
    T = np.random.uniform(*T_pars, size=nt)  # Temperature values
    if fNight is None:
        fNight = np.random.choice([0, 1], size=nt)  # Randomly assign day/night
    else:
        fNight = np.resize(fNight, nt)
    return t, NEE, uStar, T, fNight

def test_cpdBootstrapUStarTh4Season20100901_basic(matlab_engine, mock_data):
    t, NEE, uStar, T, fNight = mock_data
    fPlot = 0
    cSiteYr = "Site_2024"
    nBoot = 10

    # Convert mock inputs to MATLAB format
    t_matlab = matlab.double(t.tolist())
    NEE_matlab = matlab.double(NEE.tolist())
    uStar_matlab = matlab.double(uStar.tolist())
    T_matlab = matlab.double(T.tolist())
    fNight_matlab = matlab.logical(fNight.tolist())

    # Call MATLAB function
    Cp2, Stats2, Cp3, Stats3 = matlab_engine.cpdBootstrapUStarTh4Season20100901(
        t_matlab, NEE_matlab, uStar_matlab, T_matlab, fNight_matlab, fPlot, cSiteYr, nBoot, 1, nargout=4
    )
    Stats2 = json.loads(Stats2)
    Stats3 = json.loads(Stats3)

    # Assertions for output types
    assert isinstance(Cp2, matlab.double), "Cp2 should be a MATLAB double array."
    assert isinstance(Stats2, list), "Stats2 should be a list of MATLAB structs."
    assert isinstance(Cp3, matlab.double), "Cp3 should be a MATLAB double array."
    assert isinstance(Stats3, list), "Stats3 should be a list of MATLAB structs."

    # Validate dimensions of the output arrays
    assert len(Cp2) == 4, "Cp2 should have 4 seasons."
    assert len(Cp3) == 4, "Cp3 should have 4 seasons."
    assert len(Stats2) == 4, "Stats2 should have 4 entries for each season."
    assert len(Stats3) == 4, "Stats3 should have 4 entries for each season."

    # Check the structure of Stats2 and Stats3
    struct = ['n', 'Cp', 'Fmax', 'p', 'b0', 'b1', 'b2', 'c2', 'cib0', 'cib1', 'cic2', 'mt' , 'ti', 'tf', 'ruStarVsT', 'puStarVsT', 'mT', 'ciT']
    for s2, s3 in zip(Stats2, Stats3):
        for i in range(8):  # Assuming nStrataX = 8
            for j in range(nBoot):
                for k in struct:
                    assert k in (s2[i][j] and s3[i][j])

def test_cpdBootstrapUStarTh4Season20100901_edge_case_high_bootstrap(matlab_engine, mock_data):
    # Test with a high number of bootstraps
    t, NEE, uStar, T, fNight = mock_data
    fPlot = 0
    cSiteYr = "Site_2024"
    nBoot = 100  # Large number of bootstraps

    # Convert to MATLAB format
    t_matlab = matlab.double(t.tolist())
    NEE_matlab = matlab.double(NEE.tolist())
    uStar_matlab = matlab.double(uStar.tolist())
    T_matlab = matlab.double(T.tolist())
    fNight_matlab = matlab.logical(fNight.tolist())

    # Call MATLAB function
    Cp2, Stats2, Cp3, Stats3 = matlab_engine.cpdBootstrapUStarTh4Season20100901(
        t_matlab, NEE_matlab, uStar_matlab, T_matlab, fNight_matlab, fPlot, cSiteYr, nBoot, 1, nargout=4
    )
    Stats2 = json.loads(Stats2)
    Stats3 = json.loads(Stats3)

    # Validate dimensions with a high bootstrap count
    assert len(Cp2[0][0]) == nBoot, "Each Cp2 season entry should have `nBoot` bootstraps."
    assert len(Cp3[0][0]) == nBoot, "Each Cp3 season entry should have `nBoot` bootstraps."
    assert len(Stats2[0][0]) == nBoot, "Stats2 should match the number of bootstraps."
    assert len(Stats3[0][0]) == nBoot, "Stats3 should match the number of bootstraps."

def test_cpdBootstrap_against_testcases(matlab_engine):
    """Test to compare function output to test cases."""
    path_to_artifacts = "tests/test_artifacts/cpdBootstrapUStarTh4Season20100901_artifacts/"

    # Load the JSON test cases file
    with open(path_to_artifacts + "cpdBootstrapUStarTh4Season20100901_artifacts.json") as f:
        data = json.load(f)

    # Iterate over each test case in the loaded JSON
    for test_case in data["test_cases"]:
        # Ensure test_case is passed correctly to parse_testcase
        inputs, outputs = parse_testcase(test_case, path_to_artifacts)

        # Convert inputs into a list for MATLAB function call
        inputs_list = [inputs[str(i)] for i in range(len(inputs))]
        matlab_args = to_matlab_type(inputs_list)

        # Call the MATLAB function and capture its output
        Cp2, Stats2, Cp3, Stats3 = matlab_engine.cpdBootstrapUStarTh4Season20100901(*matlab_args, 1, nargout=4)
        Cp2 = mat2list(Cp2)
        Cp3 = mat2list(Cp3)
        Stats2 = json.loads(Stats2)
        Stats3 = json.loads(Stats3)

        # Extract the expected outputs for comparison
        outputs_list = [outputs[str(i)] for i in range(len(outputs))]

        # Assertions to compare MATLAB results to expected outputs
        assert Cp2 == outputs_list[0]
        assert Stats2 == outputs_list[1]
        assert Cp3 == outputs_list[2]
        assert Stats3 == outputs_list[3]

# Parameterized test for the get_nPerDay function
@pytest.mark.parametrize("input_data, expected_result", [
    ([0, 1, 2, 3, 4], 1),                         # 1 unit per day (equal spacing)
    ([0, 0.5, 1.0, 1.5, 2.0], 2),                 # 2 units per day
    ([0, 2, 4, 6, 8], 1.0),                         # Large difference, should round to 0
    ([0, 1, np.nan, 3, 4], 1),                    # Includes NaN, should ignore it
    ([0, 1.1, 2.2, 3.3, 4.4], 1),                 # Non-integer difference
])
def test_get_nPerDay(matlab_engine, input_data, expected_result):
    input_data = to_matlab_type(input_data)
    result = matlab_engine.get_nPerDay(input_data)
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

# Parameterized test for the get_nPerBin function
@pytest.mark.parametrize("input_data, expected_result", [
    ([0, 1/24, 2/24, 3/24, 4/24], 3),          # 24 points per day, expect 3 per bin
    ([0, 1/48, 2/48, 3/48, 4/48], 5),          # 48 points per day, expect 5 per bin
    ([0, 1/12, 2/12, 3/12, 4/12], 5),          # Other case, expect default 5 per bin
    ([0, 1, 2, 3, np.nan, 5, 6], 5),           # Includes NaN, should default to 5 per bin
    ([0, 0.5, 1.0, 1.5, 2.0], 5),              # 2 points per day, default case, expect 5 per bin
])
def test_get_nPerBin(matlab_engine, input_data, expected_result):
    input_data = to_matlab_type(input_data)
    result = matlab_engine.get_nPerBin(input_data)
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

# Parameterized test for the get_iNight function
@pytest.mark.parametrize("input_data, expected_result", [
    ([0, 1, 0, 1, 0], matlab.double([2.0, 4.0])),                # Two true values at indices 2 and 4 (MATLAB uses 1-based indexing)
    ([1, 1, 1, 1], matlab.double([1.0, 2.0, 3.0, 4.0])),             # All true values, expect all indices
    ([0, 0, 0, 0], matlab.double([[]])),                       # No true values, expect empty array
    #([0, 1, np.nan, 1, 0], matlab.double([2.0, 4.0])),           # NaN should be ignored, expect indices 2 and 4
    ([1, 0, 0, 1, 1, 0], matlab.double([1.0, 4.0, 5.0]))           # True values at indices 1, 4, and 5
])
def test_get_iNight(matlab_engine, input_data, expected_result):
    input_data = to_matlab_type(input_data)
    result = matlab_engine.get_iNight(input_data)
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

# Parameterized test for the update_ustar function
@pytest.mark.parametrize("input_data, expected_result", [
    ([1, 2, 3, 4], matlab.double([1.0, 2.0, 3.0, 4.0])),                     # No values out of bounds
    ([-1, 2, 3, 5], matlab.double([np.nan, 2.0, 3.0, np.nan])),               # Values < 0 or > 4 should be NaN
    ([0, 4, 4.1], matlab.double([0.0, 4.0, np.nan])),                         # Edge cases with 0, 4, and out-of-bound 4.1
    ([np.nan, 2, 3], matlab.double([np.nan, 2.0, 3.0])),                      # Input with NaN should remain NaN
    ([5, -2, 0, 3], matlab.double([np.nan, np.nan, 0.0, 3.0]))                # Multiple values out of bounds
])
def test_update_uStar(matlab_engine, input_data, expected_result):
    input_data = to_matlab_type(input_data)
    result = matlab_engine.update_uStar(input_data)
    # Compare the MATLAB arrays, allowing for NaN equality
    assert compare_matlab_arrays(result, expected_result), f"Expected {expected_result}, but got {result}"

# Define the expected field names for StatsMT
expected_fields = ['n', 'Cp', 'Fmax', 'p', 'b0', 'b1', 'b2', 'c2', 'cib0', 'cib1', 'cic2',
    'mt', 'ti', 'tf', 'ruStarVsT', 'puStarVsT', 'mT', 'ciT'
]

# Test for the generate_statsMT function
def test_generate_statsMT(matlab_engine):
    # Generate the StatsMT struct
    StatsMT = matlab_engine.generate_statsMT()

    # Ensure all expected fields exist and are NaN
    for field in expected_fields:
        assert field in StatsMT, f"Missing field: {field}"  # Access fields like dict keys
        assert np.isnan(StatsMT[field]), f"Field {field} is not NaN"

# Parameterized test for the get_ntN function
@pytest.mark.parametrize("t_input, nSeasons, expected_ntN", [
    ([0, 1, 2, 3, 4], 2, 2000),    # 2 seasons
    ([0, 0.5, 1.0, 1.5, 2.0], 1, 1000),  #1 season
    ([0, 1, 2], 3, 3000),          # Small time array, 3 seasons
    ([0, 1, 2, 3, 4], 1, 1000),     # 1 season
    ([0, 1], 5, 5000)              # Larger nSeasons
])
def test_get_ntN(matlab_engine, t_input, nSeasons, expected_ntN):
    t_input = to_matlab_type(t_input)

    # Call get_ntN and check the result
    result = matlab_engine.get_ntN(t_input, nSeasons)
    assert result == expected_ntN, f"Expected {expected_ntN}, but got {result}"

# Test for the get_itNee function
@pytest.mark.parametrize(
    "NEE, uStar, T, iNight, expected_itNee",
    [
        # Case 1: No NaNs and full intersection with iNight
        ([1, 2, 3, 4], [1, 1, 1, 1], [1, 1, 1, 1], [1, 2, 3], matlab.double([1.0,2.0,3.0])),
        
        # Case 2: Some NaN values, partial intersection with iNight
        ([1, np.nan, 3, 4], [1, 1, np.nan, 1], [1, 1, 1, np.nan], [1, 3], 1.0),
        
        # Case 3: No intersection with iNight
        ([1, 2, 3, 4], [1, 1, 1, 1], [1, 1, 1, 1], [5, 6], [[]]),
        
        # Case 4: All elements are NaN, so no valid indices
        ([np.nan, np.nan], [np.nan, np.nan], [np.nan, np.nan], [1, 2], matlab.double([[]])),
        
        # Case 5: All valid values, but no intersection with iNight
        ([1, 2, 3, 4], [1, 1, 1, 1], [1, 1, 1, 1], [], []),
        
        # Case 6: All valid values and full intersection with iNight
        ([1, 2, 3], [1, 1, 1], [1, 1, 1], [1, 2, 3], matlab.double([1.0, 2.0, 3.0]))
    ]
)
def test_get_itNee(matlab_engine, NEE, uStar, T, iNight, expected_itNee):
    # Convert input arrays to MATLAB-compatible types
    NEE_matlab = to_matlab_type(NEE)
    uStar_matlab = to_matlab_type(uStar)
    T_matlab = to_matlab_type(T)
    iNight_matlab = to_matlab_type(iNight)
    
    # Call the MATLAB function
    itNee = matlab_engine.get_itNee(NEE_matlab, uStar_matlab, T_matlab, iNight_matlab)
    
    # Compare results
    if type(itNee) != float:
        assert compare_matlab_arrays(itNee, expected_itNee), f"Expected {expected_itNee}, but got {itNee}"
    else:
        assert itNee==expected_itNee

# Test for the setup_Cp function
@pytest.mark.parametrize(
    "nSeasons, nStrataX, nBoot, expected_shape",
    [
        # Case 1: Basic 2x2x2 array
        (2, 2, 2, (2, 2, 2)),

        # Case 2: Single season, single strata, single boot
        (1, 1, 1, ()),

        # Case 3: 3 seasons, 4 strata, 5 bootstrap iterations
        (3, 4, 5, (3, 4, 5)),

        # Case 4: No bootstrap iterations (nBoot=0)
        (2, 3, 0, (2, 3, 0)),

        # Case 5: One season, multiple strata, multiple bootstraps
        (1, 5, 4, (1, 5, 4)),
    ]
)
def test_setup_Cp(matlab_engine, nSeasons, nStrataX, nBoot, expected_shape):
    # Call the MATLAB function
    Cp = matlab_engine.setup_Cp(nSeasons, nStrataX, nBoot)

    # Convert the MATLAB output to numpy arrays for comparison
    Cp_array = np.array(Cp)

    # Check the shape of Cp2 and Cp3
    assert Cp_array.shape == expected_shape, f"Expected shape {expected_shape} for Cp, but got {Cp_array.shape}"

    # Ensure all elements are NaN
    assert np.isnan(Cp_array).all(), "Not all elements in Cp2 are NaN"

stats_entry = {'n': None, 'Cp': None, 'Fmax': None, 'p': None, 'b0': None, 'b1': None, 'b2': None, 'c2': None, 'cib0': None, 'cib1': None, 'cic2': None, 'mt': None, 'ti': None, 'tf': None, 'ruStarVsT': None, 'puStarVsT': None, 'mT': None, 'ciT': None}
# Test for the setup_Stats function
@pytest.mark.parametrize(
    "nBoot, nSeasons, nStrataX, expected_shape",
    [
        # Case 1: Basic 2x2x2 array
        (2, 2, 2, ([[[stats_entry, stats_entry],[stats_entry,stats_entry]],[[stats_entry,stats_entry],[stats_entry,stats_entry]]])),

        # Case 2: Single season, single strata, single boot
        (1, 1, 1, stats_entry),

        # Case 3: No bootstrap iterations (nBoot=0)
        (0, 2, 3, []),
    ]
)
def test_setup_Stats(matlab_engine, nBoot, nSeasons, nStrataX, expected_shape):
    # Call the MATLAB function
    Stats= matlab_engine.setup_Stats(nBoot, nSeasons, nStrataX, 1)

    Stats = json.loads(Stats)

    assert Stats == expected_shape
