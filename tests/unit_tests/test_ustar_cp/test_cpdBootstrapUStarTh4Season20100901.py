"""Test module for the cpdBootstrapUStarTh4Season20100901 matlab function.

This module contains the unit tests for the cpdBootstrapUStarTh4Season20100901. 
These tests cover basic behaviour, edge cases and errors.
"""

import pytest
import matlab.engine
import numpy as np

@pytest.fixture(scope="module")
def matlab_engine():
    # Initialize MATLAB engine
    eng = matlab.engine.start_matlab()
    yield eng
    eng.quit()

@pytest.fixture(scope="module")
def mock_data(nt=200, tspan=(0, 1), uStar_pars=(0.1, 3.5), T_pars=(-10, 30), fNight=None):
    """
    Fixture to generate mock time series data for testing purposes. This fixture 
    creates a set of synthetic data typically used in environmental studies, 
    such as Net Ecosystem Exchange (NEE), uStar values, temperature, and day/night flags.

    Args:
        nt (int, optional): Number of time points to generate in the series. 
                            Defaults to 200.
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
    NEE = np.random.normal(size=nt)  # Random Net Ecosystem Exchange values
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
        t_matlab, NEE_matlab, uStar_matlab, T_matlab, fNight_matlab, fPlot, cSiteYr, nBoot, nargout=4
    )

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

def test_cpdBootstrapUStarTh4Season20100901_invalid_input(matlab_engine):
    # Test with invalid inputs to ensure the function handles them gracefully
    t = [1, 2, 3]  # Insufficient time points
    NEE = [0.5, -0.2, 0.1]
    uStar = [0.3, 0.4, 0.5]
    T = [15, 16, 17]
    fNight = [1, 0, 1]
    fPlot = 0
    cSiteYr = "Site_2024"
    nBoot = 5

    # Convert inputs to MATLAB format
    t_matlab = matlab.double(t)
    NEE_matlab = matlab.double(NEE)
    uStar_matlab = matlab.double(uStar)
    T_matlab = matlab.double(T)
    fNight_matlab = matlab.logical(fNight)

    # Call MATLAB function
    Cp2, Stats2, Cp3, Stats3 = matlab_engine.cpdBootstrapUStarTh4Season20100901(
        t_matlab, NEE_matlab, uStar_matlab, T_matlab, fNight_matlab, fPlot, cSiteYr, nBoot, nargout=4
    )

    # Check if function handles insufficient data gracefully
    assert Cp2 == [], "Cp2 should be empty for insufficient data."
    assert Stats2 == [], "Stats2 should be empty for insufficient data."
    assert Cp3 == [], "Cp3 should be empty for insufficient data."
    assert Stats3 == [], "Stats3 should be empty for insufficient data."

def test_cpdBootstrapUStarTh4Season20100901_edge_case_high_bootstrap(matlab_engine, mock_data):
    # Test with a high number of bootstraps
    nt = 500  # More extensive dataset
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
        t_matlab, NEE_matlab, uStar_matlab, T_matlab, fNight_matlab, fPlot, cSiteYr, nBoot, nargout=4
    )

    # Validate dimensions with a high bootstrap count
    assert len(Cp2[0][0]) == nBoot, "Each Cp2 season entry should have `nBoot` bootstraps."
    assert len(Cp3[0][0]) == nBoot, "Each Cp3 season entry should have `nBoot` bootstraps."
    assert len(Stats2[0][0]) == nBoot, "Stats2 should match the number of bootstraps."
    assert len(Stats3[0][0]) == nBoot, "Stats3 should match the number of bootstraps."
