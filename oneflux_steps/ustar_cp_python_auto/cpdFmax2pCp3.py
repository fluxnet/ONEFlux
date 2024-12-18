# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m


@function
def cpdFmax2pCp3(Fmax=None, n=None):
    globals().update(load_all_vars())

    # cpdFmax2pCp3 calculates the probability p that the 3-parameter
    # diagnostic change-point model fit is significant.

    # Validate inputs
    if logical_not(validate_inputs(Fmax, n)):
        p = copy(NaN)
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:7
        return p

    # Get data tables
    pTable = get_pTable()
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:12
    nTable = get_nTable()
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:13
    FmaxTable = get_FmaxTable()
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:14

    FmaxCritical = interpolate_FmaxCritical(n, nTable, FmaxTable)
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:17

    if Fmax < take(FmaxCritical, 1):
        p = calculate_p_low(Fmax, take(FmaxCritical, 1), n)
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:21
    else:
        if Fmax > take(FmaxCritical, 3):
            p = calculate_p_high(Fmax, take(FmaxCritical, 3), n)
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:23
        else:
            p = calculate_p_interpolate(Fmax, FmaxCritical, pTable)
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:25

    return p


if __name__ == "__main__":
    pass
