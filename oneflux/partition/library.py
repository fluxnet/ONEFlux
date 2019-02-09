'''
oneflux.partition.library

For license information:
see LICENSE file or headers in oneflux.__init__.py 

Library of optimization related functions

@author: Gilberto Pastorello, Abdelrahman Elbashandy
@contact: gzpastorello@lbl.gov, aaelbashandy@lbl.gov
@date: 2017-01-31
'''

import os
import sys
import logging
import numpy
from datetime import datetime

from scipy.optimize import leastsq
from scipy.stats import rankdata

from oneflux import ONEFluxError
from oneflux.partition.ecogeo import lloyd_taylor, lloyd_taylor_dt, hlrc_lloyd, hlrc_lloydvpd
from oneflux.partition.ecogeo import hlrc_lloyd_afix, hlrc_lloydvpd_afix, lloydt_e0fix
from oneflux.partition.auxiliary import FLOAT_PREC, DOUBLE_PREC, NAN, nan, not_nan

from oneflux.graph.compare import plot_comparison
from oneflux.utils.files import file_exists_not_empty

_log = logging.getLogger(__name__)

NT_STR = 'NT'
DT_STR = 'DT'

QC_AUTO_DIR = "02_qc_auto"
METEO_PROC_DIR = "07_meteo_proc"
NEE_PROC_DIR = "08_nee_proc"
NT_OUTPUT_DIR = "10_nee_partition_nt"
DT_OUTPUT_DIR = "11_nee_partition_dt"

STRING_HEADERS = ['isodate', 'timestamp', 'timestamp_start', 'timestamp_end', 'dtime', 'date', 'time']

HEADER_SEPARATOR = '__'

PERCENTILES_DATA_COLUMNS = ['1.25', '3.75', '6.25', '8.75', '11.25', '13.75', '16.25', '18.75',
                            '21.25', '23.75', '26.25', '28.75', '31.25', '33.75', '36.25', '38.75',
                            '41.25', '43.75', '46.25', '48.75', '50', '51.25', '53.75', '56.25', '58.75',
                            '61.25', '63.75', '66.25', '68.75', '71.25', '73.75', '76.25', '78.75',
                            '81.25', '83.75', '86.25', '88.75', '91.25', '93.75', '96.25', '98.75', ]
PERCENTILES_DATA_COLUMNS = [i.replace('.', HEADER_SEPARATOR) for i in PERCENTILES_DATA_COLUMNS]

EXTRA_FILENAME = ""


class ONEFluxPartitionError(ONEFluxError):
    """
    Pipeline ONEFlux error - Partitioning specific
    """
    pass


def load_output(filename, delimiter=',', skip_header=1):
    """
    Loads 'output' formatted file (e.g., from output of nee_proc or meteo_proc)
    
    :param filename: Name of file to be loaded
    :type filename: str
    """
    _log.info("Started loading '{f}'".format(f=filename))

    _log.debug("Started loading headers")
    with open(filename, 'r') as f:
        header_line = f.readline()
    headers = [i.strip().replace('.', HEADER_SEPARATOR).lower() for i in header_line.strip().split(delimiter)]
    _log.debug("Finished loading headers: {h}".format(h=headers))

    _log.debug("Started loading data")
    dtype = [(i, ('a25' if i.lower() in STRING_HEADERS else FLOAT_PREC)) for i in headers]
    vfill = [('' if i.lower() in STRING_HEADERS else numpy.NaN) for i in headers]
    data = numpy.genfromtxt(fname=filename, dtype=dtype, names=headers, delimiter=delimiter, skip_header=skip_header, missing_values='-9999,-9999.0,-6999,-6999.0, ', usemask=True)
    data = numpy.ma.filled(data, vfill)

    new_dtype = dtype + [('year', FLOAT_PREC), ('month', FLOAT_PREC), ('day', FLOAT_PREC), ('hour', FLOAT_PREC), ('minute', FLOAT_PREC)]
    new_data = numpy.zeros(len(data), dtype=new_dtype)
    for h in headers:
        new_data[h] = data[h]
    _log.debug("Finished loading data")

    _log.debug("Started loading timestamps")
    timestamp_list = []

    # TODO: the arrays below were added as a workaround for slower performance for structured arrays in numpy 1.10.1;
    #       once fixed (1.10.2?), array_* should be removed
    #       see bug: https://github.com/numpy/numpy/issues/6467
    array_year = numpy.empty(len(data), dtype='i4')
    array_month = numpy.empty(len(data), dtype='i4')
    array_day = numpy.empty(len(data), dtype='i4')
    array_hour = numpy.empty(len(data), dtype='i4')
    array_minute = numpy.empty(len(data), dtype='i4')
    it = numpy.nditer(new_data['timestamp_end'], flags=['f_index'])
    while not it.finished:
        timestamp = datetime.strptime(str(it.value), "%Y%m%d%H%M")
        array_year[it.index] = timestamp.year
        array_month[it.index] = timestamp.month
        array_day[it.index] = timestamp.day
        array_hour[it.index] = timestamp.hour
        array_minute[it.index] = timestamp.minute
        timestamp_list.append(timestamp)
        it.iternext()
    new_data['year'][:] = array_year
    new_data['month'][:] = array_month
    new_data['day'][:] = array_day
    new_data['hour'][:] = array_hour
    new_data['minute'][:] = array_minute
    year_array = numpy.unique(ar=new_data['year'])

    _log.debug("Finished loading timestamps: first(END)={f}, last(END)={l}, years={y}".format(f=new_data['timestamp_end'][0], l=new_data['timestamp_end'][-1], y=list(year_array)))

    # need to remove last entry when using end-of-averaging period convention
    year_list = sorted([int(i) for i in year_array])[:-1]

    _log.info("Finished loading '{f}'".format(f=filename))
    return new_data, headers, timestamp_list, year_list


def get_latitude(filename, delimiter=','):
    """
    Retrieves latitude from year 'input' formatted data file
    
    :param filename: Name of file to be loaded
    :type filename: str
    :param delimiter: Cell delimiter character(s)
    :type delimiter: str
    """
    _log.debug("Looking for latitude field in '{f}'".format(f=filename))
    with open(filename, 'r') as f:
        field_name = ''
        while field_name.lower() not in STRING_HEADERS:
            line = f.readline()
            l = [i.strip().lower() for i in line.strip().split(delimiter)]
            field_name = l[0]
            if field_name == 'lat':
                return float(l[1])
    msg = "Latitude field not found in file '{f}'".format(f=filename)
    _log.critical(msg)
    raise ONEFluxError(msg)


def add_empty_vars(data, records, column, unit='-'):
    """
    Checks 'column' is a valid column name and assigns records to that column

    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param records: records to be added to 'new' column (was vari in original code)
    :type records: numpuy.ndarray
    :param column: column/variable name (was name in original code)
    :type column: str
    :param unit: variable units (not used here)
    :type unit: str
    """

    if column not in list(data.dtype.names):
        msg = "Column '{c}' not found in data array".format(c=column)
        _log.error(msg)
        raise ONEFluxError(msg)

    # if no len attribute, it's a scalar; note: not accounting for strings...
    if hasattr(records, "__len__") and (len(records) != len(data)):
        msg = "Number of records '{r}' differ data array size '{s}'".format(r=len(records), s=len(data))
        _log.error(msg)
        raise ONEFluxError(msg)

    data[column][:] = records


def var(data, column):
    """
    Returns 1D array of data in column label
    
    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param column: column/variable name to be retrieved
    :type column: str
    """

    # check columns and prepare parameters for function
    varnum(data=data, columns=[column])

    return data[column]


def varnum(data, columns):
    """
    Checks if data array has all columns
    
    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param columns: list of columns from data array to be used as target and parameters
    :type columns: list (of str)
    """
    for col in columns:
        if col not in list(data.dtype.names):
            msg = "Column '{c}' not found in data array".format(c=col)
            _log.error(msg)
            raise ONEFluxError(msg)


