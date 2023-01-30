'''
For license information:
see LICENSE file or headers in oneflux.__init__.py

Context file for tests; import resolution when path not set

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''
import sys

# support execution without package set (e.g., call unittest from command line)
if __package__ is None:
    import os
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)

import oneflux
