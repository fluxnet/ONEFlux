# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_nPerBin.m

    
@function
def get_nPerBin(t=None,*args,**kwargs):
    varargin = get_nPerBin.varargin
    nargin = get_nPerBin.nargin

    nPerDay=get_nPerDay(t)
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_nPerBin.m:3
    if 24 == nPerDay:
        nPerBin=3
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_nPerBin.m:7
    else:
        if 48 == nPerDay:
            nPerBin=5
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_nPerBin.m:9
        else:
            nPerBin=5
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/get_nPerBin.m:11
    
    return nPerBin
    
if __name__ == '__main__':
    pass
    