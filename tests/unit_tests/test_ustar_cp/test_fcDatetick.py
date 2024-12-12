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
        # Case 1: Daily Frequency
        {
            "t": np.array([737647, 737648, 737649, 737650, 737651]),
            "sFrequency": "daily",
            "iDateStr": "dd-mmm",
            "fLimits": [737647, 737651],
            "expected": [
                "01-Jan", "02-Jan", "03-Jan", "04-Jan", "05-Jan"
            ],
        },
        # Case 2: Weekly Frequency
        {
            "t": np.array([737647, 737654, 737661, 737668, 737675]),
            "sFrequency": "weekly",
            "iDateStr": "dd-mmm",
            "fLimits": [737647, 737675],
            "expected": [
                "01-Jan", "08-Jan", "15-Jan", "22-Jan", "29-Jan"
            ],
        },
        # Case 3: Monthly Frequency
        {
            "t": np.array([737647, 737677, 737708, 737738, 737769]),
            "sFrequency": "monthly",
            "iDateStr": "dd-mmm",
            "fLimits": [737647, 737769],
            "expected": [
                "01-Jan", "01-Feb", "01-Mar", "01-Apr", "01-May"
            ],
        },
        # Case 4: Yearly Frequency
        {
            "t": np.array([737647, 737647+365, 737647+365*2, 737647+365*3, 737647+365*4]),
            "sFrequency": "yearly",
            "iDateStr": "dd-mmm",
            "fLimits": [737647, 737647+365*4],
            "expected": [
                "01-Jan", "01-Jan", "01-Jan", "01-Jan", "01-Jan"
            ],
        }])
# Parameterised tests using the above fixtures
def test_fcDatetick(matlab_engine, data):
    """
    Test MATLAB's fcDatetick function with various edge cases.
    """
    # Prepare MATLAB inputs
    t_matlab = matlab.double(data["t"].tolist())
    sFrequency = data["sFrequency"]
    iDateStr = data["iDateStr"]
    fLimits = matlab.double(data["fLimits"])

    # Call MATLAB function
    result = matlab_engine.fcDatetick(t_matlab, sFrequency, iDateStr, fLimits)

    # Verify Result
    assert result is not None, "Expected non-None result from MATLAB function"

    # Perform Element-wise Comparison
    for idx, exp_val in enumerate(data["expected"]):
        # Extract result as scalar
        try:
            result_value = str(result[idx])
        except (IndexError, TypeError):
            result_value = np.nan

        # Handle NaN and numerical comparisons
        assert result_value == exp_val, f"Expected {exp_val}, got {result_value} at index {idx}"

