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
        # Above f-critical(3)
        (17, 53, 0.0363346810492975),
        # Between f-critical(1) and f-critical(3)
        (10, 52, 0.0761404222166437),
        # fmax = 0
        (0, 55, 1),
        # fmax = fcritical(1)
        (1.6301, 52, 1),
        # Nominal
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


import pytest
import numpy as np
import matlab.engine

@pytest.mark.parametrize(
    "Fmax, n, expected",
    [
        (np.nan, 10, np.nan),     # Test case with Fmax = NaN
        (10, np.nan, np.nan),     # Test case with n = NaN
        (10, 5, np.nan),          # Test case with n < 10
        ],
)
def test_cpdFmax2pCp3_return_nan(matlab_engine, Fmax, n, expected):
    """
    Test the cpdFmax2pCp3 MATLAB function for cases where `nan` is returned.
    """
    # Handle NaN inputs for MATLAB
    Fmax_matlab = matlab.double([Fmax]) if not np.isnan(Fmax) else matlab.double([float('nan')])
    n_matlab = matlab.double([n]) if not np.isnan(n) else matlab.double([float('nan')])

    # Call the MATLAB function
    result = matlab_engine.cpdFmax2pCp3(Fmax_matlab, n_matlab)

    assert type(result) == type(expected), f"Result should be a {type(expected)}, got {type(result)}"


@pytest.mark.parametrize(
    "Fmax, n, expected",
    [
        (5, 20, 0.4393355161666135),       # Fmax below critical value
        (30, 1000, 2.7278340575698223e-05),# Fmax above critical value
        (11.5, 100, 0.0432111321429921),   # Fmax within critical range
    ],
)

def test_cpdFmax2pCp3_return_numeric(matlab_engine, Fmax, n, expected):
    """
    Test the cpdFmax2pCp3 MATLAB function for cases where numeric values are returned.
    """
    # Handle NaN inputs for MATLAB
    Fmax_matlab = matlab.double([Fmax]) if not np.isnan(Fmax) else matlab.double([float('nan')])
    n_matlab = matlab.double([n]) if not np.isnan(n) else matlab.double([float('nan')])

    # Call the MATLAB function
    result = matlab_engine.cpdFmax2pCp3(Fmax_matlab, n_matlab)

    assert type(result) == type(expected), f"Result should be a {type(expected)}, got {type(result)}"
    assert np.allclose(np.array(result), np.array(expected))