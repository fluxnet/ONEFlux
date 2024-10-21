# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m

    
@function
def setup_Stats(nBoot=None,nSeasons=None,nStrataX=None,varargin=None,*args,**kwargs):
    varargin = setup_Stats.varargin
    nargin = setup_Stats.nargin

    StatsMT=generate_statsMT()
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m:3
    
    # This function will return different outputs for the case where any of
	# nBoot, nSeasons or nStrataX are zero, depending on whether 'Stats' is 
	# preallocated with 'StatsMT' or not.
	# This does not affect the normal running of the code. Just this edge case.
    
    # We should follow up with Gilberto to understand his preferred implementation.
	# James Emberton 21/10/2024
    
    # Preallocate the Stats array by repeating the template
    Stats[arange(1,nSeasons),arange(1,nStrataX),arange(1,nBoot)]=StatsMT
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m:16
    if size(varargin) > 0:
        Stats=jsonencode(Stats)
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/setup_Stats.m:18
    