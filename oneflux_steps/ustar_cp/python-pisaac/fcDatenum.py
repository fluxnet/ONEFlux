from datetime import datetime as dt
from datetime import timedelta as td

def mydatenum(Y, M, D, h, m, s):
    trap_Y0 = False
    if Y == 0:
        trap_Y0 = True
        Y = 1
    d = dt(Y, M, D, h, m, s)
    if trap_Y0:
        dn = 1 + d.toordinal() + (d - dt.fromordinal(d.toordinal())).total_seconds()/(24*60*60)
    else:
        dn = 366 + d.toordinal() + (d - dt.fromordinal(d.toordinal())).total_seconds()/(24*60*60)
    return dn
