# test_cpdEvaluateUStarTh4Season20100901.py

import pytest
import numpy as np
import matlab
import math

def test_cpdEvaluateUStarTh4Season20100901_small_data(matlab_engine):
    """
    Test the function with a dataset smaller than the required threshold.
    The function should return outputs filled with NaNs.
    """
    # Generate a small dataset
    n_days = 10  # Less than the required number of days
    n_per_day = 48
    total_points = n_days * n_per_day

    # Time vector
    t = np.linspace(0, n_days, total_points)

    # Generate random data for NEE, uStar, and T
    np.random.seed(0)
    NEE = np.random.normal(0, 1, total_points)
    uStar = np.random.uniform(0, 2, total_points)
    T = np.random.uniform(-10, 30, total_points)

    # Generate fNight logical array (assuming night from 18:00 to 6:00)
    fNight = np.zeros(total_points, dtype=bool)
    for day in range(n_days):
        night_start = day * n_per_day + 36  # 18:00
        night_end = day * n_per_day + 48 + 12  # Next day 6:00
        fNight[night_start:night_end % total_points] = True

    # Set plotting flag and site-year string
    fPlot = False
    cSiteYr = 'TestSite_2024'

    # Convert numpy arrays to MATLAB arrays
    t_mat = matlab.double(t.tolist())
    NEE_mat = matlab.double(NEE.tolist())
    uStar_mat = matlab.double(uStar.tolist())
    T_mat = matlab.double(T.tolist())
    fNight_mat = matlab.logical(fNight.tolist())

    # Call the MATLAB function
    Cp2, Stats2, Cp3, Stats3 = matlab_engine.cpdEvaluateUStarTh4Season20100901(
        t_mat, NEE_mat, uStar_mat, T_mat, fNight_mat, fPlot, cSiteYr, nargout=4
    )

    # Verify that outputs are filled with NaNs due to insufficient data
    assert all(math.isnan(c) for c in Cp2[:])
    assert all(math.isnan(c) for c in Cp3[:])

def test_cpdEvaluateUStarTh4Season20100901_adequate_data(matlab_engine):
    """
    Test the function with an adequately sized dataset.
    The function should process the data and return valid outputs.
    """
    # Generate an adequate dataset
    n_days = 120  # Sufficient number of days
    n_per_day = 48
    total_points = n_days * n_per_day

    # Time vector
    t = np.linspace(0, n_days, total_points)

    # Generate random data for NEE, uStar, and T
    np.random.seed(1)
    NEE = np.random.normal(0, 1, total_points)
    uStar = np.random.uniform(0, 2, total_points)
    T = np.random.uniform(-10, 30, total_points)

    # Generate fNight logical array
    fNight = np.zeros(total_points, dtype=bool)
    for day in range(n_days):
        night_start = day * n_per_day + 36
        night_end = day * n_per_day + 48 + 12
        fNight[night_start:night_end % total_points] = True

    # Set plotting flag and site-year string
    fPlot = False
    cSiteYr = 'TestSite_2024'

    # Convert numpy arrays to MATLAB arrays
    t_mat = matlab.double(t.tolist())
    NEE_mat = matlab.double(NEE.tolist())
    uStar_mat = matlab.double(uStar.tolist())
    T_mat = matlab.double(T.tolist())
    fNight_mat = matlab.logical(fNight.tolist())

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

def test_cpdEvaluateUStarTh4Season20100901_with_NaNs(matlab_engine):
    """
    Test the function with datasets containing NaN values.
    The function should handle NaNs appropriately.
    """
    # Generate an adequate dataset
    n_days = 120
    n_per_day = 48
    total_points = n_days * n_per_day

    # Time vector
    t = np.linspace(0, n_days, total_points)

    # Generate random data for NEE, uStar, and T with NaNs
    np.random.seed(2)
    NEE = np.random.normal(0, 1, total_points)
    uStar = np.random.uniform(0, 2, total_points)
    T = np.random.uniform(-10, 30, total_points)

    # Introduce NaNs randomly
    nan_indices = np.random.choice(total_points, size=int(0.1 * total_points), replace=False)
    NEE[nan_indices] = np.nan
    uStar[nan_indices] = np.nan
    T[nan_indices] = np.nan

    # Generate fNight logical array
    fNight = np.zeros(total_points, dtype=bool)
    for day in range(n_days):
        night_start = day * n_per_day + 36
        night_end = day * n_per_day + 48 + 12
        fNight[night_start:night_end % total_points] = True

    # Set plotting flag and site-year string
    fPlot = False
    cSiteYr = 'TestSite_2024'

    # Convert numpy arrays to MATLAB arrays
    t_mat = matlab.double(t.tolist())
    NEE_mat = matlab.double(NEE.tolist())
    uStar_mat = matlab.double(uStar.tolist())
    T_mat = matlab.double(T.tolist())
    fNight_mat = matlab.logical(fNight.tolist())

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

