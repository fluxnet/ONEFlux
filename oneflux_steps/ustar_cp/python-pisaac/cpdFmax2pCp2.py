import numpy
import scipy
import scipy.stats

def cpdFmax2pCp2(Fmax, n):
    """
    p = cpdFmax2pCp2(Fmax,n)
    assigns the probability p that the 2-parameter,
    operational change-point model fit is significant.
    It interpolates within a Table pTable, generated
    for the 2-parameter model by Alan Barr following Wang (2003).
    If Fmax is outside the range in the table,
    then the normal F stat is used to help extrapolate.
    Functions called: stats toolbox - fcdf, finv
    Written by Alan Barr April 2010
    """
    p = numpy.nan
    if numpy.isnan(Fmax) or numpy.isnan(n) or n < 10:
        return p
    pTable = numpy.array([0.8, 0.9, 0.95, 0.99])
    np = len(pTable)
    nTable = numpy.array([10, 15, 20, 30, 50, 70, 100, 150, 200, 300, 500, 700, 1000])
    FmaxTable = numpy.array([[3.9293, 6.2992, 9.1471, 18.2659],
                             [3.7734, 5.6988, 7.877, 13.81],
                             [3.7516, 5.5172, 7.4426, 12.6481],
                             [3.7538, 5.3224, 7.0306, 11.4461],
                             [3.7941, 5.303, 6.8758, 10.6635],
                             [3.8548, 5.348, 6.8883, 10.5026],
                             [3.9798, 5.4465, 6.9184, 10.4527],
                             [4.0732, 5.5235, 6.9811, 10.3859],
                             [4.1467, 5.6136, 7.0624, 10.5596],
                             [4.277, 5.7391, 7.2005, 10.6871],
                             [4.4169, 5.8733, 7.3421, 10.6751],
                             [4.5556, 6.0591, 7.5627, 11.0072],
                             [4.7356, 6.2738, 7.7834, 11.2319]])
    FmaxCritical = numpy.full(np, numpy.nan)
    for ip in numpy.arange(np):
        interp_func = scipy.interpolate.PchipInterpolator(nTable, FmaxTable[:, ip])
        FmaxCritical[ip] = interp_func(n)
    if Fmax < FmaxCritical[0]:
        fAdj = (scipy.stats.f.ppf(0.9, 3, n)*Fmax) / FmaxCritical[0]
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
