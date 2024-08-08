# Generated with SMOP  0.41-beta
from .libsmop import *

# ../ONEFlux/oneflux_steps/ustar_cp/fcEqnAnnualSine.m


@function
def fcEqnAnnualSine(b=None, t=None, *args, **kwargs):
    varargin = fcEqnAnnualSine.varargin
    nargin = fcEqnAnnualSine.nargin

    nDaysPerYr = datenum(2000 - 1, 12, 31) / 2000
    # ../ONEFlux/oneflux_steps/ustar_cp/fcEqnAnnualSine.m:3
    Omega = dot(2, pi) / nDaysPerYr
    # ../ONEFlux/oneflux_steps/ustar_cp/fcEqnAnnualSine.m:4
    y = b(1) + dot(b(2), sin(dot(Omega, (t - b(3)))))


# ../ONEFlux/oneflux_steps/ustar_cp/fcEqnAnnualSine.m:5
