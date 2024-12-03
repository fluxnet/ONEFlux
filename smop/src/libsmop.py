# SMOP compiler runtime support library
# Copyright 2014 Victor Leikehman

# MIT license

from copy import deepcopy
import numpy as np
from numpy import sqrt, prod, exp, log, multiply, inf, rint as fix
from numpy.fft import fft2
from numpy.linalg import inv
from numpy.linalg import qr as _qr
import scipy
from scipy.stats import pearsonr as corr
import pandas as pd

try:
    from scipy.linalg import schur as _schur
except ImportError:
    pass

import re
import os
import sys
import time
import json
import glob
import importlib
from pathlib import Path
from sys import stdin, stdout, stderr

from scipy.io import loadmat
from scipy.special import gamma

import matlab


pwd = os.getcwd()
eps = np.finfo(float).eps
NaN = np.nan


ALL_MATLAB_TYPES = (
    matlab.double, matlab.logical,
    matlab.int8, matlab.int16, matlab.int32, matlab.int64,
    matlab.uint8, matlab.uint16, matlab.uint32, matlab.uint64,
)

def function(f):
    from contextlib import redirect_stdout, redirect_stderr
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        with (
            redirect_stdout(kwargs.pop("stdout", stdout)),
            redirect_stderr(kwargs.pop("stderr", stderr)),
        ):
            nargout = kwargs.pop("nargout", 0)
            kwargs.pop("jsonencode", None)
            kwargs.pop("jsondecode", None)
            args = list(args)
            for i, a in enumerate(args):
                if isinstance(a, ALL_MATLAB_TYPES):
                    if np.size(a) == 1:
                        args[i] = a.item()
                    else:
                        args[i] = matlabarray(a)
            out = f(*args, **kwargs)
            if nargout:
                out = out[:nargout]
            flag = False
            if isinstance(out, tuple):
                out = list(out)
            else:
                flag = True
                out = [out]
            for i, a in enumerate(out):
                if isinstance(a, np.ndarray):
                    if a.size == 1:
                        out[i] = a.item()
                    elif not isinstance(a, matlabarray):
                        out[i] = matlabarray(a)
            return out[0] if flag else tuple(out)

    return wrapper


def load_all_vars():
    root = Path(__file__).parent
    sys.path.append(str(root))
    for p in root.rglob("*.py"):
        if p != root / "__init__.py":
            p = str(p.relative_to(root))
            module_name = p[:-3].replace("/", ".")  # Remove the .py extension
            m = importlib.import_module(f"{module_name}", package=__name__)
            globals().update(vars(m))
    return globals()


def check_struct(a):
    if isinstance(a, struct):
        return a
    if isinstance(a, matlabarray) and a.size == 0:
        return struct()
    raise TypeError("Unable to perform assignment because dot indexing is not supported for variables of this type.")


def logical(a):
    return matlabarray(a, bool)


def exec_(s, globals=None, locals=None):
    s = re.sub(r"(?=^|;)\s*(\w+)\s*=", r"global \1; \1 =", s)
    exec(s, globals, locals)


def jsonencode(a):
    return a if isinstance(a, cellarray) else json.dumps(a)


def jsondecode(a):
    return a if isinstance(a, cellarray) else json.loads(a)


def getfield(a, *fields):
    for f in fields:
        if isinstance(f, np.ndarray):
            f = tuple(f.astype(int).flatten())
            a = a[f]
        else:
            a = getattr(a, f)
    return a


def dir(s):
    return cellarray([Path(s) for s in glob.glob(s)])


def clear(*args):
    for a in args:
        if a in globals():
            del globals()[a]


def fclose(fp):
    fp.close()


def take(a, *i):
    """Get an item with matlab indexing (1-based)."""
    if isinstance(a, matlabarray):
        return a[i]
    elif not isinstance(a, np.ndarray):
        assert len(i) == 1
        return a[i[0] - 1]
    else:
       return matlabarray(a)[i]


def textscan(fp, fmt):
    if fmt == "%[^\n]":
        return [[ln.strip("\n") for ln in fp.readlines()]]
    else:
        raise NotImplementedError


