# test_cpdAssignUStarTh20100901.py

import pytest
import numpy as np

def create_mock_stats_2d(matlab_engine):
    # Create a mock 2D Stats structure for testing
    nWindows = 4
    nBoot = 10
    Stats = matlab_engine.struct()
    Stats.mt = matlab_engine.randn(nWindows, nBoot)
    Stats.Cp = matlab_engine.randn(nWindows, nBoot)
    Stats.b1 = matlab_engine.randn(nWindows, nBoot)
    Stats.c2 = matlab_engine.randn(nWindows, nBoot)
    Stats.cib1 = matlab_engine.randn(nWindows, nBoot)
    Stats.cic2 = matlab_engine.randn(nWindows, nBoot)
    Stats.p = matlab_engine.rand(nWindows, nBoot)
    return Stats

def create_mock_stats_3d(matlab_engine):
    # Create a mock 3D Stats structure for testing
    nWindows = 4
    nStrata = 3
    nBoot = 10
    Stats = matlab_engine.struct()
    Stats.mt = matlab_engine.randn(nWindows, nStrata, nBoot)
    Stats.Cp = matlab_engine.randn(nWindows, nStrata, nBoot)
    Stats.b1 = matlab_engine.randn(nWindows, nStrata, nBoot)
    Stats.c2 = matlab_engine.randn(nWindows, nStrata, nBoot)
    Stats.cib1 = matlab_engine.randn(nWindows, nStrata, nBoot)
    Stats.cic2 = matlab_engine.randn(nWindows, nStrata, nBoot)
    Stats.p = matlab_engine.rand(nWindows, nStrata, nBoot)
    return Stats

def test_cpdAssignUStarTh20100901_2d_stats(matlab_engine):
    # Test the function with a 2D Stats input
    Stats = create_mock_stats_2d(matlab_engine)
    fPlot = 0
    cSiteYr = 'test_site_2022'
    
    result = matlab_engine.cpdAssignUStarTh20100901(Stats, fPlot, cSiteYr, nargout=10)
    
    assert len(result[0]) > 0  # CpA should not be empty
    assert len(result[1]) > 0  # nA should not be empty
    assert len(result[2]) > 0  # tW should not be empty
    assert len(result[3]) > 0  # CpW should not be empty
    assert result[4] in ['D', 'E']  # cMode should be 'D' or 'E'
    assert isinstance(result[5], str)  # cFailure should be a string
    assert len(result[6]) == len(result[0])  # fSelect should match CpA size
    assert len(result[7]) == 4  # sSine should have 4 elements
    assert 0 <= result[8] <= 1  # FracSig should be between 0 and 1
    assert 0 <= result[9] <= 1  # FracModeD should be between 0 and 1
    assert 0 <= result[10] <= 1  # FracSelect should be between 0 and 1

def test_cpdAssignUStarTh20100901_3d_stats(matlab_engine):
    # Test the function with a 3D Stats input
    Stats = create_mock_stats_3d(matlab_engine)
    fPlot = 0
    cSiteYr = 'test_site_2022'
    
    result = matlab_engine.cpdAssignUStarTh20100901(Stats, fPlot, cSiteYr, nargout=10)
    
    assert len(result[0]) > 0  # CpA should not be empty
    assert len(result[1]) > 0  # nA should not be empty
    assert len(result[2]) > 0  # tW should not be empty
    assert len(result[3]) > 0  # CpW should not be empty
    assert result[4] in ['D', 'E']  # cMode should be 'D' or 'E'
    assert isinstance(result[5], str)  # cFailure should be a string
    assert len(result[6]) == len(result[0])  # fSelect should match CpA size
    assert len(result[7]) == 4  # sSine should have 4 elements
    assert 0 <= result[8] <= 1  # FracSig should be between 0 and 1
    assert 0 <= result[9] <= 1  # FracModeD should be between 0 and 1
    assert 0 <= result[10] <= 1  # FracSelect should be between 0 and 1

def test_cpdAssignUStarTh20100901_invalid_stats(matlab_engine):
    # Test the function with an invalid Stats input (not 2D or 3D)
    Stats = matlab_engine.randn(5, 5, 5, 5)  # Invalid 4D array
    fPlot = 0
    cSiteYr = 'test_site_2022'
    
    result = matlab_engine.cpdAssignUStarTh20100901(Stats, fPlot, cSiteYr, nargout=10)
    
    assert result[5] == 'Stats must be 2D or 3D.'  # cFailure should indicate an invalid Stats dimension

def test_cpdAssignUStarTh20100901_insufficient_detections(matlab_engine):
    # Test the function with insufficient significant detections
    Stats = create_mock_stats_2d(matlab_engine)
    Stats.p = matlab_engine.ones(*Stats.p.shape)  # Set p-values to 1 (non-significant)
    fPlot = 0
    cSiteYr = 'test_site_2022'
    
    result = matlab_engine.cpdAssignUStarTh20100901(Stats, fPlot, cSiteYr, nargout=10)
    
    assert result[5] == 'Less than 10% successful detections.'  # cFailure should indicate insufficient detections
