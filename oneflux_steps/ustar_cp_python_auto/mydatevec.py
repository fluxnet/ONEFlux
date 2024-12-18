# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/mydatevec.m


@function
def mydatevec(t=None):
    globals().update(load_all_vars())

    #
    # function [y,m,d,h,mn,s]=mydatevec(t)
    # was written by Alan Barr to return 2400 UTC rather than 0000 UTC.

    iYaN = find(logical_not(isnan(t)))
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:6
    y = matlabarray(dot(NaN, ones(size(t))))
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:8
    m = copy(y)
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:8
    d = copy(y)
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:8
    h = copy(y)
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:8
    mn = copy(y)
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:8
    s = copy(y)
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:8
    yy, mm, dd, hh, mmn, ss = datevec(take(t, iYaN), nargout=6)
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:10
    y[iYaN] = yy
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:11
    m[iYaN] = mm
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:11
    d[iYaN] = dd
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:11
    h[iYaN] = hh
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:12
    mn[iYaN] = mmn
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:12
    s[iYaN] = ss
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:12
    # set 0000 UTC to 2400 UTC, previous day.

    i2400 = find(logical_and(logical_and(h == 0, mn == 0), s == 0))
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:16
    y2400, m2400, d2400, q, q, q = datevec(take(t, i2400) - 1, nargout=6)
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:17
    y[i2400] = y2400
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:18
    m[i2400] = m2400
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:18
    d[i2400] = d2400
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:18
    h[i2400] = 24
    # oneflux_steps/ustar_cp_refactor_wip/mydatevec.m:18
    return y, m, d, h, mn, s
