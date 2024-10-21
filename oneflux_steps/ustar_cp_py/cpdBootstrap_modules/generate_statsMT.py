# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/generate_statsMT.m

    
@function
def generate_statsMT(*args,**kwargs):
    varargin = generate_statsMT.varargin
    nargin = generate_statsMT.nargin

    StatsMT=matlabarray([])
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/generate_statsMT.m:2
    
    StatsMT.n,StatsMT.Cp,StatsMT.Fmax,StatsMT.p,StatsMT.b0,StatsMT.b1,StatsMT.b2,StatsMT.c2,StatsMT.cib0,StatsMT.cib1,StatsMT.cic2,StatsMT.mt,StatsMT.ti,StatsMT.tf,StatsMT.ruStarVsT,StatsMT.puStarVsT,StatsMT.mT,StatsMT.ciT=deal(NaN,nargout=18)
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrap_modules/generate_statsMT.m:6
    return StatsMT
    
if __name__ == '__main__':
    pass
    