def newselif(data, condition, drop=False, columns=None):
    """
    Filter data set using condition; drops records or removes variables
    depending on drop and vars parameters
    
    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param condition: numpy boolean mask of condition
    :type condition: numpy.ndarray (dtype bool)
    :param drop: if True, returns only records where condition True (all vars);
                 if False, returns copy array with original dimensions
                 and records where condition is False set to NAN (only vars listed in columns)
    :type drop: boolean
    :param columns: list of columns to be filtered if drop is false (if None, filters all)
    :type columns: list
    """

    if condition.any() == False:
        condition[0] = True
    ok = numpy.where(condition)   # indices of where condition is True
    nok = numpy.where(~condition) # indices of where condition is False

    result = data

    if columns:
        # check columns and prepare parameters for function
        varnum(data=data, columns=columns)
    else:
        # if None, filter all columns
        columns = list(data.dtype.names)

    if drop:
        result = result[condition]
    else:
        result = result.copy()
        for var in columns:
            result[var][~condition] = NAN

    return (result, ok, nok)


def nomi(data, columns):
    """
    Returns array with only the columns listed, filtering to include
    only records where all columns are non-NA 
    
    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param columns: list of columns to be filtered
    :type columns: list (of str)
    """

    # check columns and prepare parameters for function
    varnum(data=data, columns=columns)

    nonnan_mask = numpy.ones(data.size, dtype=bool)
    if len(columns) > 0:
        for col in columns:
            nonnan_mask = nonnan_mask & not_nan(data[col])
    nan_mask = ~nonnan_mask

    return data[nonnan_mask], nonnan_mask, nan_mask


def jacobian(func, data, params_filled_arr, params_filled_arr2, params):
    '''
    :Task:  Calculate the jacobian matrix

    :param func: function model to use
    :type func: str
    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param params_filled_arr: Array of replicated E0 values
    :type params_filled_arr: numpy.ndarray
    :param params_filled_arr2: Array of replicated alpha values
    :type params_filled_arr2: numpy.ndarray
    :param params: optimized parameters to be applied to the model
    :type params: numpy.ndarray
    '''

    funcval = None
    if func == "HLRC_Lloyd":
        funcval = hlrc_lloyd(rg_f=data['rg_f'].astype(DOUBLE_PREC), ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), parameter=params)
    if func == "HLRC_LloydVPD":
        funcval = hlrc_lloydvpd(rg_f=data['rg_f'].astype(DOUBLE_PREC), ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), vpd_f=data['vpd_f'].astype(DOUBLE_PREC), parameter=params)
    if func == "HLRC_Lloyd_afix":
        funcval = hlrc_lloyd_afix(rg_f=data['rg_f'].astype(DOUBLE_PREC), ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), alpha=params_filled_arr2.astype(DOUBLE_PREC), parameter=params)
    if func == "HLRC_LloydVPD_afix":
        funcval = hlrc_lloydvpd_afix(rg_f=data['rg_f'].astype(DOUBLE_PREC), ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), vpd_f=data['vpd_f'].astype(DOUBLE_PREC), alpha=params_filled_arr2.astype(DOUBLE_PREC), parameter=params)
    if func == "LloydT_E0fix":
        funcval = lloydt_e0fix(ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), parameter=params)

    if isinstance(params, numpy.float32) or isinstance(params, numpy.float64) \
        or isinstance(params, numpy.int32) or isinstance(params, numpy.int64):
        #print("params = [params]")
        params = [params]

    nf = funcval.size
    np = len(params)

    '''
    print("nf")
    print(nf)
    print("np")
    print(np)
    '''

    j = numpy.zeros((np, nf), dtype=FLOAT_PREC)
    deltaRel = 1.e-3
    for p in range(np):
        paramsPlus = numpy.copy(params)
        paramsPlus[p] = params[p] + deltaRel * numpy.abs(params[p])
        paramsMinus = numpy.copy(params)
        paramsMinus[p] = params[p] - deltaRel * numpy.abs(params[p])
        fplus = None
        fminus = None
        #print("func")
        #print(func)
        if func == "HLRC_Lloyd":
            fplus = hlrc_lloyd(rg_f=data['rg_f'].astype(DOUBLE_PREC), ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), parameter=paramsPlus)
            fminus = hlrc_lloyd(rg_f=data['rg_f'].astype(DOUBLE_PREC), ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), parameter=paramsMinus)
        if func == "HLRC_LloydVPD":
            #print("paramsPlus")
            #print(paramsPlus)
            fplus = hlrc_lloydvpd(rg_f=data['rg_f'].astype(DOUBLE_PREC), ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), vpd_f=data['vpd_f'].astype(DOUBLE_PREC), parameter=paramsPlus)
            fminus = hlrc_lloydvpd(rg_f=data['rg_f'].astype(DOUBLE_PREC), ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), vpd_f=data['vpd_f'].astype(DOUBLE_PREC), parameter=paramsMinus)
        if func == "HLRC_Lloyd_afix":
            fplus = hlrc_lloyd_afix(rg_f=data['rg_f'].astype(DOUBLE_PREC), ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), alpha=params_filled_arr2.astype(DOUBLE_PREC), parameter=paramsPlus)
            fminus = hlrc_lloyd_afix(rg_f=data['rg_f'].astype(DOUBLE_PREC), ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), alpha=params_filled_arr2.astype(DOUBLE_PREC), parameter=paramsMinus)
        if func == "HLRC_LloydVPD_afix":
            fplus = hlrc_lloydvpd_afix(rg_f=data['rg_f'].astype(DOUBLE_PREC), ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), vpd_f=data['vpd_f'].astype(DOUBLE_PREC), alpha=params_filled_arr2.astype(DOUBLE_PREC), parameter=paramsPlus)
            fminus = hlrc_lloydvpd_afix(rg_f=data['rg_f'].astype(DOUBLE_PREC), ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), vpd_f=data['vpd_f'].astype(DOUBLE_PREC), alpha=params_filled_arr2.astype(DOUBLE_PREC), parameter=paramsMinus)
        if func == "LloydT_E0fix":
            fplus = lloydt_e0fix(ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), parameter=paramsPlus)
            fminus = lloydt_e0fix(ta_f=data['tair_f'].astype(DOUBLE_PREC), e0=params_filled_arr.astype(DOUBLE_PREC), parameter=paramsMinus)

        j[p, :] = (fplus - fminus) / (paramsPlus[p] - paramsMinus[p])

    return j



WINDOW_SIZE = 4      # number of days to include in window
BR_PERC = 0.0
def nlinlts2(data, lts_func, depvar, indepvar_arr, npara, xguess,
                mprior, sigm, sigd, window_size=WINDOW_SIZE, trim_perc=BR_PERC):
    """
    Main non-linear least-squares driver function
    
    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param func: function to be optimized
    :type func: function
    :param depvar: dependent variable (computed by function)
    :type depvar: str
    :param indepvar: independent variable (parameter to function)
    :type indepvar: str list
    :param npara: number of parameters to be optimized
    :type npara: int
    :param xguess: list with initial/starting guesses for variables to be optimized 
    :type xguess: list
    :param trim_perc: precentage to trim from residual values
    :type trim_perc: float
    """
    if len(xguess) != npara:
        msg = "Incompatible number of parameters '{n}' and length of initial guess '{i}'".format(n=npara, i=len(xguess))
        _log.critical(msg)
        raise ONEFluxError(msg)

    status = 0 # status of execution; 0 optimization executed successfully, -1 problem with execution of optimization
    first_ts, last_ts = get_first_last_ts(data=data)
