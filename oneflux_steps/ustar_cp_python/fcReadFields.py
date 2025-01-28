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
    nd = ndims(s)
    ns = size(s, b = 0, nargout=2)
    print(ns)
    print("nd: ", nd)
    print("len s: ", len(s))
    # if s is not a structure array then wrap it up into a structure array
    if not isinstance(s, np.ndarray):
        s = np.array([s])

    print("s[0] = ", s[0])
    print("s[0][0] = ", s[0][0])
    x = np.full(ns, np.nan)
    if nd == 2:
        print("nd == 2")
        for i in range(ns[0]):
            for j in range(ns[1]):
                print( s[i][j].get(field_name))
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