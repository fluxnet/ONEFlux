# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/fcx2rowvec.m


@function
def myrv(x=None):
    globals().update(load_all_vars())

    rv = reshape(x, 1, prod(size(x)))
    # oneflux_steps/ustar_cp_refactor_wip/fcx2rowvec.m:3
    return rv
