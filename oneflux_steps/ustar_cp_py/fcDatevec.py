# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m


@function
def mydatevec(t=None):
    #
    # function [y,m,d,h,mn,s]=mydatevec(t)
    # was written by Alan Barr to return 2400 UTC rather than 0000 UTC.

    iYaN = find(logical_not(isnan(t)))
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:6
    y = dot(NaN, ones(size(t)))
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:8
    m = copy(y)
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:8
    d = copy(y)
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:8
    h = copy(y)
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:8
    mn = copy(y)
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:8
    s = copy(y)
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:8
    yy, mm, dd, hh, mmn, ss = datevec(t[iYaN], nargout=6)
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:10
    y[iYaN] = yy
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:11
    m[iYaN] = mm
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:11
    d[iYaN] = dd
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:11
    h[iYaN] = hh
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:12
    mn[iYaN] = mmn
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:12
    s[iYaN] = ss
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:12
    # set 0000 UTC to 2400 UTC, previous day.

    i2400 = find(h == logical_and(0, mn) == logical_and(0, s) == 0)
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:16
    y2400, m2400, d2400, q, q, q = datevec(t[i2400] - 1, nargout=6)
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:17
    y[i2400] = y2400
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:18
    m[i2400] = m2400
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:18
    d[i2400] = d2400
    # oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:18
    h[i2400] = 24


# oneflux_steps/ustar_cp_refactor_wip/fcDatevec.m:18
