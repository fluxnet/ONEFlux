# Generated with SMOP  0.41-beta
from .libsmop import *

# ../ONEFlux/oneflux_steps/ustar_cp/fcx2rowvec.m


@function
def myrv(x=None, *args, **kwargs):
    varargin = myrv.varargin
    nargin = myrv.nargin

    rv = reshape(x, 1, prod(size(x)))


# ../ONEFlux/oneflux_steps/ustar_cp/fcx2rowvec.m:3
