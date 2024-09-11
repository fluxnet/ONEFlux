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

def generate_mock_data(nt):
    """Generates mock time series data for testing."""
    t = np.linspace(0, 1, nt)  # Generate time vector
    NEE = np.random.normal(size=nt)  # Random Net Ecosystem Exchange values
    uStar = np.random.uniform(0.1, 3.5, size=nt)  # u* values between typical ranges
    T = np.random.uniform(-10, 30, size=nt)  # Temperature values
    fNight = np.random.choice([0, 1], size=nt)  # Randomly assign day/night
    return t, NEE, uStar, T, fNight

def test_cpdBootstrapUStarTh4Season20100901_basic(matlab_engine):
    # Generate mock inputs
    nt = 200  # Number of time points
    t, NEE, uStar, T, fNight = generate_mock_data(nt)
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

def test_cpdBootstrapUStarTh4Season20100901_edge_case_high_bootstrap(matlab_engine):
    # Test with a high number of bootstraps
    nt = 500  # More extensive dataset
    t, NEE, uStar, T, fNight = generate_mock_data(nt)
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