#    _log.debug("Starting optimization step for period '{ts1}' - '{ts2}'".format(ts1=first_ts.strftime('%Y-%m-%d %H:%M'), ts2=last_ts.strftime('%Y-%m-%d %H:%M')))

    # check number of entries for independent variable
    _, nonnan_indep_mask, _ = nomi(data, indepvar_arr)

    '''
    print("numpy.sum(nonnan_indep_mask)")
    print(numpy.sum(nonnan_indep_mask))
    print("npara")
    print(npara)
    print("npara * 3")
    print(npara * 3)
    '''

    # Adding dictionary to include all the returned values
    temp_res = numpy.empty(numpy.sum(nonnan_indep_mask))
    temp_res.fill(NAN)
    temp_cov_matrix = numpy.zeros((npara, npara))
    temp_cor_matrix = numpy.empty((npara, npara))
    temp_cor_matrix.fill(numpy.NINF)
    result_dict = {
        'status':-1,
        'alpha':-9999.0,
        'beta':-9999.0,
        'k':-9999.0,
        'rref':-9999.0,
        'e0':-9999.0,
        'alpha_std_error': 0.0,
        'beta_std_error': 0.0,
        'k_std_error': 0.0,
        'rref_std_error': 0.0,
        'e0_std_error': 0.0,
        'residuals': temp_res,
        'cov_matrix': temp_cov_matrix,
        'cor_matrix': temp_cor_matrix,
        'rmse': 0.0,
        'ls_status': None
    }

    if numpy.sum(nonnan_indep_mask) < (npara * 3):
        _log.warning("Not enough data points (independent variable filtered) for optimization: {n}".format(n=numpy.sum(nonnan_indep_mask)))
        status = -1

        #return status, -9999.0, -9999.0, -9999.0, -9999.0, None, None
        return result_dict

    # check number of entries for dependent AND independent variable
    nonnan_dep_mask = not_nan(data[depvar])
    nonnan_combined_mask = nonnan_indep_mask & nonnan_dep_mask
    if numpy.sum(nonnan_combined_mask) < (npara * 3):
        _log.warning("Not enough data points (dependent and independent variable filtered) for optimization: {n}".format(n=numpy.sum(nonnan_combined_mask)))
        status = -1
        '''
        if lts_func == "LloydTemp":
            return status, -9999.0, -9999.0, -9999.0, -9999.0, None, None
        if lts_func == "HLRC_Lloyd":
            return status, -9999.0, -9999.0, -9999.0, -9999.0, None, None
        if lts_func == "HLRC_LloydVPD":
            return status, -9999.0, -9999.0, -9999.0, -9999.0, None, None
        if lts_func == "HLRC_Lloyd_afix":
            return status, -9999.0, -9999.0, -9999.0, -9999.0, None, None
        if lts_func == "HLRC_LloydVPD_afix":
            return status, -9999.0, -9999.0, -9999.0, -9999.0, None, None
        if lts_func == "LloydT_E0fix":
            return status, -9999.0, -9999.0, -9999.0, -9999.0, None, None
        '''

        #return status, -9999.0, -9999.0, -9999.0, -9999.0, None, None
        return result_dict

    # "clean" dependent variable so not to use NAs from independent variable
    clean_dep = data[depvar].copy()
    clean_dep[~nonnan_indep_mask] = NAN

    leastsq_count = [1]

    # define inner function to be used for optimization
    def trimmed_bayes_res(par, nee=clean_dep, trim_perc=trim_perc):
        """
        (inner) Function to be evaluated at each iteration,
        taking care of handling NAs and trimming residuals.
        Inner function used so extra arguments not needed in
        call to scipy leastsq function

        :param nee: array with (non-cleaned) nee values (dependent variable)
        :type nee: numpy.ndarray
        :param temp: array with (cleaned, no NAs) temperature (independent variable)
        :type temp: numpy.ndarray
        :param rref: reference respiration (1st parameter to be optimized)
        :type rref: float
        :param e0: temperature sensitivity (2nd parameter to be optimized)
        :type e0: float
        :param trim_perc: percentiled to be trimmed off
        :type trim_perc: float
        """
        prediction = None

        #print("leastsq_count")
        #print(leastsq_count)

        if lts_func == "LloydTemp":
            prediction = lloyd_taylor_dt(ta_f=data[indepvar_arr[0]].astype(DOUBLE_PREC), parameter=par)
            '''
            print("par")
            print(par)
            print("mprior")
            print(mprior)
            print("sigm")
            print(sigm)
            print("sigd")
            print(sigd)
            #print("indepvar[0]")
            #print(indepvar[0])
            #print("data[indepvar[0]]")
            #print(data[indepvar[0]])
            #print("prediction")
            #print(prediction)
            '''
        if lts_func == "HLRC_Lloyd":
            prediction = hlrc_lloyd(rg_f=data[indepvar_arr[0]].astype(DOUBLE_PREC), ta_f=data[indepvar_arr[1]].astype(DOUBLE_PREC), e0=data[indepvar_arr[2]].astype(DOUBLE_PREC), parameter=par)
        if lts_func == "HLRC_LloydVPD":
            #if leastsq_count[0] == 6:
            #    par = numpy.array([-0.020768575, 1.9603746, 0.0, 0.40222415], dtype=DOUBLE_PREC)
            prediction = hlrc_lloydvpd(rg_f=data[indepvar_arr[0]].astype(DOUBLE_PREC), ta_f=data[indepvar_arr[1]].astype(DOUBLE_PREC), e0=data[indepvar_arr[2]].astype(DOUBLE_PREC), vpd_f=data[indepvar_arr[3]].astype(DOUBLE_PREC), parameter=par)
            #print("par")
            #print(par)
            #if leastsq_count[0] == 1:
            #    print("mprior")
            #    print(mprior)
            #    print("sigm")
            #    print(sigm)
            #    print("sigd")
            #    print(sigd)
            #print("indepvar[0]")
            #print(indepvar[0])
            #print("data[indepvar[0]]")
            #print(data[indepvar[0]])
            #print("prediction")
            #print(prediction)
        if lts_func == "HLRC_Lloyd_afix":
            prediction = hlrc_lloyd_afix(rg_f=data[indepvar_arr[0]].astype(DOUBLE_PREC), ta_f=data[indepvar_arr[1]].astype(DOUBLE_PREC), e0=data[indepvar_arr[2]].astype(DOUBLE_PREC), alpha=data[indepvar_arr[3]].astype(DOUBLE_PREC), parameter=par)
        if lts_func == "HLRC_LloydVPD_afix":
            prediction = hlrc_lloydvpd_afix(rg_f=data[indepvar_arr[0]].astype(DOUBLE_PREC), ta_f=data[indepvar_arr[1]].astype(DOUBLE_PREC), e0=data[indepvar_arr[2]].astype(DOUBLE_PREC), vpd_f=data[indepvar_arr[3]].astype(DOUBLE_PREC), alpha=data[indepvar_arr[4]].astype(DOUBLE_PREC), parameter=par)
        if lts_func == "LloydT_E0fix":
            prediction = lloydt_e0fix(ta_f=data[indepvar_arr[0]].astype(DOUBLE_PREC), e0=data[indepvar_arr[1]].astype(DOUBLE_PREC), parameter=par)


        residuals = (nee - prediction) / sigd
        nonnan_nee_mask = not_nan(nee)
        residuals[~nonnan_nee_mask] = 0.0

        pres = (par - mprior) / sigm


        #print("residuals")
        #print(residuals)
        #print("pres")
        #print(pres)
        #print("numpy.append(residuals, pres)")
        #print(numpy.append(residuals, pres))


        #print("par.dtype")
        #print(par.dtype)
        #print("data[indepvar[0]].dtype")
        #print(data[indepvar[0]].dtype)
        #print("prediction.dtype")
        #print(prediction.dtype)
        #print("nee.dtype")
        #print(nee.dtype)
        #print("sigm.dtype")
        #print(sigm.dtype)
        #print("sigd.dtype")
        #print(sigd.dtype)
        #print("mprior.dtype")
        #print(mprior.dtype)
        #print("residuals.dtype")
        #print(residuals.dtype)
        #print("pres.dtype")
        #print(pres.dtype)
        #print("(par - mprior).dtype")
        #print((par - mprior).dtype)


        # NOTE: compareIndex and compindex not used in NT partitioning code

        #if leastsq_count[0] == 10 and lts_func == "HLRC_LloydVPD":
        #    exit()
        leastsq_count[0] += 1


        if trim_perc == 0.0:
            return numpy.append(residuals, pres)

        absolute_residuals = numpy.abs(residuals)
        pct_calc = pct(absolute_residuals, 100.0 - trim_perc)
        trim_mask = (absolute_residuals > pct_calc)
        residuals[trim_mask] = 0.0