def importdata(filename, delimiter=",", header=1):
    import pandas as pd

    df = pd.read_csv(filename, delimiter=delimiter, header=header - 1)
    return dataframe(df)


def abs(a):
    return np.abs(a)


def all(a):
    return np.all(a)


def any(a):
    return np.any(a)


def arange(start, stop, step=1, **kwargs):
    """
    >>> a=arange(1,10) # 1:10
    >>> size(a)
    matlabarray([[ 1, 10]])
    """
    expand_value = 1 if step > 0 else -1
    return matlabarray(
        np.arange(start, stop + expand_value, step, **kwargs).reshape(1, -1),
        **kwargs,
    )


def concat(args, axis=1):
    """
    >>> concat([[1,2,3,4,5] , [1,2,3,4,5]])
    [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
    """
    if all([isinstance(a, str) for a in args]):
        return "".join(args)
    t = [matlabarray(a) for a in args]
    return np.concatenate(t, axis=axis).view(matlabarray)


def squeeze(a, axis=None):
    if axis is not None and a.shape[axis] != 1:
        return a
    if axis is None and a.ndim == 2 and a.shape[0] == 1:
        return a.reshape(-1)
    return np.squeeze(a, axis=axis)


def reshape(a, *shape):
    return np.reshape(a, shape)


def ceil(a):
    return np.ceil(a)


def cell(*args):
    if len(args) == 1:
        args += args
    return cellarray(np.zeros(args, dtype=object, order="F"))


def clc():
    pass


def copy(a):
    if isinstance(a, matlabarray):
        return a.copy()
    if isinstance(a, np.ndarray):
        return matlabarray(np.asanyarray(a).copy(order="F"))
    return deepcopy(a)


