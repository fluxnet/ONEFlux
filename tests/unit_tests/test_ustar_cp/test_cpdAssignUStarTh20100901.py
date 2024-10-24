import pytest
import json
import matlab.engine
import numpy as np


@pytest.fixture(scope="module")
def mock_data(matlab_engine, nt=300, tspan=(0, 1), uStar_pars=(0.1, 3.5), T_pars=(-10, 30), fNight=None):
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
    fPlot = 0
    nBoot = 10
    cSiteYr = "Site_2024"
    t = np.linspace(*tspan, nt)  # Generate time vector
    NEE = np.piecewise(t, [t < 100, (t >= 100) & (t < 200), t >= 200],
                       [lambda x: 2 * x + 1, lambda x: -x + 300, lambda x: 0.5 * x + 100])
    uStar = np.random.uniform(*uStar_pars, size=nt)  # u* values between typical ranges
    T = np.random.uniform(*T_pars, size=nt)  # Temperature values
    if fNight is None:
        fNight = np.random.choice([0, 1], size=nt)  # Randomly assign day/night
    else:
        fNight = np.resize(fNight, nt)
    
    Cp2, Stats2, Cp3, Stats3 = matlab_engine.cpdBootstrapUStarTh4Season20100901(
        t,NEE,uStar,T,fNight,fPlot,cSiteYr,nBoot,1,nargout=4
    )
    Stats2 = json.loads(Stats2)
    return Stats2, fPlot, cSiteYr


def test_cpdAssignUStarTh20100901_basic(matlab_engine, mock_data):
    stats, fPlot, cSiteYr = mock_data

    # Call MATLAB function
    CpA, nA, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect = matlab_engine.cpdAssignUStarTh20100901(
        stats, fPlot, cSiteYr, nargout=11
    )

    # Assertions
    assert isinstance(CpA, matlab.double), "CpA should be a MATLAB double array"
    assert isinstance(nA, matlab.double), "nA should be a MATLAB double array"
    assert isinstance(tW, matlab.double), "tW should be a MATLAB double array"
    assert isinstance(CpW, matlab.double), "CpW should be a MATLAB double array"
    assert isinstance(cMode, str), "cMode should be a string"
    assert isinstance(cFailure, str), "cFailure should be a string"
    assert isinstance(fSelect, matlab.logical), "fSelect should be a MATLAB logical array"
    assert isinstance(sSine, matlab.double), "sSine should be a MATLAB double array"
    assert isinstance(FracSig, float), "FracSig should be a float"
    assert isinstance(FracModeD, float), "FracModeD should be a float"
    assert isinstance(FracSelect, float), "FracSelect should be a float"


def test_cpdAssignUStarTh20100901_plotting(matlab_engine, mock_data):
    stats, fPlot, cSiteYr = mock_data

    # Call MATLAB function
    results = matlab_engine.cpdAssignUStarTh20100901(stats, fPlot, cSiteYr, nargout=11)

    # Check if the function runs without errors when plotting is enabled
    assert len(results) == 11, "Function should return 11 outputs even with plotting enabled"


@pytest.mark.parametrize("invalid_input", [[], None, "invalid"])
def test_cpdAssignUStarTh20100901_invalid_input(matlab_engine, mock_data, invalid_input):
    stats, fPlot, cSiteYr = mock_data
    
    # Test with invalid input
    stats['mt'] = matlab.double(invalid_input)  # Invalid input

    # Call MATLAB function
    results = matlab_engine.cpdAssignUStarTh20100901(stats, fPlot, cSiteYr, nargout=11)

    # Check if function handles invalid input gracefully
    assert len(results[0]) == 0, "CpA should be empty for invalid input"
    assert len(results[5]) > 0, "cFailure should contain an error message for invalid input"


def test_cpdAssignUStarTh20100901_edge_cases(matlab_engine, mock_data):
    mock_stats, fPlot, cSiteYr = mock_data
    edge_stats = mock_stats.copy()
    
    # Case 1: All significant change points
    edge_stats.b1 = matlab.double(np.ones_like(mock_stats.b1).tolist())  # All positive b1
    edge_stats.c2 = matlab.double(np.zeros_like(mock_stats.c2).tolist())  # All zero c2
    edge_stats.p = matlab.double(np.zeros_like(mock_stats.p).tolist())  # All significant

    results_all_sig = matlab_engine.cpdAssignUStarTh20100901(edge_stats, 0, "AllSig_2024", nargout=11)
    
    # Case 2: No significant change points
    edge_stats.p = matlab.double(np.ones_like(mock_stats.p).tolist())  # All non-significant

    results_no_sig = matlab_engine.cpdAssignUStarTh20100901(edge_stats, 0, "NoSig_2024", nargout=11)

    # Assertions for edge cases
    assert len(results_all_sig[0]) > 0, "Should produce results for all significant change points"
    assert len(results_no_sig[5]) > 0, "Should produce a failure message for no significant change points"