#        print 'rref/e0/res:', rref, e0, numpy.sum(residuals ** 2)

        return numpy.append(residuals, pres)

    #print("starting least_squares")
    parameters, std_devs, ls_status, residuals, covariance_matrix, cor_matrix = least_squares(func=trimmed_bayes_res,
                                                                                  initial_guess=xguess,
                                                                                  entries=len(clean_dep),
                                                                                  iterations=1000 * (len(clean_dep) + 1),
                                                                                  return_residuals_cov_mat=True)
    '''
    print("ending least_squares")
    print("ls_status")
    print(ls_status)
    print("parameters")
    print(parameters)
    print("std_devs")
    print(std_devs)
    print("residuals")
    print(residuals)
    print("covariance_matrix")
    print(covariance_matrix)
    print("cor_matrix")
    print(cor_matrix)
    '''
    # NOTE: calculation of residuals in the original code used only for graph, so not added here

    # add zeros to residuals, if lenght of residuals less than maximum number of entries for window
    # done to match original code, purpose unclear
    #if len(residuals) < 48 * window_size:
    #    new_residuals = numpy.zeros(48 * window_size, dtype=FLOAT_PREC)
    #    new_residuals[:len(residuals)] = residuals
    #else:
    #    new_residuals = residuals

    # TODO: save est_e0_std (****std errors****) -- compare with new output from PV-Wave

    # NOTE: if changing return values, also update case for "not enough data points"

    nee = clean_dep

    if lts_func == "LloydTemp":
        est_rref, est_e0 = parameters
        est_rref_std, est_e0_std = std_devs
        prediction = lloyd_taylor_dt(ta_f=data[indepvar_arr[0]].astype(DOUBLE_PREC), parameter=parameters)

        est_rmse = root_mean_sq_error(nee, prediction, trim_perc)

        result_dict.update({
            'status': status,
            'alpha':-9999.0,
            'beta':-9999.0,
            'k':-9999.0,
            'rref': est_rref,
            'e0': est_e0,
            'alpha_std_error':-9999.0,
            'beta_std_error':-9999.0,
            'k_std_error':-9999.0,
            'rref_std_error': est_rref_std,
            'e0_std_error': est_e0_std,
            'residuals': residuals,
            'cov_matrix': covariance_matrix,
            'cor_matrix': cor_matrix,
            'rmse': est_rmse,
            'ls_status': ls_status
        })

        #return status, est_rref, est_e0, est_rref_std, est_e0_std, residuals, covariance_matrix, cor_matrix, est_rmse, ls_status
        return result_dict
    if lts_func == "HLRC_Lloyd":
        est_alpha, est_beta, est_rref = parameters
        est_alpha_std, est_beta_std, est_rref_std = std_devs
        prediction = hlrc_lloyd(rg_f=data[indepvar_arr[0]].astype(DOUBLE_PREC), ta_f=data[indepvar_arr[1]].astype(DOUBLE_PREC), e0=data[indepvar_arr[2]].astype(DOUBLE_PREC), parameter=parameters)

        est_rmse = root_mean_sq_error(nee, prediction, trim_perc)

        result_dict.update({
            'status': status,
            'alpha': est_alpha,
            'beta': est_beta,
            'k':-9999.0,
            'rref': est_rref,
            'e0':-9999.0,
            'alpha_std_error': est_alpha_std,
            'beta_std_error': est_beta_std,
            'k_std_error':-9999.0,
            'rref_std_error': est_rref_std,
            'e0_std_error':-9999.0,
            'residuals': residuals,
            'cov_matrix': covariance_matrix,
            'cor_matrix': cor_matrix,
            'rmse': est_rmse,
            'ls_status': ls_status
        })

        #return status, est_alpha, est_beta, est_rref, est_alpha_std, est_beta_std, est_rref_std, residuals, covariance_matrix, cor_matrix, est_rmse, ls_status
        return result_dict
    if lts_func == "HLRC_LloydVPD":
        est_alpha, est_beta, est_k, est_rref = parameters
        est_alpha_std, est_beta_std, est_k_std, est_rref_std = std_devs
        prediction = hlrc_lloydvpd(rg_f=data[indepvar_arr[0]].astype(DOUBLE_PREC), ta_f=data[indepvar_arr[1]].astype(DOUBLE_PREC), e0=data[indepvar_arr[2]].astype(DOUBLE_PREC), vpd_f=data[indepvar_arr[3]].astype(DOUBLE_PREC), parameter=parameters)

        est_rmse = root_mean_sq_error(nee, prediction, trim_perc)

        result_dict.update({
            'status': status,
            'alpha': est_alpha,
            'beta': est_beta,
            'k': est_k,
            'rref': est_rref,
            'e0':-9999.0,
            'alpha_std_error': est_alpha_std,
            'beta_std_error': est_beta_std,
            'k_std_error': est_k_std,
            'rref_std_error': est_rref_std,
            'e0_std_error':-9999.0,
            'residuals': residuals,
            'cov_matrix': covariance_matrix,
            'cor_matrix': cor_matrix,
            'rmse': est_rmse,
            'ls_status': ls_status
        })

        '''
        print("status")
        print(status)
        print("parameters")
        print(parameters)
        print("std_devs")
        print(std_devs)
        print("est_alpha")
        print(est_alpha)
        print("est_beta")
        print(est_beta)
        print("est_k")
        print(est_k)
        print("est_rref")
        print(est_rref)
        print("est_alpha_std")
        print(est_alpha_std)
        print("est_beta_std")
        print(est_beta_std)
        print("est_k_std")
        print(est_k_std)
        print("est_rref_std")
        print(est_rref_std)
        #print("prediction")
        #print(prediction)
        print("residuals")
        print(residuals)
        print("covariance_matrix")
        print(covariance_matrix)
        print("cor_matrix")
        print(cor_matrix)
        print("est_rmse")
        print(est_rmse)
        #exit()
        '''

        #return status, est_alpha, est_beta, est_k, est_rref, est_alpha_std, est_beta_std, est_k_std, est_rref_std, residuals, covariance_matrix, cor_matrix, est_rmse, ls_status
        return result_dict
    if lts_func == "HLRC_Lloyd_afix":
        est_beta, est_rref = parameters
        est_beta_std, est_rref_std = std_devs
        prediction = hlrc_lloyd_afix(rg_f=data[indepvar_arr[0]].astype(DOUBLE_PREC), ta_f=data[indepvar_arr[1]].astype(DOUBLE_PREC), e0=data[indepvar_arr[2]].astype(DOUBLE_PREC), alpha=data[indepvar_arr[3]].astype(DOUBLE_PREC), parameter=parameters)

        est_rmse = root_mean_sq_error(nee, prediction, trim_perc)

        result_dict.update({
            'status': status,
            'alpha':-9999.0,
            'beta': est_beta,
            'k':-9999.0,
            'rref': est_rref,
            'e0':-9999.0,
            'alpha_std_error':-9999.0,
            'beta_std_error': est_beta_std,
            'k_std_error':-9999.0,
            'rref_std_error': est_rref_std,
            'e0_std_error':-9999.0,
            'residuals': residuals,
            'cov_matrix': covariance_matrix,
            'cor_matrix': cor_matrix,
            'rmse': est_rmse,
            'ls_status': ls_status
        })

        #return status, est_beta, est_rref, est_beta_std, est_rref_std, residuals, covariance_matrix, cor_matrix, est_rmse, ls_status
        return result_dict
    if lts_func == "HLRC_LloydVPD_afix":
        est_beta, est_k, est_rref = parameters
        est_beta_std, est_k_std, est_rref_std = std_devs
        prediction = hlrc_lloydvpd_afix(rg_f=data[indepvar_arr[0]].astype(DOUBLE_PREC), ta_f=data[indepvar_arr[1]].astype(DOUBLE_PREC), e0=data[indepvar_arr[2]].astype(DOUBLE_PREC), vpd_f=data[indepvar_arr[3]].astype(DOUBLE_PREC), alpha=data[indepvar_arr[4]].astype(DOUBLE_PREC), parameter=parameters)

        est_rmse = root_mean_sq_error(nee, prediction, trim_perc)

        result_dict.update({
            'status': status,
            'alpha':-9999.0,
            'beta': est_beta,
            'k': est_k,
            'rref': est_rref,
            'e0':-9999.0,
            'alpha_std_error':-9999.0,
            'beta_std_error': est_beta_std,
            'k_std_error': est_k_std,
            'rref_std_error': est_rref_std,
            'e0_std_error':-9999.0,
            'residuals': residuals,
            'cov_matrix': covariance_matrix,
            'cor_matrix': cor_matrix,
            'rmse': est_rmse,
            'ls_status': ls_status
        })

        #return status, est_beta, est_k, est_rref, est_beta_std, est_k_std, est_rref_std, residuals, covariance_matrix, cor_matrix, est_rmse, ls_status
        return result_dict
    if lts_func == "LloydT_E0fix":
        est_rref = parameters[0]
        est_rref_std = std_devs[0]
        prediction = lloydt_e0fix(ta_f=data[indepvar_arr[0]].astype(DOUBLE_PREC), e0=data[indepvar_arr[1]].astype(DOUBLE_PREC), parameter=parameters)

        est_rmse = root_mean_sq_error(nee, prediction, trim_perc)

        result_dict.update({
            'status': status,
            'alpha':-9999.0,
            'beta':-9999.0,
            'k':-9999.0,
            'rref': est_rref,
            'e0':-9999.0,
            'alpha_std_error':-9999.0,
            'beta_std_error':-9999.0,
            'k_std_error':-9999.0,
            'rref_std_error': est_rref_std,
            'e0_std_error':-9999.0,
            'residuals': residuals,
            'cov_matrix': covariance_matrix,
            'cor_matrix': cor_matrix,
            'rmse': est_rmse,
            'ls_status': ls_status
        })

        #return status, est_rref, est_rref_std, residuals, covariance_matrix, cor_matrix, est_rmse, ls_status
        return result_dict

    return -1


