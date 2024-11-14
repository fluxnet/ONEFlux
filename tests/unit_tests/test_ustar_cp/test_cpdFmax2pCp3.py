import matlab.engine
import numpy as np
import pytest


testcases = [
        # Input values are NaN
        (np.nan, 52, np.nan),
        # Different input value is NaN
        (42, np.nan, np.nan),
        # n < 10
        (3.14159265358979323, 9, np.nan),
        # Below f-critical(1)
        (5.45204127574611, 52, 0.384643400326067),
        # Test case 3: Above f-critical(3)
        (12, 53, 0.0363346810492975),
        # Test case 4: Between f-critical(1) and f-critical(3)
        (10, 52, 0.0761404222166437),
        # Test case 5: fmax = 0
        (0, 55, 1),
        # Test case 6: fmax = fcritical(1)
        (1.6301, 52, 1),
        # Test case 7: Nominal
        (2.37324492970613, 55, 1),
        (10.3567400792636, 54, 0.0657053181314848)
]
@pytest.mark.parametrize("fmax, n, expected_p3", testcases)
def test_cpdFmax2pCp3(matlab_engine, fmax, n, expected_p3):
    """
    Test the cpdFmax2pCp3 function in MATLAB.
    Args:
        matlab_engine (fixture): Fixture that initializes and manages the MATLAB engine session.
        fmax, n : Matlab function input arguments
        expected_p3 (float): The expected value of p3.
    """
    # Convert the input values to MATLAB compatible data types
    fmax = matlab.double(fmax)
    n = matlab.double(n)

    # Run the MATLAB function
    output_p3 = matlab_engine.cpdFmax2pCp3(fmax, n, nargout=1)


    assert np.isclose(output_p3, expected_p3, equal_nan=True), f"Expected p3 value of {expected_p3}, but got {output_p3}."


