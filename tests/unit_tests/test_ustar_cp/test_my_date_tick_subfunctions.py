# test_my_date_tick_subfunctions.py

import pytest
import matlab.engine

# Assuming that confest.py sets up MATLAB engine
@pytest.fixture(scope="module")
def engine():
    eng = matlab.engine.start_matlab()
    yield eng
    eng.quit()

def test_get_ticks_for_frequency(engine):
    t = engine.datenum([2024, 1, 1, 0, 0, 0]) + list(range(0, 365, 1))  # Example data

    # Test daily frequency
    ticks_daily = engine.get_ticks_for_frequency(t, 'Dy')
    assert len(ticks_daily) > 0
    assert ticks_daily[1] - ticks_daily[0] == 1, "Daily ticks are not correct"

    # Test monthly frequency
    ticks_monthly = engine.get_ticks_for_frequency(t, 'Mo')
    assert len(ticks_monthly) > 0
    assert ticks_monthly[1] - ticks_monthly[0] > 28 and ticks_monthly[1] - ticks_monthly[0] < 32, "Monthly ticks are not correct"

    # Test custom interval (e.g., 10 days)
    ticks_custom = engine.get_ticks_for_frequency(t, '10Dy')
    assert len(ticks_custom) > 0
    assert ticks_custom[1] - ticks_custom[0] == 10, "Custom interval ticks are not correct"

def test_format_dates(engine):
    ticks = [engine.datenum([2024, 1, 1, 0, 0, 0]) + i for i in range(0, 365, 30)]
    formatted_ticks = engine.format_dates(ticks, '%Y-%m-%d')

    assert len(formatted_ticks) == len(ticks)
    assert formatted_ticks[0] == '2024-01-01'
    assert formatted_ticks[-1] == '2024-12-01'

def test_myDateTick_daily(engine):
    t = engine.datenum([2024, 1, 1, 0, 0, 0]) + list(range(0, 365, 1))
    sFrequency = 'Dy'
    iDateStr = 0
    fLimits = 1

    engine.myDateTick(t, sFrequency, iDateStr, fLimits, nargout=0)

    x_ticks = engine.get(gca(), 'xTick')
    assert len(x_ticks) > 0, "xTicks should not be empty"
    assert len(x_ticks) == len(t), "Number of xTicks does not match expected daily intervals"

def test_myDateTick_monthly(engine):
    t = engine.datenum([2024, 1, 1, 0, 0, 0]) + list(range(0, 365, 30))
    sFrequency = 'Mo'
    iDateStr = 0
    fLimits = 1

    engine.myDateTick(t, sFrequency, iDateStr, fLimits, nargout=0)

    x_ticks = engine.get(gca(), 'xTick')
    assert len(x_ticks) > 0, "xTicks should not be empty"
    expected_ticks = [engine.datenum([2024, 1, 1, 0, 0, 0]) + i for i in range(0, 365, 30)]
    assert sorted(x_ticks) == sorted(expected_ticks), "xTicks do not match expected monthly intervals"

def test_myDateTick_invalid_frequency(engine):
    t = engine.datenum([2024, 1, 1, 0, 0, 0]) + list(range(0, 365, 1))
    sFrequency = 'Invalid'
    iDateStr = 0
    fLimits = 1

    try:
        engine.myDateTick(t, sFrequency, iDateStr, fLimits, nargout=0)
        x_ticks = engine.get(gca(), 'xTick')
        assert len(x_ticks) == 0, "xTicks should be empty for invalid frequency"
    except Exception as e:
        pytest.fail(f"Function raised an exception for invalid frequency: {e}")

def test_myDateTick_date_labels(engine):
    t = engine.datenum([2024, 1, 1, 0, 0, 0]) + list(range(0, 365, 30))
    sFrequency = 'Mo'
    iDateStr = 1  # Use a specific date format
    fLimits = 1

    engine.myDateTick(t, sFrequency, iDateStr, fLimits, nargout=0)

    x_ticks_labels = engine.get(gca(), 'xTickLabel')
    assert len(x_ticks_labels) > 0, "xTickLabels should not be empty"
    assert len(x_ticks_labels) == len(t[::30]), "Number of xTickLabels does not match expected"
