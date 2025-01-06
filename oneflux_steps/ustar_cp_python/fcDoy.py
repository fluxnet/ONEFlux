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

    y, m, d, h, mi, s = fcDatevec(t)
    # oneflux_steps/ustar_cp_refactor_wip/fcDoy.m:16
    # apply the following to every element of y, m, d pointwise

    def convert(y, m, d):
      tt = mydatenum(int(y), int(m), int(d), 0, 0, 0) # datenum(y, m, d)
      # oneflux_steps/ustar_cp_refactor_wip/fcDoy.m:17
      d = np.floor(tt - mydatenum(int(y - 1), 12, 31, 0, 0, 0))
      #oneflux_steps/ustar_cp_refactor_wip/fcDoy.m:18
      return d
    
    d = np.vectorize(convert)(y, m, d)
    return d
