# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/validate_inputs.m


@function
def validate_inputs(Fmax=None, n=None):
    globals().update(load_all_vars())

    # validate_inputs checks if Fmax and n are valid inputs.
    isValid = logical_not((isnan(Fmax) or isnan(n) or n < 10))
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/validate_inputs.m:3
    return isValid


if __name__ == "__main__":
    pass
