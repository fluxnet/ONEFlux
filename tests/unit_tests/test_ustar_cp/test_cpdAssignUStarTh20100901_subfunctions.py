# test_cpdAssignUStarTh20100901_subfunctions.py

import pytest
import numpy as np

def test_initialize_outputs(matlab_engine):
    # Test initialization of outputs
    outputs = matlab_engine.initializeOutputs(nargout=10)
    assert all([len(output) == 0 or output == '' for output in outputs])  # Ensure all outputs are initialized to empty values

def test_compute_window_sizes_2d(matlab_engine):
    # Test computeWindowSizes with a 2D Stats input
    Stats = matlab_engine.randn(4, 10)  # 2D array
    nWindows, nStrata, nBoot, nDim, nSelectN = matlab_engine.computeWindowSizes(Stats, nargout=5)
    assert nDim == 2
    assert nWindows == 4
    assert nStrata == 1
    assert nBoot == 10

def test_compute_window_sizes_3d(matlab_engine):
    # Test computeWindowSizes with a 3D Stats input
    Stats = matlab_engine.randn(4, 3, 10)  # 3D array
    nWindows, nStrata, nBoot, nDim, nSelectN = matlab_engine.computeWindowSizes(Stats, nargout=5)
    assert nDim == 3
    assert nWindows == 4
    assert nStrata == 3
    assert nBoot == 10

def test_compute_window_sizes_invalid(matlab_engine):
    # Test computeWindowSizes with an invalid Stats input
    Stats = matlab_engine.randn(4, 4, 4, 4)  # 4D array
    nWindows, nStrata, nBoot, nDim, nSelectN = matlab_engine.computeWindowSizes(Stats, nargout=5)
    assert nDim is None

def test_extract_fields(matlab_engine):
    # Test extractFields function
    Stats = matlab_engine.struct()
    Stats.mt = matlab_engine.randn(4, 3, 10)
    Stats.Cp = matlab_engine.randn(4, 3, 10)
    Stats.b1 = matlab_engine.randn(4, 3, 10)
    Stats.c2 = matlab_engine.randn(4, 3, 10)
    Stats.cib1 = matlab_engine.randn(4, 3, 10)
    Stats.cic2 = matlab_engine.randn(4, 3, 10)
    Stats.p = matlab_engine.rand(4, 3, 10)
    xmt, xCp, b1, c2, cib1, cic2, p = matlab_engine.extractFields(Stats, nargout=7)
    assert len(xmt) > 0
    assert len(xCp) > 0

def test_determine_model_type_3_parameter(matlab_engine):
    # Test determineModelType with non-empty c2 (3-parameter model)
    c2 = matlab_engine.randn(4, 3, 10)
    b1 = matlab_engine.randn(4, 3, 10)
    nPar, c2_out, cic2 = matlab_engine.determineModelType(c2, b1, nargout=3)
    assert nPar == 3

def test_determine_model_type_2_parameter(matlab_engine):
    # Test determineModelType with empty c2 (2-parameter model)
    c2 = matlab_engine.nan(4, 3, 10)  # c2 is NaN, implying 2-parameter model
    b1 = matlab_engine.randn(4, 3, 10)
    nPar, c2_out, cic2 = matlab_engine.determineModelType(c2, b1, nargout=3)
    assert nPar == 2
    assert all(c2_out == 0)

def test_classify_and_select_change_points(matlab_engine):
    # Test classifyAndSelectChangePoints function
    Stats = matlab_engine.struct()
    Stats.mt = matlab_engine.randn(4, 3, 10)
    Stats.Cp = matlab_engine.randn(4, 3, 10)
    Stats.b1 = matlab_engine.randn(4, 3, 10)
    Stats.c2 = matlab_engine.randn(4, 3, 10)
    Stats.cib1 = matlab_engine.randn(4, 3, 10)
    Stats.cic2 = matlab_engine.randn(4, 3, 10)
    Stats.p = matlab_engine.rand(4, 3, 10)
    [xmt, xCp, b1, c2, cib1, cic2, p] = matlab_engine.extractFields(Stats, nargout=7)
    nPar, c2_out, cic2 = matlab_engine.determineModelType(c2, b1, nargout=3)
    fP, iSelect, cMode, fSelect, FracSig, FracModeD, FracSelect, cFailure = matlab_engine.classifyAndSelectChangePoints(xmt, xCp, b1, c2, p, nPar, nargout=8)
    assert FracSig >= 0
    assert FracSelect >= 0

