import numpy

def myprctile(Y, q):
    """
    Stripped down version of Octave prctile.m
    """
    Q = myquantile(Y, q/float(100))
    return Q

def myquantile(x, p, method=5):
    """
    Stripped down version of Octave quantile.m;
     - assumes x is 1D
     - assumes 0 <= p[i] <= 1
     - only implements the switch case (method) 5
    """
    x = numpy.sort(x)
    m = numpy.sum(~numpy.isnan(x))
    mm = numpy.full(len(p), m)
    # we are only dealing with 1D vectors so xc=0 and xr*(0:xc-1)=0
    pcd = numpy.full(len(p), 0)
    p = numpy.kron(p, m) + 0.5
    pi = numpy.maximum(numpy.minimum(numpy.floor(p), mm-1), 1)
    pr = numpy.maximum(numpy.minimum(p - pi, 1), 0)
    pi = pi + pcd
    inv = numpy.multiply((1-pr), x[pi.astype(int)-1]) + numpy.multiply(pr, x[pi.astype(int)])
    return inv