def pct(array, percent):
    """
    Calculates "percent" percentile of array -- not really a percentile,
    but similar intention. Following implementation in original code.
    
    :param array: 1-d array to be used in calculation
    :type array: numpy.ndarray
    :param percent: target percent value for percentile
    :type percent: float
    """

    nonnan_mask = not_nan(array)
    if numpy.sum(nonnan_mask) > 1:
        nonnan_array = array[nonnan_mask]
    else:
        msg = "No non-NA value in percentile calculation"
        _log.critical(msg)
        raise ONEFluxError(msg)

    # indices of ascending ranking of entries in array
    rank_idx_array = rankdata(nonnan_array, method='ordinal')
    critical_rank = len(nonnan_array) * percent / 100.
    over_critical_rank_mask = (rank_idx_array > critical_rank)

    # if no index over critical rank, return max values
    if numpy.sum(over_critical_rank_mask) == 0.0:
        return numpy.max(nonnan_array)

    ### smallest rank that is greater than critical rank (or SM-RK-GT-CR)
    critical_rank_idx = numpy.where(rank_idx_array == numpy.min(rank_idx_array[over_critical_rank_mask]))

    ### rank immediately before (SM-RK-GT-CR)
    critical_rank_idx_previous = numpy.where(rank_idx_array == (numpy.min(rank_idx_array[over_critical_rank_mask]) - 1))

    if critical_rank.is_integer() and (numpy.sum(critical_rank_idx_previous) != 0):
        return numpy.average([nonnan_array[critical_rank_idx[0]], nonnan_array[critical_rank_idx_previous[0]]])
    else:
        return nonnan_array[critical_rank_idx[0]][0]


STEP_BOUND_FACTOR = 0.25    # factor to restrict initial step  (default in scipy is 100.0, but PV-Wave seems to be closer to 0.1)
NO_CONVERGENCE_RETRY = 20  # multiplicative factor to increase number of iterations allowed for retrying optimization that did not converge
def least_squares(func, initial_guess, entries, iterations=None, stop=False, return_residuals_cov_mat=False):
    """
    Wrapper for least squares paramater optimization
    
    Function used here (legacy wrapper):
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.leastsq.html
    
    Alternative function (more options, better documented, requires more config):
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html
    
    Underlying method implementation (from MINPACK Fortran implementation):
    https://www.math.utah.edu/software/minpack/minpack/lmdif.html
    
    :param func: function with N parameters to be optimized
    :type func: function
    :param initial_guess: array with initial guess for N parameters
    :type initial_guess: list or tuple
    :param iterations: maximum number of iterations to be performed if not converging
    :type iterations: int
    :param stop: should stop if not converging
    :type stop: bool
    :param return_residuals_cov_mat: returns residuals and covariance matrix if True
    :type return_residuals_cov_mat: bool
    :rtype: 4-tuple (of tuple estimated parameters and corresponding std_devs), or 6-tuple
    """
    if iterations is None:
        iterations = 1000 * (len(entries) + 1)

    # call to scipy.optimize.leastsq (implementation of the Levenberg-Marquardt algorithm)
    pars, cov_x, info, msg, success = leastsq(func=func, x0=initial_guess, full_output=True, maxfev=iterations, factor=STEP_BOUND_FACTOR) #ftol=1.11e-16

    if success != 1:# and (info['nfev'] == iterations):
        if info['nfev'] >= iterations:
            if not stop:
                _log.warning("No convergence (code '{p}'), retrying ({r}-fold limit increase). Least squares message: [[{m}]]".format(p=success, r=NO_CONVERGENCE_RETRY, m=msg.replace('\r', '').replace('\n', ' ')))
                return least_squares(func=func, initial_guess=initial_guess, entries=entries, iterations=iterations * NO_CONVERGENCE_RETRY, stop=True, return_residuals_cov_mat=return_residuals_cov_mat)
            else:
                _log.warning("No convergence (code '{p}'), stopping. Least squares message: [[{m}]]".format(p=success, m=msg.replace('\r', '').replace('\n', ' ')))
        else:
            _log.debug("Unclean minimization (code '{p}'). Least squares message: [[{m}]]".format(p=success, m=msg.replace('\r', '').replace('\n', ' ')))

    # from residuals, get covariance matrix, then variances, then standard deviations
    residuals = info['fvec']
    if entries > len(initial_guess) and cov_x is not None:
        s_squared = (residuals ** 2).sum() / (entries - len(initial_guess))
        cov_matrix = cov_x * s_squared
        cor_matrix = cov2cor(cov_matrix)
        variances = [cov_matrix[i][i] for i in range(len(cov_matrix))]
        std_devs = [numpy.sqrt(i) for i in variances]
    else:
        std_devs = [numpy.nan] * len(initial_guess)
        cov_matrix = None
        cor_matrix = None

    if return_residuals_cov_mat:
        return (pars, std_devs, success, residuals, cov_matrix, cor_matrix)
    else:
        return (pars, std_devs)

def check_parameters(params, fguess):
    #  Checks parameters, true if parameters are ok
    #  0  <= alpha < 0.22 and not equal to starting value
    #  0  <= beta  <250
    #  0  <= k
    #  0  <= rd
    #  50 <= E0    <400

    #IF (params(0) GE 0 AND params(0) LT 0.22 AND params(1) GE 0 AND params(1) LT 250 AND params(2) GE 0 AND params(3) GT 0 AND params(4) GE 50 AND params(4) LE 400 AND params(0) NE fguess(0)) THEN OK = 1 ELSE OK = 0
    #IF params(1) gt 100 AND params(1) LT params(6) THEN OK = 0

    is_ok = 0

    '''
    print("params")
    print(params)
    print("params[0]")
    print(params[0])
    print("(params[0] >= 0)")
    print(params[0] >= 0)
    #exit()
    '''

    if (params[0] >= 0) and (params[0] < 0.22) and (params[1] >= 0) and (params[1] < 250) and (params[2] >= 0) and (params[3] > 0) and (params[4] >= 50) and (params[4] <= 400) and (params[0] != fguess[0]):
        is_ok = 1
    if (params[1] > 100) and (params[1] < params[6]):
        is_ok = 0

    return is_ok


