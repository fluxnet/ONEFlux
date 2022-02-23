'''
oneflux.pipeline.common

For license information:
see LICENSE file or headers in oneflux.__init__.py 

Pipeline common/shared configuration parameters

@author: Gilberto Z. Pastorello
@contact: gzpastorello@lbl.gov
@date: 2014-04-19
'''
import sys
import os
import copy
import collections
import logging
import argparse
import re
import numpy
import socket
import shutil
import fnmatch

from datetime import datetime, date, timedelta

from oneflux import ONEFluxError
from oneflux.utils.strings import is_int
from oneflux.pipeline.variables_codes import VARIABLE_LIST_MUST_BE_PRESENT, VARIABLE_LIST_SHOULD_BE_PRESENT, VARIABLE_LIST_COULD_BE_PRESENT

log = logging.getLogger(__name__)

HOSTNAME = socket.gethostname()

NOW_DATETIME = datetime.now()
NOW_TS = NOW_DATETIME.strftime("%Y%m%dT%H%M%S")

try:
    from oneflux.local_settings import MODE_ISSUER, MODE_PRODUCT, MODE_ERA, ERA_FIRST_YEAR, ERA_LAST_YEAR
except ImportError as e:
    MODE_ISSUER = 'FLX'
    MODE_PRODUCT = 'FLUXNET2015'
    MODE_ERA = 'ERAI'
    # most recent year available for ERA -- assuming new ERA year available after March each year
    ERA_FIRST_YEAR = '1989'
    ERA_LAST_YEAR = (NOW_DATETIME.year - 1 if (NOW_DATETIME.month > 3) else NOW_DATETIME.year - 2)

ERA_FIRST_TIMESTAMP_START_TEMPLATE = '{y}01010000'
ERA_LAST_TIMESTAMP_START_TEMPLATE = '{y}12312330'
ERA_FIRST_TIMESTAMP_START = ERA_FIRST_TIMESTAMP_START_TEMPLATE.format(y=ERA_FIRST_YEAR)
ERA_LAST_TIMESTAMP_START = ERA_LAST_TIMESTAMP_START_TEMPLATE.format(y=str(ERA_LAST_YEAR))

HOME_DIRECTORY = os.path.expanduser('~')
TOOL_DIRECTORY = os.path.join(HOME_DIRECTORY, 'bin', 'oneflux')
MCR_DIRECTORY = os.path.join(HOME_DIRECTORY, 'bin', 'MATLAB_Compiler_Runtime', 'v717')
WORKING_DIRECTORY = os.path.join(HOME_DIRECTORY, 'data', 'fluxnet', 'FLUXNET2015')
WORKING_DIRECTORY_SITE = os.path.join(WORKING_DIRECTORY, '{sd}')
QCDIR = os.path.join(WORKING_DIRECTORY_SITE, "01_qc_visual", "qcv_files") # NEW FOR APRIL2016
MPDIR = os.path.join(WORKING_DIRECTORY_SITE, "04_ustar_mp")
CPDIR = os.path.join(WORKING_DIRECTORY_SITE, "05_ustar_cp")
METEODIR = os.path.join(WORKING_DIRECTORY_SITE, "07_meteo_proc")
NEEDIR_PATTERN = "08_nee_proc"
NEEDIR = os.path.join(WORKING_DIRECTORY_SITE, NEEDIR_PATTERN)
ENERGYDIR = os.path.join(WORKING_DIRECTORY_SITE, "09_energy_proc")
UNCDIR = os.path.join(WORKING_DIRECTORY_SITE, "12_ure")
PRODDIR = os.path.join(WORKING_DIRECTORY_SITE, "99_fluxnet2015")
PRODFILE_TEMPLATE_F = MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_{g}_{r}_{fy}-{ly}_{vd}-{vp}.csv"
PRODFILE_AUX_TEMPLATE_F = MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_{aux}_{fy}-{ly}_{vd}-{vp}.csv"
PRODFILE_YEARS_TEMPLATE_F = MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_YEARS_{vd}-{vp}.csv"
PRODFILE_FIGURE_TEMPLATE_F = MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_FIG-{f}_{fy}-{ly}_{vd}-{vp}.png"
ZIPFILE_TEMPLATE_F = MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_{g}_{fy}-{ly}_{vd}-{vp}.zip"
PRODFILE_TEMPLATE = os.path.join(PRODDIR, PRODFILE_TEMPLATE_F)
PRODFILE_AUX_TEMPLATE = os.path.join(PRODDIR, PRODFILE_AUX_TEMPLATE_F)
PRODFILE_YEARS_TEMPLATE = os.path.join(PRODDIR, PRODFILE_YEARS_TEMPLATE_F)
PRODFILE_FIGURE_TEMPLATE = os.path.join(PRODDIR, PRODFILE_FIGURE_TEMPLATE_F)
ZIPFILE_TEMPLATE = os.path.join(PRODDIR, ZIPFILE_TEMPLATE_F)

