# Generated with SMOP  0.41-beta
from .libsmop import *

# ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m


@function
def mydatevec(t=None, *args, **kwargs):
    varargin = mydatevec.varargin
    nargin = mydatevec.nargin

    #
    # 	function [y,m,d,h,mn,s]=mydatevec(t)
    # 	was written by Alan Barr to return 2400 UTC rather than 0000 UTC.

    iYaN = find(logical_not(isnan(t)))
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:6
    y = dot(NaN, ones(size(t)))
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:8
    m = copy(y)
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:8
    d = copy(y)
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:8
    h = copy(y)
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:8
    mn = copy(y)
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:8
    s = copy(y)
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:8
    yy, mm, dd, hh, mmn, ss = datevec(t(iYaN), nargout=6)
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:10
    y[iYaN] = yy
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:11
    m[iYaN] = mm
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:11
    d[iYaN] = dd
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:11
    h[iYaN] = hh
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:12
    mn[iYaN] = mmn
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:12
    s[iYaN] = ss
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:12
    # 	set 0000 UTC to 2400 UTC, previous day.

    i2400 = find(h == logical_and(0, mn) == logical_and(0, s) == 0)
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:16
    y2400, m2400, d2400, q, q, q = datevec(t(i2400) - 1, nargout=6)
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:17
    y[i2400] = y2400
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:18
    m[i2400] = m2400
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:18
    d[i2400] = d2400
    # ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:18
    h[i2400] = 24


# ../ONEFlux/oneflux_steps/ustar_cp/mydatevec.m:18