def root_mean_sq_error(nee, nee_prediction, trim_perc):
    ### Calculate the root mean square error

    residuals = nee - nee_prediction
    absolute_residuals = numpy.abs(residuals)
    nonnan_nee_mask = not_nan(nee)
    absolute_residuals_ok = absolute_residuals[nonnan_nee_mask]
    pct_calc = pct(absolute_residuals_ok, 100.0 - trim_perc)
    trim_mask = (absolute_residuals <= pct_calc)

    absErr = numpy.abs(nee - nee_prediction)
    squErr = absErr * absErr
    squErr_sum = squErr.sum()

    rmse = numpy.sqrt(squErr_sum / len(nee))

    return rmse

def cov2cor(covmatr):
    ### converts covariance matrix into correlation matrix
    ###
    ### covmatr: input covariance matrix
    ### Wandelt Covariance matrix in correlation matrix um
    #print("covmatr.shape")
    #print(covmatr.shape)

    n = covmatr.shape[0]

    cormatr = numpy.zeros((n, n), dtype=FLOAT_PREC)
    for i in range(n):
        for j in range(n):
            cormatr[j][i] = covmatr[j][i] / numpy.sqrt(covmatr[i][i] * covmatr[j][j])

    '''
    print("covmatr")
    print(covmatr)
    print("cormatr")
    print(cormatr)

    print("(covmatr[j][i] / numpy.sqrt(covmatr[i][i] * covmatr[j][j])).dtype")
    print((covmatr[0][0] / numpy.sqrt(covmatr[0][0] * covmatr[0][0])).dtype)
    print("covmatr.dtype")
    print(covmatr.dtype)
    print("cormatr.dtype")
    print(cormatr.dtype)

    exit()
    '''

    return cormatr


def get_first_last_ts(data):
    """
    Retrieves datetime objects for first and last timestamps in data structure for partitioning

    :param data: data structure
    :type data: numpy.ndarray
    """
    first_ts = datetime(int(data['year'][0]), int(data['month'][0]), int(data['day'][0]), int(data['hour'][0]), int(data['minute'][0]))
    last_ts = datetime(int(data['year'][-1]), int(data['month'][-1]), int(data['day'][-1]), int(data['hour'][-1]), int(data['minute'][-1]))
    return first_ts, last_ts


#PARTITIONING_DT_ERROR_FILE = os.path.join(os.pardir, 'error_files/partitioning_dt_error.txt')
#PARTITIONING_DT_ERROR_FILE = os.path.join('oneflux/error_files', 'partitioning_dt_error.txt')
#PARTITIONING_DT_ERROR_FILE = os.path.join('oneflux/error_files', 'partitioning_dt_error_original_FLUXNET2015.txt')
#PARTITIONING_DT_ERROR_FILE = os.path.join(os.path.expanduser("~"), 'dev/oneflux/oneflux/error_files', 'partitioning_dt_error_original_FLUXNET2015.txt')
PARTITIONING_DT_ERROR_FILE = '11_nee_partition_dt_{s}.txt'
def remove_errored_entries(ustar_type, site, site_dir, year, working_year_data):
    """
    :Task:  Remove entries that fall into error-ranges.
    
    :Explanation:   For the specified site, we look for it in paritioning_dt_error.txt to 
                    check if it falls in the written error-ranges. If we found a match, we'll
                    removes the entries that fall within the specified julday ranges.


    :param ustar_type: Type of UStar for current file/percentile ['c'|'y']
    :type ustar_type: str
    :param site: Site ID
    :type site: str
    :param site_dir: Absolute path to site dir
    :type site_dir: str
    :param year: Year being processed
    :type year: int
    :param working_year_data: Data structure loaded from create_data_structures
    :type working_year_data: numpy.ndarray
    """
    _log.debug("Removing entries with error range")

    filename = os.path.join(site_dir, PARTITIONING_DT_ERROR_FILE.format(s=site))

    # no error file, nothing to remove
    if not os.path.isfile(filename):
        _log.debug('Partitioning DT error file not found, skipping: {f}'.format(f=filename))
        return working_year_data

    data = numpy.genfromtxt(filename, dtype='|S50,i4,i4', delimiter=',', names=True)
    data = numpy.atleast_1d(data)

    site_error_key = str(site) + "_" + str(year) + "_" + str(ustar_type)

    _log.debug("site_error_key:  {s}".format(s=site_error_key))

    site_year_nee_des_mask = (data['site_year_nee_des'][:] == site_error_key)

    data_error_mask = numpy.ones(working_year_data.shape[0], dtype=bool)

    for begin, end in zip(data['begin'][site_year_nee_des_mask], data['end'][site_year_nee_des_mask]):
        data_error_mask_begin = (working_year_data['julday'][:] > begin)
        data_error_mask_end = (working_year_data['julday'][:] <= end)

        data_error_mask = (data_error_mask_begin == data_error_mask_end)

        working_year_data['nee'][data_error_mask] = NAN
        working_year_data['qcnee'][data_error_mask] = 1
        working_year_data['nee_fqc'][data_error_mask] = 1
        working_year_data['nee_fqcok'][data_error_mask] = 0

        _log.debug("From Error File, Begin:  {b}, End: {e}".format(b=str(begin), e=str(end)))

    #numpy.savetxt('test_error.csv', working_year_data, delimiter=',', fmt='%s')

    return working_year_data

def create_data_structures(ustar_type, whole_dataset_nee, whole_dataset_meteo, percentile, year_mask_nee, year_mask_meteo, latitude, part_type=NT_STR):
    """
    :Task:  Creates data structure needed for partitioning; return working copy of populated input data array
    
    :Explanation:   Return working copy of populated input data array. In other words, 
                    we pass the read data to numpy to be able to have a flexible structure.
                    
                    Hourly daytime data is also handled by duplicating each record to match
                    the half hourly scheme.


    :param ustar_type: Type of UStar for current file/percentile ['c'|'y']
    :type ustar_type: str
    :param whole_dataset_nee: Data structure loaded from NEE percentiles file
    :type whole_dataset_nee: numpy.ndarray
    :param whole_dataset_meteo: Data structure loaded from meteo_proc
    :type whole_dataset_meteo: numpy.ndarray
    :param percentile: UStar percentile value that is currently being processed
    :type percentile: str
    :param year_mask_nee: Mask of NEE rows that constitute current year
    :type year_mask_nee: numpy.ndarray
    :param year_mask_meteo: Mask of meteo rows that constitute current year
    :type year_mask_meteo: numpy.ndarray
    :param latitude: Lattitude for site (current year)
    :type latitude: float
    :param part_type: Partitioning Type (Day time or Night time)
    :type part_type: str
    """

    # headers
    original_headers = ['Year', 'Month', 'Day', 'Hour', 'Minute', 'NEE', 'Tair', 'Tsoil', 'VPD', 'Lat', 'Rg', 'Tair_f', 'Rg_f', 'Tsoil_f', 'qcNEE', 'NEE_f', 'NEE_fqc', 'NEE_fqcOK']


    output_headers = ['julday', 'Hr', 'sunrise', 'sunset', 'daylight', 'NEENight', 'Recoopt_ordE0_0_from_Tair', 'RRef_1_from_Tair', 'E0_1_from_Tair',
                      'Rref_2_from_Tair', 'Rref_2_SE_from_Tair', 'E0_2_from_Tair', 'E0_2_SE_from_Tair', 'Reco_2e_from_Tair',
                      'Rrefoptord', 'Rrefoptord_SE', 'RrefoptTRIM', 'RrefoptTRIM_SE', # TRIM and ROB are the same variables
                      'Reco_2', 'Reco_2rob', # TRIM and ROB are the same variables
                      'GPP_2', 'GPP_2rob', 'GPP_2e', # TRIM and ROB are the same variables
                      'GPP_2_nongf', 'GPP_2rob_nongf', 'GPP_2e_nongf', # TRIM and ROB are the same variables
                      'ls_status', # optimization status code
                      'pvalue', # p-value (measured NEE vs NEE from estimated parameters)
                      'nee_std', # std dev of NEE
                      'ta_std', # std dev of TA
                      ]

    if part_type == DT_STR:
        output_headers = ['julday', 'Hr', 'vpd_f', 'NEE_f_unc', 'NEE_fmet_unc', 'NEE_fwin_unc', 'NEE_fn_unc', 'NEE_fs_unc', 'NEE_fsrob_unc', 'NEE_fmed_unc',
                          'NEE_fqc_unc', 'NEE_fqcOK_unc', 'ind', 'E0_1_from_Tair', 'alpha_1_from_Tair', 'Reco_HBLR', 'GPP_HBLR', 'SE_GPP_HBLR', 'NEE_HBLR',
                          'p_flag1', 'p_flag2', 'rb', 'beta', 'k', 'E0', 'alpha', 'flag_sum']

    working_headers = original_headers + output_headers
    working_headers = [i.lower() for i in working_headers]

