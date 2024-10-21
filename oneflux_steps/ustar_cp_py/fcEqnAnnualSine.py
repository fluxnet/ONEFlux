# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/fcEqnAnnualSine.m


@function
def fcEqnAnnualSine(b=None, t=None):
    nDaysPerYr = datenum(2000 - 1, 12, 31) / 2000
    # oneflux_steps/ustar_cp_refactor_wip/fcEqnAnnualSine.m:3
    Omega = dot(2, pi) / nDaysPerYr
    # oneflux_steps/ustar_cp_refactor_wip/fcEqnAnnualSine.m:4
    y = b[1] + dot(b[2], sin(dot(Omega, (t - b[3]))))


# oneflux_steps/ustar_cp_refactor_wip/fcEqnAnnualSine.m:5
