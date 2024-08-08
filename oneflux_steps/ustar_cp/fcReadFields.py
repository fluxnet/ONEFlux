# Generated with SMOP  0.41-beta
from .libsmop import *

# ../ONEFlux/oneflux_steps/ustar_cp/fcReadFields.m


@function
def fcReadFields(s=None, FieldName=None, *args, **kwargs):
    varargin = fcReadFields.varargin
    nargin = fcReadFields.nargin

    nd = ndims(s)
    # ../ONEFlux/oneflux_steps/ustar_cp/fcReadFields.m:3
    ns = size(s)
    # ../ONEFlux/oneflux_steps/ustar_cp/fcReadFields.m:3
    x = dot(NaN, ones(ns))
    # ../ONEFlux/oneflux_steps/ustar_cp/fcReadFields.m:3
    if 2 == nd:
        for i in arange(1, ns(1)).reshape(-1):
            for j in arange(1, ns(2)).reshape(-1):
                tmp = getfield(s, cellarray([i, j]), FieldName)
                # ../ONEFlux/oneflux_steps/ustar_cp/fcReadFields.m:9
                if logical_not(isempty(tmp)):
                    x[i, j] = tmp
    # ../ONEFlux/oneflux_steps/ustar_cp/fcReadFields.m:10
    else:
        if 3 == nd:
            for i in arange(1, ns(1)).reshape(-1):
                for j in arange(1, ns(2)).reshape(-1):
                    for k in arange(1, ns(3)).reshape(-1):
                        tmp = getfield(s, cellarray([i, j, k]), FieldName)
                        # ../ONEFlux/oneflux_steps/ustar_cp/fcReadFields.m:17
                        if logical_not(isempty(tmp)):
                            x[i, j, k] = tmp


# ../ONEFlux/oneflux_steps/ustar_cp/fcReadFields.m:18