def deal(a, nargout=1):
    return tuple(np.repeat(a, nargout // np.size(a)).flat)


def disp(*args):
    print(args)


def eig(a):
    u, v = np.linalg.eig(a)
    return u.T


def linsolve(a, b):
    if a.shape[0] == a.shape[1]:
        return np.linalg.solve(a, b)
    else:
        return np.linalg.pinv(a) @ b


def logical_not(a):
    return np.logical_not(a)


def logical_and(a, b):
    return np.logical_and(a, b)


def logical_or(a, b):
    return np.logical_or(a, b)


def diff(a, n=1, axis=0):
    x = squeeze(np.asarray(a))
    return np.diff(x, n=n, axis=axis).view(matlabarray)


def exist(a, b="file"):
    if str(b) == "builtin":
        return str(a) in globals()
    if str(b) == "file":
        return os.path.exists(str(a))
    raise NotImplementedError


def mkdir(directory):
    """
    Create a directory if it does not exist.
    Parameters:
    directory : str
        The path of the directory to create.
    """
    os.makedirs(directory, exist_ok=True)


def true(*args):
    if len(args) == 1:
        args += args
    return matlabarray(np.ones(args, dtype=bool, order="F"))


def false(*args):
    if not args:
        return False  # or matlabarray(False) ???
    if len(args) == 1:
        args += args
    return np.zeros(args, dtype=bool, order="F")


def find(a, n=None, d=None, nargout=1):
    if d:
        raise NotImplementedError
    # there is no promise that nonzero or flatnonzero
    # use or will use indexing of the argument without
    # converting it to array first.  So we use asarray
    # instead of asanyarray
    if nargout == 1:
        i = np.flatnonzero(np.asarray(a)).reshape(1, -1) + 1
        if n is not None:
            i = i.take(n)
        return matlabarray(i)
    if nargout == 2:
        i, j = np.nonzero(np.asarray(a))
        if n is not None:
            i = i.take(n)
            j = j.take(n)
        return (
            matlabarray((i + 1).reshape(-1, 1)),
            matlabarray((j + 1).reshape(-1, 1)),
        )
    raise NotImplementedError


def floor(a):
    return np.asanyarray(a // 1).astype(int)


def fopen(*args):
    try:
        fp = open(*args)
        assert fp != -1
        return fp
    except:
        return -1


def fflush(fp):
    fp.flush()


def fullfile(*args):
    return os.path.join(*args)


def intersect(a, b, nargout=1):
    from builtins import set

    if nargout == 1:
        c = sorted(set(a.flat) & set(b.flat))
        if isinstance(a, str):
            return "".join(c)
        elif isinstance(a, list):
            return c
        else:
            # FIXME: the result is a column vector if
            # both args are column vectors; otherwise row vector
            return matlabarray(c).reshape((1, -1) if a.shape[1] > 1 else (-1, 1))
    raise NotImplementedError


def union(a, b, nargout=1):
    from builtins import set

    if nargout == 1:
        c = sorted(set(a.flat) | set(b.flat))
        if isinstance(a, str):
            return "".join(c)
        elif isinstance(a, list):
            return c
        else:
            return matlabarray(c)
    raise NotImplementedError


def iscell(a):
    return isinstance(a, cellarray)


def iscellstr(a):
    # TODO return isinstance(a,cellarray) and all(ischar(t) for t in a.flat)
    return isinstance(a, cellarray) and all(isinstance(t, str) for t in a.flat)


def ischar(a):
    try:
        return a.dtype == "|S1"
    except AttributeError:
        return False


# ----------------------------------------------------
def isempty(a):
    try:
        return 0 in np.asarray(a).shape
    except AttributeError:
        return False


def isequal(a, b):
    return np.array_equal(np.asanyarray(a), np.asanyarray(b))


def isfield(a, b):
    return str(b) in list(a.__dict__.keys())


def ismatrix(a):
    return True


def isnumeric(a):
    return np.asarray(a).dtype in (int, float)


def isscalar(a):
    """np.isscalar returns True if a.__class__ is a scalar
    type (i.e., int, and also immutable containers str and
    tuple, but not list.) Our requirements are different"""
    try:
        return a.size == 1
    except AttributeError:
        return np.isscalar(a)


def length(a):
    if not isinstance(a, np.ndarray) and hasattr(a, "__len__"):
        return len(a)
    elif np.ndim(a) < 2 or min(np.shape(a)) == 0:
        return np.array(np.size(a))
    else:
        return np.array(max(np.asarray(a).shape))
    
    
def setdiff(a, b, nargout=1):
    from builtins import set
    a = np.asarray(a)
    b = np.asarray(b)
    if nargout == 1:
        c = sorted(set(a.flat) - set(b.flat))
        if isinstance(a, str):
            return "".join(c)
        elif isinstance(a, list):
            return c
        else:
            return matlabarray(c)
    raise NotImplementedError


def load(a):
    return loadmat(a)  # FIXME


def mod(a, b):
    try:
        return a % b
    except ZeroDivisionError:
        return a


def ndims(a):
    return np.asarray(a).ndim


def numel(a):
    return np.asarray(a).size


# def primes2(upto):
#    primes=np.arange(2,upto+1)
#    isprime=np.ones(upto-1,dtype=bool)
#    for factor in primes[:int(math.sqrt(upto))]:
#        if isprime[factor-2]: isprime[factor*2-2::factor]=0
#    return primes[isprime]

# def primes(*args):
#    return _primes.primes(*args)


def qr(a):
    return matlabarray(_qr(np.asarray(a)))


def rand(*args, **kwargs):
    if not args:
        return np.random.rand()  # No arguments, return a single random float
    if len(args) == 1:
        args += args
    try:
        return np.random.rand(np.prod(args)).reshape(args, order="F")
    except:
        pass


def randn(*args, **kwargs):
    if not args:
        return np.random.randn()
    if len(args) == 1:
        args += args
    return np.random.randn(np.prod(args)).reshape(args, order="F")


def randi(hi, *args, **kwargs):
    if len(args) == 1:
        args += args
    return np.random.randint(1, hi + 1, args).reshape(args, order="F")


def assert_(a, b=None, c=None):
    if c:
        if c >= 0:
            assert (abs(a - b) < c).all()
        else:
            assert (abs(a - b) < abs(b * c)).all()
    elif b is None:
        assert a
    else:
        # assert isequal(a,b),(a,b)
        # assert not any(a-b == 0)
        assert (a == b).all()


def shared(a):
    raise NotImplementedError


def ravel(a):
    return np.asanyarray(a).reshape(-1, 1)


def roots(a):
    return matlabarray(np.roots(np.asarray(a).ravel()))


def round(a):
    return np.round(np.asanyarray(a))


def rows(a):
    return np.asarray(a).shape[0]


def schur(a):
    return matlabarray(_schur(np.asarray(a)))


def size(a, b=0, nargout=1):
    """
    >>> size(zeros(3,3)) + 1
    matlabarray([[4, 4]])
    """
    s = np.asarray(a).shape
    if s == ():
        return 1 if b else (1,) * nargout
    # a is not a scalar
    try:
        if b:
            return s[b - 1]
        else:
            return np.squeeze(s)
    except IndexError:
        return 1


def size_equal(a, b):
    if a.size != b.size:
        return False
    for i in range(len(a.shape)):
        if a.shape[i] != b.shape[i]:
            return False
    return True


def strcmp(a, b):
    return str(a) == str(b)


def strncmp(a, b, n):
    return str(a)[:n] == str(b)[:n]


def strcmpi(a, b):
    return str(a).lower() == str(b).lower()


def strncmpi(a, b, n):
    return str(a).lower()[:n] == str(b).lower()[:n]


def strread(s, format="", nargout=1):
    if format == "":
        a = [float(x) for x in s.split()]
        return tuple(a) if nargout > 1 else np.asanyarray([a])
    raise NotImplementedError


def strrep(a, b, c):
    return str(a).replace(str(b), str(c))


def strcat(*args):
    return "".join(str(a) for a in args)


def sum(a, dim=None):
    if dim is None:
        return np.asanyarray(a).sum()
    else:
        return np.asanyarray(a).sum(dim - 1)


def toupper(a):
    return char(str(a.data).upper())


def tic():
    return time.clock()


def toc(t):
    return time.clock() - t


def version():
    return char("0.29")


def zeros(*args, **kwargs):
    if not args:
        return 0.0
    if hasattr(args[0], '__len__'):
        args = args[0]
    if np.size(args) == 1:
        args += args
    return matlabarray(np.zeros(args, **kwargs))


def ones(*args, **kwargs):
    if not args:
        return 1
    if len(args) == 1:
        if isinstance(args[0], (tuple, list, np.ndarray)):
            args = args[0]
        else:
            args += args
    return matlabarray(np.ones(args, order="F", **kwargs))


def print_usage():
    raise Exception


def error(s):
    raise s


def isreal(a):
    return True


def linspace(start, stop, num=50):
    """
    Return evenly spaced numbers over a specified interval.
    """
    return matlabarray(np.linspace(start, stop, num))


def logspace(start, stop, num=50, base=10.0):
    """
    Return numbers spaced evenly on a log scale.
    """
    return matlabarray(np.logspace(start, stop, num, base=base))


@function
def mean(a, axis=0):
    """
    Compute the mean of the elements along the specified axis.
    """
    return np.mean(squeeze(np.asarray(a)), axis=axis)


@function
def std(a, axis=0):
    """
    Compute the standard deviation of the elements along the specified axis.
    """
    return np.std(squeeze(np.asarray(a)), axis=axis)


@function
def var(a, axis=0):
    """
    Compute the variance of the elements along the specified axis.
    """
    return np.var(squeeze(np.asarray(a)), axis=axis)


@function
def max(a, b=[], axis=0, nargout=1):
    """
    Return the maximum of an array or maximum along an axis.
    """
    if np.size(b) > 0:
        return np.maximum(np.asarray(a), np.asarray(b))
    if np.size(a) == 0:
        if nargout == 1:
            return a
        return a, a
    if axis == 'all':
        axis = None
    if axis:
        axis -= 1
    a = squeeze(np.asarray(a))
    m = np.max(a, axis=axis)
    if nargout == 1:
        return m
    i = np.argmax(a, axis=axis)
    return m, i


@function
def min(a, b=[], axis=0, nargout=1):
    """
    Return the minimum of an array or minimum along an axis.
    """
    if np.size(b) > 0:
        return np.minimum(np.asarray(a), np.asarray(b))
    if np.size(a) == 0:
        if nargout == 1:
            return a
        return a, a
    if axis == 'all':
        axis = None
    if axis:
        axis -= 1
    a = squeeze(np.asarray(a))
    m = np.min(a, axis=axis)
    if nargout == 1:
        return m
    i = np.argmin(a, axis=axis)
    return m, i


@function
def isnan(a):
    """
    Return a boolean array indicating whether each element is NaN.
    """
    return np.isnan(np.asarray(a))


def unique(a):
    """
    Return the unique elements of an array.
    """
    return matlabarray(np.unique(np.asarray(a)))


def interp1(x, v, xq, method):
    """
    One-dimensional linear interpolation.
    """
    x = np.asarray(x).flatten()
    v = np.asarray(v).flatten()
    xq = np.asarray(xq).flatten()

    if np.isnan(x).any() or np.isnan(v).any() or np.size(x) < 2 or np.size(v) < 2 or np.diff(x).min() < 0:
        return matlabarray(np.full_like(xq, np.nan))
    
    if method in ['linear', 'nearest', 'next', 'previous', 'cubic']:
        f = scipy.interp1d(x, v, kind=method)
    elif method == 'pchip':
        f = scipy.interpolate.PchipInterpolator(x, v, extrapolate=False)
    else:
        raise ValueError(f"Unknown interpolation method: {method}")

    return matlabarray(f(xq))


def prctile(a, q):
    """
    Compute the q-th percentile of the data along the specified axis.
    """
    q = np.asarray(q)
    if np.size(a) == 0:
        return np.full_like(q, np.nan)
    a = np.percentile(np.asarray(a), q)
    return matlabarray(a)


def dot(a, b):
    """
    Compute the dot product of two arrays.
    """
    try:
        return np.dot(a, b)
    except ValueError:
        return sum([x * y for x, y in zip(a, b)])


def datenum(a, *args):
    if isinstance(a, str):
        d = matlabarray(np.datetime64(a) - np.datetime64("1970-01-01"))
        return d.astype("timedelta64[D]") + 719529
    from datetime import datetime, timedelta

    y, m, d = [np.squeeze(a).item() for a in (a, *args)]
    t = datetime(int(y) + 2000, int(m), 1) + timedelta(days=d + 1)
    return matlabarray(t - datetime(2000, 1, 1)).astype("timedelta64[D]")


def datevec(datenum, nargout=6):
    """
    Convert a MATLAB datenum to a date vector.
    """
    dt = np.datetime64("1970-01-01") + (datenum - 719529).astype("timedelta64[D]")
    return (
        dt.astype("datetime64[Y]").astype(int) + 1970,
        dt.astype("datetime64[M]").astype(int) % 12 + 1,
        dt.astype("datetime64[D]").astype(int) % 31 + 1,
        dt.astype("datetime64[h]").astype(int) % 24,
        dt.astype("datetime64[m]").astype(int) % 60,
        dt.astype("datetime64[s]").astype(int) % 60,
    )[:nargout]


@function
def median(a, axis=0):
    """
    Compute the median of an array.
    """
    return np.median(squeeze(np.asarray(a)), axis=axis)


@function
def nanmean(a, axis=0):
    """
    Compute the mean of an array while ignoring NaNs.
    """
    return np.nanmean(squeeze(np.asarray(a)), axis=axis)


@function
def nanmedian(a, axis=0):
    """
    Compute the median of an array while ignoring NaNs.
    """
    return np.nanmedian(squeeze(np.asarray(a)), axis=axis)


def fcdf(x, dfn, dfd):
    """
    Cumulative distribution function of the F-distribution.
    """
    from scipy.stats import f

    return f.cdf(x, dfn, dfd)


def finv(p, dfn, dfd):
    """
    Inverse of the cumulative distribution function of the F-distribution.
    """
    from scipy.stats import f

    return f.ppf(p, dfn, dfd)


def regress(y, x, nargout=1, alpha=0.05):
    """
    Perform linear regression.
    """
    import statsmodels.api as sm

    x = sm.add_constant(x)
    model = sm.OLS(y, x).fit()
    b = matlabarray(model.params)
    if nargout == 1:
        return b
    elif nargout == 2:
        bint = model.conf_int(alpha=0.05)
        return b, bint
    raise ValueError


def corrcoef(x, y, nargout=1):
    """
    Return the correlation coefficients.
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()
    if np.isnan(x).any() or np.isnan(y).any():
        r, p = NaN, NaN
    else:
        r, p = corr(x, y)
    r = matlabarray([[1.0 if i == j else r for i in range(2)] for j in range(2)])
    p = matlabarray([[1.0 if i == j else p for i in range(2)] for j in range(2)])
    return r, p


def sort(a, axis=-1, kind="quicksort", order=None):
    """
    Return a sorted copy of an array.
    """
    return matlabarray(np.sort(np.asarray(a), axis=axis, kind=kind))


def fprintf(format_string, *args):
    """
    Print formatted output to the console.
    """
    print((format_string % args))


def sprintf(format_string, *args):
    """
    Return a formatted string.
    """
    return format_string % args


def plot(*args, **kwargs):
    """
    Basic plotting function.
    """
    import matplotlib.pyplot as plt

    plt.plot(*args, **kwargs)
    plt.show()


def hold():
    """
    Hold the current plot.
    """
    import matplotlib.pyplot as plt

    plt.gca().set_prop_cycle(None)


def grid(on=True):
    """
    Turn the grid on or off.
    """
    import matplotlib.pyplot as plt

    plt.grid(on)


def box(on=True):
    """
    Turn the box around the plot on or off.
    """
    import matplotlib.pyplot as plt

    plt.box(on)


def xlim(left=None, right=None):
    """
    Set the x limits of the current axes.
    """
    import matplotlib.pyplot as plt

    plt.xlim(left, right)


def ylim(bottom=None, top=None):
    """
    Set the y limits of the current axes.
    """
    import matplotlib.pyplot as plt

    plt.ylim(bottom, top)


def set(artist, **kwargs):
    """
    Set the properties of a matplotlib artist.
    """
    for key, value in list(kwargs.items()):
        setattr(artist, key, value)


def figure():
    """
    Create a new figure.
    """
    import matplotlib.pyplot as plt

    plt.figure()


def clf():
    """
    Clear the current figure.
    """
    import matplotlib.pyplot as plt

    plt.clf()


def warning(message):
    """
    Display a warning message to the user.

    Parameters:
    message : str
        The warning message to display.
    """
    import warnings

    if message == "off":
        warnings.filterwarnings("ignore")
    elif message == "on":
        warnings.filterwarnings("default")
    else:
        warnings.warn(message)


def isvector_or_scalar(a):
    """
    one-dimensional arrays having shape [N],
    row and column matrices having shape [1 N] and
    [N 1] correspondingly, and their generalizations
    having shape [1 1 ... N ... 1 1 1].
    Scalars have shape [1 1 ... 1].
    Empty arrays dont count
    """
    try:
        return a.size and a.ndim - a.shape.count(1) <= 1
    except AttributeError:
        return False


def isvector(a):
    """
    one-dimensional arrays having shape [N],
    row and column matrices having shape [1 N] and
    [N 1] correspondingly, and their generalizations
    having shape [1 1 ... N ... 1 1 1]
    """
    try:
        return a.ndim - a.shape.count(1) == 1
    except AttributeError:
        return False


class matlabarray(np.ndarray):
    """
    >>> matlabarray()
    matlabarray([], shape=(0, 0), dtype=float64)
    >>> matlabarray([arange(1,5), arange(1,5)])
    matlabarray([1, 2, 3, 4, 5, 1, 2, 3, 4, 5])
    >>> matlabarray(["hello","world"])
    matlabarray("helloworld")
    """

    def __new__(cls, a=(), dtype=None):
        if isinstance(a, matlabarray) and dtype is None:
            return a
        if isinstance(a, list) and np.any([isinstance(x, np.ndarray) for x in a]):
            return concat(a)
        if np.size(a) == 0 and dtype is None:
            dtype = object
        copy = not isinstance(a, np.ndarray) or dtype and a.dtype != dtype
        obj = (
            np.array(a, dtype=dtype, order="F", copy=copy, ndmin=2)
            .view(cls)
            .copy(order="F")
        )
        if obj.size == 0:
            obj.shape = (0, 0)
        return obj

    def __array_finalize__(self, obj):
        return
            
    def __copy__(self):
        return np.ndarray.copy(self, order="F")

    def __iter__(self):
        """must define iter or char won't work"""
        return np.asarray(self).__iter__()

    def compute_indices(self, index):
        if not isinstance(index, tuple):
            index = (index,)
        assert len(index) > 0
        if self.size:
            sh = self.shape + tuple(1 for _ in range(self.ndim, len(index)))
            sh = (*sh[: len(index) - 1], -1)
        else:
            sh = (0, 0)
        self = self.reshape(*sh, order="F")
        indices = []
        for i, ix in enumerate(index):
            if ix.__class__ is end:
                indices.append(ix.index(self, i) - 1)
            elif ix.__class__ is slice:
                start, stop = ix.start, ix.stop
                if isinstance(start, end):
                    start = start.index(self, i)
                if isinstance(stop, end):
                    stop = stop.index(self, i)
                if start is not None:
                    start -= 1
                indices.append(slice(start, stop, ix.step))
            else:
                try:
                    indices.append(int(ix) - 1)
                except TypeError:
                    indices.append(np.asarray(ix).astype("int32") - 1)
        if len(indices) == 2 and isvector(indices[0]) and isvector(indices[1]):
            indices[0].shape = (-1, 1)
            indices[1].shape = (-1,)
        return self, tuple(indices)

    def __getslice__(self, i, j):
        if i == 0 and j == sys.maxsize:
            return self.reshape(-1, 1, order="F")
        return self.__getitem__(slice(i, j))

    def __setslice__(self, i, j, value):
        index = slice(i, None if j == sys.maxsize else j)
        self.__setitem__(index, value)

    def __getitem__(self, index):
        return self.get(index)

    def get(self, index):
        self, indices = self.compute_indices(index)
        return np.ndarray.__getitem__(self, indices)

    def sizeof(self, ix, axis=None):
        if isinstance(ix, int):
            n = ix + 1
        elif isinstance(ix, slice):
            n = ix.stop
            if n is None:
                n = self.shape[axis]
        elif isinstance(ix, (list, np.ndarray)):
            n = int(max(ix) + 1)
        else:
            raise ValueError("Invalid index: %s" % ix)
        if not isinstance(n, int):
            raise IndexError
        return n

    def delete(self, ix, axis=0):
        if not np.size(ix):
            return self
        _, indices = self.compute_indices((ix,))
        return matlabarray(np.delete(np.asarray(self), indices[0], axis=axis))

    def __setitem__(self, index, value):
        view, indices = self.compute_indices(index)
        if self.size == 0:
            if all([np.size(i) > 0 for i in indices]):
                new_shape = [self.sizeof(i) for i in indices]
                self.resize(new_shape, refcheck=0)
                self.fill(value)
            return
        try:
            np.ndarray.__setitem__(view, indices, value)
        except (ValueError, IndexError):
            # import pdb; pdb.set_trace()
            if len(indices) == 1:
                # One-dimensional resize is only implemented for
                # two cases:
                #
                # a. empty matrices having shape [0 0]. These
                #    matries may be resized to any shape.  A[B]=C
                #    where A=[], and B is specific -- A[1:10]=C
                #    rather than A[:]=C or A[1:end]=C
                if self.size and not isvector_or_scalar(self):
                    raise IndexError(
                        "One-dimensional resize "
                        "works only on vectors, and "
                        "row and column matrices"
                    )
                # One dimensional resize of scalars creates row matrices
                # ai = 3
                # a(4) = 1
                # 3 0 0 1
                n = self.sizeof(indices[0])  # zero-based
                if max(self.shape) == 1:
                    new_shape = list(self.shape)
                    new_shape[-1] = n
                else:
                    new_shape = [(1 if s == 1 else n) for s in self.shape]
                self.resize(new_shape, refcheck=0)
                np.asarray(self).reshape(-1, order="F").__setitem__(indices, value)
            else:
                new_shape = [self.sizeof(i) for i in indices]
                self.resize(new_shape, refcheck=0)
                np.asarray(self).__setitem__(indices, value)

    def __setattr__(self, name, value):
        if self.size > 0:
            raise ValueError("Unable to perform assignment because dot indexing is not supported for variables of this type.")

    def __repr__(self):
        return self.__class__.__name__ + repr(np.asarray(self))[5:]

    def __str__(self):
        return str(np.asarray(self))

    def __add__(self, other):
        return matlabarray(np.asarray(self) + np.asarray(other))

    def __neg__(self):
        return matlabarray(np.asarray(self).__neg__())


class end(object):
    def __init__(self):
        self.n = 0

    def __add__(self, n):
        self.n += n
        return self

    def __sub__(self, n):
        self.n -= n
        return self

    def index(self, m, axis=0):
        return np.shape(m)[axis] + self.n


class cellarray(matlabarray):
    """
    Cell array corresponds to matlab ``{}``

    """

    def __new__(cls, a=[]):
        """
        Create a cell array and initialize it with a.
        Without arguments, create an empty cell array.
        Parameters:
        a : list, ndarray, matlabarray, etc.
        >>> a=cellarray([123,"hello"])
        >>> print(a.shape)
        (1, 2)
        >>> print(a[1])
        123
        >>> print(a[2])
        hello
        """
        return super().__new__(cls, a, dtype=object)


class cellstr(matlabarray):
    """
    >>> s=cellstr(char('helloworldkitty').reshape(3,5))
    >>> s
    cellstr([['hello', 'world', 'kitty']], dtype=object)
    >>> print(s)
    hello
    world
    kitty
    >>> s.shape
    (1, 3)
    """

    def __new__(cls, a):
        """
        Given a two-dimensional char object,
        create a cell array where each cell contains
        a line.
        """
        obj = (
            np.array(["".join(s) for s in a], dtype=object, order="C", ndmin=2)
            .view(cls)
            .copy(order="F")
        )
        if obj.size == 0:
            obj.shape = (0, 0)
        return obj

    def __str__(self):
        return "\n".join("".join(s) for s in self.reshape(-1))

    def __getitem__(self, index):
        return self.get(index)


class char(matlabarray):
    """
    class char is a rectangular string matrix, which
    inherits from matlabarray all its features except
    dtype.
    >>> s=char()
    >>> s.shape
    (0, 0)
    >>> s=char('helloworld')
    >>> reshape(s, [2,5])
    hlool
    elwrd
    >>> s=char([104, 101, 108, 108, 111, 119, 111, 114, 108, 100])
    >>> s.shape = 2,5
    >>> print(s)
    hello
    world
    """

    def __new__(cls, a=""):
        if not isinstance(a, str):
            a = "".join([chr(c) for c in a])
        obj = (
            np.array(list(a), dtype="|U1", order="F", ndmin=2)
            .view(cls)
            .copy(order="F")
        )
        if obj.size == 0:
            obj.shape = (0, 0)
        return obj

    def __getitem__(self, index):
        return self.get(index)

    def __str__(self):
        if self.ndim == 0:
            return ""
        if self.ndim == 1:
            return "".join(s for s in self)
        if self.ndim == 2:
            return "\n".join("".join(s) for s in self)
        raise NotImplementedError

    def __add__(self, other):
        return str(self) + other

    def __radd__(self, other):
        return other + str(self)

    def __eq__(self, other):
        if isinstance(other, str):
            return str(self) == other
        return super().__eq__(other)


class struct(matlabarray):
    def __init__(self, *args):
        if len(args) < 2:
            return
        for i in range(0, len(args), 2):
            setattr(self, str(args[i]), args[i + 1])


class dataframe(pd.DataFrame):
    @property
    def textdata(self):
        return cellstr(self.columns.values)

    @property
    def data(self):
        return matlabarray(self.values)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
