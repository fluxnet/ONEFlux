import pytest
import matlab.engine
import numpy as np

# Parameterised test fixtures for fcDatetick (myDateTick)
# which takes four argument, t, sFrequency, iDateStr, fLimits
# t: time vector
# sFrequency: frequency of the ticks
# iDateStr: date string
# fLimits: limits of the plot
# Expected output: tick labels
@pytest.mark.parametrize(
    "data", [
        # Case: Daily Frequency
        {
            "t": list(range(0,49)),
            "sFrequency": "Dy",
            "iDateStr": 4,
            "fLimits": 1
        },
        # Case: Daily Frequency (skip 14)
        {
            "t": [737647, 737647+365, 737647+365*2, 737647+365*3, 737647+365*4],
            "sFrequency": "14Dy",
            "iDateStr": 4,
            "fLimits": 1
        },
        # Case: Monthly
        {
            "t": [737647, 737647+365, 737647+365*2, 737647+365*3, 737647+365*4],
            "sFrequency": "Mo",
            "iDateStr": 4,
            "fLimits": 1
        },
        # # Case: Monthly
        {
            "t": ([737647, 737647+365, 737647+365*2, 737647+365*3, 737647+365*4]),
            "sFrequency": "Mo",
            "iDateStr": 4,
            "fLimits": 0
        },
        # # Case: Monthly
        {
            "t": ([737647, 737647+365, 737647+365*2, 737647+365*3, 737647+365*4]),
            "sFrequency": "Yr",
            "iDateStr": 4,
            "fLimits": 1
        }
        ])
# Parameterised tests using the above fixtures
def test_fcDatetick(matlab_engine, data):
    """
    Test MATLAB's fcDatetick function with various edge cases.
    """
    # Prepare MATLAB inputs
    t_matlab = matlab.double(data["t"])
    sFrequency = data["sFrequency"]
    iDateStr = data["iDateStr"]
    fLimits = matlab.double(data["fLimits"])

    # Call MATLAB function
    result = 0
    try:
      result = matlab_engine.fcDatetick(t_matlab, sFrequency, iDateStr, fLimits, nargout=0)
    except:
      # Failure
      assert False

    # Verify Result
    assert result is None, "Expected None result from MATLAB function"