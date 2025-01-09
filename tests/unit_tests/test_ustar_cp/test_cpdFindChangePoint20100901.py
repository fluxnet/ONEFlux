import pytest
import numpy as np
import matlab

@pytest.fixture
def test_data():
    # Generate synthetic data with change points
    xx = np.linspace(0, 10, 101)
    yy = np.piecewise(xx, [xx < 3, (xx >= 3) & (xx < 7), xx >= 7],
                      [lambda x: 2 * x + 1, lambda x: -x + 10, lambda x: 0.5 * x - 0.5])
    return xx, yy

def test_cpdFindChangePoint20100901(test_engine, test_data):
    # Define test inputs
    xx, yy = test_data
    fPlot = 0
    cPlot = 'Test Plot'

    # Call the MATLAB function
    Cp2, s2, Cp3, s3 = test_engine.cpdFindChangePoint20100901(xx, yy, fPlot, cPlot, nargout=4)

    # Perform assertions
    assert isinstance(Cp2, float)
    assert isinstance(Cp3, float)
    assert isinstance(s2, dict)
    assert isinstance(s3, dict)

    # Check the structure of s2 and s3
    for s in [s2, s3]:
        assert isinstance(s['n'], float)
        assert isinstance(s['Cp'], float)
        assert isinstance(s['Fmax'], float)
        assert isinstance(s['p'], float)
        assert isinstance(s['b0'], float)
        assert isinstance(s['b1'], float)
        assert isinstance(s['b2'], float)
        assert isinstance(s['c2'], float)
        assert isinstance(s['cib0'], float)
        assert isinstance(s['cib1'], float)
        assert isinstance(s['cic2'], float)

    # Additional checks can be added based on expected output
    assert s2['n'] == len(xx)
    assert s3['n'] == len(xx)
    assert Cp2 == 1.8
    assert Cp3 == 2.6

def test_cpdFindChangePoint_no_change(test_engine):
    # Data with no change point
    xx = np.linspace(0, 10, 101)
    yy = 2 * xx + 1
    fPlot = 0
    cPlot = 'No Change Point'

    # Call the MATLAB function
    Cp2, s2, Cp3, s3 = test_engine.cpdFindChangePoint20100901(
        matlab.double(xx.tolist()), matlab.double(yy.tolist()), fPlot, cPlot, nargout=4)

    # Assertions
    assert np.isnan(Cp2), "Cp2 should be NaN when there's no change point"
    assert np.isnan(Cp3), "Cp3 should be NaN when there's no change point"

def test_cpdFindChangePoint_change_at_start(test_engine):
    # Data with a change point at the start
    xx = np.linspace(0, 10, 101)
    yy = np.piecewise(xx, [xx < 0.1, xx >= 0.1], [lambda x: 5 * x, lambda x: 2 * x + 1])
    fPlot = 0
    cPlot = 'Change Point at Start'

    # Call the MATLAB function
    Cp2, s2, Cp3, s3 = test_engine.cpdFindChangePoint20100901(
        matlab.double(xx.tolist()), matlab.double(yy.tolist()), fPlot, cPlot, nargout=4)

    # Assertions
    assert Cp2 <= xx[2], "Cp2 should be near the start"
    assert Cp3 <= xx[2], "Cp3 should be near the start"

def test_cpdFindChangePoint_change_at_end(test_engine):
    # Data with a change point at the end
    xx = np.linspace(0, 10, 101)
    yy = np.piecewise(xx, [xx < 9.9, xx >= 9.9], [lambda x: 2 * x + 1, lambda x: 5 * x])
    fPlot = 0
    cPlot = 'Change Point at End'

    # Call the MATLAB function
    Cp2, s2, Cp3, s3 = test_engine.cpdFindChangePoint20100901(
        matlab.double(xx.tolist()), matlab.double(yy.tolist()), fPlot, cPlot, nargout=4)

    # Assertions
    assert Cp2 >= xx[-3], "Cp2 should be near the end"
    assert Cp3 >= xx[-3], "Cp3 should be near the end"

def test_cpdFindChangePoint_with_noise(test_engine):
    # Data with a change point and added noise
    np.random.seed(0)
    xx = np.linspace(0, 10, 101)
    yy = np.piecewise(xx, [xx < 5, xx >= 5], [lambda x: 2 * x + 1, lambda x: -x + 15])
    noise = np.random.normal(0, 0.5, size=yy.shape)
    yy_noisy = yy + noise
    fPlot = 0
    cPlot = 'Noisy Data'

    # Call the MATLAB function
    Cp2, s2, Cp3, s3 = test_engine.cpdFindChangePoint20100901(
        matlab.double(xx.tolist()), matlab.double(yy_noisy.tolist()), fPlot, cPlot, nargout=4)

    # Assertions
    assert abs(Cp2 - 5) < 1, "Cp2 should be near 5 despite noise"
    assert abs(Cp3 - 5) < 1, "Cp3 should be near 5 despite noise"

def test_cpdFindChangePoint_invalid_input(test_engine):
    # Invalid inputs: empty arrays
    xx = np.array([])
    yy = np.array([])
    fPlot = 0
    cPlot = 'Invalid Input'

    # Call the MATLAB function and expect failure or NaN outputs
    Cp2, s2, Cp3, s3 = test_engine.cpdFindChangePoint20100901(
        matlab.double(xx.tolist()), matlab.double(yy.tolist()), fPlot, cPlot, nargout=4)

    # Assertions
    assert np.isnan(Cp2), "Cp2 should be NaN for empty input"
    assert np.isnan(Cp3), "Cp3 should be NaN for empty input"

def test_cpdFindChangePoint_insufficient_data(test_engine):
    # Insufficient data
    xx = np.array([1])
    yy = np.array([2])
    fPlot = 0
    cPlot = 'Insufficient Data'

    # Call the MATLAB function and expect NaN outputs
    Cp2, s2, Cp3, s3 = test_engine.cpdFindChangePoint20100901(
        matlab.double(xx.tolist()), matlab.double(yy.tolist()), fPlot, cPlot, nargout=4)

    # Assertions
    assert np.isnan(Cp2), "Cp2 should be NaN for insufficient data"
    assert np.isnan(Cp3), "Cp3 should be NaN for insufficient data"