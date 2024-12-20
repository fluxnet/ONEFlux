import datetime
import numpy

import oneflux_steps.ustar_cp_python.utils as u

def fcDatevec(t):
    """
    function [y,m,d,h,mn,s]=mydatevec(t)
    was written by Alan Barr to return 2400 UTC rather than 0000 UTC.
    NOTE:
     This function has been rewritten to preserve the intent of
     the original code (as received from Carlo Trotti).  Under Octave,
     the original code did not work as expected.  For a 30 minute time
     step, the Octave "datevec" routine returned minutes as 29 or 59
     with seconds as 60!  This meant that 00:00 was never converted t0
     24:00 the previous day as intended.
     This function converts times of 00:00 to 24:00 the previous day.
    """
    # use year 2000 as an offset, this is needed because MATLAB will accept
    # year = 0 but Python will not (year >= 1)
    # also, MATLAB treats year = 0 as a leap year, so we choose a year offset
    # that is also a leap year
    yr0 = 2000
    # mimic MATLAB's ability to handle scalar or vector inputs
    t = numpy.asarray(t)
    scalar_input = False
    if t.ndim == 0:
        t = t[None]  # Makes x 1D
        scalar_input = True
    # do the business
    iYaN = numpy.where(~numpy.isnan(t))[0]
    y = numpy.full(len(t), numpy.nan)
    m = y.copy()
    d = y.copy()
    h = y.copy()
    mn = y.copy()
    s = y.copy()
    dt0 = datetime.datetime(yr0, 1, 1)

    dt00 = numpy.array([dt0 + datetime.timedelta(int(tt) - 1) for tt in t[iYaN]])
    y[iYaN] = numpy.array([dt.year for dt in dt00]) - yr0
    m[iYaN] = numpy.array([dt.month for dt in dt00])
    d[iYaN] = numpy.array([dt.day for dt in dt00])
    h[iYaN] = numpy.array([dt.hour for dt in dt00])
    mn[iYaN] = numpy.array([dt.minute for dt in dt00])
    s[iYaN] = numpy.array([dt.second for dt in dt00])
    # index of midnights
    idx = numpy.where((h == 0) & (mn == 0) & (s == 0))[0]
    
    #dt24 = numpy.array([dt00[i] - datetime.timedelta(1) for i in idx])
    m[idx] = m[idx] - (1 + y[idx])
    d[idx] = numpy.array([dt.day for dt in dt00]) - 1
    # y[idx] = y2400 # numpy.array([dt.year for dt in dt24]) - yr0
    # m[idx] = m2400 # numpy.array([dt.month for dt in dt24])
    # d[idx] = d2400 # numpy.array([dt.day for dt in dt24])

    h[idx] = 24
    if scalar_input:
        # convert back to scalar
        return numpy.ndarray.item(y), numpy.ndarray.item(m), numpy.ndarray.item(d), \
                numpy.ndarray.item(h), numpy.ndarray.item(mn), numpy.ndarray.item(s)
    else:
        return y, m, d, h, mn, s
