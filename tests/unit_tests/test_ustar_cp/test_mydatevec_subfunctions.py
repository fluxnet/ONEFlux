import pytest
import numpy as np
import matlab.engine

def test_initialize_vectors(matlab_engine):
    eng = matlab_engine
    # Define MATLAB function to be tested
    initialize_vectors = eng.eval(
        "function [y, m, d, h, mn, s] = initializeVectors(sizeVec)\n"
        "    y = NaN * ones(sizeVec);\n"
        "    m = y; d = y; h = y; mn = y; s = y;\n"
        "end", nargout=0)
    
    # Call the MATLAB function with test input
    sizeVec = [3, 1]
    y, m, d, h, mn, s = eng.initializeVectors(matlab.double(sizeVec))
    
    # Convert MATLAB arrays to numpy arrays for comparison
    y = np.array(y).flatten()
    m = np.array(m).flatten()
    d = np.array(d).flatten()
    h = np.array(h).flatten()
    mn = np.array(mn).flatten()
    s = np.array(s).flatten()
    
    np.testing.assert_array_equal(y, [np.nan] * 3)
    np.testing.assert_array_equal(m, [np.nan] * 3)
    np.testing.assert_array_equal(d, [np.nan] * 3)
    np.testing.assert_array_equal(h, [np.nan] * 3)
    np.testing.assert_array_equal(mn, [np.nan] * 3)
    np.testing.assert_array_equal(s, [np.nan] * 3)

def test_convert_to_date_vec(matlab_engine):
    eng = matlab_engine
    # Define MATLAB function to be tested
    convert_to_date_vec = eng.eval(
        "function [yy, mm, dd, hh, mmn, ss] = convertToDateVec(t)\n"
        "    [yy, mm, dd, hh, mmn, ss] = datevec(t);\n"
        "end", nargout=0)
    
    # Call the MATLAB function with a test input
    t = matlab.double([datenum(2024, 1, 1, 12, 30, 15)])
    yy, mm, dd, hh, mmn, ss = eng.convertToDateVec(t)
    
    assert yy[0] == 2024
    assert mm[0] == 1
    assert dd[0] == 1
    assert hh[0] == 12
    assert mmn[0] == 30
    assert ss[0] == 15

def test_populate_date_components(matlab_engine):
    eng = matlab_engine
    # Define MATLAB function to be tested
    populate_date_components = eng.eval(
        "function [y, m, d, h, mn, s] = populateDateComponents(iYaN, yy, mm, dd, hh, mmn, ss, y, m, d, h, mn, s)\n"
        "    y(iYaN) = yy;\n"
        "    m(iYaN) = mm;\n"
        "    d(iYaN) = dd;\n"
        "    h(iYaN) = hh;\n"
        "    mn(iYaN) = mmn;\n"
        "    s(iYaN) = ss;\n"
        "end", nargout=0)
    
    # Call the MATLAB function with test inputs
    iYaN = matlab.double([1, 3])
    yy = matlab.double([2024, 2024])
    mm = matlab.double([1, 1])
    dd = matlab.double([1, 2])
    hh = matlab.double([0, 0])
    mmn = matlab.double([0, 0])
    ss = matlab.double([0, 0])
    y = matlab.double([np.nan, np.nan, np.nan])
    m = matlab.double([np.nan, np.nan, np.nan])
    d = matlab.double([np.nan, np.nan, np.nan])
    h = matlab.double([np.nan, np.nan, np.nan])
    mn = matlab.double([np.nan, np.nan, np.nan])
    s = matlab.double([np.nan, np.nan, np.nan])
    
    y, m, d, h, mn, s = eng.populateDateComponents(iYaN, yy, mm, dd, hh, mmn, ss, y, m, d, h, mn, s)
    
    # Convert MATLAB arrays to numpy arrays for comparison
    y = np.array(y).flatten()
    m = np.array(m).flatten()
    d = np.array(d).flatten()
    h = np.array(h).flatten()
    mn = np.array(mn).flatten()
    s = np.array(s).flatten()
    
    expected_y = [2024, np.nan, 2024]
    expected_m = [1, np.nan, 1]
    expected_d = [1, np.nan, 2]
    expected_h = [0, np.nan, 0]
    expected_mn = [0, np.nan, 0]
    expected_s = [0, np.nan, 0]
    
    np.testing.assert_array_equal(y, expected_y)
    np.testing.assert_array_equal(m, expected_m)
    np.testing.assert_array_equal(d, expected_d)
    np.testing.assert_array_equal(h, expected_h)
    np.testing.assert_array_equal(mn, expected_mn)
    np.testing.assert_array_equal(s, expected_s)

def test_handle_midnight_case(matlab_engine):
    eng = matlab_engine
    # Define MATLAB function to be tested
    handle_midnight_case = eng.eval(
        "function [y, m, d, h] = handleMidnightCase(h, mn, s, t, y, m, d, h)\n"
        "    i2400 = find(h == 0 & mn == 0 & s == 0);\n"
        "    [y2400, m2400, d2400, ~, ~, ~] = datevec(t(i2400) - 1);\n"
        "    y(i2400) = y2400;\n"
        "    m(i2400) = m2400;\n"
        "    d(i2400) = d2400;\n"
        "    h(i2400) = 24;\n"
        "end", nargout=0)
    
    # Call the MATLAB function with a test input
    t = matlab.double([datenum(2024, 1, 1, 0, 0, 0)])
    y = matlab.double([np.nan])
    m = matlab.double([np.nan])
    d = matlab.double([np.nan])
    h = matlab.double([0])
    
    y, m, d, h = eng.handleMidnightCase(h, mn, s, t, y, m, d, h)
    
    assert y[0] == 2023
    assert m[0] == 12
    assert d[0] == 31
    assert h[0] == 24
