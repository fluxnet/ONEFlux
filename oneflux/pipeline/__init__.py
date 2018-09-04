'''
oneflux.pipeline

For license information:
see LICENSE file or headers in oneflux.__init__.py

Pipeline execution controller code (combined modules/functions)

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''
import os

# system parameters
HOMEDIR = os.path.expanduser("~")

# operating system commands
COPY = ('cp -av' if os.name == 'posix' else 'copy')
DELETE = ('rm -v' if os.name == 'posix' else 'del')
DELETE_DIR = ('rm -rf' if os.name == 'posix' else 'rmdir /s /q')
CMD_SEP = (';' if os.name == 'posix' else '&')

# constants
OUTPUT_LOG_TEMPLATE = 'report_{t}.txt'
DATA_DIR = os.path.join(HOMEDIR, 'data', 'fluxnet')
TOOL_DIR = os.path.join(HOMEDIR, 'bin', 'oneflux')
