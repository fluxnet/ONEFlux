# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_itNee.m


@function
def get_itNee(NEE=None, uStar=None, T=None, iNight=None, *args, **kwargs):
    varargin = get_itNee.varargin
    nargin = get_itNee.nargin

    itNee = find(logical_not(isnan(NEE + uStar + T)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_itNee.m:3
    itNee = intersect(itNee, iNight)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_itNee.m:5
    return itNee


if __name__ == "__main__":
    pass
