# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_nPerDay.m


@function
def get_nPerDay(t=None):
    nPerDay = round(1 / nanmedian(diff(t)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_nPerDay.m:2
    return nPerDay


if __name__ == "__main__":
    pass
