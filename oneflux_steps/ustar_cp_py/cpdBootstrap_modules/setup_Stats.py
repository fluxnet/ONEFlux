# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m


@function
def setup_Stats(nBoot=None, nSeasons=None, nStrataX=None, *varargin):
    globals().update(load_all_vars())

    nargin = len(varargin)

    StatsMT = generate_statsMT()
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m:3

    # This function will return different outputs for the case where any of
    # nBoot, nSeasons or nStrataX are zero, depending on whether 'Stats' is
    # preallocated with 'StatsMT' or not.
    # This does not affect the normal running of the code. Just this edge case.

    # We should follow up with Gilberto to understand his preferred implementation.
    # James Emberton 21/10/2024

    # Preallocate the Stats array by repeating the template
    try:
        Stats
    except:
        Stats = cellarray()
    Stats[1:nSeasons, 1:nStrataX, 1:nBoot] = StatsMT
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m:16
    for i in arange(1, length(varargin)).reshape(-1):
        a = take(varargin, i)
        # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m:20
        if iscell(a) and strcmp(take(a, 1), "jsonencode"):
            for j in arange(2, length(a)).reshape(-1):
                if 1 == take(a, j):
                    Stats = jsonencode(Stats)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m:25

    return Stats


if __name__ == "__main__":
    pass
