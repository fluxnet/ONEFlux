# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Cp.m


@function
def setup_Cp(nSeasons=None, nStrataX=None, nBoot=None, *args, **kwargs):
    varargin = setup_Cp.varargin
    nargin = setup_Cp.nargin

    Cp = dot(NaN, ones(nSeasons, nStrataX, nBoot))
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Cp.m:3
    return Cp


if __name__ == "__main__":
    pass