def test_cpdEvaluateUStarTh4Season20100901_day_vs_night(matlab_engine):
    """
    Test the function with a dataset where fNight is all 0 (day) or all 1 (night).
    """
    # Generate an adequate dataset
    n_days = 120
    n_per_day = 48
    total_points = n_days * n_per_day

    # Time vector
    t = np.linspace(0, n_days, total_points)

    # Generate random data for NEE, uStar, and T
    np.random.seed(3)
    NEE = np.random.normal(0, 1, total_points)
    uStar = np.random.uniform(0, 2, total_points)
    T = np.random.uniform(-10, 30, total_points)

    # Test all day (fNight = 0)
    fNight_day = np.zeros(total_points, dtype=bool)

    # Test all night (fNight = 1)
    fNight_night = np.ones(total_points, dtype=bool)

    # Set plotting flag and site-year string
    fPlot = False
    cSiteYr = 'TestSite_2024'

    # Convert numpy arrays to MATLAB arrays
    t_mat = matlab.double(t.tolist())
    NEE_mat = matlab.double(NEE.tolist())
    uStar_mat = matlab.double(uStar.tolist())
    T_mat = matlab.double(T.tolist())

    # Day test
    fNight_mat_day = matlab.logical(fNight_day.tolist())
    Cp2_day, Stats2_day, Cp3_day, Stats3_day = matlab_engine.cpdEvaluateUStarTh4Season20100901(
        t_mat, NEE_mat, uStar_mat, T_mat, fNight_mat_day, fPlot, cSiteYr, nargout=4
    )
    assert np.array(Cp2_day).shape == (4, 8)
    assert np.array(Cp3_day).shape == (4, 8)
    assert not np.isnan(np.array(Cp2_day)).all()
    assert not np.isnan(np.array(Cp3_day)).all()

    # Night test
    fNight_mat_night = matlab.logical(fNight_night.tolist())
    Cp2_night, Stats2_night, Cp3_night, Stats3_night = matlab_engine.cpdEvaluateUStarTh4Season20100901(
        t_mat, NEE_mat, uStar_mat, T_mat, fNight_mat_night, fPlot, cSiteYr, nargout=4
    )
    assert np.array(Cp2_night).shape == (4, 8)
    assert np.array(Cp3_night).shape == (4, 8)
    assert not np.isnan(np.array(Cp2_night)).all()
    assert not np.isnan(np.array(Cp3_night)).all()

def test_cpdEvaluateUStarTh4Season20100901_inconsistent_input_lengths(matlab_engine):
    """
    Test the function with inconsistent lengths of input arrays.
    The function should raise an error.
    """
    # Generate an adequate dataset
    n_days = 120
    n_per_day = 48
    total_points = n_days * n_per_day

    # Time vector
    t = np.linspace(0, n_days, total_points)

    # Generate random data for NEE, uStar, and T
    np.random.seed(4)
    NEE = np.random.normal(0, 1, total_points)
    uStar = np.random.uniform(0, 2, total_points + 10)  # Inconsistent length
    T = np.random.uniform(-10, 30, total_points)

    # Generate fNight logical array
    fNight = np.zeros(total_points, dtype=bool)
    for day in range(n_days):
        night_start = day * n_per_day + 36
        night_end = day * n_per_day + 48 + 12
        fNight[night_start:night_end % total_points] = True

    # Set plotting flag and site-year string
    fPlot = False
    cSiteYr = 'TestSite_2024'

    # Convert numpy arrays to MATLAB arrays
    t_mat = matlab.double(t.tolist())
    NEE_mat = matlab.double(NEE.tolist())
    uStar_mat = matlab.double(uStar.tolist())  # This has a different length
    T_mat = matlab.double(T.tolist())
    fNight_mat = matlab.logical(fNight.tolist())

    # Attempt to call the MATLAB function and expect an error
    with pytest.raises(matlab.engine.MatlabExecutionError):
        Cp2, Stats2, Cp3, Stats3 = matlab_engine.cpdEvaluateUStarTh4Season20100901(
            t_mat, NEE_mat, uStar_mat, T_mat, fNight_mat, fPlot, cSiteYr, nargout=4
        )
