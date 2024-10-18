"""
For license information:
see LICENSE file or headers in oneflux.__init__.py

Simple context/import setup test

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
"""


def test_import_oneflux():
    """
    Test import by checking imported 'oneflux' module has '__version__' attribute
    """
    import oneflux

    assert hasattr(oneflux, "__version__")
