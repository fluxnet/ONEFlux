# test_cpdBin.py

import pytest
import matlab

def test_cpdBin_with_dx_empty(matlab_engine):
    """
    Test cpdBin with dx as an empty array, using nPerBin to bin the data.
    """
    x = matlab.double([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    y = matlab.double([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
    dx = matlab.double([])
    nPerBin = 2

    # Call the MATLAB function
    nBins, mx, my = matlab_engine.cpdBin(x, y, dx, nPerBin, nargout=3)

    # Check that the number of bins is correct
    assert nBins == 5, "The number of bins should be 5 when nPerBin is 2 for 10 elements."

    # Check that the bin means are calculated correctly
    assert mx == [1.5, 3.5, 5.5, 7.5, 9.5], "The mean x values in each bin are incorrect."
    assert my == [9.5, 7.5, 5.5, 3.5, 1.5], "The mean y values in each bin are incorrect."

def test_cpdBin_with_dx_scalar(matlab_engine):
    """
    Test cpdBin with dx as a scalar specifying the binning interval.
    """
    x = matlab.double([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    y = matlab.double([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
    dx = 2
    nPerBin = 1

    # Call the MATLAB function
    nBins, mx, my = matlab_engine.cpdBin(x, y, dx, nPerBin, nargout=3)

    # Check that the number of bins is correct
    assert nBins == 5, "The number of bins should be 5 when dx is 2 for x ranging from 1 to 10."

    # Check that the bin means are calculated correctly
    assert mx == [1.5, 3.5, 5.5, 7.5, 9.5], "The mean x values in each bin are incorrect."
    assert my == [9.5, 7.5, 5.5, 3.5, 1.5], "The mean y values in each bin are incorrect."

def test_cpdBin_with_dx_vector(matlab_engine):
    """
    Test cpdBin with dx as a vector specifying the binning borders.
    """
    x = matlab.double([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    y = matlab.double([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
    dx = matlab.double([1, 4, 7, 10])
    nPerBin = 1

    # Call the MATLAB function
    nBins, mx, my = matlab_engine.cpdBin(x, y, dx, nPerBin, nargout=3)

    # Check that the number of bins is correct
    assert nBins == 3, "The number of bins should be 3 when dx has 4 elements (3 bins)."

    # Check that the bin means are calculated correctly
    assert mx == [2, 5, 8], "The mean x values in each bin are incorrect."
    assert my == [8, 5, 2], "The mean y values in each bin are incorrect."

def test_cpdBin_with_dx_negative(matlab_engine):
    """
    Test cpdBin with a negative dx value, which should abort the function.
    """
    x = matlab.double([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    y = matlab.double([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
    dx = -2
    nPerBin = 1

    # Call the MATLAB function
    nBins, mx, my = matlab_engine.cpdBin(x, y, dx, nPerBin, nargout=3)

    # Check that the function aborted with no bins created
    assert nBins == 0, "No bins should be created when dx is negative."
    assert mx == [], "No mean x values should be calculated when dx is negative."
    assert my == [], "No mean y values should be calculated when dx is negative."

def test_cpdBin_with_nan_values(matlab_engine):
    """
    Test cpdBin with NaN values in the input vectors.
    """
    x = matlab.double([1, 2, 3, float('nan'), 5, 6, 7, float('nan'), 9, 10])
    y = matlab.double([10, 9, 8, 7, 6, float('nan'), 4, 3, 2, 1])
    dx = matlab.double([])
    nPerBin = 2

    # Call the MATLAB function
    nBins, mx, my = matlab_engine.cpdBin(x, y, dx, nPerBin, nargout=3)

    # Check that the number of bins is correct
    assert nBins == 4, "The number of bins should be 4 when nPerBin is 2, ignoring NaN values."

    # Check that the bin means are calculated correctly
    assert mx == [1.5, 5.5, 7, 9.5], "The mean x values in each bin are incorrect."
    assert my == [9.5, 6, 4, 1.5], "The mean y values in each bin are incorrect."