#    # units
#    original_units = ['-', '-', '-', '-', '-', 'umolm-2s-1', 'degC', 'degC', 'kPa', 'deg', 'Wm-2', 'degC', 'Wm-2', 'degC', '-', '-', '-', '-', '-']
#    output_units = ['-', '-', 'trueSolTime', 'trueSolTime', 'binary', 'umolm-2s-1', 'umolm-2s-1', 'umol m-2 s-1', '-',
#                    'umol m-2 s-1', 'umol m-2 s-1', '-', '-', '-']
#    working_units = original_units + output_units
#    working_units = [i.lower() for i in working_units]

    # check headers
    for i, column in enumerate(working_headers):
        if column in working_headers[i + 1:]:
            msg = "Duplicated column/variable labels '{c}'".format(c=column)
            _log.critical(msg)
            raise ONEFluxError(msg)

    working_year_data = numpy.zeros(numpy.sum(year_mask_nee), dtype=[(i, FLOAT_PREC) for i in working_headers])
    working_year_data[:] = NAN

    # Lat
    working_year_data['lat'][:] = latitude

    ### from NEE
    # ['isodate', '1__25',  '1__25_qc',  '3__75',  '3__75_qc',  '6__25',  '6__25_qc',  '8__75',  '8__75_qc',
    #            '11__25', '11__25_qc', '13__75', '13__75_qc', '16__25', '16__25_qc', '18__75', '18__75_qc',
    #             ...
    #            '91__25', '91__25_qc', '93__75', '93__75_qc', '96__25', '96__25_qc', '98__75', '98__75_qc',
    #            '50', '50_qc']
    working_year_data['year'][:] = whole_dataset_nee['year'][year_mask_nee]
    working_year_data['month'][:] = whole_dataset_nee['month'][year_mask_nee]
    working_year_data['day'][:] = whole_dataset_nee['day'][year_mask_nee]
    working_year_data['hour'][:] = whole_dataset_nee['hour'][year_mask_nee]
    working_year_data['minute'][:] = whole_dataset_nee['minute'][year_mask_nee]

    # compute julday
    _log.debug("Computing days-of-year (julday)")
    time_array = working_year_data[['year', 'month', 'day', 'hour', 'minute']]
    for i, time_record in enumerate(time_array):
        time_record_int = [int(t) for t in time_record]
        working_year_data['julday'][i] = int(datetime(*time_record_int).strftime("%j"))
    if (working_year_data['julday'][-1] == 1) and (working_year_data['julday'][-2] == 365):
        working_year_data['julday'][-1] = 366
    elif (working_year_data['julday'][-1] == 1) and (working_year_data['julday'][-2] == 366):
        working_year_data['julday'][-1] = 367

    # computr Hr
    hour_mask = (whole_dataset_nee['minute'][year_mask_nee] == 0.)
    halfhour_mask = (whole_dataset_nee['minute'][year_mask_nee] == 30.)
    working_year_data['hr'][hour_mask] = whole_dataset_nee['hour'][year_mask_nee][hour_mask]
    working_year_data['hr'][halfhour_mask] = whole_dataset_nee['hour'][year_mask_nee][halfhour_mask] + 0.5


    # NEE, removing non-measured values using percentile_qc (0: measured)
    working_year_data['nee'][:] = whole_dataset_nee[percentile][year_mask_nee]
    measured_nee_mask = (whole_dataset_nee[percentile + '_qc'][year_mask_nee] == 0)
    working_year_data['nee'][~measured_nee_mask] = NAN

    # qcNEE (1: missing, 0: present)
    working_year_data['qcnee'][:] = 0.0
    missing_mask = nan(working_year_data['nee'])
    working_year_data['qcnee'][missing_mask] = 1.0

    # NEE_f (gapfilled)
    working_year_data['nee_f'][:] = whole_dataset_nee[percentile][year_mask_nee]

    # NEE_fqc (quality of gapfilling, 0:measured, 1:high, 2:medium, 3:low)
    # NOTE: original didn't use flags from nee_proc, just 0 if measured or 1 if missing...
    working_year_data['nee_fqc'][:] = 0.0
    working_year_data['nee_fqc'][missing_mask] = 1.0

    # NEE_fqcOK (quality good enough to be used, 1:good enough, 0:too low)
    working_year_data['nee_fqcok'][:] = 0.0
    good_enough_mask = (working_year_data['nee_fqc'] <= 1.0)
    working_year_data['nee_fqcok'][good_enough_mask] = 1.0


    ### from meteo proc
    # ['isodate', 'dtime',
    #  'ta_f', 'ta_fqc', 'ta_era', 'ta_m', 'ta_mqc',
    #  'swin_pot', 'swin_f', 'swin_fqc', 'swin_era', 'swin_m', 'swin_mqc',
    #  'lwin_f', 'lwin_fqc', 'lwin_era', 'lwin_m', 'lwin_mqc', 'lwin_calc', 'lwin_calc_qc', 'lwin_calc_era', 'lwin_calc_m', 'lwin_calc_mqc',
    #  'vpd_f', 'vpd_fqc', 'vpd_era', 'vpd_m', 'vpd_mqc', 'pa', 'pa_era', 'pa_m', 'pa_mqc', 'p', 'p_era',
    #  'p_m', 'p_mqc', 'ws', 'ws_era', 'ws_m', 'ws_mqc',
    #  'co2_f', 'co2_fqc', 'ts_1_f', 'ts_1_fqc', 'swc_1_f', 'swc_1_fqc']

    # Tair, removing non-measured values using Ta_mqc (0: measured)
    working_year_data['tair'][:] = whole_dataset_meteo['ta_m'][year_mask_meteo]
    measured_tair_mask = (whole_dataset_meteo['ta_mqc'][year_mask_meteo] == 0)
    working_year_data['tair'][~measured_tair_mask] = NAN

    # Tair_f
    working_year_data['tair_f'][:] = whole_dataset_meteo['ta_m'][year_mask_meteo]

    # Tsoil
    working_year_data['tsoil'][:] = NAN

    # Tsoil_f
    working_year_data['tsoil_f'][:] = NAN

    # Rg (SW_IN), removing non-measured values using SWin_mqc (0: measured)
    working_year_data['rg'][:] = whole_dataset_meteo['sw_in_m'][year_mask_meteo]
    measured_swin_mask = (whole_dataset_meteo['sw_in_mqc'][year_mask_meteo] == 0)
    working_year_data['rg'][~measured_swin_mask] = NAN

    # Rg_f (SW_IN)
    working_year_data['rg_f'][:] = whole_dataset_meteo['sw_in_m'][year_mask_meteo]

    # VPD
    # NOTE: removing non-measured values using VPD_mqc (0: measured) NOT DONE (commented out) in original code
    working_year_data['vpd'][:] = whole_dataset_meteo['vpd_m'][year_mask_meteo]

    _log.debug("Finished creating working data set. Headers: {h}".format(h=working_year_data.dtype.names))
    first_ts = datetime(int(working_year_data['year'][0]), int(working_year_data['month'][0]), int(working_year_data['day'][0]), int(working_year_data['hour'][0]), int(working_year_data['minute'][0]))
    last_ts = datetime(int(working_year_data['year'][-1]), int(working_year_data['month'][-1]), int(working_year_data['day'][-1]), int(working_year_data['hour'][-1]), int(working_year_data['minute'][-1]))
    _log.debug("First timestamp (YYYY-MM-DD HH:MM): {s}".format(s=first_ts.strftime("%Y-%m-%d %H:%M")))
    _log.debug("Last timestamp (YYYY-MM-DD HH:MM): {s}".format(s=last_ts.strftime("%Y-%m-%d %H:%M")))

    #working_year_data = working_year_data[1::2]
    _log.debug("Debug: working_year_data.shape = {s}".format(s=str(working_year_data.shape)))

    _log.debug("Percentile = {s}".format(s=str(percentile)))
    #numpy.savetxt('test_error_dt.csv', working_year_data, delimiter=',', fmt='%s')
    #numpy.savetxt('test_error_nt.csv', working_year_data, delimiter=',', fmt='%s')

    #exit()

    #### Check if the data is hourly only - then duplicate the tuples
    #### Keep in mind that we need to handle the dates of the duplicated
    #### tuples to correctly assess the data.
    if working_year_data.shape[0] < 17000 and part_type == DT_STR:
        _log.debug("Duplicating hourly data")

        working_year_data_temp = numpy.repeat(working_year_data, 2, axis=0)
        hr_value = working_year_data_temp['hour'][::2]
        working_year_data_temp['hour'][::2] = hr_value - 1
        working_year_data_temp['minute'][::2] = 30
        working_year_data_temp['hr'][::2] = hr_value + 0.5

        before_midnight_hour_mask = (working_year_data_temp['hr'][:] == 23)
        before_midnight_half_mask = (working_year_data_temp['hour'][:] == -1)

        working_year_data_temp['hour'][before_midnight_half_mask] = working_year_data_temp['hour'][before_midnight_hour_mask]
        working_year_data_temp['hr'][before_midnight_half_mask] = working_year_data_temp['hr'][before_midnight_hour_mask] + 0.5
        working_year_data_temp['year'][before_midnight_half_mask] = working_year_data_temp['year'][before_midnight_hour_mask]
        working_year_data_temp['month'][before_midnight_half_mask] = working_year_data_temp['month'][before_midnight_hour_mask]
        working_year_data_temp['julday'][before_midnight_half_mask] = working_year_data_temp['julday'][before_midnight_hour_mask]
        working_year_data_temp['day'][before_midnight_half_mask] = working_year_data_temp['day'][before_midnight_hour_mask]

        working_year_data = working_year_data_temp
        #numpy.savetxt('test.csv', working_year_data, delimiter=',', fmt='%s')
        #exit()

    return working_year_data

