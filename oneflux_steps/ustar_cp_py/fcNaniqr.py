# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m


@function
def fcnaniqr(X=None, *args, **kwargs):
    varargin = fcnaniqr.varargin
    nargin = fcnaniqr.nargin

    # fcnaniqr computes the interquartile range, ignoring NaNs.

    # IQR = fcnaniqr(X)
    # returns the interquartile range of the values in X,
    # treating NaNs as missing.

    # fcnaniqr is a limited adaptation of IQR:
    # X cannot exceed 3 dimensions,
    # and IQR is always computed across the
    # first non-singleton dimension of X.

    # For vector input, IQR is a scalar.
    # For 2D matrix input, IQR is a row vector containing
    # the interquartile range of each column of X.
    # For a 3D arrays, IQR is a 2d array, computed
    # along the first non-singleton dimension of X.
    #
    # The IQR is a robust estimate of the spread of the data,
    # since changes in the upper and lower 25# of the data
    # do not affect it.

    # Written by Alan Barr

    # =======================================================================
    # =======================================================================

    # find non-singleton dimensions of length d

    d = size(X)
    # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:32
    d = setdiff(d, 1)
    # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:32
    nd = length(d)
    # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:32
    if 1 == nd:
        iYaN = find(logical_not(isnan(X)))
        # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:36
        nYaN = length(iYaN)
        # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:36
        IQR = copy(NaN)
        # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:36
        if nYaN <= 3:
            y = X[iYaN]
            # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:38
            yN = prctile(y, 25)
            # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:38
            yX = prctile(y, 75)
            # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:38
            IQR = yX - yN
    # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:38
    else:
        if 2 == nd:
            nr, nc = size(X, nargout=2)
            # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:41
            IQR = dot(NaN, ones(1, nc))
            # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:41
            for ic in arange(1, nc).reshape(-1):
                iYaN = find(logical_not(isnan(X[arange(), ic])))
                # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:43
                nYaN = length(iYaN)
                # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:43
                if nYaN > 3:
                    y = X[iYaN, ic]
                    # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:45
                    yN = prctile(y, 25)
                    # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:45
                    yX = prctile(y, 75)
                    # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:45
                    IQR[ic] = yX - yN
        # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:45
        else:
            if 3 == nd:
                nr, nc, nq = size(X, nargout=3)
                # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:49
                IQR = dot(NaN, ones(nc, nq))
                # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:49
                for iq in arange(1, nq).reshape(-1):
                    for ic in arange(1, nc).reshape(-1):
                        iYaN = find(logical_not(isnan(X[arange(), ic, iq])))
                        # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:52
                        nYaN = length(iYaN)
                        # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:52
                        if nYaN > 3:
                            y = X[iYaN, ic, iq]
                            # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:54
                            yN = prctile(y, 25)
                            # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:54
                            yX = prctile(y, 75)
                            # oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:54
                            IQR[ic, iq] = yX - yN


# oneflux_steps/ustar_cp_refactor_wip/fcNaniqr.m:54
