import numpy
import scipy
import scipy.stats

def cpdFmax2pCp3(Fmax, n):
    """
    p = cpdFmax2pCp3(Fmax,n)
    assigns the probability p that the 3-parameter,
    diagnostic change-point model fit is significant.
    It interpolates within a Table pTable, generated
    for the 3-parameter model by Wang (2003).
    If Fmax is outside the range in the table,
    then the normal F stat is used to help extrapolate.
    Functions called: stats toolbox - fcdf, finv
    Written by Alan Barr April 2010
    """
    p = numpy.nan
    if numpy.isnan(Fmax) or numpy.isnan(n) or n < 10:
        return p
    pTable = numpy.array([0.9, 0.95, 0.99])
    np = len(pTable)
    nTable = numpy.concatenate([numpy.arange(10, 110, 10),
                                numpy.arange(150, 600, 50),
                                numpy.arange(600, 1200, 200),
                                numpy.arange(2500, 3500, 1000)])
    FmaxTable = numpy.array([[11.646, 15.559, 28.412],
                             [9.651, 11.948, 18.043],
                             [9.379, 11.396, 16.249],
                             [9.261, 11.148, 15.75],
                             [9.269, 11.068, 15.237],
                             [9.296, 11.072, 15.252],
                             [9.296, 11.059, 14.985],
                             [9.341, 11.072, 15.013],
                             [9.397, 11.08, 14.891],
                             [9.398, 11.085, 14.874],
                             [9.506, 11.127, 14.828],
                             [9.694, 11.208, 14.898],
                             [9.691, 11.31, 14.975],
                             [9.79, 11.406, 14.998],
                             [9.794, 11.392, 15.044],
                             [9.84, 11.416, 14.98],
                             [9.872, 11.474, 15.072],
                             [9.929, 11.537, 15.115],
                             [9.955, 11.552, 15.086],
                             [9.995, 11.549, 15.164],
                             [10.102, 11.673, 15.292],
                             [10.169, 11.749, 15.154],
                             [10.478, 12.064, 15.519]])
    FmaxCritical = numpy.full(np, numpy.nan)
    for ip in numpy.arange(np):
        interp_func = scipy.interpolate.PchipInterpolator(nTable, FmaxTable[:, ip])
        FmaxCritical[ip] = interp_func(n)
    if Fmax < FmaxCritical[0]:
        fAdj = (scipy.stats.f.ppf(0.95, 3, n)*Fmax) / FmaxCritical[0]
        p = 2*(1 - scipy.stats.f.cdf(fAdj, 3, n))
        if p > 1:
            p = 1
        return p
    if Fmax > FmaxCritical[-1]:
        fAdj = (scipy.stats.f.ppf(0.995, 3, n)*Fmax) / FmaxCritical[2]
        p = 2*(1 - scipy.stats.f.cdf(fAdj, 3, n))
        if p < 0:
            p = 0
        return p
    interp_func = scipy.interpolate.PchipInterpolator(FmaxCritical, 1 - pTable)
    p = interp_func(Fmax)
    return numpy.asscalar(p)
