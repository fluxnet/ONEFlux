import numpy as np
#from oneflux_steps.ustar_cp_python.myprctile import myprctile
from oneflux_steps.ustar_cp_python.utils import prctile, transpose

def allNonPositive(dx):
    """
    Helper function that determines whether the input is all zero or negative

    For a scalar this is checking <= 0 for a vector
    it is checking whether all are <= 0
    """
    if hasattr(dx, "__len__") and len(dx) > 0:
        return np.all(dx.flatten() <= 0)
    elif dx <= 0:
        return True
    else:
        return False


def fcBin(x, y, dx, nPerBin):
    """
    fcBin calculates binned mean values of vectors x and y
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

    shrinkFactor = 0 # Used to resize the bins at the end

    if allNonPositive(dx):
        print('Function cpdBin aborted. dx cannot be <=0. ')
        return nBins, mx, my

    # dx is an empty vector
    if hasattr(dx, "__len__") and (len(dx) == 0):
        # bin the data into bins with nPerBin points in each bin.

        # Positions of `x` and `y` where neither is NaN
        # and the number of such positions
        iYaN = np.where(~np.isnan(x + y) == True)[0]
        nYaN = len(iYaN)

        # Number of bins we need is then the non-values / number of points per bin
        nBins = int(np.floor(nYaN / nPerBin))

        # Initialize the output vectors with NaNs
        mx = np.full(nBins, np.nan)
        my = np.full(nBins, np.nan)

        # Calculate the percentile boundaries for the bins
        if nBins == 0:
          # Avoid divide-by-zero
          iprctile = np.array([0])
        else:
          step = 100. / float(nBins)
          iprctile = np.arange(0, 100 + (step / 2.0), step)
          # Clamp each value to 0-100 because np.arrange can give us a value slightly past 100
          iprctile = np.clip(iprctile, 0, 100)

        # Calculate the `x` value at the top of percentile per bin
        dx = prctile(x[iYaN], iprctile)

        # xL has all but last point
        # xU has all but first point
        xL = dx[:-1]
        xU = dx[1:]
        jx = 0

        for i in np.arange(0, len(xL)):
            # indices of all points that should go in bin `jx`
            ix = np.where((~np.isnan(x+y)) & (x >= xL[i]) & (x <= xU[i]))

            # if there are not too many points to go in the bin
            # store the mean of x and y vectors in the bin
            if len(x[ix]) >= nPerBin:
                mx[jx] = np.mean(x[ix])
                my[jx] = np.mean(y[ix])
                jx = jx + 1
            else:
                shrinkFactor += 1

    # dx is a scalar (or single element vector, and not a 2D matrix)
    elif (not(hasattr(dx, "__len__"))) or (hasattr(dx, "__len__") and (len(dx) == 1) and not(hasattr(dx[0], "__len__"))):

        # Find the lower and upper bounds with x
        nx = np.min(x, 0)
        xx = np.max(x, 0)

        # Turn these into the integer values of the bounds
        nx = dx*np.floor(nx / dx)
        xx = dx*np.ceil(xx / dx)

        if hasattr(nx, "__len__"):
            nx = nx[0]
            xx = xx[0]

        mx = np.full(len(np.arange(nx, xx+dx, dx)), np.nan)
        my = np.full(len(np.arange(nx, xx+dx, dx)), np.nan)

        # Iterate through the space with `jx` giving
        # the bottom of the bin value between the lower and
        # upper bounds here, covering `dx` at a time
        shrinkFactor = 0
        for jx in np.arange(nx, xx+dx, dx):

            # indices of all points that should go in this bin:
            # those which arent nan and which lie within the lower half of the bin
            # (which will *throw some data away*)
            ix = np.where(((~np.isnan(x+y)) & (abs(x - jx) < 0.5*dx)))

            # If the number of items that will be extracted here is at least
            # the bin size then we can proceed:
            if len(x[ix]) >= nPerBin:
                mx[nBins] = np.mean(x[ix])
                my[nBins] = np.mean(y[ix])
                nBins = nBins + 1
            else:
                shrinkFactor += 1


    # dx is a vector (with more than one element)
    else:
        xL = dx[:-1]
        xU = dx[1:]
        mx = np.full(len(xL), np.nan)
        my = np.full(len(xL), np.nan)
        shrinkFactor = 0

        for i in np.arange(0, len(xL)):
            ix = np.where((~np.isnan(x+y)) & (x >= xL[i]) & (x <= xU[i]))
            if len(x[ix]) >= nPerBin:
                mx[nBins] = np.mean(x[ix])
                my[nBins] = np.mean(y[ix])
                nBins = nBins + 1
            else:
                shrinkFactor += 1

    # Shrink the mx and my outputs to fit their final size
    if shrinkFactor > 0:
      mx = mx[:-shrinkFactor]
      my = my[:-shrinkFactor]

    return nBins, transpose(mx), transpose(my)
