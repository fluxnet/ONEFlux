# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/calculate_p_interpolate.m


@function
def calculate_p_interpolate(Fmax=None, FmaxCritical=None, pTable=None):
    globals().update(load_all_vars())

    # calculate_p_interpolate calculates p using interpolation.
    p = interp1(FmaxCritical, 1 - pTable, Fmax, "pchip")
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/calculate_p_interpolate.m:2
    return p


if __name__ == "__main__":
    pass
