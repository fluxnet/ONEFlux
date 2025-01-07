# Generated with SMOP  0.41-beta
from oneflux_steps.ustar_cp_python.libsmop import datenum
from oneflux_steps.ustar_cp_python.fcDatevec import fcDatevec
from oneflux_steps.ustar_cp_python.fcDatenum import mydatenum
# oneflux_steps/ustar_cp_refactor_wip/fcDoy.m
import numpy as np
from datetime import datetime, timedelta

def fcDoy(t=None):
    # d=doy(t);

    # doy is a day-of-year function
    # that converts the serial date number t to the day of year.
    # See datenum for a definition of t.

    # doy differs from other formulations in that the last
    # period of each day (denoted as 2400 by fcDatevec)
    # is attributed to the day ending 2400
    # rather than the day beginning 0000.

    # Written by Alan Barr 2002.

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
