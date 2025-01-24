import numpy as np
from typing import Optional

from oneflux_steps.ustar_cp_python.cpdFmax2pCore import cpdFmax2pCore

def cpdFmax2pCp2(Fmax: float, n: int) -> Optional[float]:
    """
    Calculates the probability `p` that the 2-parameter diagnostic change-point
    model fit is significant.

    Based on the method implemented by Alan Barr in 2010 in Matlab.

    It interpolates within a Table pTable, generated 
  	for the 2-parameter model by Alan Barr following Wang (2003).

    If Fmax is outside the range in the table, 
  	then the normal F stat is used to help extrapolate.

    Args:
        Fmax: The Fmax value to be evaluated.
        n: Sample size or degrees of freedom.

    Returns:
        The calculated probability `p`, or `NaN` if inputs are invalid.
    """

    # Lower tail probability for the 2-parmater model
    lowerP = 0.90

    return cpdFmax2pCore(Fmax, n, 2, pTable, nTable, FmaxTable, lowerP)

""" The critical F-max values as a 2D NumPy array. """
FmaxTable : np.ndarray = np.array([
    [3.9293, 6.2992, 9.1471, 18.2659],
    [3.7734, 5.6988, 7.8770, 13.8100],
    [3.7516, 5.5172, 7.4426, 12.6481],
    [3.7538, 5.3224, 7.0306, 11.4461],
    [3.7941, 5.3030, 6.8758, 10.6635],
    [3.8548, 5.3480, 6.8883, 10.5026],
    [3.9798, 5.4465, 6.9184, 10.4527],
    [4.0732, 5.5235, 6.9811, 10.3859],
    [4.1467, 5.6136, 7.0624, 10.5596],
    [4.2770, 5.7391, 7.2005, 10.6871],
    [4.4169, 5.8733, 7.3421, 10.6751],
    [4.5556, 6.0591, 7.5627, 11.0072],
    [4.7356, 6.2738, 7.7834, 11.2319]
])

""" A 1D NumPy array containing sample sizes. """
# tmp run to 200 1e5 reps
nTable : np.ndarray = np.array([10, 15, 20, 30, 50, 70, 100
                       , 150, 200, 300, 500, 700, 1000])

""" A 1D NumPy array containing significance levels. """
pTable : np.ndarray = np.array([0.80, 0.90, 0.95, 0.99])