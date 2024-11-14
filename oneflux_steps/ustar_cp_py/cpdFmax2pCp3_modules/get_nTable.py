# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/get_nTable.m


@function
def get_nTable():
    globals().update(load_all_vars())

    # get_nTable returns the sample sizes.
    nTable = concat([arange(10, 100, 10), arange(150, 600, 50), 800, 1000, 2500]).T
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/get_nTable.m:3
    return nTable


if __name__ == "__main__":
    pass
