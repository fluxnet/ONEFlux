'''
For license information:
see LICENSE file or headers in oneflux.__init__.py

Simple context/import setup test

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''
import unittest

from context import oneflux

class BasicTest(unittest.TestCase):
    def test_context(self):
        """Test import by checking imported 'oneflux' module has '__version__' attribute"""
        self.assertTrue(hasattr(oneflux, '__version__'))

if __name__ == '__main__':
    unittest.main()