def load_outputs(filename, delimiter=',', skip_header=1, is_not_hourly=True, is_python=True):
    _log.debug("Started loading {f}".format(f=filename))
    with open(filename, 'r') as f:
        header_line = f.readline()
    headers = [i.strip().replace('.', '__').lower() for i in header_line.strip().split(delimiter)]
    headers = [(h if h not in headers[i + 1:] else h + '_alt') for i, h in enumerate(headers)]
    headers = [(h if h not in headers[i + 1:] else h + '_alt') for i, h in enumerate(headers)]
    _log.debug("Loaded headers: {h}".format(h=headers))

    _log.debug("Started loading data")
    dtype = [(i, ('a25' if i.lower() in STRING_HEADERS else FLOAT_PREC)) for i in headers]
    vfill = [('' if i.lower() in STRING_HEADERS else numpy.NaN) for i in headers]
    data = numpy.genfromtxt(fname=filename, dtype=dtype, names=headers, delimiter=delimiter, skip_header=skip_header, missing_values='-9999,-9999.0,-6999,-6999.0, ', usemask=True)
    data = numpy.ma.filled(data, vfill)

    #timestamp_list = [datetime(int(i['year']), int(i['month']), int(i['day']), int(i['hour']), int(i['minute'])) for i in data]

    timestamp_list = []
    current_month = 1
    if is_python:
        for i in data:
            '''
            if not is_python_csv:
                print("#### 1")
                print("int(i['year']")
                print(int(i['year']))
                print("int(i['month'])")
                print(int(i['month']))
                print("int(i['day'])")
                print(int(i['day']))
                print("int(i['hour'])")
                print(int(i['hour']))
                print("int(i['minute'])")
                print(int(i['minute']))
            '''

            if not is_not_hourly and int(i['hour']) == 23 and int(i['minute']) == 30:
                if int(i['month']) != current_month:
                    i['month'] = current_month
                    current_month = current_month + 1
                    if current_month == 13:
                        current_month = 1

            timestamp_list.append(datetime(int(i['year']), int(i['month']), int(i['day']), int(i['hour']), int(i['minute'])))

    _log.debug("Finished loading {f}".format(f=filename))
    return data, headers, timestamp_list

def compare_python_pvwave_vars(py_filename, pw_filename_csv):
    _log.debug("Python / PV-Wave comparison started")

    # check Python output
    if not file_exists_not_empty(filename=py_filename):
        _log.error("Python output file not found, skipping comparison: {f}".format(f=py_filename))
        exit()

    # check PV-Wave output
    if not file_exists_not_empty(filename=pw_filename_csv):
        _log.error("PV-Wave output files not found, skipping comparison: {f}".format(f=pw_filename_csv))
        exit()

    # load py
    py_data, py_headers, py_timestamps = load_outputs(filename=py_filename, skip_header=1)

    # load pw
    #pw_data, pw_headers, pw_timestamps = load_outputs(filename=pw_filename_csv, skip_header=2, is_python_csv=False)
    pw_data, pw_headers, pw_timestamps = load_outputs(filename=pw_filename_csv, skip_header=1, is_not_hourly=True, is_python=False)

    # compare e0, rref (e, ord, trim/rob), reco (e, ord, trim/rob), gpp (e, ord, trim/rob)
    vars_to_compare = [ # (py-label, pw-label) pairs
        # selected E0 computed within window, optimizing E0 and RREF -- USE THIS VERSION
        ('nee', 'NEE'),

        ('nee_f', 'NEE_f'),

        ('tair', 'Tair'),

        ('tair_f', 'Tair_f'),

        ('vpd', 'VPD'),

        ('vpd_f', 'vpd_f'),

        ('rg', 'Rg'),

        ('rg_f', 'Rg_f'),

        ('nee_fs_unc', 'NEE_fs_unc'),

        ('lat', 'Lat'),
        ]
    vars_to_compare = [(i.lower(), j.lower()) for i, j in vars_to_compare]

    #if (py_timestamps[0] != pw_timestamps[0]):
    #    raise ONEFluxError("Timestamps mismatch: {py} != {pw}".format(py=py_timestamps[0], pw=pw_timestamps[0]))
    #if (py_timestamps[-1] != pw_timestamps[-1]):
    #    raise ONEFluxError("Timestamps mismatch: {py} != {pw}".format(py=py_timestamps[-1], pw=pw_timestamps[-1]))

    file_basename, _ = os.path.splitext(pw_filename_csv)
    for py_var, pw_var in vars_to_compare:
        if py_var not in py_headers:
            _log.error("Python header not found: {h}".format(h=py_var))
            exit()
        if pw_var not in pw_headers:
            _log.error("PV-Wave header not found: {h}".format(h=py_var))
            exit()

        _log.debug("processing {v}".format(v=py_var))
        figure_basename = file_basename + '__' + py_var
        plot_comparison(timestamp_list=py_timestamps, data1=py_data[py_var], data2=pw_data[pw_var], label1='Python', label2='PV-Wave', title=py_var, basename=figure_basename, show=False)

    _log.debug("Python / PV-Wave comparison finished")

if __name__ == '__main__':
    raise ONEFluxError('Not executable')
