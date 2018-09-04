'''
oneflux.partition.auxiliary

For license information:
see LICENSE file or headers in oneflux.__init__.py 

Partitioning auxiliary functions

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''
import sys
import os
import logging
import numpy

from io import StringIO
from datetime import datetime, timedelta

from oneflux import ONEFluxError

from oneflux.graph.compare import plot_comparison

NAN = -9999.0
NAN_TEST = -9990.0
NAN_EXT_TEST = -6990.0
#FLOAT_PREC = 'f8'
FLOAT_PREC = 'f4'
DOUBLE_PREC = 'f8'


_log = logging.getLogger(__name__)

def nan(array):
    """
    Returns boolean value/array with True at all positions where
    number is NAN or INF or <= NAN_TEST 
    
    :param array: array (or float) - not record/structured arrays
    :type array: numpy.array
    """
    return numpy.isnan(array) | numpy.isinf(array) | (array <= NAN_TEST)

def nan_ext(array):
    """
    Returns boolean value/array with True at all positions where
    number is NAN or INF or <= NAN_TEST or <= NAN_EXT_TEST  
    
    :param array: array (or float) - not record/structured arrays
    :type array: numpy.array
    """
    return numpy.isnan(array) | numpy.isinf(array) | (array <= NAN_TEST) | (array <= NAN_EXT_TEST)

def not_nan(array):
    """
    Returns boolean value/array with False at all positions where
    number is NAN or INF or <= NAN_TEST 
    
    :param array: array (or float) - not record/structured arrays
    :type array: numpy.array
    """
    return ~nan(array=array)

def compare_col_to_pvwave(py_array, filename, label=None, diff=False, show_plot=False, save_plot=False, year=None, resolution=None, epsilon=None):
    """
    Compares data in 1D array to data in file (output from PV-Wave)
    
    sample call:
            compare_col_to_pvwave(py_array=data['daylight'],
                                  filename="/path/to/data/fluxnet/CC-SSS/test_daylight.csv",
                                  label='daylight',
                                  diff=True,
                                  plot=False,
                                  epsilon=0.01)

    :param py_array: data from Python execution to be compared
    :type py_array: numpy.ndarray
    :param filename: full path filename for equivalent PV-Wave data
    :type filename: str
    :param label: variable being compared
    :type label: str
    :param diff: if True, prints differences between data
    :type diff: bool
    :param show_plot: if True, generates comparison plot between data (show interactive)
    :type show_plot: bool
    :param save_plot: if True, generates comparison plot between data (save png using filename)
    :type save_plot: bool
    :param year: year for array being compared (plot only)
    :type year: int
    :param resolution: either hh or hr (plot only)
    :type resolution: str
    :param epsilon: max difference values
    :type epsilon: float
    """

    if not os.path.isfile(filename):
        msg = "PV-Wave output data file does not exit: '{f}'".format(f=filename)
        _log.error(msg)
        return

    if label is None:
        label = os.path.basename(filename)
        _log.debug("Label set to '{l}'".format(l=label))

    # load PV-Wave output data
    _log.info("Loading PV-Wave data output file: '{f}'".format(f=filename))
    # using string load because genfromtxt does not handle all missing values correctly
    with open(filename) as f:
        s_string = f.read()
    s_string = s_string.replace(' ', '')
    s_string = s_string.replace('-1.#IND000', '-9999')
    s_string = s_string.replace('\r', '')
    u_string = unicode(s_string)
    pw_array = numpy.genfromtxt(StringIO(u_string), dtype=FLOAT_PREC, delimiter=',', skip_header=0, missing_values='-9999,-9999.0,-6999,-6999.0, ', usemask=True)
    pw_array = numpy.ma.filled(pw_array, numpy.NaN)
    # **************************************************************************************************************************************************
    pw_array = pw_array[:, 1]  # remove jday # TODO: incorporate jday into plot, loading from output files instead of within python code ***************

    if py_array.size != pw_array.size:
        msg = "Python size ({py}) differs from PV-Wave site ({pw})".format(py=py_array.size, pw=pw_array.size)
        _log.error(msg)
        return

    # set -9999 to NaN
    py_nan = nan(py_array)
    pw_nan = nan(pw_array)
    all_nan = py_nan | pw_nan
    no_nan = ~all_nan
    py_array[py_nan] = numpy.NaN
    pw_array[pw_nan] = numpy.NaN

    # generate 1-1 difference info
    if diff:
        _log.info("Generating Python / PV-Wave difference info for '{l}'".format(l=label))

        # compare NaN values
        nan_diff = py_nan != pw_nan
        nan_equal = py_nan == pw_nan
        _log.info("Python / PV-Wave NaN - total: {t}, NaN-equal: {e}, NaN-differ: {d}".format(t=nan_diff.size, e=numpy.sum(nan_equal), d=numpy.sum(nan_diff)))

        # compare non-NaN values
        if epsilon is None:
            v_equal = py_array == pw_array
            v_differ = ~v_equal
            _log.info("Python / PV-Wave non-NaN - all equal: {v}, total: {t}, equal: {e}, differ: {d}".format(v=numpy.all(v_equal[no_nan])), t=v_equal[no_nan].size, e=numpy.sum(v_equal[no_nan]), d=numpy.sum(v_differ[no_nan]))
        else:
            v_equal = numpy.absolute(py_array - pw_array) < epsilon
            v_differ = ~v_equal
            _log.info("Python / PV-Wave non-NaN (epsilon: {r}) - all equal: {v}, total: {t}, equal: {e}, differ: {d}".format(r=epsilon, v=numpy.all(v_equal[no_nan]), t=v_equal[no_nan].size, e=numpy.sum(v_equal[no_nan]), d=numpy.sum(v_differ[no_nan])))

        # show non-NaN differences
        count_differ = numpy.sum(v_differ[no_nan])
        if count_differ != 0:
            idx_differ = numpy.where(v_differ)[0]
            idx_no_nan = numpy.where(no_nan)[0]
            idx_differ_no_nan = numpy.intersect1d(idx_differ, idx_no_nan)
            if idx_differ_no_nan.size <= 10:
                entries = ""
                for i in idx_differ_no_nan:
                    entries += "( PY[{i}]={py}, PW[{i}]={pw} ), ".format(i=i, py=py_array[i], pw=pw_array[i])
                entries = entries[:-2]
            else:
                entries = ""
                for i in idx_differ_no_nan[:5]:
                    entries += "( PY[{i}]={py}, PW[{i}]={pw} ), ".format(i=i, py=py_array[i], pw=pw_array[i])
                entries += '..., '
                for i in idx_differ_no_nan[-5:]:
                    entries += "( PY[{i}]={py}, PW[{i}]={pw} ), ".format(i=i, py=py_array[i], pw=pw_array[i])
                entries = entries[:-2]
            _log.info("Python / PV-Wave non-NaN (epsilon: {r}) differences: {d}".format(r=epsilon, d=entries))

    # generate comparison plot
    if show_plot or save_plot:
        _log.info("Generating Python / PV-Wave comparison plot for '{l}'".format(l=label))
        # TODO: test
        # TODO: refactor for each possible values, error when not one of the 4 possible...
        # TODO: add epsilon

        if py_array.size == 17520:
            if year is None: year = 2001
            if resolution is None: resolution = 'hh'
        elif py_array.size == 17568:
            if year is None: year = 2000
            if resolution is None: resolution = 'hh'
        elif py_array.size == 8760:
            if year is None: year = 2001
            if resolution is None: resolution = 'hr'
        elif py_array.size == 8788:
            if year is None: year = 2000
            if resolution is None: resolution = 'hr'
        elif py_array.size < 8760:
            _log.info("Not time series, using 'time' for non-temporal comparison")
            if year is None: year = 2000
            if resolution is None: resolution = 'hr'
        else:
            msg = "Unexpected array size '{s}', should be one of [17520, 17568, 8760, 8788]".format(s=py_array.size)
            _log.error(msg)
            return

        figure_basename = None
        if save_plot:
            figure_basename, _ = os.path.splitext(filename)
            figure_basename = figure_basename.replace('_PW', '') # remove _PW from PW data source filename

        record_interval = (timedelta(minutes=30) if resolution == 'hh' else timedelta(minutes=60))
        timestamp_list = [datetime(year, 1, 1, 0, 0) + (record_interval * i) for i in xrange(1, py_array.size + 1)]

        _log.debug("Using year={y}, resolution={r}, first timestamp={f}, last timestamp={l}".format(y=year, r=resolution, f=timestamp_list[0], l=timestamp_list[-1]))

        plot_comparison(timestamp_list=timestamp_list, data1=py_array, data2=pw_array, label1='PY', label2='PW', title=label, basename=figure_basename, show=show_plot)



if __name__ == '__main__':
    raise ONEFluxError('Not executable')
