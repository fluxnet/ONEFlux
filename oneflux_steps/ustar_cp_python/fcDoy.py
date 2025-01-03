# Generated with SMOP  0.41-beta
from oneflux_steps.ustar_cp_python.libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/fcDoy.m


@function
def fcDoy(t=None):
    globals().update(load_all_vars())

    # d=doy(t);

    # doy is a day-of-year function
    # that converts the serial date number t to the day of year.
    # See datenum for a definition of t.

    # doy differs from other formulations in that the last
    # period of each day (denoted as 2400 by fcDatevec)
    # is attributed to the day ending 2400
    # rather than the day beginning 0000.

    # Written by Alan Barr 2002.

    y, m, d, h, mi, s = fcDatevec(t, nargout=6)
    # oneflux_steps/ustar_cp_refactor_wip/fcDoy.m:16
    tt = datenum(y, m, d)
    # oneflux_steps/ustar_cp_refactor_wip/fcDoy.m:17
    d = floor(tt - datenum(y - 1, 12, 31))
    # oneflux_steps/ustar_cp_refactor_wip/fcDoy.m:18
    return d
