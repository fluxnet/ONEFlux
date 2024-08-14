import pytest
import numpy as np
import matlab.engine

def create_figure():
    # Create a new figure and return its ID
    fig = eng.figure()
    return fig.Number

def test_myFigLoc():
    test_cases = [
        # Test cases with different positions and sizes
        {
            "iFig": create_figure(),
            "dx": 0.5,
            "dy": 0.5,
            "cLoc": 'LowerLeft',
            "expected": [0, 0, 800, 600]  # Example values, adjust based on screen size
        },
        {
            "iFig": create_figure(),
            "dx": 0.3,
            "dy": 0.4,
            "cLoc": 'NW',
            "expected": [0, 480, 480, 480]  # Example values, adjust based on screen size
        },
        {
            "iFig": create_figure(),
            "dx": 0.3,
            "dy": 0.4,
            "cLoc": 'xShift=1 yShift=0.4',
            "expected": [1440, 480, 480, 480]  # Example values, adjust based on screen size
        },
        {
            "iFig": create_figure(),
            "dx": 1.0,
            "dy": 1.0,
            "cLoc": 'UpperLeft',
            "expected": [0, 600, 1600, 1200]  # Example values, adjust based on screen size
        }
    ]

    for case in test_cases:
        iFig = case["iFig"]
        dx = case["dx"]
        dy = case["dy"]
        cLoc = case["cLoc"]
        expected = case["expected"]

        # Call the MATLAB function
        eng.myFigLoc(iFig, dx, dy, cLoc, nargout=0)

        # Get the figure position
        fig_pos = eng.get(iFig, 'Position')
        fig_pos = np.array(fig_pos)

        # Check if the output matches the expected values
        np.testing.assert_almost_equal(fig_pos, expected, decimal=0, err_msg=f"Failed for iFig={iFig}, dx={dx}, dy={dy}, cLoc={cLoc}")

