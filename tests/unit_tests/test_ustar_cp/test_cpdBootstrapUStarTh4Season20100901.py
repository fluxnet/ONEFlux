"""Test module for the cpdBootstrapUStarTh4Season20100901 matlab function.

This module contains the unit tests for the cpdBootstrapUStarTh4Season20100901. 
These tests cover basic behaviour, edge cases and errors.
"""

import pytest
import matlab.engine
import numpy as np
import json
import csv
import os

@pytest.fixture
def load_json(name):
    """Loads json."""

    with open(name, 'r') as file:
        return json.load(file)

@pytest.fixture(scope="module")
def matlab_engine():
    # Initialize MATLAB engine
    eng = matlab.engine.start_matlab()
    eng.addpath('/home/tcai/Projects/ONEFlux/oneflux_steps/ustar_cp')
    yield eng
    eng.quit()

@pytest.fixture(scope="module")
def mock_data(nt=300, tspan=(0, 1), uStar_pars=(0.1, 3.5), T_pars=(-10, 30), fNight=None):
    """
    Fixture to generate mock time series data for testing purposes. This fixture 
    creates a set of synthetic data typically used in environmental studies, 
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
    if fNight == None:
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
    for s2, s3 in zip(Stats2, Stats3):
        for i in range(8):  # Assuming nStrataX = 8
            for j in range(nBoot):
                assert 'n' in s2[i][j]
                assert 'Cp' in s2[i][j]
                assert 'Fmax' in s2[i][j]
                assert 'p' in s2[i][j]
                assert 'b0' in s2[i][j]
                assert 'b1' in s2[i][j]
                assert 'b2' in s2[i][j]
                assert 'c2' in s2[i][j]
                assert 'cib0' in s2[i][j]
                assert 'cib1' in s2[i][j]
                assert 'cic2' in s2[i][j]
                assert 'mt' in s2[i][j]
                assert 'ti' in s2[i][j]
                assert 'tf' in s2[i][j]
                assert 'ruStarVsT' in s2[i][j]
                assert 'puStarVsT' in s2[i][j]
                assert 'mT' in s2[i][j]
                assert 'ciT' in s2[i][j]

                assert 'n' in s3[i][j]
                assert 'Cp' in s3[i][j]
                assert 'Fmax' in s3[i][j]
                assert 'p' in s3[i][j]
                assert 'b0' in s3[i][j]
                assert 'b1' in s3[i][j]
                assert 'b2' in s3[i][j]
                assert 'c2' in s3[i][j]
                assert 'cib0' in s3[i][j]
                assert 'cib1' in s3[i][j]
                assert 'cic2' in s3[i][j]
                assert 'mt' in s3[i][j]
                assert 'ti' in s3[i][j]
                assert 'tf' in s3[i][j]
                assert 'ruStarVsT' in s3[i][j]
                assert 'puStarVsT' in s3[i][j]
                assert 'mT' in s3[i][j]
                assert 'ciT' in s3[i][j]

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

def read_csv_with_csv_module(file_path):
    return np.loadtxt(file_path, delimiter=',')
    # with open(file_path, mode='r') as file:
    #     reader = csv.reader(file)
    #     data = [row for row in reader]
    # return data

def read_file(file_path):
    # Check the file extension to differentiate between CSV and JSON
    if file_path.endswith('.csv'):
        return read_csv_with_csv_module(file_path)
    elif file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            return json.load(f)  # Load JSON file
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

def to_matlab_type(data):
    if isinstance(data, dict):
        # Convert a Python dictionary to a MATLAB struct
        matlab_struct = matlab.struct()
        for key, value in data.items():
            matlab_struct[key] = to_matlab_type(value)  # Recursively handle nested structures
        return matlab_struct
    elif isinstance(data, np.ndarray):
        if data.dtype == bool:
            return matlab.logical(data.tolist())
        elif np.isreal(data).all():
            return matlab.double(data.tolist())
        else:
            return data.tolist()  # Convert non-numeric arrays to lists
    elif isinstance(data, list):
        # Convert Python list to MATLAB double array if all elements are numbers
        if all(isinstance(elem, (int, float)) for elem in data):
            return matlab.double(data)
        else:
            # Create a cell array for lists containing non-numeric data
            return [to_matlab_type(elem) for elem in data]
    elif isinstance(data, (int, float)):
        return matlab.double([data])  # Convert single numbers
    else:
        return data  # If the data type is already MATLAB-compatible

def test_cpdBootstrap_against_testcases(matlab_engine):
    """Test to compare function output to testcases."""
    path_to_artifacts= "tests/test_artifacts/cpdBootstrapUStarTh4Season20100901_artifacts/"

    with open(path_to_artifacts + "cpdBootstrapUStarTh4Season20100901_artifacts.json") as f:
        data = json.load(f)
    for test_case in data["test_cases"]:
        inputs_list = {}
        for key, value in test_case['input'].items():
            if isinstance(value, str):  # Check if the value is a string (likely a file path)
                path = os.path.join(path_to_artifacts, test_case["id"], value)
                if os.path.exists(path):  # Check if the file exists
                    # Read the file using the fixture function and store the data
                    file_data = read_file(path)
                    inputs_list[key] = file_data
                else:
                    inputs_list[key] = value
            else:
                # If it's not a string, directly store the value in the inputs list
                inputs_list[key] = value
        
        inputs_list = [inputs_list[str(i)] for i in range(len(inputs_list))]
        matlab_args = to_matlab_type(inputs_list)

        Cp2, Stats2, Cp3, Stats3 = matlab_engine.cpdBootstrapUStarTh4Season20100901(*matlab_args, 1, nargout=4)
        Cp2 = mat2list(Cp2)
        Cp3 = mat2list(Cp3)
        Stats2 = json.loads(Stats2)
        Stats3 = json.loads(Stats3)

        outputs_list = {}
        for key, value in test_case['expected_output'].items():
            if isinstance(value, str):  # Check if the value is a string (likely a file path)
                path = os.path.join(path_to_artifacts, test_case["id"], value)
                if os.path.exists(path):  # Check if the file exists
                    # Read the file using the fixture function and store the data
                    file_data = read_file(path)
                    outputs_list[key] = file_data
                else:
                    outputs_list[key] = value
            else:
                # If it's not a string, directly store the value in the inputs list
                outputs_list[key] = value
        outputs_list = [outputs_list[str(i)] for i in range(len(outputs_list))]

        assert Cp2 == outputs_list[0]
        assert Stats2 == outputs_list[1]
        assert Cp3 == outputs_list[2]
        assert Stats3 == outputs_list[3]

def mat2list(arr):
    return np.where(np.isnan(arr), None, arr).tolist()