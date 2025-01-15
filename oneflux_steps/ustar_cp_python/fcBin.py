import numpy
#from oneflux_steps.ustar_cp_python.myprctile import myprctile
from oneflux_steps.ustar_cp_python.utils import prctile

def fcBin(x, y, dx, nPerBin):
    """
    cpdBin
    calculates binned mean values of vectors x and y
    for use in change-point (uStarTh) detection
    Syntax: [nBins,mx,my] = cpdBin(x,y,dx,nPerBin);

    dx and nPerBin control how the data are binned.
    if dx is a positive scalar, it specifies the binning increment.
    if dx is a vector, it specifies the bin borders.
    if dx is empty, then nPerBin is used to bin the data,
    into bins with nPerBin points in each bin.
    """
    nBins = 0
    mx = []
    my = []
    if numpy.any(numpy.array(dx) <= 0):
        print('Function cpdBin aborted. dx cannot be <=0. ')
        return nBins, mx, my

    # dx is an empty vector
    if hasattr(dx, "__len__") and (len(dx) == 0):
        # into bins with nPerBin points in each bin.
        iYaN = numpy.where(~numpy.isnan(x + y) == True)[0]
        nYaN = len(iYaN)
        nBins = int(numpy.floor(nYaN / nPerBin))
        mx = numpy.full(nBins, numpy.nan)
        my = numpy.full(nBins, numpy.nan)
        if nBins == 0:
          # Avoid divide-by-zero
          iprctile = numpy.array([0])
        else:
          iprctile = numpy.arange(0, 101, (100. / float(nBins)))
        # PRI - October 2019
        # replace numpy.percentile() with Python translation of MATLAB/Octave
        # prctile() and quantile() functions.
        dx = prctile(x[iYaN], iprctile)
        xL = dx[:-1]
        xU = dx[1:]
        jx = 0
        for i in numpy.arange(0, len(xL)):
            ix = numpy.where(((~numpy.isnan(x+y)) & (x >= xL[i]) & (x <= xU[i])) == True)[0]
            if len(ix) >= nPerBin:
                mx[jx] = numpy.mean(x[ix])
                my[jx] = numpy.mean(y[ix])
                jx = jx + 1

    # dx is a scalar (or single element vector)
    elif (not(hasattr(dx, "__len__"))) or (hasattr(dx, "__len__") and (len(dx) == 1)):
        nx = numpy.min(x)
        xx = numpy.max(x)
        nx = dx*int(numpy.floor(nx / dx))
        xx = dx*int(numpy.ceil(xx / dx))
        mx = numpy.full(len(numpy.arange(nx, xx, dx)), numpy.nan)
        my = numpy.full(len(numpy.arange(nx, xx, dx)), numpy.nan)
        for jx in numpy.arange(nx, xx, dx):
            ix = numpy.where(((~numpy.isnan(x+y)) & (abs(x - jx) < 0.5*dx)) == True)[0]
            if len(ix) >= nPerBin:
                mx[nBins] = numpy.mean(x[ix])
                my[nBins] = numpy.mean(y[ix])
                nBins = nBins + 1
    
    # dx is a vector (with more than one element)
    else:
        xL = dx[:-1]
        xU = dx[1:]
        mx = numpy.full(len(xL), numpy.nan)
        my = numpy.full(len(xL), numpy.nan)
        for i in numpy.arange(0, len(xL)):
            ix = numpy.where(((~numpy.isnan(x+y)) & (x >= xL[i]) & (x <= xU[i])) == True)[0]
            if len(ix) >= nPerBin:
                mx[nBins] = numpy.mean(x[ix])
                my[nBins] = numpy.mean(y[ix])
                nBins = nBins + 1
    return nBins, mx.reshape(-1, 1), my.reshape(-1, 1)
