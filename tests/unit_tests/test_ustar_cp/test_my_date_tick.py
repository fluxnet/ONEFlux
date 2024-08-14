# test_my_date_tick.py
import pytest

def test_myDateTick_daily(matlab_engine):
    t = matlab_engine.datenum(2023, 1, 1) + list(range(10))  # Example data
    sFrequency = 'Dy'
    iDateStr = 0
    fLimits = 1
    nBins, mx, my = matlab_engine.myDateTick(t, sFrequency, iDateStr, fLimits, nargout=3)
    assert len(nBins) > 0, "Test failed: nBins is empty."
    assert len(mx) == len(t), "Test failed: mx size mismatch."
    assert len(my) == len(t), "Test failed: my size mismatch."

def test_myDateTick_monthly(matlab_engine):
    t = matlab_engine.datenum(2023, 1, 1) + list(range(12))  # Example data
    sFrequency = 'Mo'
    iDateStr = 0
    fLimits = 0
    nBins, mx, my = matlab_engine.myDateTick(t, sFrequency, iDateStr, fLimits, nargout=3)
    assert len(nBins) > 0, "Test failed: nBins is empty."
    assert len(mx) == len(t), "Test failed: mx size mismatch."
    assert len(my) == len(t), "Test failed: my size mismatch."

def test_myDateTick_invalid_frequency(matlab_engine):
    t = matlab_engine.datenum(2023, 1, 1) + list(range(10))  # Example data
    sFrequency = 'Invalid'
    iDateStr = 0
    fLimits = 1
    try:
        matlab_engine.myDateTick(t, sFrequency, iDateStr, fLimits, nargout=3)
        pytest.fail("Test failed: No error raised for invalid frequency.")
    except matlab.engine.MatlabExecutionError:
        pass  # Expected error

def test_myDateTick_custom_binning(matlab_engine):
    t = matlab_engine.datenum(2023, 1, 1) + list(range(30))  # Example data
    sFrequency = '15Dy'
    iDateStr = 0
    fLimits = 0
    nBins, mx, my = matlab_engine.myDateTick(t, sFrequency, iDateStr, fLimits, nargout=3)
    assert len(nBins) > 0, "Test failed: nBins is empty."
    assert len(mx) == len(t), "Test failed: mx size mismatch."
    assert len(my) == len(t), "Test failed: my size mismatch."

def test_myDateTick_date_ticks(matlab_engine):
    t = matlab_engine.datenum(2023, 1, 1) + list(range(365))  # Example data for a year
    sFrequency = 'Mo'
    iDateStr = 0
    fLimits = 1
    matlab_engine.myDateTick(t, sFrequency, iDateStr, fLimits)  # Call to set the ticks
    xTicks = matlab_engine.get(gca, 'xTick')
    expectedTicks = matlab_engine.datenum(2023, 1, 1) + list(range(0, 365, 30))  # Every month
    for tick in xTicks:
        assert tick in expectedTicks, f"Test failed: xTick value {tick} not in expectedTicks."
