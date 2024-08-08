# Generated with SMOP  0.41-beta
from .libsmop import *

# ../ONEFlux/oneflux_steps/ustar_cp/fcx2colvec.m


@function
def fcx2colvec(x=None, *args, **kwargs):
    varargin = fcx2colvec.varargin
    nargin = fcx2colvec.nargin

    # 	fcx2colvec(x) converts an array x to an n x 1 column vector cv

    cv = reshape(x, numel(x), 1)


# ../ONEFlux/oneflux_steps/ustar_cp/fcx2colvec.m:5
