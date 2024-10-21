# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/fcx2rowvec.m


@function
def myrv(x=None, *args, **kwargs):
    varargin = myrv.varargin
    nargin = myrv.nargin

    rv = reshape(x, 1, prod(size(x)))


# oneflux_steps/ustar_cp_refactor_wip/fcx2rowvec.m:3
