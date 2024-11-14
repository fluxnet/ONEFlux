# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/calculate_p_low.m


@function
def calculate_p_low(Fmax=None, FmaxCritical_low=None, n=None):
    globals().update(load_all_vars())

    # calculate_p_low calculates p when Fmax is below the lowest critical value.
    fAdj = dot(finv(0.95, 3, n), Fmax) / FmaxCritical_low
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/calculate_p_low.m:3
    p = dot(2, (1 - fcdf(fAdj, 3, n)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/calculate_p_low.m:4
    p = min(p, 1)
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/calculate_p_low.m:5
    return p


if __name__ == "__main__":
    pass
