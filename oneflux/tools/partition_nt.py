'''
oneflux.tools.partition_nt

For license information:
see LICENSE file or headers in oneflux.__init__.py

Execution controller module for NT partitioning method

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''
import sys
import os
import glob
import logging
import time
import numpy
import subprocess
import socket
import numpy
import calendar
import pytest

from datetime import datetime
from io import StringIO
from oneflux import ONEFluxError
from oneflux.partition.nighttime import partitioning_nt, STEP_SIZE
from oneflux.partition.library import STRING_HEADERS, NT_OUTPUT_DIR, EXTRA_FILENAME
from oneflux.partition.auxiliary import FLOAT_PREC, NAN, NAN_TEST, nan, not_nan
from oneflux.graph.compare import plot_comparison, plot_e0_comparison, plot_param_diff_vs, compute_plot_e0_diffs
from oneflux.utils.files import file_exists_not_empty, check_create_directory


log = logging.getLogger(__name__)

HOSTNAME = socket.gethostname()


def save_remove_file(filename):
    noext_filename, ext = os.path.splitext(filename)
    orig_filename = noext_filename + '_orig' + ext

    # check file exists
    if not file_exists_not_empty(filename=filename):
        log.warning("Cannot remove, file not found '{f}'".format(f=filename))
        return

    # check backup of file exists
    if file_exists_not_empty(filename=orig_filename):
        log.debug("Removing file '{f}'".format(f=filename))
        os.remove(filename)
    else:
        log.debug("Renaming file to '{f}'".format(f=orig_filename))
        os.rename(filename, orig_filename)
    return


def remove_previous_run(datadir, siteid, sitedir, prod_to_compare, perc_to_compare, years_to_compare, python=False):
    if python:
        for prod in prod_to_compare:
            for perc in perc_to_compare:
                for year in years_to_compare:
                    py_filename = os.path.join(datadir, sitedir, NT_OUTPUT_DIR, FILENAME_TEMPLATE.format(prod=prod, perc=perc, y=year, s=siteid, e='csv', add=EXTRA_FILENAME))
                    if python:
                        save_remove_file(py_filename)
    else:
        log.info("Nothing selected for removal")
    return


def run_python(datadir, siteid, sitedir, prod_to_compare, perc_to_compare, years_to_compare):
    log.debug("Python partitioning execution started")
    partitioning_nt(datadir=datadir, siteid=siteid, sitedir=sitedir, prod_to_compare=prod_to_compare, perc_to_compare=perc_to_compare, years_to_compare=years_to_compare)
    log.debug("Python partitioning execution finished")
    return


def load_outputs(filename, delimiter=',', skip_header=1):
    log.debug("Started loading {f}".format(f=filename))
    with open(filename, 'r') as f:
        header_line = f.readline()
    headers = [i.strip().replace('.', '__').lower() for i in header_line.strip().split(delimiter)]
    headers = [(h if h not in headers[i + 1:] else h + '_alt') for i, h in enumerate(headers)]
    headers = [(h if h not in headers[i + 1:] else h + '_alt') for i, h in enumerate(headers)]
    log.debug("Loaded headers: {h}".format(h=headers))

    log.debug("Started loading data")
    dtype = [(i, ('a25' if i.lower() in STRING_HEADERS else FLOAT_PREC)) for i in headers]
    vfill = [('' if i.lower() in STRING_HEADERS else numpy.NaN) for i in headers]
    data = numpy.genfromtxt(fname=filename, dtype=dtype, names=headers, delimiter=delimiter, skip_header=skip_header, missing_values='-9999,-9999.0,-6999,-6999.0, ', usemask=True)
    data = numpy.ma.filled(data, vfill)

    timestamp_list = [datetime(int(i['year']), int(i['month']), int(i['day']), int(i['hour']), int(i['minute'])) for i in data]

    log.debug("Finished loading {f}".format(f=filename))
    return data, headers, timestamp_list


FILENAME_TEMPLATE = "nee_{prod}_{perc}_{s}_{y}{add}.{e}"
PROD_TO_COMPARE = ['c', 'y']
PERC_TO_COMPARE = ['1.25', '3.75', '6.25', '8.75', '11.25', '13.75', '16.25', '18.75',
                   '21.25', '23.75', '26.25', '28.75', '31.25', '33.75', '36.25', '38.75',
                   '41.25', '43.75', '46.25', '48.75', '51.25', '53.75', '56.25', '58.75',
                   '61.25', '63.75', '66.25', '68.75', '71.25', '73.75', '76.25', '78.75',
                   '81.25', '83.75', '86.25', '88.75', '91.25', '93.75', '96.25', '98.75',
                   '50', ]
def run_partition_nt(datadir, siteid, sitedir, years_to_compare,
                     nt_dir=NT_OUTPUT_DIR, filename_template=FILENAME_TEMPLATE,
                     prod_to_compare=PROD_TO_COMPARE, perc_to_compare=PERC_TO_COMPARE,
                     py_remove_old=False):
    """
    Runs nighttime partitioning

    :param sitedir: absolute path to data directory
    :type sitedir: str
    :param siteid: site id in CC-SSS format
    :type siteid: str
    :param sitedir: relative path to data directory for site data
    :type sitedir: str
    :param years_to_compare: list of years to be compared
    :type years_to_compare: list
    :param nt_dir: template name for directory with nighttime partitioning data
    :type nt_dir: str
    :param filename_template: template of filename for nighttime partitioning data
                              (product, percentile, siteid, year, format, extension)
    :type filename_template: str
    :param prod_to_compare: list of products to compare ('c', 'y') - CUT/VUT
    :type prod_to_compare: list
    :param perc_to_compare: list of percentiles to compare ('1.25', '3.75', ..., '50', ..., '96.25', '98.75')
    :type perc_to_compare: list
    :param py_remove_old: if True, removes old python partitioning results (after backup), file has to be missing for run
    :type py_remove_old: bool
    """
    remove_previous_run(datadir=datadir, siteid=siteid, sitedir=sitedir, python=py_remove_old, prod_to_compare=prod_to_compare, perc_to_compare=perc_to_compare, years_to_compare=years_to_compare)
    run_python(datadir=datadir, siteid=siteid, sitedir=sitedir, prod_to_compare=prod_to_compare, perc_to_compare=perc_to_compare, years_to_compare=years_to_compare)

@pytest.fixture
def get_data():
    pass

def equal_csv(csv_1, csv_2):
    with open(csv_1, 'r') as t1, open(csv_2, 'r') as t2:
        fileone = t1.readlines()
        filetwo = t2.readlines()
        for line in filetwo:
            if line not in fileone:
                return False
    
# TODO: deal with fixtures for running nt_test
# step 10
def test_run_partition_nt():
    datadir = "./datadir/test_input"
    data_output = "./datadir/test_output"
    siteid = "US-ARc"
    sitedir = "US-ARc_sample_input"
    years = [2005] # years = [2005, 2006]
    PROD_TO_COMPARE = ['c', 'y']
    # PERC_TO_COMPARE = ['1.25', '3.75',]
    PERC_TO_COMPARE = ['1.25',]
    remove_previous_run(datadir=datadir, siteid=siteid, sitedir=sitedir, python=True, 
                        prod_to_compare=PROD_TO_COMPARE, perc_to_compare=PERC_TO_COMPARE,
                        years_to_compare=years)

    run_python(datadir=datadir, siteid=siteid, sitedir=sitedir, prod_to_compare=PROD_TO_COMPARE,
               perc_to_compare=PERC_TO_COMPARE, years_to_compare=years)
    
    # now do simple check of output 
    rootdir = os.path.join(datadir, sitedir, "10_nee_partition_nt")
    nee_y_files = glob.glob(os.path.join(rootdir, "nee_y_1.25_US-ARc_2005*"))
    ref_output = os.path.join(data_output, sitedir, "10_nee_partition_nt")
    ref_y_files = glob.glob(os.path.join(ref_output, "nee_y_1.25_US-ARc_2005*"))
    
    # log.info(nee_y_files)
    # log.info(compare_y_files)
    for f, b in zip(nee_y_files, ref_y_files):
        if not equal_csv(f, b):
            return False

    # glob the files with this root
    # for file in glob.glob(nee_y_files):
    #     print(file)
    #     log.info(file)
    #     if not equal_csv(file, )
    # with open('saved/nee_y_1.25_US-ARc_2005.csv', 'r') as t1, open(nee_y, 'r') as t2:

    

if __name__ == '__main__':
    raise ONEFluxError('Not executable')
