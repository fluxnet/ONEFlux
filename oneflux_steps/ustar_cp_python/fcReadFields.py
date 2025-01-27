from oneflux_steps.ustar_cp_python.utils import *

# @function
# def fcReadFields(s=None, FieldName=None):
#     globals().update(load_all_vars())

#     nd = ndims(s)
#     # oneflux_steps/ustar_cp_refactor_wip/fcReadFields.m:3
#     ns = size(s)
#     # oneflux_steps/ustar_cp_refactor_wip/fcReadFields.m:3
#     x = matlabarray(dot(NaN, ones(ns)))
#     # oneflux_steps/ustar_cp_refactor_wip/fcReadFields.m:3
#     if 2 == nd:
#         for i in arange(1, take(ns, 1)).reshape(-1):
#             for j in arange(1, take(ns, 2)).reshape(-1):
#                 tmp = getfield(s, cellarray([i, j]), FieldName)
#                 # oneflux_steps/ustar_cp_refactor_wip/fcReadFields.m:9
#                 if logical_not(isempty(tmp)):
#                     x[i, j] = tmp
#     # oneflux_steps/ustar_cp_refactor_wip/fcReadFields.m:10
#     else:
#         if 3 == nd:
#             for i in arange(1, take(ns, 1)).reshape(-1):
#                 for j in arange(1, take(ns, 2)).reshape(-1):
#                     for k in arange(1, take(ns, 3)).reshape(-1):
#                         tmp = getfield(s, cellarray([i, j, k]), FieldName)
#                         # oneflux_steps/ustar_cp_refactor_wip/fcReadFields.m:17
#                         if logical_not(isempty(tmp)):
#                             x[i, j, k] = tmp
#     # oneflux_steps/ustar_cp_refactor_wip/fcReadFields.m:18

#     return x

import numpy as np

def fcReadFields(s, field_name, *vargs):
    """
    Extracts the specified field from a structured array.

    Parameters:
    s (array-like): Structured array.
    field_name (str): Name of the field to extract.

    Returns:
    np.ndarray: Array containing the values of the specified field.
    """
    s = jsondecode(s)
    nd = np.ndim(s)
    ns = np.shape(s)
    x = np.full(ns, np.nan)
    error(s[0][0])
    if nd == 2:
        for i in range(ns[0]):
            for j in range(ns[1]):
                print( s[i][j].get(field_name))
                fail(s[i][j].get(field_name))
                tmp = getfield(s, cellarray([i, j]), FieldName) # s[i][j].get(field_name, np.nan)
                if tmp is not None:
                    x[i, j] = tmp
    elif nd == 3:
        for i in range(ns[0]):
            for j in range(ns[1]):
                for k in range(ns[2]):
                    tmp = getfield(s, cellarray([i, j, k]), FieldName) # s[i][j][k].get(field_name, np.nan)
                    if tmp is not None:
                        x[i, j, k] = tmp
    return x