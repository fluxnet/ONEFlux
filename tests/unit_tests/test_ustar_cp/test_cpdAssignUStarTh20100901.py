
import pytest
import matlab.engine
import numpy as np

@pytest.fixture(scope="module")
def matlab_engine():
    # Initialize MATLAB engine
    eng = matlab.engine.start_matlab()
    yield eng
    eng.quit()

@pytest.fixture
def mock_stats():
    # Create a mock Stats structure
    class MockStats:
        def __init__(self):
            self.mt = np.random.rand(40)
            self.Cp = np.random.rand(40)
            self.b1 = np.random.rand(40)
            self.c2 = np.random.rand(40)
            self.cib1 = np.random.rand(40)
            self.cic2 = np.random.rand(40)
            self.p = np.random.rand(40)

    return MockStats()

def test_cpdAssignUStarTh20100901_basic(matlab_engine, mock_stats):
    # Convert mock stats to MATLAB structure
    stats_matlab = matlab_engine.struct()
    for field in ['mt', 'Cp', 'b1', 'c2', 'cib1', 'cic2', 'p']:
        setattr(stats_matlab, field, matlab.double(getattr(mock_stats, field).tolist()))

    fPlot = 0
    cSiteYr = "TestSite_2024"

    # Call MATLAB function
    CpA, nA, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect = matlab_engine.cpdAssignUStarTh20100901(
        stats_matlab, fPlot, cSiteYr, nargout=11
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

def test_cpdAssignUStarTh20100901_plotting(matlab_engine, mock_stats):
    # Test with plotting enabled
    stats_matlab = matlab_engine.struct()
    for field in ['mt', 'Cp', 'b1', 'c2', 'cib1', 'cic2', 'p']:
        setattr(stats_matlab, field, matlab.double(getattr(mock_stats, field).tolist()))

    fPlot = 1
    cSiteYr = "TestSite_2024"

    # Call MATLAB function
    results = matlab_engine.cpdAssignUStarTh20100901(stats_matlab, fPlot, cSiteYr, nargout=11)

    # Check if the function runs without errors when plotting is enabled
    assert len(results) == 11, "Function should return 11 outputs even with plotting enabled"

def test_cpdAssignUStarTh20100901_invalid_input(matlab_engine):
    # Test with invalid input
    invalid_stats = matlab_engine.struct()
    invalid_stats.mt = matlab.double([])  # Empty array

    fPlot = 0
    cSiteYr = "TestSite_2024"

    # Call MATLAB function
    CpA, nA, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect = matlab_engine.cpdAssignUStarTh20100901(
        invalid_stats, fPlot, cSiteYr, nargout=11
    )

    # Check if function handles invalid input gracefully
    assert len(CpA) == 0, "CpA should be empty for invalid input"
    assert len(cFailure) > 0, "cFailure should contain an error message for invalid input"

def test_cpdAssignUStarTh20100901_edge_cases(matlab_engine, mock_stats):
    # Test edge cases (e.g., all significant change points, no significant change points)
    edge_stats = matlab_engine.struct()
    
    # Case 1: All significant change points
    edge_stats.mt = matlab.double(mock_stats.mt.tolist())
    edge_stats.Cp = matlab.double(mock_stats.Cp.tolist())
    edge_stats.b1 = matlab.double(np.ones_like(mock_stats.b1).tolist())  # All positive b1
    edge_stats.c2 = matlab.double(np.zeros_like(mock_stats.c2).tolist())  # All zero c2
    edge_stats.cib1 = matlab.double(mock_stats.cib1.tolist())
    edge_stats.cic2 = matlab.double(mock_stats.cic2.tolist())
    edge_stats.p = matlab.double(np.zeros_like(mock_stats.p).tolist())  # All significant

    results_all_sig = matlab_engine.cpdAssignUStarTh20100901(edge_stats, 0, "AllSig_2024", nargout=11)
    
    # Case 2: No significant change points
    edge_stats.p = matlab.double(np.ones_like(mock_stats.p).tolist())  # All non-significant

    results_no_sig = matlab_engine.cpdAssignUStarTh20100901(edge_stats, 0, "NoSig_2024", nargout=11)

    # Assertions for edge cases
    assert len(results_all_sig[0]) > 0, "Should produce results for all significant change points"
    assert len(results_no_sig[5]) > 0, "Should produce a failure message for no significant change points"
