from oneflux_steps.ustar_cp_python.utilities import size, jsondecode, ndims
import numpy as np

def fcReadFields(s : str | dict, field_name : str, *vargs) -> np.ndarray:
    """
    Extracts the specified field from a structured array or JSON string.

    Parameters:
    s: Structured data either as a dictionary or a JSON string.
    field_name (str): Name of the field to extract.

    Returns:
    np.ndarray: Array containing the values of the specified field.
    """
    # Decode the JSON string 
    if isinstance(s, str):
      s_decoded = jsondecode(s)
    else:
      s_decoded = s
    # Computer the number of dimension (minimum 2)
    nd = ndims(s_decoded)
    # Compute the size
    ns = size(s_decoded, b = 0, nargout=2)

    # if s is not a structure array or list then wrap it up into a structured array
    # corresponding to the dimensionality
    if not isinstance(s_decoded, np.ndarray) and not isinstance(s_decoded, list):
        if nd == 2:
          s_struct = np.array([[s_decoded]])
        elif nd == 3:
          s_struct = np.array([[[s_decoded]]])
        else:
          s_struct = s_decoded
    else:
        s_struct = s_decoded

    x = np.full(ns, np.nan)
    if nd == 2:
        for i in range(ns[0]):
            for j in range(ns[1]):
                tmp = s_struct[i][j].get(field_name, np.nan)
                if tmp is not None:
                    x[i, j] = tmp
    elif nd == 3:
        for i in range(ns[0]):
            for j in range(ns[1]):
                for k in range(ns[2]):
                    tmp = s_struct[i][j][k].get(field_name, np.nan)
                    if tmp is not None:
                        x[i, j, k] = tmp
    return x