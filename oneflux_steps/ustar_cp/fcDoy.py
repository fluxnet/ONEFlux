# Generated with SMOP  0.41-beta
from .libsmop import *

# ../ONEFlux/oneflux_steps/ustar_cp/fcDoy.m


@function
def mydoy(t=None, *args, **kwargs):
    varargin = mydoy.varargin
    nargin = mydoy.nargin

    # 	d=doy(t);

    # 	doy is a day-of-year function
    # 	that converts the serial date number t to the day of year.
    # 	See datenum for a definition of t.

    # 	doy differs from other formulations in that the last
    # 	period of each day (denoted as 2400 by mydatevec)
    # 	is attributed to the day ending 2400
    # 	rather than the day beginning 0000.

    # 	Written by Alan Barr 2002.

    y, m, d, h, mi, s = mydatevec(t, nargout=6)
    # ../ONEFlux/oneflux_steps/ustar_cp/fcDoy.m:16
    tt = datenum(y, m, d)
    # ../ONEFlux/oneflux_steps/ustar_cp/fcDoy.m:17
    d = floor(tt - datenum(y - 1, 12, 31))


# ../ONEFlux/oneflux_steps/ustar_cp/fcDoy.m:18
