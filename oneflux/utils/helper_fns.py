'''
oneflux.utils.helper_fns

For license information:
see LICENSE file or headers in oneflux.__init__.py 

Comparison helper functions

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''

def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def islessthan(a, b):
    return (not isclose(a, b) and a < b)
