# Import single-function-per-file modules
from .fcx2colvec import fcx2colvec
from .fcx2rowvec import fcx2rowvec
from .fcDatetick import fcDatetick
from .fcDoy import fcDoy
from .fcr2Calc import fcr2Calc
from .cpdFmax2pCp3 import cpdFmax2pCp3
from .fcNaniqr import *
from .cpdFmax2pCp2 import cpdFmax2pCp2
from .cpdFmax2pCore import interpolate_FmaxCritical, calculate_p_low, calculate_p_interpolate
from .fcDatenum import datenum
from .fcBin import fcBin


from os.path import dirname, basename, isfile, join
import glob
modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