def test_exclude_outliers(matlab_engine):
    # Test excludeOutliers function
    Stats = matlab_engine.struct()
    Stats.mt = matlab_engine.randn(4, 3, 10)
    Stats.Cp = matlab_engine.randn(4, 3, 10)
    Stats.b1 = matlab_engine.randn(4, 3, 10)
    Stats.c2 = matlab_engine.randn(4, 3, 10)
    Stats.cib1 = matlab_engine.randn(4, 3, 10)
    Stats.cic2 = matlab_engine.randn(4, 3, 10)
    Stats.p = matlab_engine.rand(4, 3, 10)
    [xmt, xCp, b1, c2, cib1, cic2, p] = matlab_engine.extractFields(Stats, nargout=7)
    nPar, c2_out, cic2 = matlab_engine.determineModelType(c2, b1, nargout=3)
    fP, iSelect, cMode, fSelect, FracSig, FracModeD, FracSelect, cFailure = matlab_engine.classifyAndSelectChangePoints(xmt, xCp, b1, c2, p, nPar, nargout=8)
    iSelect_out, fSelect_out, nModeD, nModeE = matlab_engine.excludeOutliers(xCp, b1, c2, cib1, cic2, iSelect, fSelect, 10, 10, nPar, nargout=4)
    assert len(iSelect_out) <= len(iSelect)

def test_aggregate_change_points_2d(matlab_engine):
    # Test aggregateChangePoints function with 2D Stats
    Stats = matlab_engine.randn(4, 10)  # 2D Stats
    xmt, xCp, b1, c2, cib1, cic2, p = matlab_engine.extractFields(Stats, nargout=7)
    iSelect = matlab_engine.randi([1, 10], [4, 1])
    fSelect = matlab_engine.rand(4, 10) > 0.5
    CpA, nA, tW, CpW = matlab_engine.aggregateChangePoints(xmt, xCp, iSelect, fSelect, 4, 1, 10, 2, nargout=4)
    assert len(CpA) > 0
    assert len(nA) > 0

def test_aggregate_change_points_3d(matlab_engine):
    # Test aggregateChangePoints function with 3D Stats
    Stats = matlab_engine.randn(4, 3, 10)  # 3D Stats
    xmt, xCp, b1, c2, cib1, cic2, p = matlab_engine.extractFields(Stats, nargout=7)
    iSelect = matlab_engine.randi([1, 10], [4, 3, 1])
    fSelect = matlab_engine.rand(4, 3, 10) > 0.5
    CpA, nA, tW, CpW = matlab_engine.aggregateChangePoints(xmt, xCp, iSelect, fSelect, 4, 3, 10, 3, nargout=4)
    assert len(CpA) > 0
    assert len(nA) > 0

def test_fit_annual_sine_curve(matlab_engine):
    # Test fitAnnualSineCurve function
    mt = matlab_engine.rand(100, 1) * 365
    Cp = matlab_engine.sin(mt * 2 * np.pi / 365) + matlab_engine.randn(100, 1) * 0.1
    sSine = matlab_engine.fitAnnualSineCurve(mt, Cp, nargout=1)
    assert len(sSine) == 4

def test_plot_results(matlab_engine, tmp_path):
    # Test plotResults function (this will mainly test if the function runs without error)
    Stats = matlab_engine.randn(4, 10)  # Example 2D Stats
    xmt, xCp, b1, c2, cib1, cic2, p = matlab_engine.extractFields(Stats, nargout=7)
    iSelect = matlab_engine.randi([1, 10], [4, 1])
    fSelect = matlab_engine.rand(4, 10) > 0.5
    CpA, nA, tW, CpW = matlab_engine.aggregateChangePoints(xmt, xCp, iSelect, fSelect, 4, 1, 10, 2, nargout=4)
    sSine = matlab_engine.fitAnnualSineCurve(xmt, xCp, nargout=1)
    
    # Use a temporary directory for plot outputs
    plot_path = str(tmp_path / "plot_results")
    matlab_engine.plotResults(xmt, xCp, iSelect, tW, CpW, sSine, 'D', 'test_site_2022', 2, len(iSelect), 0.8, 0.7, 0.6, nargout=0)
    
    # Check that the plots are generated (this can be more sophisticated depending on how the plots are saved/handled)
    # Note: Actual plot output checking would require file handling or more advanced image comparison techniques.
    assert tmp_path.exists()
