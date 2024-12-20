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
    yy,mm,dd,hh,mmn,ss = u.datevec(t[iYaN]) # numpy.array([dt0 + datetime.timedelta(tt - 1) for tt in t[iYaN]])
    y[iYaN] = yy # numpy.array([dt.year for dt in dt00]) - yr0
    m[iYaN] = mm # numpy.array([dt.month for dt in dt00])
    d[iYaN] = dd #  numpy.array([dt.day for dt in dt00])
    h[iYaN] = hh # numpy.array([dt.hour for dt in dt00])
    mn[iYaN] = mmn # numpy.array([dt.minute for dt in dt00])
    s[iYaN] = ss # numpy.array([dt.second for dt in dt00])
    # index of midnights
    idx = numpy.where((h == 0) & (mn == 0) & (s == 0))[0]
    y2400,m2400,d2400,_,_,_ = u.datevec(t[idx]-1) # numpy.array([dt00[i] - datetime.timedelta(1) for i in idx])
    y[idx] = y2400 # numpy.array([dt.year for dt in dt24]) - yr0
    m[idx] = m2400 # numpy.array([dt.month for dt in dt24])
    d[idx] = d2400 # numpy.array([dt.day for dt in dt24])
    h[idx] = 24
    if scalar_input:
        # convert back to scalar
        return numpy.ndarray.item(y), numpy.ndarray.item(m), numpy.ndarray.item(d), \
               numpy.ndarray.item(h), numpy.ndarray.item(mn), numpy.ndarray.item(s)
    else:
        return y, m, d, h, mn, s
