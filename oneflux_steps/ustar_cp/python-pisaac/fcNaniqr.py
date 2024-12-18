# standard modules
# 3rd party modules
import numpy
# local modules
from myprctile import myprctile

def fcnaniqr(X):
    """
    fcnaniqr computes the interquartile range, ignoring NaNs.

    IQR = fcnaniqr(X)
     returns the interquartile range of the values in X,
     treating NaNs as missing.

     fcnaniqr is a limited adaptation of IQR:
     X cannot exceed 3 dimensions,
     and IQR is always computed across the
     first non-singleton dimension of X.

     For vector input, IQR is a scalar.
     For 2D matrix input, IQR is a row vector containing
      the interquartile range of each column of X.
     For a 3D arrays, IQR is a 2d array, computed
      along the first non-singleton dimension of X.

     The IQR is a robust estimate of the spread of the data,
     since changes in the upper and lower 25% of the data
     do not affect it.

     Written by Alan Barr
     Translated to Python by PRI in October 2019
    """
    # find non-singleton dimensions of length d
    d = X.shape
    d = numpy.setdiff1d(d, 1)
    nd = len(d)
    if nd == 1:
        iYaN = numpy.where(~numpy.isnan(X))[0]
        nYaN = len(iYaN)
        IQR = numpy.nan
        if nYaN <= 3:
            y = X[iYaN]
            # PRI - October 2019
            # replace numpy.percentile() with Python translation of MATLAB/Octave
            # prctile() and quantile() functions.
            yN, yX = myprctile(y, numpy.array([25, 75]))
            IQR = yX - yN
    else:
        if nd == 2:
            nr, nc = X.shape
            IQR = numpy.full((nc), numpy.nan)
            for ic in range(nc):
                iYaN = numpy.where(~numpy.isnan(X[:,ic]))[0]
                nYaN = len(iYaN)
                if nYaN > 3:
                    y = X[iYaN, ic]
                    # PRI - October 2019
                    # replace numpy.percentile() with Python translation of MATLAB/Octave
                    # prctile() and quantile() functions.
                    yN, yX = myprctile(y, numpy.array([25, 75]))
                    IQR[ic] = yX - yN
        else:
            if nd == 3:
                nr, nc, nq = X.shape
                IQR = numpy.full((nc, nq), numpy.nan)
                for iq in range(nq):
                    for ic in range(nc):
                        iYaN = numpy.where(~numpy.isnan(X[:, ic, iq]))[0]
                        nYaN = len(iYaN)
                        if nYaN > 3:
                            y = X[iYaN, ic, iq]
                            # PRI - October 2019
                            # replace numpy.percentile() with Python translation of MATLAB/Octave
                            # prctile() and quantile() functions.
                            yN, yX = myprctile(y, numpy.array([25, 75]))
                            IQR[ic, iq] = yX - yN
    return IQR
