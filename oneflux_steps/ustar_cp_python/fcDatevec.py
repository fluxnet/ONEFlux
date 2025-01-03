import datetime
import numpy

def fcDatevec(t : numpy.ndarray) -> tuple:
    """
      Parameters:
      - t: A scalar or vector of time values in days since year 2000 (or any other leap year)
      Returns:
      - y: A scalar or vector of years.
      - m: A scalar or vector of months.
      - d: A scalar or vector of days.
      - h: A scalar or vector of hours.
      - mn: A scalar or vector of minutes.
      - s: A scalar or vector of seconds.

    function [y,m,d,h,mn,s]=mydatevec(t)
    was written by Alan Barr to return 2400 UTC rather than 0000 UTC.
    NOTE:
     This function has been rewritten to preserve the intent of
     the original code (as received from Carlo Trotti).
     This function converts times of 00:00 to 24:00 the previous day.
    """
    # mimic MATLAB's ability to handle scalar or vector inputs
    t = numpy.asarray(t)
    # Quantise the input to the granularity of 0.0001 seconds in a day
    hundredmicrosecond_days = 1.1574074074074074e-09
    t = numpy.round(t / hundredmicrosecond_days) * hundredmicrosecond_days

    scalar_input = False
    if t.ndim == 0: # | t.ndim == 1:
        t = t[None]  # Makes x 1D
        scalar_input = True

    # use year 2000 as an offset, this is needed because MATLAB will accept
    # year = 0 but Python will not (year >= 1)
    # also, MATLAB treats year = 0 as a leap year, so we choose a year offset
    # that is also a leap year

    yr0 = 2000

    # Create base set of numpy arrays for the output date
    iYaN = numpy.where(~numpy.isnan(t))[0]
    y = numpy.full(len(t), numpy.nan)
    m = y.copy()
    d = y.copy()
    h = y.copy()
    mn = y.copy()
    s = y.copy()

    # Initial time basis
    dt0 = datetime.datetime(yr0, 1, 1)
    dt00 = numpy.array([dt0 + datetime.timedelta(float(tt) - 1) for tt in t[iYaN]])

    # Extract the date components
    y[iYaN] = numpy.array([dt.year for dt in dt00]) - yr0
    m[iYaN] = numpy.array([dt.month for dt in dt00])
    d[iYaN] = numpy.array([dt.day for dt in dt00])
    h[iYaN] = numpy.array([dt.hour for dt in dt00])
    mn[iYaN] = numpy.array([dt.minute for dt in dt00])
    s[iYaN] = numpy.array([dt.second + dt.microsecond/1E6 for dt in dt00])

    # Handle midnights

    # index of midnights
    idx = numpy.where((h == 0) & (mn == 0) & (s == 0))[0]
    for ix in idx:
        # If we are at the start of the month we need to go back t
        # the last day of the previous month
        if (d[ix] == 1) & (m[ix] != 0):
            m[ix] -= 1
            if m[ix] == 0:
                m[ix] = 12
                y[ix] -= 1
            # Get the number of days in the previous month
            d[ix] = (datetime.datetime(int(y[ix]) + yr0 + int(m[ix] / 12), (int(m[ix]) + 1) % 12, 1)
                      - datetime.datetime(int(y[ix]) + yr0, int(m[ix]), 1)).days
        else:
            d[ix] -= 1

        # Set the hour to 24
        h[ix] = 24

    # Handle the case where the time is 00:00
    for ix in iYaN:
        # If the time is 00:00 then year is -1
        if t[ix] == 0:
            y[ix] = -1
        else:
            # If the day is between 0 and 1 then we set the year to 0
            # and the month and day to 0
            if (t[ix] > 0) & (t[ix] <= 1):
              y[ix] = 0
              m[ix] = 0
              d[ix] = 0

    if scalar_input:
        # convert back to scalar
        return numpy.ndarray.item(y), numpy.ndarray.item(m), numpy.ndarray.item(d), \
                numpy.ndarray.item(h), numpy.ndarray.item(mn), numpy.ndarray.item(s)
    else:
        return y, m, d, h, mn, s
