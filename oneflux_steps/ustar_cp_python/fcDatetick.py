from oneflux_steps.ustar_cp_python.utils import floor, ceil, dot, arange, xlim, unique
from oneflux_steps.ustar_cp_python.fcDatevec import fcDatevec
from oneflux_steps.ustar_cp_python.fcDatenum import datenum
import numpy as np
import matplotlib.pyplot as plt
import datetime

def fcDatetick(t : float | np.ndarray, sFrequency : str, iDateStr : int, fLimits : float):
    """
    Generate date ticks for a plot based on the given time vector and frequency.

    This function generates date ticks for a plot based on the provided time vector `t`,
    the frequency `sFrequency`, the date string format `iDateStr`, and the plot limits `fLimits`.
    It replicates some minimal behavior from the previous codebase for plotting purposes.

    Parameters:
    t (array-like): Time vector.
    sFrequency (str): Frequency of the ticks. Possible values are "Dy", "14Dy", "Mo".
    iDateStr (int): Date string format.
    fLimits (float): Limits of the plot.

    Returns:
    None

    Notes:
    - This function is *not* used in the rest of the Python code.
    - It is *not* thoroughly tested and only replicates some minimal behavior from the previous codebase for plotting.

    Examples:
    >>> t = list(range(0, 49))
    >>> sFrequency = "Mo"
    >>> iDateStr = 4
    >>> fLimits = 1
    >>> fcDatetick(t, sFrequency, iDateStr, fLimits)
    """

    y, m, d, h, mn, s = fcDatevec(t)
    iYrs = unique(y)
    iSerMos = dot((y - 1), 12) + m
    iSerMo1 = min(iSerMos)
    iSerMo2 = max(iSerMos)
    nSerMos = iSerMo2 - iSerMo1 + 1
    xDates = np.array([])

    match (sFrequency):
      case "Dy":
        xDates = t[::48]

      case "14Dy":
        iYr1 = floor(iSerMo1 / 12) + 1
        iMo1 = iSerMo1 % 12
        if iMo1 == 0:
            iMo1 = 12
            iYr1 = iYr1 - 1
        for iDy in arange(1, 15, 14).reshape(-1):
            xDates = [datenum(iYr1, int(month), iDy) for month in arange(iMo1, (iMo1 + nSerMos))]

      case "Mo":
        iYr1 = floor(iSerMo1 / 12) + 1
        iMo1 = iSerMo1 % 12
        if iMo1 == 0:
            iMo1 = 12
            iYr1 = iYr1 - 1
        # define xDates as the array given my mapping over
        # every month in arange(iMo1, (iMo1 + nSerMos)) 
        # and applying `datenum(iYr1, month, 1)` to it
        xDates = [datenum(iYr1, int(month), 1) for month in arange(iMo1, (iMo1 + nSerMos))]
        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:36
        # # # 			datestr(xDates)
        # # # 			datestr([min(t) max(t)])
        # # # 			pause;
                                  
    xDates = unique(xDates)

    # Set current `x` access to have values given by xDates
    plt.gca().set_xticks(xDates)
    # set label to empty
    plt.gca().set_xticklabels([])
    if iDateStr > 0:
        # compute a datestring for each xDates based on iDateStr
        # TODO: this is different to the original MATLAB code which was
        # cDates = datestr(xDates, iDateStr)

        # convert from a date floating-point
        # ordinal to a datetime object
        cDates = [datetime.datetime.fromordinal(floor(t) + 1).strftime("%Y-%m-%d") for t in xDates]

        plt.gca().set_xticklabels(cDates)

    if fLimits == 1:
        xlim([floor(min(xDates)), ceil(max(xDates))])
        # Turn on the grid and box using matplotlib
        plt.grid("on")
        plt.box("on")

    return None
