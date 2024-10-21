# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_ntN.m


@function
def get_ntN(t=None, nSeasons=None):
    nStrataN = 4
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_ntN.m:3

    nBins = 50
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_ntN.m:4

    nPerBin = get_nPerBin(t)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_ntN.m:6

    nPerSeason = dot(dot(nStrataN, nBins), nPerBin)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_ntN.m:9
    ntN = dot(nSeasons, nPerSeason)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_ntN.m:10
    return ntN


if __name__ == "__main__":
    pass
