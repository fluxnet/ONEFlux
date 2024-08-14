# test_cpdFindChangePoint20100901.py

import pytest
import numpy as np
import matlab

def test_cpdFindChangePoint_with_valid_data(matlab_engine):
    """
    Test cpdFindChangePoint20100901 with a dataset that should produce valid change points.
    """
    # Generate example data
    np.random.seed(0)
    n_points = 100
    xx = np.linspace(0, 10, n_points)
    yy = np.piecewise(xx, [xx < 5, xx >= 5], [lambda x: x, lambda x: 5 + 0.5 * (x - 5)])
    yy += np.random.normal(0, 0.5, n_points)  # Add some noise

    # Convert to MATLAB arrays
    xx_mat = matlab.double(xx.tolist())
    yy_mat = matlab.double(yy.tolist())

    # Call the MATLAB function
    Cp2, s2, Cp3, s3 = matlab_engine.cpdFindChangePoint20100901(xx_mat, yy_mat, False, '', nargout=4)

    # Check the results
    assert not np.isnan(Cp2), "Cp2 should not be NaN"
    assert not np.isnan(Cp3), "Cp3 should not be NaN"
    assert isinstance(s2, dict), "s2 should be a struct (dictionary in Python)"
    assert isinstance(s3, dict), "s3 should be a struct (dictionary in Python)"
    assert s2['n'] == n_points, "s2.n should equal the number of valid data points"
    assert s3['n'] == n_points, "s3.n should equal the number of valid data points"

def test_cpdFindChangePoint_with_nan_data(matlab_engine):
    """
    Test cpdFindChangePoint20100901 with data containing NaN values.
    The function should handle missing data appropriately.
    """
    # Generate example data with NaNs
    np.random.seed(1)
    n_points = 100
    xx = np.linspace(0, 10, n_points)
    yy = np.piecewise(xx, [xx < 5, xx >= 5], [lambda x: x, lambda x: 5 + 0.5 * (x - 5)])
    yy += np.random.normal(0, 0.5, n_points)  # Add some noise
    yy[::10] = np.nan  # Introduce NaN values

    # Convert to MATLAB arrays
    xx_mat = matlab.double(xx.tolist())
    yy_mat = matlab.double(yy.tolist())

    # Call the MATLAB function
    Cp2, s2, Cp3, s3 = matlab_engine.cpdFindChangePoint20100901(xx_mat, yy_mat, False, '', nargout=4)

    # Check that the function handled NaNs appropriately
    assert not np.isnan(Cp2), "Cp2 should not be NaN even with NaNs in input"
    assert not np.isnan(Cp3), "Cp3 should not be NaN even with NaNs in input"
    assert isinstance(s2, dict), "s2 should be a struct (dictionary in Python)"
    assert isinstance(s3, dict), "s3 should be a struct (dictionary in Python)"
    assert s2['n'] == n_points - 10, "s2.n should account for the removal of NaN data points"
    assert s3['n'] == n_points - 10, "s3.n should account for the removal of NaN data points"

def test_cpdFindChangePoint_with_insufficient_data(matlab_engine):
    """
    Test cpdFindChangePoint20100901 with insufficient data points.
    The function should return NaNs and an empty struct.
    """
    # Generate insufficient data
    xx = [1, 2, 3]
    yy = [1, 2, 3]

    # Convert to MATLAB arrays
    xx_mat = matlab.double(xx)
    yy_mat = matlab.double(yy)

    # Call the MATLAB function
    Cp2, s2, Cp3, s3 = matlab_engine.cpdFindChangePoint20100901(xx_mat, yy_mat, False, '', nargout=4)

    # Check that the function returned NaNs due to insufficient data
    assert np.isnan(Cp2), "Cp2 should be NaN with insufficient data"
    assert np.isnan(Cp3), "Cp3 should be NaN with insufficient data"
    assert s2['n'] == 3, "s2.n should be 3 even with insufficient data"
    assert s3['n'] == 3, "s3.n should be 3 even with insufficient data"

def test_cpdFindChangePoint_with_extreme_outliers(matlab_engine):
    """
    Test cpdFindChangePoint20100901 with data containing extreme outliers.
    The function should handle outliers correctly.
    """
    # Generate data with extreme outliers
    np.random.seed(2)
    n_points = 100
    xx = np.linspace(0, 10, n_points)
    yy = np.piecewise(xx, [xx < 5, xx >= 5], [lambda x: x, lambda x: 5 + 0.5 * (x - 5)])
    yy += np.random.normal(0, 0.5, n_points)  # Add some noise
    yy[95:] += 10  # Add extreme outliers

    # Convert to MATLAB arrays
    xx_mat = matlab.double(xx.tolist())
    yy_mat = matlab.double(yy.tolist())

    # Call the MATLAB function
    Cp2, s2, Cp3, s3 = matlab_engine.cpdFindChangePoint20100901(xx_mat, yy_mat, False, '', nargout=4)

    # Check that the function handled outliers correctly
    assert not np.isnan(Cp2), "Cp2 should not be NaN even with outliers"
    assert not np.isnan(Cp3), "Cp3 should not be NaN even with outliers"
    assert isinstance(s2, dict), "s2 should be a struct (dictionary in Python)"
    assert isinstance(s3, dict), "s3 should be a struct (dictionary in Python)"
    assert s2['n'] == n_points, "s2.n should equal the number of valid data points after outlier removal"
    assert s3['n'] == n_points, "s3.n should equal the number of valid data points after outlier removal"

def test_cpdFindChangePoint_plotting(matlab_engine):
    """
    Test the plotting functionality of cpdFindChangePoint20100901.
    """
    # Generate example data
    np.random.seed(3)
    n_points = 100
    xx = np.linspace(0, 10, n_points)
    yy = np.piecewise(xx, [xx < 5, xx >= 5], [lambda x: x, lambda x: 5 + 0.5 * (x - 5)])
    yy += np.random.normal(0, 0.5, n_points)  # Add some noise

    # Convert to MATLAB arrays
    xx_mat = matlab.double(xx.tolist())
    yy_mat = matlab.double(yy.tolist())

    # Call the MATLAB function with plotting enabled
    Cp2, s2, Cp3, s3 = matlab_engine.cpdFindChangePoint20100901(xx_mat, yy_mat, True, 'Test Plot', nargout=4)

    # Check that the function ran without errors
    assert not np.isnan(Cp2), "Cp2 should not be NaN"
    assert not np.isnan(Cp3), "Cp3 should not be NaN"
    # We cannot directly test the plot, but the absence of an error is a good sign

