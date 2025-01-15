import numpy
from fcDatevec import mydatevec
from fcDatenum import datenum

def mydoy(t):
    """
    doy is a day-of-year function
    that converts the serial date number t to the day of year.
    See datenum for a definition of t.
    doy differs from other formulations in that the last
    period of each day (denoted as 2400 by mydatevec)
    is attributed to the day ending 2400
    rather than the day beginning 0000.
    Original MATLAB code "Written by Alan Barr 2002."
    Rewritten for Python by PRI
    """
    # use year 2000 as an offset, this is needed because MATLAB will accept
    # year = 0 but Python will not (year >= 1)
    # also, MATLAB treats year = 0 as a leap year, so we choose a year offset
    # that is also a leap year
    yr0 = 2000
    Y, M, D, h, m, s = mydatevec(t)
    Y = Y + yr0
    tt = datenum(int(Y), int(M), int(D), 0, 0, 0)
    d = numpy.floor(tt - datenum(int(Y) - 1, 12, 31, 0, 0, 0))
    return d
