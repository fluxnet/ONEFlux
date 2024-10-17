"""Test module for the cpdBootstrapUStarTh4Season20100901 matlab function.

This module contains the unit tests for the cpdBootstrapUStarTh4Season20100901. 
These tests cover basic behaviour, edge cases and errors.
"""

import pytest
import matlab.engine
import numpy as np
import json
import os
from tests.conftest import to_matlab_type, read_file, mat2list, parse_testcase

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