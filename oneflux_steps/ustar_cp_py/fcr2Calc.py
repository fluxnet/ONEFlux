# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/fcr2Calc.m


@function
def r2Calc(y=None, yHat=None, *args, **kwargs):
    varargin = r2Calc.varargin
    nargin = r2Calc.nargin

    n = length(y)
    # oneflux_steps/ustar_cp_refactor_wip/fcr2Calc.m:3
    ym = mean(y)
    # oneflux_steps/ustar_cp_refactor_wip/fcr2Calc.m:3
    SSreg = sum((yHat - ym) ** 2)
    # oneflux_steps/ustar_cp_refactor_wip/fcr2Calc.m:5
    SStotal = sum((y - ym) ** 2)
    # oneflux_steps/ustar_cp_refactor_wip/fcr2Calc.m:6
    rmse = sum((yHat - y) ** 2)
    # oneflux_steps/ustar_cp_refactor_wip/fcr2Calc.m:7
    r2 = SSreg / SStotal


# oneflux_steps/ustar_cp_refactor_wip/fcr2Calc.m:8
# # #    sprintf('#7.4f #7.4f #7.4f ',[SSreg SStotal r2 rmse])
