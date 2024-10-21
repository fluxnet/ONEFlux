# SMOP compiler runtime support library
# Copyright 2014 Victor Leikehman

# MIT license

import numpy as np
from numpy import sqrt, prod, exp, log, dot, multiply, inf, rint as fix
from numpy.fft import fft2
from numpy.linalg import inv
from numpy.linalg import qr as _qr

try:
    from scipy.linalg import schur as _schur
except ImportError:
    pass

import os
import sys
import time
from sys import stdin, stdout, stderr

from scipy.io import loadmat
from scipy.special import gamma


pwd = os.getcwd()
eps = np.finfo(float).eps


# def _load_matlab_builtins(*names):
#     import oct2py
#     oc = oct2py.Oct2Py()
#     globals().update(
#         (k, getattr(oc, k)) for k in names
#     )

# _load_matlab_builtins("""
# """.split())


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

    def __new__(cls, a=[], dtype=None):
        obj = (
            np.array(a, dtype=dtype, copy=False, order="F", ndmin=2)
            .view(cls)
            .copy(order="F")
        )
        if obj.size == 0:
            obj.shape = (0, 0)
        return obj

    # def __array_finalize__(self,obj):

    def __copy__(self):
        return np.ndarray.copy(self, order="F")

    def __iter__(self):
        """must define iter or char won't work"""
        return np.asarray(self).__iter__()

    def compute_indices(self, index):
        if not isinstance(index, tuple):
            index = (index,)
        if len(index) != 1 and len(index) != self.ndim:
            raise IndexError
        indices = []
        for i, ix in enumerate(index):
            if ix.__class__ is end:
                indices.append(self.shape[i] - 1 + ix.n)
            elif ix.__class__ is slice:
                if self.size == 0 and ix.stop is None:
                    raise IndexError
                if len(index) == 1:
                    n = self.size
                else:
                    n = self.shape[i]
                indices.append(
                    np.arange(
                        (ix.start or 1) - 1, ix.stop or n, ix.step or 1, dtype=int
                    )
                )
            else:
                try:
                    indices.append(int(ix) - 1)
                except TypeError:
                    indices.append(np.asarray(ix).astype("int32") - 1)
        if len(indices) == 2 and isvector(indices[0]) and isvector(indices[1]):
            indices[0].shape = (-1, 1)
            indices[1].shape = (-1,)
        return tuple(indices)

    def __getslice__(self, i, j):
        if i == 0 and j == sys.maxsize:
            return self.reshape(-1, 1, order="F")
        return self.__getitem__(slice(i, j))

    def __getitem__(self, index):
        return matlabarray(self.get(index))

    def get(self, index):
        # import pdb; pdb.set_trace()
        indices = self.compute_indices(index)
        if len(indices) == 1:
            return np.ndarray.__getitem__(self.reshape(-1, order="F"), indices)
        else:
            return np.ndarray.__getitem__(self, indices)

    def __setslice__(self, i, j, value):
        if i == 0 and j == sys.maxsize:
            index = slice(None, None)
        else:
            index = slice(i, j)
        self.__setitem__(index, value)

    def sizeof(self, ix):
        if isinstance(ix, int):
            n = ix + 1
        elif isinstance(ix, slice):
            n = ix.stop
        elif isinstance(ix, (list, np.ndarray)):
            n = max(ix) + 1
        else:
            assert 0, ix
        if not isinstance(n, int):
            raise IndexError
        return n

    def __setitem__(self, index, value):
        # import pdb; pdb.set_trace()
        indices = self.compute_indices(index)
        try:
            if len(indices) == 1:
                np.asarray(self).reshape(-1, order="F").__setitem__(indices, value)
            else:
                np.asarray(self).__setitem__(indices, value)
        except (ValueError, IndexError):
            # import pdb; pdb.set_trace()
            if not self.size:
                new_shape = [self.sizeof(s) for s in indices]
                self.resize(new_shape, refcheck=0)
                np.asarray(self).__setitem__(indices, value)
            elif len(indices) == 1:
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
                new_shape = list(self.shape)
                if self.flags["C_CONTIGUOUS"]:
                    new_shape[0] = self.sizeof(indices[0])
                elif self.flags["F_CONTIGUOUS"]:
                    new_shape[-1] = self.sizeof(indices[-1])
                self.resize(new_shape, refcheck=0)
                np.asarray(self).__setitem__(indices, value)

    def __repr__(self):
        return self.__class__.__name__ + repr(np.asarray(self))[5:]

    def __str__(self):
        return str(np.asarray(self))

    def __add__(self, other):
        return matlabarray(np.asarray(self) + np.asarray(other))

    def __neg__(self):
        return matlabarray(np.asarray(self).__neg__())


class end(object):
    def __add__(self, n):
        self.n = n
        return self

    def __sub__(self, n):
        self.n = -n
        return self


####
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
        obj = np.array(a, dtype=object, order="F", ndmin=2).view(cls).copy(order="F")
        if obj.size == 0:
            obj.shape = (0, 0)
        return obj

    def __getitem__(self, index):
        return self.get(index)


#    def __str__(self):
#        if self.ndim == 0:
#            return ""
#        if self.ndim == 1:
#            return "".join(s for s in self)
#        if self.ndim == 2:
#            return "\n".join("".join(s) for s in self)
#        raise NotImplementedError


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
            np.array(
                ["".join(s) for s in a], dtype=object, copy=False, order="C", ndmin=2
            )
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
            np.array(list(a), dtype="|S1", copy=False, order="F", ndmin=2)
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