# added path requested to physically locate files..............
WINDOWS_DESTINATION_FOLDER = "\\\\EDDY\FLUXNET2015\\"
WINDOWS_DESTINATION_FOLDER_ACTIVE = True

CSVMANIFEST_HEADER = "zipfilename,filename,fileSize,fileChecksum,processor,createDate\n"
ZIPMANIFEST_HEADER = "filename,fileSize,fileChecksum,fileCount,tier,processor,createDate\n"

METEO_INFO_F = '{s}_meteo_{r}_info.txt'
METEO_INFO = os.path.join(METEODIR, METEO_INFO_F)
NEE_INFO_F = '{s}_NEE_{r}_info.txt'
NEE_INFO = os.path.join(NEEDIR, NEE_INFO_F)
NEE_PERC_USTAR_VUT_PATTERN = '{s}_USTAR_percentiles_y.csv'
NEE_PERC_USTAR_VUT = os.path.join(NEEDIR, NEE_PERC_USTAR_VUT_PATTERN)
NEE_PERC_USTAR_CUT_PATTERN = '{s}_{fy}_{ly}_USTAR_percentiles_c.csv'
NEE_PERC_USTAR_CUT = os.path.join(NEEDIR, NEE_PERC_USTAR_CUT_PATTERN)
NEE_PERC_NEE_F = '{s}_NEE_percentiles_{t}.csv'
NEE_PERC_NEE = os.path.join(NEEDIR, NEE_PERC_NEE_F)
#NEE_MEF_MATRIX = os.path.join(NEEDIR, '{s}_mef_matrix_{r}_{t}_{fy}_{ly}.csv') # HH, DD, WW, MM, YY __ VUT, CUT
#ENERGY_INFO = None # No metadata
UNC_INFO_F = 'info_{s}_{m}_{v}_{r}.txt'
UNC_INFO = os.path.join(UNCDIR, UNC_INFO_F) # DT, NT, SR __ GPP, RECO __ HH, DD, WW, MM, YY
UNC_INFO_ALT_F = '{s}_{m}_{v}_{r}_info.txt'
UNC_INFO_ALT = os.path.join(UNCDIR, UNC_INFO_ALT_F) # DT, NT, SR __ GPP, RECO __ HH, DD, WW, MM, YY
#UNC_MEF_MATRIX = os.path.join(UNCDIR, '{s}_{m}_{v}_mef_matrix_{r}_{t}_{fy}_{ly}.csv') # DT, NT, SR __ GPP, RECO __ HH, DD, WW, MM, YY __ VUT, CUT

FULLSET_STR = 'FULLSET'
SUBSET_STR = 'SUBSET'

ERA_STR = MODE_ERA

RESOLUTION_LIST = ['hh', 'dd', 'ww', 'mm', 'yy']

