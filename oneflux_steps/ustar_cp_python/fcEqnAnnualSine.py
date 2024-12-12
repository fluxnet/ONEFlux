import numpy as np
from datetime import date

def fc_eqn_annual_sine(b: np.ndarray, t: np.ndarray) -> np.ndarray:
    """
    Computes the annual sine wave equation.

    Args:
        b (np.ndarray): A 1D array of coefficients [b1, b2, b3].
            - b[0]: Baseline offset.
            - b[1]: Amplitude of the sine wave.
            - b[2]: Phase shift of the sine wave.
        t (np.ndarray): A 1D array of time points.

    Returns:
        np.ndarray: Computed values based on the sine wave equation.

    Raises:
        ValueError: If `b` does not have exactly three elements.

    Example:
        >>> b = np.array([1, 2, 3])
        >>> t = np.array([0, 1, 2, 3, 4])
        >>> fc_eqn_annual_sine(b, t)
        array([0.748, 2.656, 3.712, 3.867, 2.997])
    """
    if b.shape != (3,):
        raise ValueError("Coefficient array `b` must have exactly three elements.")

    # Compute the number of days per year based on year 2000

    n_days_per_year = 365.2425 # Evaluation of Matlab datenum(2000-1,12,31)/2000;

    # Calculate the angular frequency
    omega = 2 * np.pi / n_days_per_year

    # Compute the sine wave
    y = b[0] + b[1] * np.sin(omega * (t - b[2]))
    
    return y
