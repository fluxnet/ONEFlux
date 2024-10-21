# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/fcBin.m


@function
def cpdBin(x=None, y=None, dx=None, nPerBin=None, *args, **kwargs):
    varargin = cpdBin.varargin
    nargin = cpdBin.nargin

    # cpdBin

    # calculates binned mean values of vectors x and y
    # for use in change-point (uStarTh) detection

    # Syntax: [nBins,mx,my] = cpdBin(x,y,dx,nPerBin);

    # dx and nPerBin control how the data are binned.
    # if dx is a positive scalar, it specifies the binning increment.
    # if dx is a vector, it specifies the bin borders.
    # if dx is empty, then nPerBin is used to bin the data,
    # into bins with nPerBin points in each bin.

    # -----------------------------------------------------------------------

    nBins = 0
    # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:18
    mx = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:18
    my = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:18
    if dx <= 0:
        disp("Function cpdBin aborted. dx cannot be <=0. ")
        return nBins, mx, my

    if 0 == length(dx):
        # into bins with nPerBin points in each bin.
        iYaN = find(logical_not(isnan(x + y)))
        # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:24
        nYaN = length(iYaN)
        # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:24
        nBins = floor(nYaN / nPerBin)
        # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:25
        mx = dot(NaN, ones(nBins, 1))
        # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:26
        my = dot(NaN, ones(nBins, 1))
        # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:26
        iprctile = arange(0, 100, (100 / nBins))
        # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:27
        dx = prctile(x[iYaN], iprctile)
        # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:28
        xL = dx[arange(1, (end() - 1))]
        # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:29
        xU = dx[arange(2, end())]
        # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:29
        jx = 0
        # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:30
        for i in arange(1, length(xL)).reshape(-1):
            ix = find(
                logical_and(logical_not(isnan(x + y)), x)
                >= logical_and(xL[i], x)
                <= xU[i]
            )
            # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:31
            if length(ix) >= nPerBin:
                jx = jx + 1
                # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:33
                mx[jx] = mean(x[ix])
                # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:34
                my[jx] = mean(y[ix])
    # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:35
    else:
        if 1 == length(dx):
            nx = min(x)
            # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:39
            xx = max(x)
            # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:39
            nx = dot(floor(nx / dx), dx)
            # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:40
            xx = dot(ceil(xx / dx), dx)
            # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:41
            for jx in arange(nx, xx, dx).reshape(-1):
                ix = find(
                    logical_and(logical_not(isnan(x + y)), abs(x - jx)) < dot(0.5, dx)
                )
                # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:43
                if length(ix) >= nPerBin:
                    nBins = nBins + 1
                    # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:45
                    mx[nBins, 1] = mean(x[ix])
                    # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:46
                    my[nBins, 1] = mean(y[ix])
        # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:47
        else:
            xL = dx[arange(1, (end() - 1))]
            # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:51
            xU = dx[arange(2, end())]
            # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:51
            for i in arange(1, length(xL)).reshape(-1):
                ix = find(
                    logical_and(logical_not(isnan(x + y)), x)
                    >= logical_and(xL[i], x)
                    <= xU[i]
                )
                # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:53
                if length(ix) >= nPerBin:
                    nBins = nBins + 1
                    # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:55
                    mx[nBins, 1] = mean(x[ix])
                    # oneflux_steps/ustar_cp_refactor_wip/fcBin.m:56
                    my[nBins, 1] = mean(y[ix])


# oneflux_steps/ustar_cp_refactor_wip/fcBin.m:57
