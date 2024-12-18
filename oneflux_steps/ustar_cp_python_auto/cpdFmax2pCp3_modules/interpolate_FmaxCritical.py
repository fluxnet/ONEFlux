# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/interpolate_FmaxCritical.m


@function
def interpolate_FmaxCritical(n=None, nTable=None, FmaxTable=None):
    globals().update(load_all_vars())

    # interpolate_FmaxCritical interpolates critical Fmax values for the given n.
    FmaxCritical = matlabarray(zeros(1, 3))
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/interpolate_FmaxCritical.m:3
    for ip in arange(1, 3).reshape(-1):
        FmaxCritical[ip] = interp1(nTable, FmaxTable[:, ip], n, "pchip")
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/interpolate_FmaxCritical.m:5

    return FmaxCritical


if __name__ == "__main__":
    pass
