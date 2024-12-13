import pytest
import matlab.engine
import numpy as np

@pytest.mark.parametrize(
    "b, t, expected",
    [
        # Case 1: Zero Amplitude (Constant)
        ([0, 0, 0], [0, 90, 180, 270, 360], [0, 0, 0, 0, 0]),

        # Case 2: Pure Sine Wave, Zero Offset
        ([0, 1, 0], [0, 90, 180, 270, 360], [0, 0.9997458409224182, 0.04507749933823567, -0.9977133433981337, -0.09006335547871482]),

        # Case 3: Sine Wave with Offset
        ([2, 1, 0], [0, 90, 180, 270, 360], [2, 2.9997458409224182, 2.0450774993382357, 1.0022866566018664, 1.909936644521285]),

        # Case 4: Phase Shift
        ([0, 1, 90], [0, 90, 180, 270, 360], [-0.9997458409224182, 0, 0.9997458409224182, 0.04507749933823567, -0.9977133433981337]),

        # Case 5: Negative Amplitude
        ([0, -1, 0], [0, 90, 180, 270, 360], [0, -0.9997458409224182, -0.04507749933823567, 0.9977133433981337, 0.09006335547871482]),
        # Case 6: Pure Sine Wave, Zero Offset, small time frame
        ([0, 1, 0], [0, 180, 360], [0, 0.04507749933823567, -0.09006335547871482]),

        # Case 7: Pure Sine Wave, Zero Offset, non monotonic time frame
        ([0, 1, 0], [0, 360, 180], [0,  -0.09006335547871482, 0.04507749933823567]),
        # Edge Case: NaN in Parameters
        ([np.nan, 1, 0], [0, 90, 180, 270, 360], [np.nan, np.nan, np.nan, np.nan, np.nan]),

        # Edge Case: NaN in Time Vector
        ([0, 1, 0], [0, np.nan, 180, 270, 360], [0, np.nan, 0.04507749933823567, -0.9977133433981337, -0.09006335547871482]),

        # Edge Case: Empty Time Vector
        ([0, 1, 0], [], []),
    ],
)
def test_fcEqnAnnualSine_edge_cases(matlab_engine, b, t, expected):
    """
    Test MATLAB's fcEqnAnnualSine function with various edge cases.
    """
    # Prepare MATLAB inputs
    b_matlab = matlab.double(b)
    t_matlab = matlab.double(t)

    # Call MATLAB function
    result = np.array(matlab_engine.fcEqnAnnualSine(b_matlab, t_matlab)).flatten()

    # Verify Result
    assert result is not None, "Expected non-None result from MATLAB function"

    # Perform Element-wise Comparison
    for idx, exp_val in enumerate(expected):
        # Extract result as scalar
        try:
            result_value = float(result[idx])
        except (IndexError, TypeError):
            result_value = np.nan

        # Handle NaN and numerical comparisons
        if np.isnan(exp_val):
            assert np.isnan(result_value), f"Expected NaN, got {result_value} at index {idx}"
        else:
            assert np.isclose(result_value, exp_val, atol=1e-6), f"Expected {exp_val}, got {result_value} at index {idx}"