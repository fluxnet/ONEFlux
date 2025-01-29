# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m


@function
def setup_Stats(nBoot=None, nSeasons=None, nStrataX=None, *varargin):
    globals().update(load_all_vars())

    nargin = len(varargin)

    StatsMT = generate_statsMT()
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m:3
    Stats = copy(StatsMT)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m:5

    # nBoot, nSeasons or nStrataX are zero, depending on whether 'Stats' is
    # preallocated with 'StatsMT' or not.
    # This does not affect the normal running of the code. Just this edge case.

    # We should follow up with Gilberto to understand his preferred implementation.
    # James Emberton 21/10/2024

    # Preallocate the Stats array by repeating the template
    # Discussed with Gilberton on 25/10/2024. Agreed to preserve current implementation.
    # Will review when we are converting to python
    for iBoot in arange(1, nBoot).reshape(-1):
        for iSeason in arange(1, nSeasons).reshape(-1):
            for iStrata in arange(1, nStrataX).reshape(-1):
                Stats[iSeason, iStrata, iBoot] = StatsMT
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m:21

    for i in arange(1, length(varargin)).reshape(-1):
        a = take(varargin, i)
        # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m:27
        if iscell(a) and strcmp(take(a, 1), "jsonencode"):
            for j in arange(2, length(a)).reshape(-1):
                if 1 == take(a, j):
                    Stats = jsonencode(Stats)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m:32

    return Stats
