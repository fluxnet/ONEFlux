from datetime import datetime as dt
from datetime import timedelta as td
from math import ceil

def mydatenum(Y, M, D, h, m, s):
    # A zero month is interpreted as 1
    if M == 0:
        M = 1
    # trap_Y0 = False
    # Y_adjust = 0
    # if Y == 0:
    #     trap_Y0 = True
    #     Y_adjust = Y
    #     Y = 1
    if Y < 0:
        # If the year is negative, treat it as if we are in
        # the year 1
        d = dt(1, M, D, h, m, s)
        # The subtract days for each negative year
        # (note Y is negative here)
        dn = d.toordinal() + Y*365
        # plus leap year corrections
        dn = dn + ceil(Y / 4)
    else:
        d = dt(Y + 1, M, D, h, m, s)
        dn = d.toordinal() + 1
    return dn
