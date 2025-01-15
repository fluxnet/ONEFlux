from oneflux_steps.ustar_cp_python.fcDatevec import fcDatevec
from oneflux_steps.ustar_cp_python.fcDatenum import mydatenum
import numpy as np

def fcDoy(t=None):
    """
    Convert serial date number(s) to day(s) of the year.

    This function converts the serial date number `t` to the day of the year.
    The last period of each day (denoted as 2400 by fcDatevec) is attributed
    to the day ending 2400 rather than the day beginning 0000.

    Parameters:
    t (int, float, list, or numpy array): Serial date number(s) to be converted.
                                          Can be a single value or a list/array of values.

    Returns:
    numpy array: Day(s) of the year corresponding to the input serial date number(s).

    Written in MATLAB initially by Alan Barr 2002.

    Examples:
    >>> fcDoy(367)
    array(366)
    >>> fcDoy([367])
    array([366])

    The serial date is considered 1-indexed, so 0 counts the previous year and 1 is current year:

    >>> fcDoy([0])
    array([364])
    >>> fcDoy([1])
    array([0])
    """

    t = np.ceil(t)
    y, m, d, h, mi, s = fcDatevec(t)

    # apply the following to every element of y, m, d pointwise
    def convert(y, m, d):
      # if y is a list or vector of some kind, apply the function to each element
      if hasattr(y, "__len__"):
        return np.vectorize(convert)(y, m, d)
      else:
        # Convert the date to a datetime object
        tt = mydatenum(int(y), int(m), int(d)) # datenum(y, m, d)
        # Subtract the last day of the previous year
        d = np.floor(tt - mydatenum(int(y - 1), 12, 31))
        return d

    d = np.vectorize(convert)(y, m, d)
    return d
