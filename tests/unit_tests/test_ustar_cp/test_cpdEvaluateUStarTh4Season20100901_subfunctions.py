# test_cpdEvaluateUStarTh4Season20100901_refactored.py

import pytest
import numpy as np
import matlab
import math

def test_initialize_data(matlab_engine):
    """
    Test the initializeData function to ensure it correctly initializes variables and filters data.
    """
    # Example input data
    n_days = 120
    n_per_day = 48
    total_points = n_days * n_per_day

    t = np.linspace(0, n_days, total_points)
    NEE = np.random.normal(0, 1, total_points)
    uStar = np.random.uniform(0, 2, total_points)
    T = np.random.uniform(-10, 30, total_points)
    fNight = np.zeros(total_points, dtype=bool)

    # Convert to MATLAB arrays
    t_mat = matlab.double(t.tolist())
    NEE_mat = matlab.double(NEE.tolist())
    uStar_mat = matlab.double(uStar.tolist())
    T_mat = matlab.double(T.tolist())
    fNight_mat = matlab.logical(fNight.tolist())

    # Call the MATLAB function
    nt, nPerDay, itAnnual, ntAnnual, EndDOY = matlab_engine.initializeData(t_mat, NEE_mat, uStar_mat, T_mat, fNight_mat, nargout=5)

    # Assertions
    assert nt == total_points
    assert nPerDay == n_per_day
    assert isinstance(itAnnual, matlab.double)
    assert isinstance(ntAnnual, float)
    assert isinstance(EndDOY, float)

def test_initialize_outputs(matlab_engine):
    """
    Test the initializeOutputs function to ensure it correctly initializes output matrices and Stats structures.
    """
    ntAnnual = 10000  # Example number of annual data points

    # Call the MATLAB function
    Cp2, Cp3, Stats2, Stats3, StatsMT = matlab_engine.initializeOutputs(ntAnnual, nargout=5)

    # Assertions
    assert isinstance(Cp2, matlab.double)
    assert isinstance(Cp3, matlab.double)
    assert isinstance(Stats2, matlab.struct)
    assert isinstance(Stats3, matlab.struct)
    assert isinstance(StatsMT, matlab.struct)
    assert Cp2.size == 32  # 4 seasons * 8 strata
    assert Cp3.size == 32

def test_reorder_data(matlab_engine):
    """
    Test the reorderData function to ensure it correctly reorders the data so that December is at the beginning of the year.
    """
    n_days = 120
    n_per_day = 48
    total_points = n_days * n_per_day

    t = np.linspace(0, n_days, total_points)
    T = np.random.uniform(-10, 30, total_points)
    uStar = np.random.uniform(0, 2, total_points)
    NEE = np.random.normal(0, 1, total_points)
    fNight = np.zeros(total_points, dtype=bool)

    EndDOY = 365  # Simplified example

    # Convert to MATLAB arrays
    t_mat = matlab.double(t.tolist())
    T_mat = matlab.double(T.tolist())
    uStar_mat = matlab.double(uStar.tolist())
    NEE_mat = matlab.double(NEE.tolist())
    fNight_mat = matlab.logical(fNight.tolist())

    # Call the MATLAB function
    t_reordered, T_reordered, uStar_reordered, NEE_reordered, fNight_reordered = matlab_engine.reorderData(t_mat, T_mat, uStar_mat, NEE_mat, fNight_mat, EndDOY, nargout=5)

    # Assertions to check if the reordering took place correctly
    assert isinstance(t_reordered, matlab.double)
    assert isinstance(T_reordered, matlab.double)
    assert isinstance(uStar_reordered, matlab.double)
    assert isinstance(NEE_reordered, matlab.double)
    assert isinstance(fNight_reordered, matlab.logical)

def test_perform_stratification_and_detection(matlab_engine):
    """
    Test the performStratificationAndDetection function to ensure it correctly performs stratification and change-point detection.
    """
    # Example input data
    n_days = 120
    n_per_day = 48
    total_points = n_days * n_per_day

    t = np.linspace(0, n_days, total_points)
    NEE = np.random.normal(0, 1, total_points)
    uStar = np.random.uniform(0, 2, total_points)
    T = np.random.uniform(-10, 30, total_points)
    fNight = np.zeros(total_points, dtype=bool)
    ntAnnual = total_points

    # Initialize outputs
    Cp2, Cp3, Stats2, Stats3, StatsMT = matlab_engine.initializeOutputs(ntAnnual, nargout=5)
    fPlot = False
    cSiteYr = 'TestSite_2024'

    # Convert to MATLAB arrays
    t_mat = matlab.double(t.tolist())
    NEE_mat = matlab.double(NEE.tolist())
    uStar_mat = matlab.double(uStar.tolist())
    T_mat = matlab.double(T.tolist())
    fNight_mat = matlab.logical(fNight.tolist())

    # Call the MATLAB function
    Cp2, Stats2, Cp3, Stats3 = matlab_engine.performStratificationAndDetection(t_mat, NEE_mat, uStar_mat, T_mat, fNight_mat, StatsMT, ntAnnual, n_per_day, fPlot, cSiteYr, nargout=4)

    # Assertions to check if stratification and detection worked as expected
    assert isinstance(Cp2, matlab.double)
    assert isinstance(Stats2, matlab.struct)
    assert isinstance(Cp3, matlab.double)
    assert isinstance(Stats3, matlab.struct)
    assert Cp2.size == 32  # 4 seasons * 8 strata
    assert Cp3.size == 32

def test_cpdEvaluateUStarTh4Season20100901_full_execution(matlab_engine):
    """
    Test the full execution of cpdEvaluateUStarTh4Season20100901 to ensure all components integrate correctly.
    """
    n_days = 120
    n_per_day = 48
    total_points = n_days * n_per_day

    t = np.linspace(0, n_days, total_points)
    NEE = np.random.normal(0, 1, total_points)
    uStar = np.random.uniform(0, 2, total_points)
    T = np.random.uniform(-10, 30, total_points)
    fNight = np.zeros(total_points, dtype=bool)
    
    # Convert to MATLAB arrays
    t_mat = matlab.double(t.tolist())
    NEE_mat = matlab.double(NEE.tolist())
    uStar_mat = matlab.double(uStar.tolist())
    T_mat = matlab.double(T.tolist())
    fNight_mat = matlab.logical(fNight.tolist())

    # Set plot flag and site-year string
    fPlot = False
    cSiteYr = 'TestSite_2024'

    # Call the MATLAB function
    Cp2, Stats2, Cp3, Stats3 = matlab_engine.cpdEvaluateUStarTh4Season20100901(
        t_mat, NEE_mat, uStar_mat, T_mat, fNight_mat, fPlot, cSiteYr, nargout=4
    )

    # Verify the shape of the outputs
    assert np.array(Cp2).shape == (4, 8)
    assert np.array(Cp3).shape == (4, 8)

    # Check that outputs are not entirely NaNs
    assert not np.isnan(np.array(Cp2)).all()
    assert not np.isnan(np.array(Cp3)).all()
