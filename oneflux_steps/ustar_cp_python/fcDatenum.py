from datetime import datetime as dt
from datetime import timedelta as td
from math import ceil

def mydatenum(Y, M, D):

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