class struct(object):
    def __init__(self, *args):
        for i in range(0, len(args), 2):
            setattr(self, str(args[i]), args[i + 1])


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
        np.arange(start, stop + expand_value, step, **kwargs).reshape(1, -1), **kwargs
    )


def concat(args):
    """
    >>> concat([[1,2,3,4,5] , [1,2,3,4,5]])
    [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
    """
    t = [matlabarray(a) for a in args]
    return np.concatenate(t)


def reshape(a, shape):
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
    return matlabarray(np.asanyarray(a).copy(order="F"))


def deal(a, **kwargs):
    # import pdb; pdb.set_trace()
    return tuple([ai for ai in a.flat])


def disp(*args):
    print(args)


def eig(a):
    u, v = np.linalg.eig(a)
    return u.T


def logical_not(a):
    return np.logical_not(a)


def logical_and(a, b):
    return np.logical_and(a, b)


def logical_or(a, b):
    return np.logical_or(a, b)


def exist(a, b='file'):
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
    return int(np.floor(a))


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
    if nargout == 1:
        c = sorted(set(a) & set(b))
        if isinstance(a, str):
            return "".join(c)
        elif isinstance(a, list):
            return c
        else:
            # FIXME: the result is a column vector if
            # both args are column vectors; otherwise row vector
            return np.array(c)
    raise NotImplementedError


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
    try:
        return max(np.asarray(a).shape)
    except ValueError:
        return 1


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
    return np.random.randint(1, hi+1, args).reshape(args, order="F")


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
    pass


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
            return matlabarray(s) if nargout <= 1 else s
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


def strread(s, format="", nargout=1):
    if format == "":
        a = [float(x) for x in s.split()]
        return tuple(a) if nargout > 1 else np.asanyarray([a])
    raise NotImplementedError


def strrep(a, b, c):
    return str(a).replace(str(b), str(c))


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
    if len(args) == 1:
        args += args
    return matlabarray(np.zeros(args, **kwargs))


def ones(*args, **kwargs):
    if not args:
        return 1
    if len(args) == 1:
        args += args
    return matlabarray(np.ones(args, order="F", **kwargs))


def print_usage():
    raise Exception


def function(f):
    from contextlib import redirect_stdout, redirect_stderr
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        with (
            redirect_stdout(kwargs.pop("stdout", stdout)),
            redirect_stderr(kwargs.pop("stderr", stderr)),
        ):
            nargout = kwargs.pop("nargout", None)
            assert not kwargs
            return f(*args)[:nargout]

    return wrapper


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


def mean(a, axis=None):
    """
    Compute the mean of the elements along the specified axis.
    """
    return np.mean(np.asarray(a), axis=axis)


def std(a, axis=None):
    """
    Compute the standard deviation of the elements along the specified axis.
    """
    return np.std(np.asarray(a), axis=axis)


def var(a, axis=None):
    """
    Compute the variance of the elements along the specified axis.
    """
    return np.var(np.asarray(a), axis=axis)


def max(a, axis=None):
    """
    Return the maximum of an array or maximum along an axis.
    """
    return np.amax(np.asarray(a), axis=axis)


def min(a, axis=None):
    """
    Return the minimum of an array or minimum along an axis.
    """
    return np.amin(np.asarray(a), axis=axis)


def NaN():
    """
    Return a NaN (Not a Number) value.
    """
    return float("nan")


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


def interp1(x, y, xi):
    """
    One-dimensional linear interpolation.
    """
    return matlabarray(np.interp(xi, x, y))


def prctile(a, q):
    """
    Compute the q-th percentile of the data along the specified axis.
    """
    return np.percentile(np.asarray(a), q)


def datenum(date):
    """
    Convert a date string to a MATLAB datenum.
    """
    return (np.datetime64(date) - np.datetime64("1970-01-01")).astype(
        "timedelta64[D]"
    ).astype(int) + 719529


def datevec(datenum):
    """
    Convert a MATLAB datenum to a date vector.
    """
    dt = np.datetime64("1970-01-01") + np.timedelta64(datenum - 719529, "D")
    return matlabarray(
        [
            dt.astype("datetime64[Y]").astype(int) + 1970,
            dt.astype("datetime64[M]").astype(int) % 12 + 1,
            dt.astype("datetime64[D]").astype(int) % 31 + 1,
            dt.astype("datetime64[h]").astype(int) % 24,
            dt.astype("datetime64[m]").astype(int) % 60,
            dt.astype("datetime64[s]").astype(int) % 60,
        ]
    )


def nanmean(a, axis=None):
    """
    Compute the mean of an array while ignoring NaNs.
    """
    return np.nanmean(np.asarray(a), axis=axis)


def nanmedian(a, axis=None):
    """
    Compute the median of an array while ignoring NaNs.
    """
    return np.nanmedian(np.asarray(a), axis=axis)


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


def regress(y, x):
    """
    Perform linear regression.
    """

    x = np.column_stack((np.ones(x.shape[0]), x))  # Add intercept
    return inv(x.T @ x) @ x.T @ y


def corrcoef(x, y):
    """
    Return the correlation coefficients.
    """
    return np.corrcoef(np.asarray(x), np.asarray(y))


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
    if message == 'off':
        warnings.filterwarnings("ignore")
    elif message == 'on':
        warnings.filterwarnings("default")
    else:
        warnings.warn(message)


if __name__ == "__main__":
    import doctest

    doctest.testmod()

