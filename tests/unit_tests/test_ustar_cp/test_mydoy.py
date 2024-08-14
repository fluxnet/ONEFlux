import pytest
import numpy as np
import matlab.engine

def test_mydoy(matlab_engine):
    eng = matlab_engine

    # Define MATLAB function to be tested
    mydoy = eng.eval(
        "function d = mydoy(t)\n"
        "    [y, m, d, h, mi, s] = mydatevec(t);\n"
        "    tt = datenum(y, m, d);\n"
        "    d = floor(tt - datenum(y - 1, 12, 31));\n"
        "end", nargout=0)

    # Define test inputs
    t = matlab.double([datenum(2024, 1, 1), datenum(2024, 2, 15), datenum(2024, 12, 31)])
    
    # Call the MATLAB function with test inputs
    d = eng.mydoy(t)
    
    # Convert MATLAB output to numpy array
    d = np.array(d).flatten()
    
    # Expected outputs
    expected_d = [1, 46, 366]
    
    # Assert results
    np.testing.assert_array_equal(d, expected_d)

def test_mydoy_midnight(matlab_engine):
    eng = matlab_engine
    
    # Test case for midnight on a day boundary
    t = matlab.double([datenum(2024, 1, 1, 0, 0, 0), datenum(2024, 12, 31, 0, 0, 0)])
    
    # Call the MATLAB function with test inputs
    d = eng.mydoy(t)
    
    # Convert MATLAB output to numpy array
    d = np.array(d).flatten()
    
    # Expected outputs
    expected_d = [1, 366]
    
    # Assert results
    np.testing.assert_array_equal(d, expected_d)

