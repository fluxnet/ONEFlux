import pytest
import json
import matlab.engine
import numpy as np


@pytest.fixture(scope="module")
def mock_data(test_engine, nt=300, tspan=(0, 1), uStar_pars=(0.1, 3.5), T_pars=(-10, 30), fNight=None):
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
    uStar = np.random.uniform(*uStar_pars, size=nt)  # u* values between typical ranges
    NEE = np.random.uniform(-10, 10, size=nt)  # Random NEE values
    T = np.random.uniform(*T_pars, size=nt)  # Temperature values
    if fNight is None:
        fNight = np.random.choice([0, 1], size=nt)  # Randomly assign day/night
    else:
        fNight = np.resize(fNight, nt)

    Cp2, Stats2, Cp3, Stats3 = test_engine.cpdBootstrapUStarTh4Season20100901(
        t,NEE,uStar,T,fNight,fPlot,cSiteYr,nBoot,jsonencode=[1,3],nargout=4
    )
    return Stats2, fPlot, cSiteYr


def test_cpdAssignUStarTh20100901_basic(test_engine, mock_data):
    stats, fPlot, cSiteYr = mock_data

    # Call MATLAB function
    CpA, nA, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect = test_engine.cpdAssignUStarTh20100901(stats, fPlot, cSiteYr, jsondecode=[0], nargout=11)

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


def test_cpdAssignUStarTh20100901_edge_cases(test_engine, mock_data):
    def set_attr(struct_array, key, val):
        np.vectorize(lambda x: x.update({key: val}))(struct_array)

    mock_stats, fPlot, cSiteYr = mock_data
    edge_stats = mock_stats.copy()

    # Case 1: All significant change points
    set_attr(edge_stats, "p", 0)
    assert edge_stats[0][0][0]['p'] == 0

    results_all_sig = test_engine.cpdAssignUStarTh20100901(edge_stats, 0, "AllSig_2024", jsondecode=[0], nargout=11)

    # Case 2: No significant change points
    set_attr(edge_stats, "p", 1)
    assert edge_stats[0][0][0]['p'] == 1

    results_no_sig = test_engine.cpdAssignUStarTh20100901(edge_stats, 0, "NoSig_2024", jsondecode=[0], nargout=11)

    # Assertions for edge cases
    assert len(results_all_sig[0]) > 0, "Should produce results for all significant change points"
    assert len(results_no_sig[5]) > 0, "Should produce a failure message for no significant change points"