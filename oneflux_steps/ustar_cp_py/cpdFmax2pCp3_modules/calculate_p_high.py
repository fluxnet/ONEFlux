# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/calculate_p_high.m


@function
def calculate_p_high(Fmax=None, FmaxCritical_high=None, n=None):
    globals().update(load_all_vars())

    # calculate_p_high calculates p when Fmax is above the highest critical value.
    fAdj = dot(finv(0.995, 3, n), Fmax) / FmaxCritical_high
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/calculate_p_high.m:3
    p = dot(2, (1 - fcdf(fAdj, 3, n)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/calculate_p_high.m:4
    p = max(p, 0)
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/calculate_p_high.m:5
    return p


if __name__ == "__main__":
    pass
