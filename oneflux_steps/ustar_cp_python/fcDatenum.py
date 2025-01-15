from datetime import datetime as dt
from datetime import timedelta as td
from math import ceil, floor
from numpy import vectorize

def datenum(Y, M, D):
    """
    Convert date to serial date number.

    This function converts a given date specified by year (Y), month (M), and day (D)
    into a serial date number. The serial date number is the number of days since a 
    fixed starting point: January 1st 1 AD.

    Parameters:
    Y (int): Year of the date. Can be negative for years BC.
    M (int): Month of the date. If 0, it is interpreted as January.
    D (int): Day of the date. If 0, it is interpreted as the last day of the previous month.

    Returns:
    int: Serial date number corresponding to the input date.

    Notes:
    - Year 0 is treated as a leap year.
    - If the day (D) is 0, it is adjusted to the last day of the previous month.
    - If the month (M) is 0, it is adjusted to January.
    - Negative years are treated as if they are in the year 1 AD, with adjustments for leap years.

    Examples:
    >>> datenum(2023, 10, 5)
    739164
    >>> datenum(0, 3, 1)
    61
    >>> datenum(-1, 12, 31)
    0
    >>> datenum(0,24,31)
    731
    >>> datenum(1,24,31)
    1096
    """
    # mimic MATLAB's ability to handle scalar or vector inputs
    if (hasattr(Y, "__len__") and len(Y) > 0 and hasattr(Y[0], "__len__")):
        # Input is 2-Dimensional, so vectorise ourselves
        return vectorize(datenum)(Y,M,D)

    adjustment = td()
    # A zero day means we need to subtract one day
    if D == 0:
      adjustment = td(-1)
      D = 1
    # A zero month is interpreted as 1
    if M == 0:
      M = 1

    # Treat year 0 (Y = 0) as a leap year, so we must
    # add the leap day from Y = 0 if we are after the
    # first leap day (Feb 29th of Year 0)
    if (Y >= 1) | (Y == 0) & (M > 2):
      adjustment = adjustment + td(1)

    if Y < 0:
        # If the year is negative, treat it as if we are in
        # the year 1
        d = dt(1, M, D, 0, 0, 0)
        # The subtract days for each negative year
        # (note Y is negative here)
        dn = d.toordinal() + Y*365
        # plus leap year corrections
        dn = dn + ceil(Y / 4)
    else:
        d = dt(Y + 1, M, D, 0, 0, 0)
        dn = d.toordinal()

    # turn adjustment (timedelta) in a number of days
    return dn + adjustment.days
