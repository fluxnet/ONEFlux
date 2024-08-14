# test_cpdBin.py

import pytest
import matlab.engine

@pytest.fixture(scope="module")
def matlab_engine():
    eng = matlab.engine.start_matlab()
    matlab_function_path = os.path.abspath('matlab_functions')
    eng.addpath(matlab_function_path, nargout=0)
    yield eng
    eng.quit()

def test_cpdBin_with_dx_empty(matlab_engine):
    x = matlab.double([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    y = matlab.double([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
    dx = matlab.double([])
    nPerBin = 2

    nBins, mx, my = matlab_engine.cpdBin(x, y, dx, nPerBin, nargout=3)

    assert nBins == 5, "The number of bins should be 5 when nPerBin is 2 for 10 elements."
    assert mx == pytest.approx([1.5, 3.5, 5.5, 7.5, 9.5]), "The mean x values in each bin are incorrect."
    assert my == pytest.approx([9.5, 7.5, 5.5, 3.5, 1.5]), "The mean y values in each bin are incorrect."

def test_cpdBin_with_dx_scalar(matlab_engine):
    x = matlab.double([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    y = matlab.double([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
    dx = 2
    nPerBin = 1

    nBins, mx, my = matlab_engine.cpdBin(x, y, dx, nPerBin, nargout=3)

    assert nBins == 5, "The number of bins should be 5 when dx is 2 for x ranging from 1 to 10."
    assert mx == pytest.approx([1.5, 3.5, 5.5, 7.5, 9.5]), "The mean x values in each bin are incorrect."
    assert my == pytest.approx([9.5, 7.5, 5.5, 3.5, 1.5]), "The mean y values in each bin are incorrect."

def test_cpdBin_with_dx_vector(matlab_engine):
    x = matlab.double([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    y = matlab.double([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
    dx = matlab.double([1, 4, 7, 10])
    nPerBin = 1

    nBins, mx, my = matlab_engine.cpdBin(x, y, dx, nPerBin, nargout=3)

    assert nBins == 3, "The number of bins should be 3 when dx has 4 elements (3 bins)."
    assert mx == pytest.approx([2, 5, 8]), "The mean x values in each bin are incorrect."
    assert my == pytest.approx([8, 5, 2]), "The mean y values in each bin are incorrect."

def test_cpdBin_with_dx_negative(matlab_engine):
    x = matlab.double([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    y = matlab.double([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
    dx = -2
    nPerBin = 1

    nBins, mx, my = matlab_engine.cpdBin(x, y, dx, nPerBin, nargout=3)

    assert nBins == 0, "No bins should be created when dx is negative."
    assert mx == [], "No mean x values should be calculated when dx is negative."
    assert my == [], "No mean y values should be calculated when dx is negative."

def test_cpdBin_with_nan_values(matlab_engine):
    x = matlab.double([1, 2, 3, float('nan'), 5, 6, 7, float('nan'), 9, 10])
    y = matlab.double([10, 9, 8, 7, 6, float('nan'), 4, 3, 2, 1])
    dx = matlab.double([])
    nPerBin = 2

    nBins, mx, my = matlab_engine.cpdBin(x, y, dx, nPerBin, nargout=3)

    assert nBins == 4, "The number of bins should be 4 when nPerBin is 2, ignoring NaN values."
    assert mx == pytest.approx([1.5, 5.5, 7, 9.5]), "The mean x values in each bin are incorrect."
    assert my == pytest.approx([9.5, 6, 4, 1.5]), "The mean y values in each bin are incorrect."
