'''
For license information:
see LICENSE file or headers in oneflux.__init__.py

Context file for tests; import resolution when path not set

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''
import sys
import unittest

# support execution without package set (e.g., call unittest from command line)
if __package__ is None:
    import os
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)

class BasicTest(unittest.TestCase):
    def test_context(self):
        import oneflux
        """Test import by checking imported 'oneflux' module has '__version__' attribute"""
        self.assertTrue(hasattr(oneflux, '__version__'))

if __name__ == '__main__':
    unittest.main()
