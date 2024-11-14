# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/get_pTable.m


@function
def get_pTable():
    globals().update(load_all_vars())

    # get_pTable returns the significance levels.
    pTable = concat([0.9, 0.95, 0.99]).T
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/get_pTable.m:3
    return pTable


if __name__ == "__main__":
    pass
