'''
oneflux.metadata

For license information:
see LICENSE file or headers in oneflux.__init__.py

Text for data product README and LICENSE files

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2026-01-09
'''
import os

LICENSE_TEXT = ''
README_TEXT = ''

CODE_DIR = os.path.dirname(os.path.abspath(__file__))
LICENSE_FILEPATH = os.path.join(CODE_DIR, 'fluxnet_data_docs', 'DATA_POLICY_LICENSE_INSTRUCTIONS.txt')
README_FILEPATH = os.path.join(CODE_DIR, 'fluxnet_data_docs', 'README.txt')

with open(LICENSE_FILEPATH, 'r') as f:
    LICENSE_TEXT = f.read()

with open(README_FILEPATH, 'r') as f:
    README_TEXT = f.read()