STRTEST = ['timestamp', 'doy', 'week', 'isodate']
INTTEST = {
'hh':[i.lower() for i in ['TA_fqc', 'TA_mqc', 'SW_IN_fqc', 'SW_IN_mqc',
                          'LW_IN_fqc', 'LW_IN_mqc', 'LW_IN_calc_qc', 'LW_IN_calc_mqc',
                          'VPD_fqc', 'VPD_mqc', 'PA_mqc', 'P_mqc', 'WS_mqc', 'CO2_fqc'] + \
                         ['TS_{n}_fqc'.format(n=i) for i in range(1, 20)] + \
                         ['SWC_{n}_fqc'.format(n=i) for i in range(1, 20)] + \
                         ['LE_qc', 'LE_randUnc_method', 'LE_randUnc_n',
                          'H_qc', 'H_randUnc_method', 'H_randUnc_n',
                          'EBCcf_method', 'night',
                          'NEE_ref_qc_c', 'NEE_ref_qc_y', 'NEE_ust50_qc_c', 'NEE_ust50_qc_y',
                          'NEE_ust50_randUnc_method_c', 'NEE_ust50_randUnc_method_y',
                          'NEE_ust50_randUnc_n_c', 'NEE_ust50_randUnc_n_y'] + \
                          ['NEE_{i}_qc_c'.format(i=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
                          ['NEE_{i}_qc_y'.format(i=i) for i in ['05', '16', '25', '50', '75', '84', '95']]
                         ],
'dd':[i.lower() for i in ['EBCcf_method', 'DOY', 'night_d', 'day_d', 'night_randUnc_n', 'day_randUnc_n']],
'ww':[i.lower() for i in ['EBCcf_method', 'WEEK', 'year']],
'mm':[i.lower() for i in ['EBCcf_method']],
'yy':[i.lower() for i in ['EBCcf_method']],
}

TIMESTAMP_DTYPE_BY_RESOLUTION = {
'hh': [('TIMESTAMP_START', 'a25'), ('TIMESTAMP_END', 'a25')],
'dd': [('TIMESTAMP', 'a25'), ],
'ww': [('TIMESTAMP_START', 'a25'), ('TIMESTAMP_END', 'a25')],
'mm': [('TIMESTAMP', 'a25'), ],
'yy': [('TIMESTAMP', 'a25'), ],
}

TIMESTAMP_DTYPE_BY_RESOLUTION_IN = {
'hh': [('TIMESTAMP_START', 'a25'), ('TIMESTAMP_END', 'a25'), ('DTIME', 'f8'), ('dtime', 'f8')],
'dd': [('TIMESTAMP', 'a25'), ('DOY', 'i8'), ('Doy', 'i8'), ('doy', 'i8'), ('DoY', 'i8')],
'ww': [('TIMESTAMP_START', 'a25'), ('TIMESTAMP_END', 'a25'), ('WEEK', 'i8'), ('Year', 'i8')],
'mm': [('TIMESTAMP', 'a25'), ],
'yy': [('TIMESTAMP', 'a25'), ],
}

TIMESTAMP_PRECISION_BY_RESOLUTION = {
'hh': 12,
'dd': 8,
'ww': 8,
'mm': 6,
'yy': 4,
}

NEW_METEO_VARS = ['WD', 'USTAR', 'RH', 'NETRAD', 'PPFD_IN', 'PPFD_DIF', 'PPFD_OUT', 'SW_DIF', 'SW_OUT', 'LW_OUT'] # NEW FOR APRIL2016 # FIX FOR JULY2016: ADDED RH
NEW_ERA_VARS = ['TA_ERA', 'TA_ERA_NIGHT', 'TA_ERA_NIGHT_SD', 'TA_ERA_DAY', 'TA_ERA_DAY_SD', 'SW_IN_ERA', 'LW_IN_ERA', 'VPD_ERA', 'PA_ERA', 'P_ERA', 'WS_ERA'] # NEW FOR JULY2016

class ONEFluxPipelineError(ONEFluxError):
    """
    Pipeline specific FPP error
    """
    pass

def run_command(cmd):
    """
    Runs command and tests return value, raises exception if failed
    
    :param cmd: command to be executed
    :type cmd: str
    """
    return_value = os.system(cmd)
    if return_value != 0:
        msg = "Non-clean execution of : {c}".format(c=cmd)
        log.error(msg)
        raise ONEFluxPipelineError(msg)

def test_dir(tdir, label, log_only=False):
    """
    Tests if directory exists, if not logs error and raises exception
    
    :param tdir: path to directory to be tested
    :type tdir: str
    :param label: label for type of directory being tested
    :type label: str
    """
    if not os.path.isdir(tdir):
        msg = "Pipeline {l} directory not found in '{d}'".format(l=label, d=tdir)
        if log_only:
            log.warning(msg)
            return False
        else:
            log.critical(msg)
            raise ONEFluxPipelineError(msg)
    log.debug("Pipeline {l} directory is '{d}'".format(l=label, d=tdir))
    return True

def test_file(tfile, label, log_only=False):
    """
    Tests if file exists, if not logs error and raises exception
    
    :param tfile: file name to be tested
    :type tfile: str
    :param label: label for type of file being tested
    :type label: str
    """
    if (not os.path.isfile(tfile)) or (not os.path.isfile(tfile.replace('_HH_', '_HR_'))):
        msg = "Pipeline {l} file not found '{d}'".format(l=label, d=tfile)
        if log_only:
            log.warning(msg)
            return False
        else:
            log.critical(msg)
            raise ONEFluxPipelineError(msg)
    log.debug("Pipeline {l} file is '{d}'".format(l=label, d=tfile))
    return True

def test_file_not_empty(tfile, label, log_only=False):
    """
    Tests if file exists and is not empty,
    if not logs error and raises exception
    
    :param tfile: file name to be tested
    :type tfile: str
    :param label: label for type of file being tested
    :type label: str
    """
    if os.path.isfile(tfile):
        if os.stat(tfile).st_size == 0:
            msg = "Pipeline {l} file empty '{d}'".format(l=label, d=tfile)
            if log_only:
                log.warning(msg)
                return False
            else:
                log.critical(msg)
                raise ONEFluxPipelineError(msg)
    elif os.path.isfile(tfile.replace('_HH_', '_HR_')):
        if os.stat(tfile.replace('_HH_', '_HR_')).st_size == 0:
            msg = "Pipeline {l} file empty '{d}'".format(l=label, d=tfile.replace('_HH_', '_HR_'))
            if log_only:
                log.warning(msg)
                return False
            else:
                log.critical(msg)
                raise ONEFluxPipelineError(msg)
    else:
        msg = "Pipeline {l} file not found '{d}'".format(l=label, d=tfile)
        if log_only:
            log.warning(msg)
            return False
        else:
            log.critical(msg)
            raise ONEFluxPipelineError(msg)
    log.debug("Pipeline {l} file is '{d}'".format(l=label, d=tfile))
    return True


def test_pattern(tdir, tpattern, label, log_only=False):
    """
    Tests if files following pattern exist in directory,
    if not logs error and raises exception

    :param tdir: path to directory to be searched and tested
    :type tdir: str
    :param tpattern: file name pattern to be tested
    :type tpattern: str
    :param label: label for type of file being tested
    :type label: str
    :rtype: list
    """
    if test_dir(tdir=tdir, label=label, log_only=log_only):
        matches = fnmatch.filter(os.listdir(tdir), tpattern)
        matches_alt = fnmatch.filter(os.listdir(tdir), tpattern.replace('_HH_', '_HR_'))
    else:
        matches, matches_alt = [], []

    if matches:
        log.debug("Pipeline {l} in '{d}' found file pattern '{p}' ({n} occurrences): {m}".format(l=label, d=tdir, p=tpattern, m=matches, n=len(matches)))
    elif matches_alt:
        matches = matches_alt
        log.debug("Pipeline {l} in '{d}' found file pattern '{p}' ({n} occurrences): {m}".format(l=label, d=tdir, p=tpattern, m=matches, n=len(matches)))
    else:
        msg = "Pipeline {l} file with pattern '{p}' not found in '{d}'".format(l=label, p=tpattern, d=tdir)
        if log_only:
            log.warning(msg)
        else:
            log.critical(msg)
            raise ONEFluxPipelineError(msg)
    return matches


def test_file_list(file_list, tdir, label, log_only=False):
    """
    Tests files in file list:
    if * or ? in filename, tests pattern in directory
    else tests filename
    
    :param file_list: list of base filenames/patterns to be tested
    :type file_list: list
    :param tdir: directory where to look for files/patterns
    :type tdir: str
    :param label: label to identify test
    :type label: str
    """
    all_true = True
    for fname in file_list:
        if '*' in fname or '?' in fname:
            res = test_pattern(tdir=tdir, tpattern=fname, label=label, log_only=log_only)
            all_true = all_true and res
        else:
            res = test_file_not_empty(tfile=os.path.join(tdir, fname), label=label, log_only=log_only)
            all_true = all_true and res
    return all_true

def test_file_list_or(file_list, tdir, label, log_only=False):
    """
    Tests files in file list (if any, returns True), tests filenames only
    
    :param file_list: list of base filenames to be tested
    :type file_list: list
    :param tdir: directory where to look for files
    :type tdir: str
    :param label: label to identify test
    :type label: str
    """
    any_true = False
    for fname in file_list:
        res = test_file_not_empty(tfile=os.path.join(tdir, fname), label=label, log_only=True)
        any_true = any_true or res

    if not any_true:
        msg = "Pipeline {l} none of the {n} files found in '{d}' [{f}{c}]".format(l=label, d=tdir, n=len(file_list), f=file_list[:5], c=('...' if len(file_list) > 5 else ''))
        if log_only:
            log.warning(msg)
        else:
            log.critical(msg)
            raise ONEFluxPipelineError(msg)
    return any_true


def test_create_dir(tdir, label, simulation=False):
    """
    Tests if directory exists, if not creates it. If yes, tests if readable/writable.
    Returns True if directory created, False if already exists

    :param tdir: path to directory to be tested/created
    :type tdir: str
    :param label: label for type of directory being tested/created
    :type label: str
    :rtype: bool
    """
    if os.path.isdir(tdir):
        if not os.access(tdir, os.W_OK):
            msg = "Cannot write to pipeline {l} directory '{d}'".format(l=label, d=tdir)
            log.critical(msg)
            raise ONEFluxPipelineError(msg)
        if not os.access(tdir, os.R_OK):
            msg = "Cannot read from pipeline {l} directory '{d}'".format(l=label, d=tdir)
            log.critical(msg)
            raise ONEFluxPipelineError(msg)
        log.debug("Pipeline {l} directory exists '{d}'".format(l=label, d=tdir))
        return False
    else:
        if not simulation:
            os.makedirs(tdir)
        log.debug("Created '{d}'".format(d=tdir))
        return True

def create_replace_dir(tdir, label, suffix=datetime.now().strftime("%Y%m%d%H%M%S"), sep='__', simulation=False):
    """
    Tests if directory exists, if not creates it. If yes, tests if readable/writable.
    Returns True if new directory created, False if already existed and replaced

    :param tdir: path to directory to be tested/created
    :type tdir: str
    :param label: label for type of directory being tested/created
    :type label: str
    :param suffix: string to old suffix directory name
    :type suffix: str
    :param suffix: string to separate suffix from original name
    :type suffix: str
    :param simulation: True if simulation only (no changes to be made), False if commands should be executed
    :type simulation: bool
    :rtype: bool
    """
    if os.path.isdir(tdir):
        if not os.access(tdir, os.W_OK):
            msg = "Cannot write to pipeline {l} directory '{d}'".format(l=label, d=tdir)
            log.critical(msg)
            raise ONEFluxPipelineError(msg)
        if not os.access(tdir, os.R_OK):
            msg = "Cannot read from pipeline {l} directory '{d}'".format(l=label, d=tdir)
            log.critical(msg)
            raise ONEFluxPipelineError(msg)
        new_tdir = tdir + sep + suffix
        if not simulation:
            shutil.move(tdir, new_tdir)
            os.makedirs(tdir)
        log.debug("Pipeline {l} moved directory '{o}' to '{n}'".format(l=label, o=tdir, n=new_tdir))
        log.debug("Created '{d}'".format(d=tdir))
        return False
    else:
        if not simulation:
            os.makedirs(tdir)
        log.debug("Created '{d}'".format(d=tdir))
        return True

def create_and_empty_dir(tdir, label, suffix=datetime.now().strftime("%Y%m%d%H%M%S"), sep='__', simulation=False):
    """
    Tests if directory exists, if not creates it. If yes, tests if readable/writable.
    Returns True if new directory created, False if already existed and emptied
    (keeping directory, not contents)

    :param tdir: path to directory to be tested/created
    :type tdir: str
    :param label: label for type of directory being tested/created
    :type label: str
    :param suffix: string to old suffix directory name
    :type suffix: str
    :param suffix: string to separate suffix from original name
    :type suffix: str
    :param simulation: True if simulation only (no changes to be made), False if commands should be executed
    :type simulation: bool
    :rtype: bool
    """
    if os.path.isdir(tdir):
        if not os.access(tdir, os.W_OK):
            msg = "Cannot write to pipeline {l} directory '{d}'".format(l=label, d=tdir)
            log.critical(msg)
            raise ONEFluxPipelineError(msg)
        if not os.access(tdir, os.R_OK):
            msg = "Cannot read from pipeline {l} directory '{d}'".format(l=label, d=tdir)
            log.critical(msg)
            raise ONEFluxPipelineError(msg)
        new_tdir = tdir + sep + suffix
        if not simulation:
            shutil.rmtree(path=tdir, ignore_errors=False, onerror=None)
            os.makedirs(new_tdir)
            os.makedirs(tdir)
        log.debug("Pipeline {l} moved EMPTY directory '{o}' to '{n}'".format(l=label, o=tdir, n=new_tdir))
        log.debug("Created '{d}'".format(d=tdir))
        return False
    else:
        if not simulation:
            os.makedirs(tdir)
        log.debug("Created '{d}'".format(d=tdir))
        return True

def get_headers(filename):
    """
    Parse headers from FPFileV2 format and returns list
    of string with header labels.
    Must have at least two columns.
    
    :param filename: name of the FPFileV2 to be loaded
    :type filename: str
    :rtype: list
    """
    with open(filename, 'r') as f:
        line = f.readline()
    headers = line.strip().split(',')
    if len(headers) < 2:
        raise ONEFluxError("Headers too short: '{h}'".format(h=line))
    headers = [i.strip() for i in headers]
    return headers

def check_headers_fluxnet2015(filename):
    """
    Checks variables that must, should, and could be present
    in FULLSET output of FLUXNET2015 Data product.
    Returns True if all present (or only missing from COULD list),
    False if any variable in MUST or SHOULD be present lists are missing
    
    :param filename: FULLSET filename to be checked
    :type filename: str
    :rtype: bool
    """
    basename = os.path.basename(filename)
    if not ((basename[:4] == MODE_ISSUER + "_") and (basename[10:11 + len(MODE_PRODUCT) + 8] == "_" + MODE_PRODUCT + "_FULLSET")):
        log.error("Filename does not match {p} FULLSET filename template: {f}".format(p=MODE_PRODUCT, f=filename))
        return False

    headers = get_headers(filename=filename)

    all_present = True
    for var_label in VARIABLE_LIST_MUST_BE_PRESENT:
        if var_label not in headers:
            log.error("Variable '{v}' missing from headers of file: {f}".format(v=var_label, f=filename))
            all_present = False
    for var_label in VARIABLE_LIST_SHOULD_BE_PRESENT:
        if var_label not in headers:
            log.warning("Variable '{v}' missing from headers of file: {f}".format(v=var_label, f=filename))
            all_present = False
    for var_label in VARIABLE_LIST_COULD_BE_PRESENT:
        if var_label not in headers:
            log.info("Variable '{v}' might be missing from headers of file: {f}".format(v=var_label, f=filename))

    return all_present

def get_empty_array_year(year=datetime.now().year, start_end=True, variable_list=['TEST', ], variable_list_dtype=None, record_interval='HH'):
    """
    Allocates and returns new empty record array for given year using list of dtypes
    (or variable labels as 8byte floats if no dtype list provided) for variables plus
    TIMESTAMP_START and TIMESTAMP_END at beginning
    
    :param year: year to be represented in array (current year if not provided)
    :type year: int
    :param start_end: if True, uses TIMESTAMP_START and TIMESTAMP_END, if not, uses only TIMESTAMP (end)
    :type start_end: bool
    :param variable_list: list of strings to be used as variable labels (assumed f8 type)
    :type variable_list: list (of str)
    :param variable_list_dtype: list of dtype tuples (label, data type) to be used as variables
    :type variable_list_dtype: list (of (str, str)-tuples)
    :param record_interval: resolution to be used for record ['HR' for hourly, 'HH' for half-hourly (default)]
    :type record_interval: str
    """
    # record_interval
    if record_interval.lower() == 'hh':
        step = timedelta(minutes=30)
    elif record_interval.lower() == 'hr':
        step = timedelta(minutes=60)
    else:
        msg = 'Unknown record_interval: {r}'.format(r=record_interval)
        log.critical(msg)
        raise ONEFluxError(msg)

    # timestamp list
    timestamp_list = []
    current_timestamp = datetime(int(year), 1, 1, 0, 0, 0)
    while current_timestamp.year < int(year) + 1:
        timestamp_list.append(current_timestamp)
        current_timestamp += step
    timestamp_list.append(current_timestamp)
    timestamp_list_begin = timestamp_list[:-1]
    timestamp_list_end = timestamp_list[1:]

    # array dtype
    dtype = ([(var, 'f8') for var in variable_list] if variable_list_dtype is None else variable_list_dtype)
    if start_end:
        dtype = [('TIMESTAMP_START', 'a25'), ('TIMESTAMP_END', 'a25')] + dtype
    else:
        dtype = [('TIMESTAMP', 'a25'), ] + dtype

    # record array
    data = numpy.zeros(len(timestamp_list_begin), dtype=dtype)
    data[:] = -9999.0
    if start_end:
        data['TIMESTAMP_START'][:] = [i.strftime('%Y%m%d%H%M') for i in timestamp_list_begin]
        data['TIMESTAMP_END'][:] = [i.strftime('%Y%m%d%H%M') for i in timestamp_list_end]
    else:
        data['TIMESTAMP'][:] = [i.strftime('%Y%m%d%H%M') for i in timestamp_list_end]

    return data


if __name__ == '__main__':
    sys.exit("ERROR: cannot run independently")
