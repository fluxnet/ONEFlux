# test_mydatevec.py

import pytest
import matlab.engine

def test_mydatevec_basic(engine):
    # Test case for basic date conversion
    t = engine.datenum([2024, 1, 1, 0, 0, 0]) + list(range(0, 5))
    y, m, d, h, mn, s = engine.mydatevec(t)

    assert y.tolist() == [2024, 2024, 2024, 2024, 2024], "Years are not correct"
    assert m.tolist() == [1, 1, 1, 1, 1], "Months are not correct"
    assert d.tolist() == [1, 2, 3, 4, 5], "Days are not correct"
    assert h.tolist() == [0, 0, 0, 0, 0], "Hours are not correct"
    assert mn.tolist() == [0, 0, 0, 0, 0], "Minutes are not correct"
    assert s.tolist() == [0, 0, 0, 0, 0], "Seconds are not correct"

def test_mydatevec_with_midnight(engine):
    # Test case for handling midnight correctly
    t = engine.datenum([2024, 1, 1, 0, 0, 0])  # Exactly midnight
    y, m, d, h, mn, s = engine.mydatevec(t)

    assert y.tolist() == [2023], "Year is not correct for midnight case"
    assert m.tolist() == [12], "Month is not correct for midnight case"
    assert d.tolist() == [31], "Day is not correct for midnight case"
    assert h.tolist() == [24], "Hour is not correct for midnight case"
    assert mn.tolist() == [0], "Minute is not correct for midnight case"
    assert s.tolist() == [0], "Second is not correct for midnight case"

def test_mydatevec_nan_handling(engine):
    # Test case for handling NaN values
    t = matlab.double([engine.datenum([2024, 1, 1, 0, 0, 0]), float('nan'), engine.datenum([2024, 1, 2, 0, 0, 0])])
    y, m, d, h, mn, s = engine.mydatevec(t)

    assert y.tolist() == [2024, float('nan'), 2024], "Years are not correct with NaNs"
    assert m.tolist() == [1, float('nan'), 1], "Months are not correct with NaNs"
    assert d.tolist() == [1, float('nan'), 2], "Days are not correct with NaNs"
    assert h.tolist() == [0, float('nan'), 0], "Hours are not correct with NaNs"
    assert mn.tolist() == [0, float('nan'), 0], "Minutes are not correct with NaNs"
    assert s.tolist() == [0, float('nan'), 0], "Seconds are not correct with NaNs"

def test_mydatevec_edge_case(engine):
    # Test case for edge cases
    t = engine.datenum([2024, 2, 29, 0, 0, 0])  # Leap year day
    y, m, d, h, mn, s = engine.mydatevec(t)

    assert y.tolist() == [2024], "Year is not correct for leap day"
    assert m.tolist() == [2], "Month is not correct for leap day"
    assert d.tolist() == [29], "Day is not correct for leap day"
    assert h.tolist() == [0], "Hour is not correct for leap day"
    assert mn.tolist() == [0], "Minute is not correct for leap day"
    assert s.tolist() == [0], "Second is not correct for leap day"

