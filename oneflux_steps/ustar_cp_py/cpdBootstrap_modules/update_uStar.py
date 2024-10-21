# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/update_uStar.m


@function
def update_uStar(uStar=None):
    updated_ustar = copy(uStar)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/update_uStar.m:3

    iOut = find(uStar < logical_or(0, uStar) > 4)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/update_uStar.m:4
    updated_ustar[iOut] = NaN
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/update_uStar.m:5

    return updated_ustar


if __name__ == "__main__":
    pass
