'''
oneflux.tools.partition_dt

For license information:
see LICENSE file or headers in oneflux.__init__.py 

Execution controller module for DT partitioning method

@author: Gilberto Pastorello and Abdelrahman Elbashandy
@contact: gzpastorello@lbl.gov & aaelbashandy@lbl.gov
@date: 2017-05-22
'''
import sys
import os
import re
import logging
import time
import numpy
import subprocess
import socket

from datetime import datetime, timedelta
from oneflux import ONEFluxError
from oneflux.partition.daytime import partitioning_dt, PARAM_DTYPE
from oneflux.partition.auxiliary import FLOAT_PREC, NAN, NAN_TEST, nan, not_nan
from oneflux.partition.library import STRING_HEADERS, DT_OUTPUT_DIR, EXTRA_FILENAME
from oneflux.graph.compare import plot_comparison, compute_plot_param_diffs
from oneflux.utils.files import file_exists_not_empty, check_create_directory

log = logging.getLogger(__name__)

HOSTNAME = socket.gethostname()


def save_remove_file(filename):
    noext_filename, ext = filename[:-4], filename[-4:]
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
                    py_filename = os.path.join(datadir, sitedir, DT_OUTPUT_DIR, FILENAME_TEMPLATE.format(prod=prod, perc=perc, y=year, s=siteid, e='csv', add=EXTRA_FILENAME))
                    if python:
                        save_remove_file(py_filename)
    else:
        log.info("Nothing selected for removal")
    return


def run_python(datadir, siteid, sitedir, prod_to_compare, perc_to_compare, years_to_compare):
    log.debug("Python partitioning execution started")
    partitioning_dt(datadir=datadir, siteid=siteid, sitedir=sitedir, prod_to_compare=prod_to_compare, perc_to_compare=perc_to_compare, years_to_compare=years_to_compare)
    log.debug("Python partitioning execution finished")
    return


def load_outputs(filename, delimiter=',', skip_header=1, is_not_hourly=True, without_date=False, without_date_timedelta=None, without_date_year=None):
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

    data = numpy.genfromtxt(fname=filename, dtype=dtype, names=headers, delimiter=delimiter, skip_header=skip_header, comments=';;;', missing_values="-9999,-9999.0,-6999,-6999.0,-1.#IND000, ", usemask=True)
    data = numpy.ma.filled(data, vfill)

    timestamp_list = []
    if not without_date:
        current_month = 1
        for i in data:
            if not is_not_hourly and int(i['hour']) == 23 and int(i['minute']) == 30:
                if int(i['month']) != current_month:
                    i['month'] = current_month
                    current_month = current_month + 1
                    if current_month == 13:
                        current_month = 1

            timestamp_list.append(datetime(int(i['year']), int(i['month']), int(i['day']), int(i['hour']), int(i['minute'])))
    else:
        record_interval = without_date_timedelta
        timestamp_list = [datetime(without_date_year, 1, 1, 0, 0) + (record_interval * i) for i in xrange(1, len(data) + 1)]

    log.debug("Finished loading {f}".format(f=filename))
    return data, headers, timestamp_list


FILENAME_TEMPLATE = "nee_{prod}_{perc}_{s}_{y}{add}.{e}"
PROD_TO_COMPARE = ['c', 'y']
PERC_TO_COMPARE = ['1.25', '3.75', '6.25', '8.75', '11.25', '13.75', '16.25', '18.75',
                   '21.25', '23.75', '26.25', '28.75', '31.25', '33.75', '36.25', '38.75',
                   '41.25', '43.75', '46.25', '48.75',
                   '50',
                   '51.25', '53.75', '56.25', '58.75',
                   '61.25', '63.75', '66.25', '68.75', '71.25', '73.75', '76.25', '78.75',
                   '81.25', '83.75', '86.25', '88.75', '91.25', '93.75', '96.25', '98.75']
def run_partition_dt(datadir, siteid, sitedir, years_to_compare,
                     dt_dir=DT_OUTPUT_DIR, filename_template=FILENAME_TEMPLATE,
                     prod_to_compare=PROD_TO_COMPARE, perc_to_compare=PERC_TO_COMPARE,
                     py_remove_old=False):
    """
    Runs daytime partitioning

    :param sitedir: absolute path to data directory
    :type sitedir: str
    :param siteid: site id in CC-SSS format
    :type siteid: str
    :param sitedir: relative path to data directory for site data
    :type sitedir: str
    :param years_to_compare: list of years to be compared
    :type years_to_compare: list
    :param dt_dir: template name for directory with daytime partitioning data
    :type dt_dir: str
    :param filename_template: template of filename for daytime partitioning data
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


if __name__ == '__main__':
    raise ONEFluxError('Not executable')
