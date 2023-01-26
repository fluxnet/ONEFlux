import pytest

def test_import_oneflux():
    import oneflux
    assert oneflux.VERSION == "0.4.1-rc"