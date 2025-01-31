import numpy as np
from typing import Optional

from oneflux_steps.ustar_cp_python.cpdFmax2pCore import cpdFmax2pCore

def cpdFmax2pCp3(Fmax: float, n: int) -> Optional[float]:
    """
    Calculates the probability `p` that the 3-parameter diagnostic change-point
    model fit is significant.

    Based on the method implemented by Alan Barr in 2010 in Matlab.

    It interpolates within a Table pTable, generated 
%	for the 3-parameter model by Wang (2003).

    Args:
        Fmax: The Fmax value to be evaluated.
        n: Sample size or degrees of freedom.

    Returns:
        The calculated probability `p`, or `NaN` if inputs are invalid.
    """
    # lower tail probability
    lowerP = 0.95

    return cpdFmax2pCore(Fmax, n, 3, pTable, nTable, FmaxTable, lowerP)

""" The critical F-max values as a 2D NumPy array. """
FmaxTable : np.ndarray = np.array([
        [11.646, 15.559, 28.412],
        [9.651, 11.948, 18.043],
        [9.379, 11.396, 16.249],
        [9.261, 11.148, 15.750],
        [9.269, 11.068, 15.237],
        [9.296, 11.072, 15.252],
        [9.296, 11.059, 14.985],
        [9.341, 11.072, 15.013],
        [9.397, 11.080, 14.891],
        [9.398, 11.085, 14.874],
        [9.506, 11.127, 14.828],
        [9.694, 11.208, 14.898],
        [9.691, 11.310, 14.975],
        [9.790, 11.406, 14.998],
        [9.794, 11.392, 15.044],
        [9.840, 11.416, 14.980],
        [9.872, 11.474, 15.072],
        [9.929, 11.537, 15.115],
        [9.955, 11.552, 15.086],
        [9.995, 11.549, 15.164],
        [10.102, 11.673, 15.292],
        [10.169, 11.749, 15.154],
        [10.478, 12.064, 15.519]
    ])

""" A 1D NumPy array containing sample sizes. """
nTable : np.ndarray = np.concatenate([
        np.arange(10, 101, 10),  # 10, 20, ..., 100
        np.arange(150, 601, 50),  # 150, 200, ..., 600
        [800, 1000, 2500]  # 800, 1000, 2500
    ])

""" A 1D NumPy array containing significance levels. """
pTable : np.ndarray = np.array([0.90, 0.95, 0.99])

