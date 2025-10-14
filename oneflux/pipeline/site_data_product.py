'''
oneflux.pipeline.site_data_product

For license information:
see LICENSE file or headers in oneflux.__init__.py 

Generation of data products in final format from standard internal processing format

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2015-12-08
'''

import sys
import os
import csv
import logging
import argparse
import numpy
import calendar
import copy

from datetime import datetime, timedelta
from math import ceil

from oneflux import ONEFluxError
from oneflux.utils.files import check_create_directory, file_stat, zip_file_list

from oneflux.pipeline.variables_codes import VARIABLE_LIST_FULL, VARIABLE_LIST_SUB, PERC_LABEL, \
                                              TIMESTAMP_VARIABLE_LIST, FULL_D, QC_FULL_D, VARIABLES_DONOT_GAPFILL_LONG, \
                                              VARIABLES_DONOT_GAPFILL_LONG_NEEXXCUT_MEAN_L, VARIABLES_DONOT_GAPFILL_LONG_NEEXXVUT_MEAN_L
from oneflux.pipeline.aux_info_files import run_site_aux
from oneflux.pipeline.common import QCDIR, METEODIR, NEEDIR, ENERGYDIR, UNCDIR, PRODDIR, WORKING_DIRECTORY, \
                                     PRODFILE_TEMPLATE, ZIPFILE_TEMPLATE, \
                                     FULLSET_STR, SUBSET_STR, RESOLUTION_LIST, STRTEST, INTTEST, \
                                     ERA_STR, \
                                     TIMESTAMP_DTYPE_BY_RESOLUTION, TIMESTAMP_DTYPE_BY_RESOLUTION_IN, PRODFILE_YEARS_TEMPLATE, \
                                     NEW_METEO_VARS, NEW_ERA_VARS, test_pattern, get_headers, \
                                     TIMESTAMP_PRECISION_BY_RESOLUTION
from oneflux.pipeline.common import ERA_FIRST_TIMESTAMP_START, ERA_LAST_TIMESTAMP_START

log = logging.getLogger(__name__)


def add_year_records(data, res, year):
    # is valid year?
    if year < 1900 or year > 2100:
        msg = "Invalid year to be added '{y}'".format(y=year)
        log.critical(msg)
        raise ONEFluxError(msg)

    # append new year before or after
    first_y, last_y = int(data[data.dtype.names[0]][0][:4]), int(data[data.dtype.names[0]][-1][:4])
    if (year < first_y) and (year < last_y) and (first_y - year == 1):
        prepend = True
    elif (year > first_y) and (year > last_y) and (year - last_y == 1):
        prepend = False
    else:
        msg = "Not adjacent year to be added '{y}' to range {f}-{l}".format(y=year, f=first_y, l=last_y)
        log.critical(msg)
        raise ONEFluxError(msg)

    log.info("Appending year {y} to the {p} of dataset, range {f}-{l}".format(y=year, p=('beginning' if prepend else 'end'), f=first_y, l=last_y))

    if res == 'hh':
        output_resolution = get_resolution(timestamps=data[data.dtype.names[0]], error_str="add_year_record-HH-HR")
        log.debug("Determining hourly/half-hourly resolution found {r}".format(r=output_resolution))
        if output_resolution == 'HH':
            extra_recs = (17568 if calendar.isleap(year) else 17520)
            record_interval = 30
        elif output_resolution == 'HR':
            extra_recs = (8784 if calendar.isleap(year) else 8760)
            record_interval = 60
        f = datetime(year, 1, 1, 0, 0)
        timestamps_start = [(f + timedelta(minutes=i * record_interval)) for i in xrange(0, extra_recs)]
        timestamps_end = [(i + timedelta(minutes=record_interval)) for i in timestamps_start]
        new_data = numpy.empty(data.size + extra_recs, dtype=data.dtype.descr)
        new_data.fill(-9999)
        if prepend:
            new_data['TIMESTAMP_START'][:extra_recs] = [i.strftime('%Y%m%d%H%M') for i in timestamps_start]
            new_data['TIMESTAMP_END'][:extra_recs] = [i.strftime('%Y%m%d%H%M') for i in timestamps_end]
            new_data[extra_recs:] = data[:]
        else:
            new_data['TIMESTAMP_START'][data.size:] = [i.strftime('%Y%m%d%H%M') for i in timestamps_start]
            new_data['TIMESTAMP_END'][data.size:] = [i.strftime('%Y%m%d%H%M') for i in timestamps_end]
            new_data[:data.size] = data[:]
    elif res == 'dd':
        extra_recs = (366 if calendar.isleap(year) else 365)
        f = datetime(year, 1, 1)
        timestamps = [(f + timedelta(days=i)) for i in xrange(0, extra_recs)]
        new_data = numpy.empty(data.size + extra_recs, dtype=data.dtype.descr)
        new_data.fill(-9999)
        if prepend:
            new_data['TIMESTAMP'][:extra_recs] = [i.strftime('%Y%m%d') for i in timestamps]
            new_data[extra_recs:] = data[:]
        else:
            new_data['TIMESTAMP'][data.size:] = [i.strftime('%Y%m%d') for i in timestamps]
            new_data[:data.size] = data[:]
    elif res == 'ww':
        extra_recs = 52
        f = datetime(year, 1, 1, 0, 0)
        timestamps_start = [(f + timedelta(days=i * 7)) for i in xrange(0, extra_recs)]
        timestamps_end = [(i + timedelta(days=6)) for i in timestamps_start]
        timestamps_end[-1] = datetime(year, 12, 31, 0, 0)
        new_data = numpy.empty(data.size + extra_recs, dtype=data.dtype.descr)
        new_data.fill(-9999)
        if prepend:
            new_data['TIMESTAMP_START'][:extra_recs] = [i.strftime('%Y%m%d') for i in timestamps_start]
            new_data['TIMESTAMP_END'][:extra_recs] = [i.strftime('%Y%m%d') for i in timestamps_end]
            new_data[extra_recs:] = data[:]
        else:
            new_data['TIMESTAMP_START'][data.size:] = [i.strftime('%Y%m%d') for i in timestamps_start]
            new_data['TIMESTAMP_END'][data.size:] = [i.strftime('%Y%m%d') for i in timestamps_end]
            new_data[:data.size] = data[:]
    elif res == 'mm':
        extra_recs = 12
        timestamps = [(datetime(year, i + 1, 1)) for i in xrange(0, extra_recs)]
        new_data = numpy.empty(data.size + extra_recs, dtype=data.dtype.descr)
        new_data.fill(-9999)
        if prepend:
            new_data['TIMESTAMP'][:extra_recs] = [i.strftime('%Y%m') for i in timestamps]
            new_data[extra_recs:] = data[:]
        else:
            new_data['TIMESTAMP'][data.size:] = [i.strftime('%Y%m') for i in timestamps]
            new_data[:data.size] = data[:]
    elif res == 'yy':
        extra_recs = 1
        timestamps = [(datetime(year, 1, 1)) for i in xrange(0, extra_recs)]
        new_data = numpy.empty(data.size + extra_recs, dtype=data.dtype.descr)
        new_data.fill(-9999)
        if prepend:
            new_data['TIMESTAMP'][:extra_recs] = [i.strftime('%Y') for i in timestamps]
            new_data[extra_recs:] = data[:]
        else:
            new_data['TIMESTAMP'][data.size:] = [i.strftime('%Y') for i in timestamps]
            new_data[:data.size] = data[:]

    return new_data


def save_csv_txt(filename, data, delimiter=',', newline='\n', header=None):
    """
    Save procedure for properly handling missing values (from fpp.formats.common.py)
    
    :param filename: name of file to be written (overwrites if exists)
    :type filename: str
    :param data: data array
    :type data: numpy.ndarray
    :param delimiter: cell delimiter character
    :type delimiter: str
    :param newline: new line character
    :type newline: str
    :param header: header to be written before data
    :type header: str
    """
    if header is None:
        header = delimiter.join(data.dtype.names)

    with open(filename, 'w') as f:
        f.write(header + newline)
        for i, row in enumerate(data):
            if i % 1000 == 0:
                log.debug("Writing {f}: line {l}".format(f=filename, l=i))
            line = delimiter.join("-9999" if (value == -9999.0 or value == -9999.9)  else str(value) for value in row)
            f.write(line + newline)


def get_headers_qc(filename, delimiter=','):
    # from FPFileCSV
    # locate information on file
    line_number = 0
    first_numeric_line = None
    headers_line = None
    timestamp_format = None
    headers_labels = None
    line_list = []

    with open(filename, 'r') as f:
        while first_numeric_line is None:
            line = f.readline()
            line_list.append(line.strip())
            l = line.strip().split(delimiter)

            # test for headers
            if ('isodate' == line.strip()[:7].lower()) and (len(l) > 1):
                headers_line = line_number
                timestamp_format = line.strip()[:7]
                headers_labels = l
            elif ('timestamp_start' == line.strip()[:15].lower()) and (len(l) > 1):
                headers_line = line_number
                timestamp_format = 'TIMESTAMP_END'
                headers_labels = l
            elif ('timestamp' == line.strip()[:9].lower()) and (len(l) > 1):
                headers_line = line_number
                timestamp_format = line.strip()[:9]
                headers_labels = l


            # test for numeric line
            all_numeric = True
            for i in l:
                try:
                    float(i.strip())
                except ValueError:
                    all_numeric = False
                    break
            if all_numeric:
                first_numeric_line = line_number
                break
            line_number += 1
    headers = [i.strip() for i in headers_labels]
    return headers, first_numeric_line, timestamp_format, headers_line, line_list[:headers_line]

def get_dtype(variable, resolution):
    for s in STRTEST:
        if s in variable.lower():
            return 'a25'
    for s in INTTEST[resolution]:
        if s == variable.lower():
            return 'i8'
    return 'f8'

def _load_data(filename, resolution, headers=None, skip_header=0):
    if headers is None:
        headers = get_headers(filename=filename)
    dtype = [(h, get_dtype(h, resolution)) for h in headers]
    data = numpy.genfromtxt(fname=filename, dtype=dtype, names=True, delimiter=",", skip_header=skip_header, usemask=False)
    data = numpy.atleast_1d(data)

    if resolution == 'hh':
        if ('timestamp' == data.dtype.names[0].lower() and 'dtime' == data.dtype.names[1].lower()) or \
           ('isodate' == data.dtype.names[0].lower()) or \
           ('TIMESTAMP' == data.dtype.names[0]) or \
           ('TIMESTAMP_END' == data.dtype.names[0]):
            if ('timestamp' == data.dtype.names[0].lower() and 'dtime' == data.dtype.names[1].lower()):
                ts_length = 2
            elif ('isodate' == data.dtype.names[0].lower()) or \
               ('TIMESTAMP' == data.dtype.names[0]) or \
               ('TIMESTAMP_END' == data.dtype.names[0]):
                ts_length = 1
            else:
                raise ONEFluxError("Unknown condition for timestamps headers")
            log.info("Handling old version variable labels HH, adapting: {f}".format(f=filename))
            res = get_resolution(timestamps=data[data.dtype.names[0]], error_str=filename)
            delta = (timedelta(minutes=30) if res == 'HH' else timedelta(minutes=60))
            first_begin = (datetime.strptime(data[data.dtype.names[0]][0], '%Y%m%d%H%M') - delta).strftime('%Y%m%d%H%M')
            new_data = numpy.empty(data.size, dtype=[('TIMESTAMP_START', 'a25'), ('TIMESTAMP_END', 'a25')] + data.dtype.descr[ts_length:])
            new_data['TIMESTAMP_START'][0] = first_begin
            new_data['TIMESTAMP_START'][1:] = data[data.dtype.names[0]][:-1]
            new_data['TIMESTAMP_END'][:] = data[data.dtype.names[0]]
            for var in data.dtype.names[ts_length:]:
                new_data[var][:] = data[var]
            data = new_data
        elif 'year' == data.dtype.names[0].lower() and 'week' == data.dtype.names[1].lower():
            raise ONEFluxError("Found year/week in non-WW file: {f}".format(f=filename))
    elif resolution == 'dd':
        if 'isodate' == data.dtype.names[0].lower():
            log.info("Handling old version variable labels DD, adapting: {f}".format(f=filename))
            data.dtype.names = ['TIMESTAMP'] + list(data.dtype.names)[1:]
        elif 'year' == data.dtype.names[0].lower() and 'week' == data.dtype.names[1].lower():
            raise ONEFluxError("Found year/week in non-WW file: {f}".format(f=filename))
    elif resolution == 'ww':
        if 'isodate' == data.dtype.names[0].lower():
            raise ONEFluxError("Found isodate in WW file: {f}".format(f=filename))
        elif 'year' == data.dtype.names[0].lower() and 'week' == data.dtype.names[1].lower():
            log.info("Handling old version variable labels WW, adapting: {f}".format(f=filename))
            new_data = numpy.empty(data.size, dtype=[('TIMESTAMP_START', 'a25'), ('TIMESTAMP_END', 'a25')] + data.dtype.descr[2:])
            idx = 0
            for _ in numpy.nditer(data):
                ts_start = datetime(data[data.dtype.names[0]][idx], 1, 1) + timedelta(days=7 * (int(data[data.dtype.names[1]][idx]) - 1))
                ts_end = ts_start + timedelta(days=6)
                new_data['TIMESTAMP_START'][idx] = ts_start.strftime('%Y%m%d')
                new_data['TIMESTAMP_END'][idx] = ts_end.strftime('%Y%m%d')
                if int(data[data.dtype.names[1]][idx]) == 52: # last week, ends in last day of year
                    new_data['TIMESTAMP_END'][idx] = datetime(data[data.dtype.names[0]][idx], 12, 31).strftime('%Y%m%d')
                idx += 1
            new_data['TIMESTAMP_END'][idx - 1] = datetime(data[data.dtype.names[0]][idx - 1], 12, 31).strftime('%Y%m%d')
            for var in data.dtype.names[2:]:
                new_data[var][:] = data[var]
            data = new_data
        elif 'timestamp' == data.dtype.names[0].lower() and 'year' == data.dtype.names[1].lower() and 'week' == data.dtype.names[2].lower():
            log.info("Handling weird version variable labels WW, adapting: {f}".format(f=filename))
            new_data = numpy.empty(data.size, dtype=[('TIMESTAMP_START', 'a25'), ('TIMESTAMP_END', 'a25')] + data.dtype.descr[3:])
            idx = 0
            for _ in numpy.nditer(data):
                ts_start = datetime(data[data.dtype.names[1]][idx], 1, 1) + timedelta(days=7 * (int(data[data.dtype.names[2]][idx]) - 1))
                ts_end = ts_start + timedelta(days=6)
                new_data['TIMESTAMP_START'][idx] = ts_start.strftime('%Y%m%d')
                new_data['TIMESTAMP_END'][idx] = ts_end.strftime('%Y%m%d')
                if int(data[data.dtype.names[2]][idx]) == 52: # last week, ends in last day of year
                    new_data['TIMESTAMP_END'][idx] = datetime(data[data.dtype.names[1]][idx], 12, 31).strftime('%Y%m%d')
                idx += 1
            new_data['TIMESTAMP_END'][idx - 1] = datetime(data[data.dtype.names[1]][idx - 1], 12, 31).strftime('%Y%m%d')
            for var in data.dtype.names[3:]:
                new_data[var][:] = data[var]
            data = new_data
    elif resolution == 'mm':
        if 'isodate' == data.dtype.names[0].lower():
            data.dtype.names = ['TIMESTAMP'] + list(data.dtype.names)[1:]
            log.info("Handling old version variable labels DD, adapting: {f}".format(f=filename))
        elif 'year' == data.dtype.names[0].lower() and 'week' == data.dtype.names[1].lower():
            raise ONEFluxError("Found year/week in non-WW file: {f}".format(f=filename))
    elif resolution == 'yy':
        if 'isodate' == data.dtype.names[0].lower():
            data.dtype.names = ['TIMESTAMP'] + list(data.dtype.names)[1:]
            log.info("Handling old version variable labels DD, adapting: {f}".format(f=filename))
        elif 'year' == data.dtype.names[0].lower() and 'week' == data.dtype.names[1].lower():
            raise ONEFluxError("Found year/week in non-WW file: {f}".format(f=filename))
    else:
        if 'isodate' == data.dtype.names[0].lower():
            raise ONEFluxError("Unknown resolution '{r}' in: {f}".format(r=resolution, f=filename))

    return data


def load_qcdata(siteid, ddir, firsty, lasty, output_resolution='HH'):

    filelist = test_pattern(tdir=ddir, tpattern="*_qcv_*.csv", label='gen_data_products_site')

    resolution = 'hh'
    header_list = []
    line_count = 0
    data_list = []
    for year in range(firsty, lasty + 1):
        filename = "{s}_qcv_{y}.csv".format(s=siteid, y=year)

        # file expected but not found (missing year?)
        if filename not in filelist:
            if year == firsty:
                raise ONEFluxError("QC-Data file expected for first year {y} but not listed: {f}".format(y=year, f=filename))
            if year == lasty:
                raise ONEFluxError("QC-Data file expected for last year {y} but not listed: {f}".format(y=year, f=filename))
            record_interval = timedelta(minutes=(60 if (output_resolution == 'HR') else 30))
            timestamp_start_list, timestamp_end_list = [], []
            timestamp = datetime(year, 1, 1, 0, 0)
            if not header_list:
                raise ONEFluxError("QC-Data no header entries (first year site exception not caught?)")
            while timestamp.year == year:
                new_timestamp = timestamp + record_interval
                timestamp_start_list.append(timestamp.strftime("%Y%m%d%H%M"))
                timestamp_end_list.append(new_timestamp.strftime("%Y%m%d%H%M"))
                timestamp = new_timestamp

            data = numpy.empty(len(timestamp_start_list), dtype=[('TIMESTAMP_START', 'a25'), ('TIMESTAMP_END', 'a25')])
            data['TIMESTAMP_START'][:] = timestamp_start_list
            data['TIMESTAMP_END'][:] = timestamp_end_list

        # file expected and found
        else:
            filelist.remove(filename)
            filename = os.path.join(ddir, filename)
            if not os.path.isfile(filename):
                raise ONEFluxError("QC-Data file not found: {f}".format(f=filename))

            log.debug("Loading qc-data/{r} file: {f}".format(r=resolution, f=filename))
            headers, first_numeric_line, _, headers_line, first_lines = get_headers_qc(filename=filename)
            data = _load_data(filename=filename, resolution=resolution, headers=headers, skip_header=first_numeric_line - 1)
            header_list = header_list + [entry for entry in data.dtype.names if entry not in header_list]
        data_list.append(data)
        line_count += data.size
    if filelist:
        log.warning("Unexpected QC-Data files found: {l}".format(l=filelist))

    # allocate output array
    dtype = [(h, get_dtype(h, resolution)) for h in list(header_list)]
    new_data = numpy.empty(line_count, dtype=dtype)
    for vlabel, vtype in dtype:
        if ('a' in vtype) or ('s' in vtype):
            new_data[vlabel][:] = ''
        elif ('i' in vtype) or ('f' in vtype):
            new_data[vlabel].fill(-9999)
        else:
            raise ONEFluxError("QC-Data file unknown data type: {t}".format(t=vtype))

    # copy data to output array
    first_rec, last_rec = 0, 0
    for data in data_list:
        first_rec = last_rec
        last_rec = last_rec + data.size
        for vlabel in data.dtype.names:
            new_data[vlabel][first_rec:last_rec] = data[vlabel]
    if data_list[0][-1] != new_data[list(data_list[0].dtype.names)][len(data_list[0]) - 1]:
        raise ONEFluxError("QC-Data file error in concatenated array. File: {f}, concatenated: {c}".format(f=data_list[0][-1], c=new_data[list(data_list[0].dtype.names)][len(data_list[0]) - 1]))
    if data_list[-1][-1] != new_data[list(data_list[-1].dtype.names)][-1]:
        raise ONEFluxError("QC-Data file error in concatenated array. File: {f}, concatenated: {c}".format(f=data_list[-1][-1], c=new_data[list(data_list[-1].dtype.names)][-1]))

    return new_data

def merge_qcdata(qcdata, output):

    if not numpy.all(qcdata['TIMESTAMP_END'] == output['TIMESTAMP_END']):
        raise ONEFluxError("Timestamps differ for QAData merging")

    var_add = []
    for var_label, var_type in qcdata.dtype.descr:
        if var_label in NEW_METEO_VARS:
            var_add.append((var_label, var_type))

    dtype = list(output.dtype.descr) + var_add

    d = numpy.empty(output.size, dtype=dtype)

    # copy output data to merged output
    for dt in output.dtype.descr:
        d[dt[0]] = output[dt[0]]

    # copy new vars to merged output
    for dt in var_add:
        d[dt[0]] = qcdata[dt[0]]

    return d

def merge_qcdata_res(qcdata, output, res):
    """
    Merges QC Data at resolutions other than HH (DD, WW, MM, YY)
    
    :param qcdata: QC Data array
    :type qcdata: numpy.recarray
    :param output: Output Data array
    :type output: numpy.recarray
    :param res: temporal resolution
    :type res: str
    """
    ts_label = TIMESTAMP_DTYPE_BY_RESOLUTION[res][-1][0]

    if not numpy.all(qcdata[ts_label] == output[ts_label]):
        raise ONEFluxError("Timestamps differ for QAData merging ({r})".format(r=res))

    var_add = [i for i in list(qcdata.dtype.descr) if (('TIMESTAMP' not in i[0].upper()) and\
                                                       ('WD' != i[0].upper()) and\
                                                       ('WD' + PERC_LABEL != i[0].upper()) and\
                                                       ('RH' != i[0].upper()) and\
                                                       ('RH' + PERC_LABEL != i[0].upper())\
                                                       )]
    dtype = list(output.dtype.descr) + var_add

    d = numpy.empty(output.size, dtype=dtype)

    # copy output data to merged output
    for dt in output.dtype.descr:
        d[dt[0]] = output[dt[0]]

    # copy new vars to merged output
    for dt in var_add:
        d[dt[0]] = qcdata[dt[0]]

    return d

def aggregate_qcdata(qcdata):
    """
    Create DD, WW, MM, and YY aggregations for QC Data from HH
    
    :param qcdata: QC Data array
    :type qcdata: numpy.recarray
    """

    # DD
    log.debug('Aggregating daily DD QC Data')
    curr_ts, last_ts = datetime.strptime(qcdata['TIMESTAMP_START'][0], '%Y%m%d%H%M'), datetime.strptime(qcdata['TIMESTAMP_START'][-1], '%Y%m%d%H%M')
    curr_y, first_y, last_y = curr_ts.year, curr_ts.year, last_ts.year
    entries_dd = 0
    while curr_y <= last_y:
        days_in_year = 366 if calendar.isleap(curr_y) else 365
        entries_dd += days_in_year
        curr_y += 1
    dtype = [(vlabel, 'f8') for vlabel in NEW_METEO_VARS if vlabel in qcdata.dtype.names]
    dtype_ext = dtype + [(vlabel + PERC_LABEL, 'f8') for vlabel, _ in dtype]
    dtype_dd = TIMESTAMP_DTYPE_BY_RESOLUTION['dd'] + dtype_ext
    data_dd = numpy.empty(entries_dd, dtype=dtype_dd)
    data_dd.fill(-9999)
    day_diff = timedelta(hours=24)
    curr_idx = 0
    while curr_ts <= last_ts:
        if curr_idx % 300 == 0:
            log.debug("Aggregating day {d}".format(d=curr_idx))
        dd = curr_ts.strftime('%Y%m%d')
        data_dd['TIMESTAMP'][curr_idx] = dd
        mask_dd = numpy.char.startswith(qcdata['TIMESTAMP_START'], dd)
        for vlabel, _ in dtype:
            values = qcdata[vlabel][mask_dd]
            perc = float(values[values > -9999].size) / float(values.size)
            if perc > 0.5:
                mean = numpy.mean(values[values > -9999])
            else:
                mean = -9999
                perc = -9999
            data_dd[vlabel][curr_idx] = mean
            data_dd[vlabel + PERC_LABEL][curr_idx] = perc
        curr_idx += 1
        curr_ts += day_diff

    # WW
    log.debug('Aggregating weekly WW QC Data')
    recs_ww = 52
    dtype_ww = TIMESTAMP_DTYPE_BY_RESOLUTION['ww'] + dtype_ext
    data_ww = numpy.empty((last_y - first_y + 1) * recs_ww, dtype=dtype_ww)
    data_ww.fill(-9999)
    for idx, year in enumerate(range(first_y, last_y + 1)):
        first_rec = idx * recs_ww
        curr_rec = first_rec
        last_rec = first_rec + recs_ww
        f = datetime(year, 1, 1, 0, 0)
        data_ww['TIMESTAMP_START'][first_rec:last_rec] = [(f + timedelta(days=i * 7)).strftime('%Y%m%d') for i in xrange(0, recs_ww)]
        data_ww['TIMESTAMP_END'][first_rec:last_rec] = [(datetime.strptime(i, '%Y%m%d') + timedelta(days=6)).strftime('%Y%m%d') for i in data_ww['TIMESTAMP_START'][first_rec:last_rec]]
        data_ww['TIMESTAMP_END'][last_rec - 1] = datetime(year, 12, 31, 0, 0).strftime('%Y%m%d')
        while curr_rec < last_rec:
            first_idx, last_idx = numpy.where(data_dd['TIMESTAMP'] == data_ww['TIMESTAMP_START'][curr_rec])[0][0], numpy.where(data_dd['TIMESTAMP'] == data_ww['TIMESTAMP_END'][curr_rec])[0][0]
            for vlabel, _ in dtype:
                values = data_dd[vlabel][first_idx:last_idx]
                values_perc = data_dd[vlabel + PERC_LABEL][first_idx:last_idx]
                values_perc[values_perc <= -9999] = 0.0
                perc = numpy.mean(values_perc)
                if perc > 0.5:
                    mean = numpy.mean(values[values > -9999])
                else:
                    mean = -9999
                    perc = -9999
                data_ww[vlabel][curr_rec] = mean
                data_ww[vlabel + PERC_LABEL][curr_rec] = perc
            curr_rec += 1


    # MM
    log.debug('Aggregating monthly MM QC Data')
    recs_mm = 12
    dtype_mm = TIMESTAMP_DTYPE_BY_RESOLUTION['mm'] + dtype_ext
    data_mm = numpy.empty((last_y - first_y + 1) * recs_mm, dtype=dtype_mm)
    data_mm.fill(-9999)
    data_mm['TIMESTAMP'] = [str(y) + str(m).zfill(2) for y in range(first_y, last_y + 1) for m in range(1, recs_mm + 1)]
    for idx, mm in enumerate(data_mm['TIMESTAMP']):
        mask_mm = numpy.char.startswith(data_dd['TIMESTAMP'], mm)
        for vlabel, _ in dtype:
            values = data_dd[vlabel][mask_mm]
            values_perc = data_dd[vlabel + PERC_LABEL][mask_mm]
            values_perc[values_perc <= -9999] = 0.0
            perc = numpy.mean(values_perc)
            if perc > 0.5:
                mean = numpy.mean(values[values > -9999])
            else:
                mean = -9999
                perc = -9999
            data_mm[vlabel][idx] = mean
            data_mm[vlabel + PERC_LABEL][idx] = perc

    # YY
    log.debug('Aggregating yearly YY QC Data')
    dtype_yy = TIMESTAMP_DTYPE_BY_RESOLUTION['yy'] + dtype_ext
    data_yy = numpy.empty((last_y - first_y + 1), dtype=dtype_yy)
    data_yy.fill(-9999)
    data_yy['TIMESTAMP'] = [str(y) for y in range(first_y, last_y + 1)]
    for idx, yy in enumerate(data_yy['TIMESTAMP']):
        mask_yy = numpy.char.startswith(data_dd['TIMESTAMP'], yy)
        for vlabel, _ in dtype:
            values = data_dd[vlabel][mask_yy]
            values_perc = data_dd[vlabel + PERC_LABEL][mask_yy]
            values_perc[values_perc <= -9999] = 0.0
            perc = numpy.mean(values_perc)
            if perc > 0.5:
                mean = numpy.mean(values[values > -9999])
            else:
                mean = -9999
                perc = -9999
            data_yy[vlabel][idx] = mean
            data_yy[vlabel + PERC_LABEL][idx] = perc

    return data_dd, data_ww, data_mm, data_yy

def load_meteo(siteid, ddir, resolution):
    filename = os.path.join(ddir, "{s}_meteo_{r}.csv".format(s=siteid, r=resolution))
    if not os.path.isfile(filename):
        raise ONEFluxError("METEO file not found: {f}".format(f=filename))

    log.debug("Loading meteo/{r} file: {f}".format(r=resolution, f=filename))
    data = _load_data(filename=filename, resolution=resolution)

    new_names = list(data.dtype.names)
    for i, l in enumerate(data.dtype.names):
        if l == 'TS_0_f': new_names[i] = 'TS_1_f'
        elif l == 'Ts_0_f': new_names[i] = 'TS_1_f'
        elif l == 'TS_0_fqc': new_names[i] = 'TS_1_fqc'
        elif l == 'Ts_0_fqc': new_names[i] = 'TS_1_fqc'
        elif l == 'SWC_0_f': new_names[i] = 'SWC_1_f'
        elif l == 'SWC_0_fqc': new_names[i] = 'SWC_1_fqc'
    if new_names != list (data.dtype.names):
        log.info('Changing old enum: old={o}, new={n}'.format(o=data.dtype.names, n=new_names))
        data.dtype.names = new_names

    # check SWC for 0-100 range, instead of 0-1 range
    log.info("Checking range of values for SWC ({s})".format(s=siteid))
    ts_label = TIMESTAMP_DTYPE_BY_RESOLUTION[resolution][0][0]
    if ts_label != data.dtype.names[0]:
        msg = "Unknown timestamp label '{u}', expected '{l}'".format(u=data.dtype.names[0], l=ts_label)
        log.critical(msg)
        raise ONEFluxError(msg)

    # find SWC variables
    swc_vars = []
    for var_label in data.dtype.names:
        if (var_label.lower().startswith('swc')) and ('qc' not in var_label.lower()):
            swc_vars.append(var_label)

    if swc_vars:
        log.debug("Found {n} SWC variables ({v}) for {s}, checking ranges".format(n=len(swc_vars), v=str(swc_vars), s=siteid))
        first_y, last_y = int(data[ts_label][0][:4]), int(data[ts_label][-1][:4])
        list_y = range(first_y, last_y + 1)
        for swc_var_label in swc_vars:
            not_missing_mask = data[swc_var_label] > -9999
            for year in list_y:
                mask = numpy.char.startswith(data[ts_label], str(year)) & not_missing_mask
                if mask.sum() > 0:
                    negative_count = (data[swc_var_label][mask] < 0).sum()
                    min_val, max_val = numpy.min(data[swc_var_label][mask]), numpy.max(data[swc_var_label][mask])
                    log.debug("SWC variable '{v}' stats ({s}, {y}): negative_count={n}  min={i}  max={a}".format(v=swc_var_label, s=siteid, y=year, n=negative_count, i=min_val, a=max_val))
                    if negative_count > 0:
                        log.error("SWC variable '{v}' ({s}, {y}) has {n} negative values in the record".format(v=swc_var_label, s=siteid, y=year, n=negative_count))
                    if max_val <= 1.0:
                        log.warning("SWC variable '{v}' ({s}, {y}) has max value of {a}, likely 0-1 range will be converted to 0-100".format(v=swc_var_label, s=siteid, y=year, a=max_val))
                        data[swc_var_label][mask] = 100.0 * data[swc_var_label][mask]
        log.debug("Done with checking SWC vars for {s}".format(s=siteid))
    else:
        log.debug("No SWC vars found for {s}".format(s=siteid))

    return data

def load_nee(siteid, ddir, resolution):
    filename = os.path.join(ddir, "{s}_NEE_{r}.csv".format(s=siteid, r=resolution))
    if not os.path.isfile(filename):
        f1 = filename
        filename = os.path.join(ddir, "{s}_NEE_{r}_v001.csv".format(s=siteid, r=resolution))
        if not os.path.isfile(filename):
            raise ONEFluxError("NEE file(s) not found: 1st={f1}, 2nd={f2}".format(f1=f1, f2=filename))

    log.debug("Loading nee/{r} file: {f}".format(r=resolution, f=filename))
    nee = _load_data(filename=filename, resolution=resolution)

    # checking and fixing timestamps for dd files
    if resolution == 'dd':
        if 'DOY' in nee.dtype.names: doy_str = 'DOY'
        elif 'Doy' in nee.dtype.names: doy_str = 'Doy'
        elif 'doy' in nee.dtype.names: doy_str = 'doy'
        elif 'DoY'  in nee.dtype.names: doy_str = 'DoY'
        else: raise ONEFluxError('Cannot find doy_str: {t}'.format(t=nee.dtype.names))
        timestamp_ts = [datetime.strptime(i, "%Y%m%d") for i in nee['TIMESTAMP']]
        year_ls = [str(i.year) for i in timestamp_ts]
        timestamp_doy = [datetime.strptime(year_ls[i] + str(nee[doy_str][i]), "%Y%j") for i in xrange(nee.size)]
        if timestamp_ts != timestamp_doy:
            log.info("Fixing DD timestamp bug for: {f}".format(f=filename))
            nee['TIMESTAMP'][:] = [i.strftime("%Y%m%d") for i in timestamp_doy]

    return nee

def load_energy(siteid, ddir, resolution):
    filename = os.path.join(ddir, "{s}_energy_{r}.csv".format(s=siteid, r=resolution))
    if not os.path.isfile(filename):
        raise ONEFluxError("ENERGY file not found: {f}".format(f=filename))

    log.debug("Loading energy/{r} file: {f}".format(r=resolution, f=filename))
    return _load_data(filename=filename, resolution=resolution)

def merge_unc(dt_reco, dt_gpp, nt_reco, nt_gpp, resolution, nt_skip=False, dt_skip=False):
    dtype_ts = TIMESTAMP_DTYPE_BY_RESOLUTION_IN[resolution]
    htype = [dt[0] for dt in dtype_ts]
    dtype_ts = TIMESTAMP_DTYPE_BY_RESOLUTION[resolution]
    dtype_comp = []
    array_size = None
    timestamp_arrays = None
    for dt in TIMESTAMP_DTYPE_BY_RESOLUTION[resolution]:
        label = dt[0]
        if not nt_skip:
            if not numpy.all(nt_reco[label] == nt_gpp[label]):
                raise ONEFluxError("Timestamps differ for NT_RECO and NT_GPP")
            array_size = nt_reco.size
        if not dt_skip:
            if not numpy.all(dt_reco[label] == dt_gpp[label]):
                raise ONEFluxError("Timestamps differ for DT_RECO and DT_GPP")
            array_size = dt_reco.size
        if (not nt_skip) and (not dt_skip):
            if not numpy.all(nt_reco[label] == dt_reco[label]):
                raise ONEFluxError("Timestamps differ for NT_RECO and DT_RECO")

    if not nt_skip:
        timestamp_arrays = {}
        for dt in dtype_ts:
            timestamp_arrays[dt[0]] = nt_reco[dt[0]]
        for dt in nt_reco.dtype.descr:
            if dt[0] not in htype:
                dtype_comp.append(('NT_' + dt[0], dt[1]))
        for dt in nt_gpp.dtype.descr:
            if dt[0] not in htype:
                dtype_comp.append(('NT_' + dt[0], dt[1]))

    if not dt_skip:
        timestamp_arrays = {}
        for dt in dtype_ts:
            timestamp_arrays[dt[0]] = dt_reco[dt[0]]
        for dt in dt_reco.dtype.descr:
            if dt[0] not in htype:
                dtype_comp.append(('DT_' + dt[0], dt[1]))
        for dt in dt_gpp.dtype.descr:
            if dt[0] not in htype:
                dtype_comp.append(('DT_' + dt[0], dt[1]))

    dtype = dtype_ts + dtype_comp
    h = [i[0] for i in dtype]
    for i in range(len(h)):
        if h[i] in h[i + 1:]:
            log.error("Load UNC/PART, duplicate header: {h}".format(h=h[i]))

    if timestamp_arrays is not None:
        d = numpy.empty(array_size, dtype=dtype)
        for dt in dtype_ts:
            d[dt[0]] = timestamp_arrays[dt[0]]
    else:
        log.warning("Nothing to merge in UNC, both NT and DT skipped")
        return None

    if not nt_skip:
        for dt in nt_reco.dtype.descr:
            if dt[0] not in htype:
                d['NT_' + dt[0]] = nt_reco[dt[0]]
        for dt in nt_gpp.dtype.descr:
            if dt[0] not in htype:
                d['NT_' + dt[0]] = nt_gpp[dt[0]]

    if not dt_skip:
        for dt in dt_reco.dtype.descr:
            if dt[0] not in htype:
                d['DT_' + dt[0]] = dt_reco[dt[0]]
        for dt in dt_gpp.dtype.descr:
            if dt[0] not in htype:
                d['DT_' + dt[0]] = dt_gpp[dt[0]]
    
    log.debug("Merged UNC headers: {h}".format(h=d.dtype.names))
    return d

def load_unc(siteid, ddir, resolution, nt_skip=False, dt_skip=False):
    nrecords = None
    nt_reco, nt_gpp, dt_reco, dt_gpp = None, None, None, None

    if not nt_skip:
        nt_reco_filename = os.path.join(ddir, "{s}_NT_RECO_{r}.csv".format(s=siteid, r=resolution))
        nt_gpp_filename = os.path.join(ddir, "{s}_NT_GPP_{r}.csv".format(s=siteid, r=resolution))
        if not os.path.isfile(nt_reco_filename):
            raise ONEFluxError("NT_RECO file not found: {f}".format(f=nt_reco_filename))
        if not os.path.isfile(nt_gpp_filename):
            raise ONEFluxError("NT_RECO file not found: {f}".format(f=nt_gpp_filename))

        # NT RECO
        log.debug("Loading partitioning/{r} file: {f}".format(r=resolution, f=nt_reco_filename))
        nt_reco = _load_data(filename=nt_reco_filename, resolution=resolution)
        if nrecords is None:
            nrecords = nt_reco.size
        elif nt_reco.size != nrecords:
            raise ONEFluxError("Incompatible number of records UNK={p}  and  NT_RECO={s}".format(p=nrecords, s=nt_reco.size))

        # NT GPP
        log.debug("Loading partitioning/{r} file: {f}".format(r=resolution, f=nt_gpp_filename))
        nt_gpp = _load_data(filename=nt_gpp_filename, resolution=resolution)
        if nt_gpp.size != nrecords:
            raise ONEFluxError("Incompatible number of records NT_RECO={p}  and  NT_GPP={s}".format(p=nrecords, s=nt_gpp.size))

    if not dt_skip:
        dt_reco_filename = os.path.join(ddir, "{s}_DT_RECO_{r}.csv".format(s=siteid, r=resolution))
        dt_gpp_filename = os.path.join(ddir, "{s}_DT_GPP_{r}.csv".format(s=siteid, r=resolution))
        if not os.path.isfile(dt_reco_filename):
            raise ONEFluxError("DT_RECO file not found: {f}".format(f=dt_reco_filename))
        if not os.path.isfile(dt_gpp_filename):
            raise ONEFluxError("DT_GPP file not found: {f}".format(f=dt_gpp_filename))

        # DT RECO
        log.debug("Loading partitioning/{r} file: {f}".format(r=resolution, f=dt_reco_filename))
        dt_reco = _load_data(filename=dt_reco_filename, resolution=resolution)
        if nrecords is None:
            nrecords = dt_reco.size
        elif dt_reco.size != nrecords:
            raise ONEFluxError("Incompatible number of records NT_RECO={p}  and  DT_RECO={s}".format(p=nrecords, s=dt_gpp.size))

        # DT GPP
        log.debug("Loading partitioning/{r} file: {f}".format(r=resolution, f=dt_gpp_filename))
        dt_gpp = _load_data(filename=dt_gpp_filename, resolution=resolution)
        if dt_gpp.size != nrecords:
            raise ONEFluxError("Incompatible number of records DT/NT_RECO={p}  and  DT_GPP={s}".format(p=nrecords, s=dt_gpp.size))

    return merge_unc(dt_reco=dt_reco, dt_gpp=dt_gpp, nt_reco=nt_reco, nt_gpp=nt_gpp, resolution=resolution, nt_skip=nt_skip, dt_skip=dt_skip)

def update_names(data):
    old_h = []
    new_h = []
    unknown_variables = []
    for e in data.dtype.names:
        new_e = FULL_D.get(e, None)
        if new_e is None:
            unknown_variables.append(e)
            log.warning("Unknown variable removed: '{v}'".format(v=e))
        else:
            old_h.append(e)
            new_h.append(new_e)
    if unknown_variables:
        data = data[old_h]
    data.dtype.names = new_h
    return data

def update_names_qc(data):
    old_h = []
    new_h = []
    unknown_variables = []
    for e in data.dtype.names:
        new_e = QC_FULL_D.get(e, None)
        if new_e is None:
            unknown_variables.append(e)
            log.warning("Unknown QC variable removed: '{v}'".format(v=e))
        else:
            old_h.append(e)
            new_h.append(new_e)
    if unknown_variables:
        data = data[old_h]
    data.dtype.names = new_h
    return data

def merge_arrays(meteo, energy, nee, unc, resolution, nt_skip=False, dt_skip=False):
    dtype_ts = TIMESTAMP_DTYPE_BY_RESOLUTION[resolution]
    htype = [dt[0] for dt in dtype_ts]
    dtype_comp = []

    # check timestamp columns match
    for dt in TIMESTAMP_DTYPE_BY_RESOLUTION[resolution]:
        label = dt[0]
        if not numpy.all(meteo[label] == energy[label]):
            diff = ~(meteo[label] == energy[label])
            raise ONEFluxError("Timestamps ({l}) differ for METEO '{t1}' and ENERGY '{t2}'".format(l=label, t1=meteo[label][diff][0], t2=energy[label][diff][0]))
        if not numpy.all(meteo[label] == nee[label]):
            diff = ~(meteo[label] == nee[label])
            raise ONEFluxError("Timestamps ({l}) differ for METEO '{t1}' and NEE '{t2}'".format(l=label, t1=meteo[label][diff][0], t2=nee[label][diff][0]))
        if (not nt_skip) or (not dt_skip):
            if not numpy.all(meteo[label] == unc[label]):
                diff = ~(meteo[label] == unc[label])
                raise ONEFluxError("Timestamps ({l}) differ for METEO '{t1}' and UNC '{t2}'".format(l=label, t1=meteo[label][diff][0], t2=unc[label][diff][0]))

    # populate new headers
    dtype_comp_labels = []
    for dt in meteo.dtype.descr:
        if dt[0] not in htype:
            if dt[0] in dtype_comp_labels:
                log.debug("Skip duplicate header: {h}".format(h=dt[0]))
            else:
                dtype_comp_labels.append(dt[0])
                dtype_comp.append((dt[0], dt[1]))
    for dt in energy.dtype.descr:
        if dt[0] not in htype:
            if dt[0] in dtype_comp_labels:
                log.debug("Skip duplicate header: {h}".format(h=dt[0]))
            else:
                dtype_comp_labels.append(dt[0])
                dtype_comp.append((dt[0], dt[1]))
    for dt in nee.dtype.descr:
        if dt[0] not in htype:
            if dt[0] in dtype_comp_labels:
                log.debug("Skip duplicate header: {h}".format(h=dt[0]))
            else:
                dtype_comp_labels.append(dt[0])
                dtype_comp.append((dt[0], dt[1]))
    
    if (not nt_skip) or (not dt_skip):
        for dt in unc.dtype.descr:
            if dt[0] not in htype:
                if dt[0] in dtype_comp_labels:
                    log.debug("Skip duplicate header: {h}".format(h=dt[0]))
                else:
                    dtype_comp_labels.append(dt[0])
                    dtype_comp.append((dt[0], dt[1]))

    dtype = dtype_ts + dtype_comp
    h = [i[0] for i in dtype]

    # check for repeated headers
    for i in range(len(h)):
        if h[i] in h[i + 1:]:
            raise ONEFluxError("Repeated header '{h}'".format(h=h[i]))

    # allocate new array and populate it
    d = numpy.empty(meteo.size, dtype=dtype)
    for dt in dtype_ts:
        d[dt[0]] = meteo[dt[0]]
    for dt in meteo.dtype.descr:
        if dt[0] not in htype:
            d[dt[0]] = meteo[dt[0]]
    for dt in energy.dtype.descr:
        if dt[0] not in htype:
            d[dt[0]] = energy[dt[0]]
    for dt in nee.dtype.descr:
        if dt[0] not in htype:
            d[dt[0]] = nee[dt[0]]
    
    if (not nt_skip) or (not dt_skip):
        for dt in unc.dtype.descr:
            if dt[0] not in htype:
                d[dt[0]] = unc[dt[0]]

    return d

def get_resolution(timestamps, error_str=''):
    if len(timestamps) < 100:
        raise ONEFluxError("Too few timestamp entries: {e}".format(e=error_str))

    diff = datetime.strptime(timestamps[1], "%Y%m%d%H%M") - datetime.strptime(timestamps[0], "%Y%m%d%H%M")
    for i in range(2, len(timestamps), 25):
        t1 = datetime.strptime(timestamps[i], "%Y%m%d%H%M")
        t0 = datetime.strptime(timestamps[i - 1], "%Y%m%d%H%M")
        d = t1 - t0
        if d != diff:
            raise ONEFluxError("Inconsistent timestamp intevals ({e}): {t1} {t0}".format(e=error_str, t1=t1.strftime("%Y%m%d%H%M"), t0=t0.strftime("%Y%m%d%H%M")))

    if ceil(diff.seconds / 60.0) == 30:
        return 'HH'
    elif ceil(diff.seconds / 60.0) == 60:
        return 'HR'
    else:
        raise ONEFluxError("Unknown resolution ({e}): {r} minutes".format(e=error_str, r=ceil(diff.seconds / 60.0)))

def get_first_last_years(timestamps, first, last, error_str=''):
    f = int(timestamps[0][:4])
    l = int(timestamps[-1][:4])
    if first is not None:
        if f != first:
            raise ONEFluxError("First year differs: {f1} <> {f2}, {e}".format(f1=f, f2=first, e=error_str))
    if last is not None:
        if l != last:
            raise ONEFluxError("Last year differs: {f1} <> {f2}, {e}".format(f1=l, f2=last, e=error_str))
    return f, l

def gen_stats_zip(filename_list, zipfilename, tier='tier2', csv_processor='ICOS-ETC', zip_processor='LBL_AMP', ts_format="%Y-%m-%d %H:%M:%S"):
    """
    Generate stats and zip file for file list 
    # ZIP:  filename, fileSize, fileChecksum, fileCount, tier, processor, createDate
    # CSV: zipfilename, filename, fileSize, fileChecksum,  processor, createDate

    :param filename_list:
    :type filename_list:
    """
    log.info("Generating ZIP and stats for: {z}".format(z=zipfilename))

    if not filename_list:
        return [], []

    today = datetime.now().strftime(ts_format)
    output_zip = zip_file_list(filename_list=filename_list, zipfilename=zipfilename)

    if output_zip != zipfilename:
        raise ONEFluxError("ZIP filenames differ: {i}  {o}".format(i=zipfilename, o=output_zip))

    size, md5sum, _ = file_stat(filename=zipfilename)
    zip_entry = [['"{e}"'.format(e=os.path.basename(zipfilename)),
                  '{e}'.format(e=format(size)),
                  '"{e}"'.format(e=md5sum),
                  '"{e}"'.format(e=len(filename_list)),
                  '"{e}"'.format(e=tier),
                  '"{e}"'.format(e=zip_processor),
                  '"{e}"'.format(e=today)], ]
    csv_entries = []
    for filename in filename_list:
        f_size, f_md5sum, f_timestamp_change = file_stat(filename=filename)
        f_today = f_timestamp_change.strftime(ts_format)
        entry = ['"{e}"'.format(e=os.path.basename(zipfilename)),
                 '"{e}"'.format(e=os.path.basename(filename)),
                 '{e}'.format(e=f_size),
                 '"{e}"'.format(e=f_md5sum),
                 '"{e}"'.format(e=csv_processor),
                 '"{e}"'.format(e=f_today)]
        csv_entries.append(entry)

    return zip_entry, csv_entries

def get_subset_idx(data, first, last):
    """ YEARS ONLY """
    if first > last:
        raise ONEFluxError("First year ({f}) less than last year ({l}) in index search".format(f=first, l=last))
    timestamps = data[data.dtype.names[0]]
    first_str, last_str = str(first), str(last)
    f, l = None, None
    idx = 0
    for x in numpy.nditer(timestamps):
        if f is None and first_str == str(x)[:4]:
            f = idx
        if l is None:
            if last_str == str(x)[:4]:
                l = idx
        else:
            if last_str != str(x)[:4]:
                l = idx - 1
                break
        idx += 1
    if idx == len(timestamps):
        l = idx - 1
    log.debug("Time slice results for {fi}-{li}: a[{f}]={ft}  a[{l}]={lt}".format(fi=first, li=last, f=f, l=l, ft=timestamps[f], lt=timestamps[l]))

    return f, l

def check_lengths(siteid, meteo, energy, nee, unc, resolution, nt_skip=False, dt_skip=False):

    # check for complete-meteo vs flux-years-only meteo
    if meteo[meteo.dtype.names[0]][0] != energy[energy.dtype.names[0]][0] or meteo[meteo.dtype.names[0]][-1] != energy[energy.dtype.names[0]][-1]:
        log.info("METEO number of records differs from ENERGY, assuming complete meteo and removing extra records")
        first, last = int(str(energy[energy.dtype.names[0]][0])[:4]), int(str(energy[energy.dtype.names[0]][-1])[:4])
        first_idx, last_idx = get_subset_idx(data=meteo, first=first, last=last)
        meteo = meteo[first_idx:last_idx + 1]
        if resolution == 'ww':
            meteo['TIMESTAMP_END'][-1] = str(meteo['TIMESTAMP_END'][-1])[:4] + '1231'

    # check record sizes
    if (not nt_skip) or (not dt_skip):
        if meteo.size != energy.size or meteo.size != nee.size or meteo.size != unc.size:
            msg = "Number of records differ: METEO={m}, ENERGY={e}, NEE={n}, UNC/PART={u}".format(m=meteo.size, e=energy.size, n=nee.size, u=unc.size)
            log.critical(msg)
            raise ONEFluxError(msg)
    else:
        if meteo.size != energy.size or meteo.size != nee.size:
            msg = "Number of records differ: METEO={m}, ENERGY={e}, NEE={n}".format(m=meteo.size, e=energy.size, n=nee.size)
            log.critical(msg)
            raise ONEFluxError(msg)

    # check timestamps match # TODO: check if repeated
    if not numpy.all(meteo[meteo.dtype.names[0]] == nee[nee.dtype.names[0]]):
        raise ONEFluxError("Different timestamp ranges METEO and NEE")
    if not numpy.all(meteo[meteo.dtype.names[0]] == energy[energy.dtype.names[0]]):
        raise ONEFluxError("Different timestamp ranges METEO and ENERGY")
    if (not nt_skip) or (not dt_skip):
        if not numpy.all(meteo[meteo.dtype.names[0]] == unc[unc.dtype.names[0]]):
            raise ONEFluxError("Different timestamp ranges METEO and UNC/PARTITIONING")

    return meteo, energy, nee, unc


def get_indices_to_filter(qcdata, qc_threshold=2, window_size=48):
    '''
    Fast creation of mask for QC flags above threshold value
    continually within window size
    '''
    # filter QC array, minimum quality acceptable
    qc_filtered = (qcdata >= qc_threshold).astype(int)

    # prepare window array of 1s for convolution
    conv_window = [1,] * window_size 
    
    # create array counting how many of entries match condition
    # (low quality, i.e., qc values higher than threshold)
    conv = numpy.convolve(qc_filtered, conv_window, mode='valid') 
    
    # create array of start indices where number of entries match window size
    indices_start = numpy.where(conv == window_size)[0]
    
    # create (start, end) pair for windows
    indices = [numpy.arange(index, index + window_size) for index in indices_start]

    # flatten all entries (and remove potential duplicates)
    indices_unique = numpy.unique(indices) 

    # merge all contiguous windows into longer tuples
    # use (i[0]:i[-1] + 1) to access indexes for each window of interest
    indices_tmp = numpy.where(numpy.diff(indices_unique) != 1)[0] + 1
    indices_contiguous = numpy.split(indices_unique, indices_tmp)

    # create mask to be used to set values to NaN in True positions
    mask = numpy.isnan(qcdata)
    mask[:] = False
    for i in indices_contiguous:
        if len(i) > 0:
            mask[i[0]:i[-1] + 1] = True
    return mask


def filter_long_gaps(data, qc_threshold=2, window_size=48):
    '''
    Using dictionary of QC variable to be applied to each data variable,
    assigns -9999 to gapfilled values when QC flags are above threshold
    value continually within window size. Returns list of timestamps to
    be filtered at higher temporal aggregations and complete dataset with
    filtered data variables -- N.B. this function only applies to HH/HR data,
    coarser resolutions are handled from the returned ftimestamp.
    '''
    ftimestamp = {}
    ftimestamp_cut_mask = numpy.zeros(data.size, dtype=bool) # for _CUT_REF filtering, start with all True
    ftimestamp_vut_mask = numpy.zeros(data.size, dtype=bool) # for _VUT_REF filtering, start with all True    
    for qcv, var_list in VARIABLES_DONOT_GAPFILL_LONG.iteritems():
        log.debug('QC variable {q}: start cleaning long gaps'.format(q=qcv))
        if qcv not in data.dtype.names:
            log.warning('QC variable {q} not part of this temporal resolution, skipping'.format(q=qcv))
            continue
        if '_MEAN' in qcv:
            log.warning('QC variable {q} is a _MEAN variable, handled next round'.format(q=qcv))
            continue

        fmask = get_indices_to_filter(qcdata=data[qcv], qc_threshold=qc_threshold, window_size=window_size)
        # HH/HR only, coarser resolutions are handled from the returned ftimestamp
        ftimestamp[qcv] = data['TIMESTAMP_START'][fmask]
        log.debug('QC variable {q} has {n} records to be restored to gaps'.format(q=qcv, n=numpy.sum(fmask)))

        if qcv in VARIABLES_DONOT_GAPFILL_LONG_NEEXXCUT_MEAN_L:
            # for _CUT_MEAN_QC variables, also create combined mask
            ftimestamp_cut_mask = (ftimestamp_cut_mask | fmask)
            log.debug('QC variable {q} has {n} records to be restored to gaps, adding to _MEAN ({m} total)'.format(q=qcv, n=numpy.sum(fmask), m=numpy.sum(ftimestamp_cut_mask)))
        if qcv in VARIABLES_DONOT_GAPFILL_LONG_NEEXXVUT_MEAN_L:
            # for _VUT_MEAN_QC variables, also create combined mask
            ftimestamp_vut_mask = (ftimestamp_vut_mask | fmask)
            log.debug('QC variable {q} has {n} records to be restored to gaps, adding to _MEAN ({m} total)'.format(q=qcv, n=numpy.sum(fmask), m=numpy.sum(ftimestamp_vut_mask)))

        for var in var_list:
            # TODO: handle _REF RECO/GPP (from AUX) and _MEAN (from intersection of _XX percentiles)
            #      NEE_[C|V]UTE_REF already handled for HH/HR, but needs to be handled for coarser resolutions from NEEAUX (same as GPP/RECO for all resolutions)
            #      _MEAN currently using _MEAN_QC which is an average of QC values, so no -9999 and _MEAN survives and needs to be handled separately
            log.debug('QC variable {q}, data variable {v}: assigning -9999'.format(q=qcv, v=var))
            data[var][fmask] = -9999.9
    
    # apply combined masks for MEAN _CUT_REF and _VUT_REF variables
    if 'NEE_CUT_MEAN' in data.dtype.names:
        ftimestamp['NEE_CUT_MEAN_QC'] = data['TIMESTAMP_START'][ftimestamp_cut_mask]
        log.debug('QC variable NEE_CUT_MEAN_QC has {n} records to be restored to gaps'.format(q=qcv, n=numpy.sum(ftimestamp_cut_mask)))
        for qcv in VARIABLES_DONOT_GAPFILL_LONG['NEE_CUT_MEAN_QC']:
            log.debug('QC variable NEE_CUT_MEAN_QC, data variable {v}: assigning -9999'.format(v=qcv))
            data[qcv][ftimestamp_cut_mask] = -9999.9

    if 'NEE_VUT_MEAN' in data.dtype.names:
        ftimestamp['NEE_VUT_MEAN_QC'] = data['TIMESTAMP_START'][ftimestamp_vut_mask]
        log.debug('QC variable NEE_VUT_MEAN_QC has {n} records to be restored to gaps'.format(q=qcv, n=numpy.sum(ftimestamp_vut_mask)))
        for qcv in VARIABLES_DONOT_GAPFILL_LONG['NEE_VUT_MEAN_QC']:
            log.debug('QC variable NEE_VUT_MEAN_QC, data variable {v}: assigning -9999'.format(v=qcv))
            data[qcv][ftimestamp_vut_mask] = -9999.9

    return ftimestamp, data


def slice_string_array(sarray, start, end):
    '''
    Slices strings at each position of array,
    keeps only values of string within [start, end)
    '''
    sb = sarray.view((str, 1)).reshape(len(sarray), -1)[:, start:end]
    return numpy.fromstring(sb.tostring(), dtype=(str, end - start))


def generate_agg_timestamp_mask(ftimestamp, data, resolution='dd'):
    '''
    For earch QC variable in ftimestamp dict,
    process list of timestamps excluded from HH/HR array,
    propagating to other temporal aggregations (DD, WW, MM, YY).
    '''
    timelabels = [i[0] for i in TIMESTAMP_DTYPE_BY_RESOLUTION[resolution]]
    fmasked = {}
    for qcv, t in ftimestamp.iteritems():
        log.debug('QC variable {q}, processing aggregation {v}, filtering {n} records from HH/HR resolution'.format(q=qcv, v=resolution, n=len(t)))
        if len(t) > 0:
            if (resolution == 'dd') or (resolution == 'ww'):
                sliced = numpy.unique(slice_string_array(t, start=0, end=8))
                if (resolution == 'dd'):
                    timestamps = data[timelabels[0]]
                    tmask = numpy.in1d(timestamps, sliced)
                elif (resolution == 'ww'):
                    timestamps_start = data[timelabels[0]]
                    timestamps_end = data[timelabels[1]]
                    tmask = (timestamps_start != timestamps_start)
                    
                    # not ideal performance-wise, but <1,000 entries max so should be fine
                    for ts in sliced:                        
                        nmask = (ts >= timestamps_start) & (ts <= timestamps_end)
                        tmask = (tmask | nmask)
                fmasked[qcv] = tmask

            elif resolution == 'mm':
                sliced = numpy.unique(slice_string_array(t, start=0, end=6))
                timestamps = data[timelabels[0]]
                tmask = numpy.in1d(timestamps, sliced)
                fmasked[qcv] = tmask
            
            elif resolution == 'yy':
                sliced = numpy.unique(slice_string_array(t, start=0, end=4))
                timestamps = data[timelabels[0]]
                tmask = numpy.in1d(timestamps, sliced)
                fmasked[qcv] = tmask

            log.debug('QC variable {v}, aggregation {a} will filter {n} entries'.format(v=qcv, a=resolution, n=tmask.sum()))
    return fmasked


def run_site(siteid,
             sitedir,
             first_t1,
             last_t1,
             version_processing=1,
             version_data=1,
             pipeline=None,
             era_first_timestamp_start=ERA_FIRST_TIMESTAMP_START,
             era_last_timestamp_start=ERA_LAST_TIMESTAMP_START):
    if pipeline is None: # TODO: remove this condition and add error handling, pipeline shoud not be None anymore
        datadir = WORKING_DIRECTORY
        meteo = METEODIR.format(sd=sitedir)
        nee = NEEDIR.format(sd=sitedir)
        energy = ENERGYDIR.format(sd=sitedir)
        unc = UNCDIR.format(sd=sitedir)
        prod = PRODDIR.format(sd=sitedir)
        prodfile_template = PRODFILE_TEMPLATE
        zipfile_template = ZIPFILE_TEMPLATE
        prodfile_years_template = PRODFILE_YEARS_TEMPLATE
        era_first_year = int(ERA_FIRST_TIMESTAMP_START[:4])
        era_last_year = int(ERA_FIRST_TIMESTAMP_START[:4])
    else:
        datadir = pipeline.data_dir_main
        meteo = pipeline.meteo_proc.meteo_proc_dir
        nee = pipeline.nee_proc.nee_proc_dir
        energy = pipeline.energy_proc.energy_proc_dir
        unc = pipeline.ure.ure_dir
        prod = pipeline.fluxnet2015.fluxnet2015_dir
        prodfile_template = pipeline.prodfile_template
        zipfile_template = pipeline.zipfile_template
        prodfile_years_template = pipeline.prodfile_years_template
        era_first_year = pipeline.era_first_year
        era_last_year = pipeline.era_last_year

    check_create_directory(prod)

    first_year, last_year = None, None
    full_filelist_t1 = []
    full_filelist_t2 = []
    sub_filelist_t1 = []
    sub_filelist_t2 = []
    erai_filelist = []
    qcdata_dd = None # NEW FOR APRIL2016
    qcdata_ww = None # NEW FOR APRIL2016
    qcdata_mm = None # NEW FOR APRIL2016
    qcdata_yy = None # NEW FOR APRIL2016
    for resolution in RESOLUTION_LIST:
        log.debug("Processing '{r}' resolution".format(r=resolution))
        meteo_data = load_meteo(siteid=siteid, ddir=meteo, resolution=resolution)
        nee_data = load_nee(siteid=siteid, ddir=nee, resolution=resolution)
        energy_data = load_energy(siteid=siteid, ddir=energy, resolution=resolution)
        unc_data = load_unc(siteid=siteid, ddir=unc, resolution=resolution, nt_skip=pipeline.nt_skip, dt_skip=pipeline.dt_skip)

        # make duplicate of full meteo data
        dt = copy.deepcopy(meteo_data.dtype)
        full_meteo_data = numpy.copy(meteo_data)
        full_meteo_data.dtype = dt

        # check lengths and update arrays if needed
        meteo_data, energy_data, nee_data, unc_data = check_lengths(siteid=siteid, meteo=meteo_data, energy=energy_data, nee=nee_data, unc=unc_data, resolution=resolution, nt_skip=pipeline.nt_skip, dt_skip=pipeline.dt_skip)

        # update column names to new standard
        log.debug("{s}: updating names for meteo data".format(s=siteid))
        meteo_data = update_names(data=meteo_data)
        log.debug("{s}: updating names for full meteo data".format(s=siteid))
        full_meteo_data = update_names(data=full_meteo_data)
        log.debug("{s}: updating names for energy data".format(s=siteid))
        energy_data = update_names(data=energy_data)
        log.debug("{s}: updating names for nee data".format(s=siteid))
        nee_data = update_names(data=nee_data)
        if (not pipeline.nt_skip) or (not pipeline.dt_skip):
            log.debug("{s}: updating names for unc data".format(s=siteid))
            unc_data = update_names(data=unc_data)

        # merge arrays
        output_data = merge_arrays(meteo=meteo_data, energy=energy_data, nee=nee_data, unc=unc_data, resolution=resolution, nt_skip=pipeline.nt_skip, dt_skip=pipeline.dt_skip)

        # find temporal resolution
        if resolution == 'hh':
            output_resolution = get_resolution(timestamps=output_data[output_data.dtype.names[0]], error_str="{s}_{r}".format(s=siteid, r=resolution))
        else:
            output_resolution = resolution.upper()

        # find first and last years
        first_year, last_year = get_first_last_years(timestamps=output_data[output_data.dtype.names[0]], first=first_year, last=last_year, error_str="{s}_{r}".format(s=siteid, r=resolution))

        # check T1
        if (first_t1 == 'none'):
            pass
        elif (first_t1 == 'all'):
            first_t1, last_t1 = first_year, last_year
        else:
            ft1, lt1 = int(first_t1), int(last_t1)
            if (ft1 < first_year):
                log.error("{s}: first Tier 1 site-year ({t}) is less than first site-year available ({a}), using latter".format(s=siteid, t=ft1, a=first_year))
                first_t1 = first_year
            if (lt1 > last_year):
                log.error("{s}: last Tier 1 site-year ({t}) is more than last site-year available ({a}), using latter".format(s=siteid, t=lt1, a=last_year))
                last_t1 = last_year

        # NEW FOR APRIL2016: process additional met variables
        if resolution == 'hh':
            qcdir_prep = (QCDIR.format(sd=sitedir) if pipeline is None else pipeline.qc_visual.qc_visual_dir_inner)
            qcdata = load_qcdata(siteid=siteid, ddir=qcdir_prep, firsty=first_year, lasty=last_year, output_resolution=output_resolution)
            log.debug("{s}: updating names for qc data".format(s=siteid))
            qcdata = update_names_qc(data=qcdata)
            output_data = merge_qcdata(qcdata=qcdata, output=output_data)
            qcdata_dd, qcdata_ww, qcdata_mm, qcdata_yy = aggregate_qcdata(qcdata=qcdata)
        elif resolution == 'dd':
            if qcdata_dd is None:
                raise ONEFluxError("Output QC Data DD resolution not computed")
            output_data = merge_qcdata_res(qcdata=qcdata_dd, output=output_data, res=resolution)
        elif resolution == 'ww':
            if qcdata_ww is None:
                raise ONEFluxError("Output QC Data WW resolution not computed")
            output_data = merge_qcdata_res(qcdata=qcdata_ww, output=output_data, res=resolution)
        elif resolution == 'mm':
            if qcdata_mm is None:
                raise ONEFluxError("Output QC Data MM resolution not computed")
            output_data = merge_qcdata_res(qcdata=qcdata_mm, output=output_data, res=resolution)
        elif resolution == 'yy':
            if qcdata_yy is None:
                raise ONEFluxError("Output QC Data YY resolution not computed")
            output_data = merge_qcdata_res(qcdata=qcdata_yy, output=output_data, res=resolution)

        # NEW FOR 2025: Cleanup of long gapfilled results,
        # remove gapfilled data for gaps longer than 21 days.
        # N.B.: this changes default ONEFlux behavior
        if output_resolution == 'HH':
            # compute windows and set gaps for window_size=48*21
            ftimestamp, output_data = filter_long_gaps(data=output_data, qc_threshold=2, window_size=48*21)
        elif output_resolution == 'HR':
            # compute windows and set gaps for window_size=24*21
            ftimestamp, output_data = filter_long_gaps(data=output_data, qc_threshold=2, window_size=24*21)
        # use list of YYYYMMDDHHMM timestamps to be filtered from HH/HR resolution to filter aggregated resolutions
        elif (output_resolution == 'DD') or (output_resolution == 'WW') or (output_resolution == 'MM') or (output_resolution == 'YY'):
            res_masks = generate_agg_timestamp_mask(ftimestamp=ftimestamp, data=output_data, resolution=resolution)
            print(res_masks)
            for qcv, fmask in res_masks.iteritems():
                for var in VARIABLES_DONOT_GAPFILL_LONG[qcv]:
                    # TODO: handle _REF RECO/GPP (from AUX) and _MEAN (from intersection of _XX percentiles)
                    if var not in output_data.dtype.names:
                        log.warning('Data variable {q} not part of temporal  resolution {r}, skipping'.format(q=var, r=resolution))
                        continue
                    log.debug('QC variable {q}, data variable {v}, resolution {r}: assigning -9999'.format(q=qcv, v=var, r=resolution))
                    output_data[var][fmask] = -9999.9
                    # TODO: consider change corresponding _QC variables to -9999 when the main variable is -9999
                    #       (e.g., if NEE_VUT_REF is -9999, then NEE_VUT_REF_QC should also be -9999).
                    #       For now, only the main variable is set to -9999, QC variable is left unchanged
           

        ### FULLSET files
        # save Tier 2 FULLSET CSV file
        filename = prodfile_template.format(sd=sitedir, s=siteid, g=FULLSET_STR, r=output_resolution, fy=first_year, ly=last_year, vd=version_data, vp=version_processing)
        log.info("Saving Tier 2 FULLSET CSV file: {f}".format(f=filename))
        subset_headers_full = [i for i in VARIABLE_LIST_FULL if i in output_data.dtype.names]
        save_csv_txt(filename=filename, data=output_data[subset_headers_full])
        full_filelist_t2.append(filename)

        # save Tier 1 FULLSET CSV file
        # no T1
        if (first_t1 == 'none'):
            log.info("No Tier 1 FULLSET (none), equivalent Tier 2 file: {f}".format(f=filename))
        # T1 is the same (all)
        elif (int(first_t1) == first_year and int(last_t1) == last_year):
            log.info("Tier 1 FULLSET CSV same as Tier 2 (all), reusing file: {f}".format(f=filename))
            full_filelist_t1.append(filename)
        # T1 differs, save new file
        elif (int(first_t1) > first_year or int(last_t1) < last_year):
            filename = prodfile_template.format(sd=sitedir, s=siteid, g=FULLSET_STR, r=output_resolution, fy=first_t1, ly=last_t1, vd=version_data, vp=version_processing)
            first_idx, last_idx = get_subset_idx(data=output_data, first=first_t1, last=last_t1)
            log.info("Saving Tier 1 FULLSET CSV file: {f}".format(f=filename))
            save_csv_txt(filename=filename, data=output_data[subset_headers_full][first_idx:last_idx])
            full_filelist_t1.append(filename)
        # UNK
        else:
            raise ONEFluxError("Unknown Tier 1 state: first_t1={f}, last_t1={l}".format(f=first_t1, l=last_t1))


        # NEW FOR JULY2016: save full ERA output
        ts_precision = TIMESTAMP_PRECISION_BY_RESOLUTION[resolution]
        ts_by_res = TIMESTAMP_DTYPE_BY_RESOLUTION[resolution][0][0]
        first_era_ts, last_era_ts = era_first_timestamp_start[:ts_precision], era_last_timestamp_start[:ts_precision]
        if (full_meteo_data[ts_by_res][0] != first_era_ts):
            msg = "{s}: mismatched first ERA timestamp expected ({e}) and found ({f})".format(s=siteid, e=first_era_ts, f=full_meteo_data[ts_by_res][0])
            log.critical(msg)
            raise ONEFluxError(msg)
        if (full_meteo_data[ts_by_res][-1] != last_era_ts):
            ww_last_era_ts_leap = last_era_ts[:6] + '24' # last weekly timestamp can be on the 24th not 31st of December
            ww_last_era_ts = last_era_ts[:6] + '23' #  23rd if not leap year
            hr_last_era_ts = last_era_ts[:-2] + '00' # last hourly timestamp is 2300 not 2330
            if (resolution == 'ww') and ((full_meteo_data[ts_by_res][-1] == ww_last_era_ts) or (full_meteo_data[ts_by_res][-1] == ww_last_era_ts_leap)):
                pass
            elif (resolution == 'hh') and (full_meteo_data[ts_by_res][-1] == hr_last_era_ts):
                pass
            else:
                msg = "{s} mismatched last ERA timestamp expected ({e}) and found ({f})".format(s=siteid, e=last_era_ts, f=full_meteo_data[ts_by_res][-1])
                log.critical(msg)
                raise ONEFluxError(msg)
        filename = prodfile_template.format(sd=sitedir, s=siteid, g=ERA_STR, r=output_resolution, fy=era_first_year, ly=era_last_year, vd=version_data, vp=version_processing)
        log.info("Saving ERA-Interim CSV file: {f}".format(f=filename))
        full_meteo_header_labels = TIMESTAMP_VARIABLE_LIST + NEW_ERA_VARS
        full_meteo_headers = [i for i in full_meteo_header_labels if i in full_meteo_data.dtype.names]
        erai_filelist.append(filename)
        save_csv_txt(filename=filename, data=full_meteo_data[full_meteo_headers])
        # TODO: add era files to zips/filelists


        ### SUBSET files
        # save Tier 2 SUBSET CSV file
        filename = prodfile_template.format(sd=sitedir, s=siteid, g=SUBSET_STR, r=output_resolution, fy=first_year, ly=last_year, vd=version_data, vp=version_processing)
        log.info("Saving Tier 2 SUBSET CSV file: {f}".format(f=filename))
        subset_headers = [i for i in VARIABLE_LIST_SUB if i in output_data.dtype.names]
        save_csv_txt(filename=filename, data=output_data[subset_headers])
        sub_filelist_t2.append(filename)

        # save Tier 1 SUBSET CSV file
        # no T1
        if (first_t1 == 'none'):
            log.info("No Tier 1 SUBSET (none), equivalent Tier 2 file: {f}".format(f=filename))
        # T1 is the same (all)
        elif (int(first_t1) == first_year and int(last_t1) == last_year):
            log.info("Tier 1 SUBSET CSV same as Tier 2 (all), reusing file: {f}".format(f=filename))
            sub_filelist_t1.append(filename)
        # T1 differs, save new file
        elif (int(first_t1) > first_year or int(last_t1) < last_year):
            filename = prodfile_template.format(sd=sitedir, s=siteid, g=SUBSET_STR, r=output_resolution, fy=first_t1, ly=last_t1, vd=version_data, vp=version_processing)
            first_idx, last_idx = get_subset_idx(data=output_data, first=first_t1, last=last_t1)
            log.info("Saving Tier 1 SUBSET CSV file: {f}".format(f=filename))
            save_csv_txt(filename=filename, data=output_data[subset_headers][first_idx:last_idx])
            sub_filelist_t1.append(filename)
        # UNK
        else:
            raise ONEFluxError("Unknown Tier 1 state: first_t1={f}, last_t1={l}".format(f=first_t1, l=last_t1))

    # save first/last year info
    prodfile_years = prodfile_years_template.format(s=siteid, sd=sitedir, vd=version_data, vp=version_processing)
    with open(prodfile_years, 'w') as f:
        f.write("first_year_t2,last_year_t2,first_year_t1,last_year_t1\n")
        f.write("{f},{l},{f1},{l1}\n".format(f=first_year, l=last_year, f1=first_t1, l1=last_t1))
    log.debug("{s}: wrote years metadata file: {f}".format(s=siteid, f=prodfile_years))

    # generate aux and info files
    aux_file_list = run_site_aux(datadir=datadir, siteid=siteid, sitedir=sitedir, first_year=first_year, last_year=last_year, version_data=version_data, version_processing=version_processing, pipeline=pipeline, nt_skip=pipeline.nt_skip, dt_skip=pipeline.dt_skip)
    if full_filelist_t1:
        full_filelist_t1.extend(aux_file_list)
        full_filelist_t1.extend(erai_filelist)
    if full_filelist_t2:
        full_filelist_t2.extend(aux_file_list)
        full_filelist_t2.extend(erai_filelist)
    if sub_filelist_t1: sub_filelist_t1.extend(aux_file_list)
    if sub_filelist_t2: sub_filelist_t2.extend(aux_file_list)

    # generate zip and csv outputs for manifests
    zip_manifest_entries = []
    csv_manifest_entries = []

    # fullset T2
    zip_entries, csv_entries = gen_stats_zip(filename_list=full_filelist_t2,
                                             tier='tier2',
                                             zipfilename=zipfile_template.format(sd=sitedir, s=siteid, g=FULLSET_STR, fy=first_year, ly=last_year, vd=version_data, vp=version_processing))
    zip_manifest_entries.extend(zip_entries)
    csv_manifest_entries.extend(csv_entries)

    # fullset T1
    if (first_t1 != 'none'):
        if (first_t1 == 'all') or (int(first_t1) == first_year and int(last_t1) == last_year):
            # ZIP:  filename, fileSize, fileChecksum, fileCount, tier, processor, createDate
            zip_entry = list(zip_entries[0])
            zip_entry[4] = '"tier1"'
            zip_entries = [zip_entry]
            zip_manifest_entries.extend(zip_entries)
        else:
            zip_entries, csv_entries = gen_stats_zip(filename_list=full_filelist_t1,
                                                     tier='tier1',
                                                     zipfilename=zipfile_template.format(sd=sitedir, s=siteid, g=FULLSET_STR, fy=first_t1, ly=last_t1, vd=version_data, vp=version_processing))
            zip_manifest_entries.extend(zip_entries)
            csv_manifest_entries.extend(csv_entries)

    # subset T2
    zip_entries, csv_entries = gen_stats_zip(filename_list=sub_filelist_t2,
                                             tier='tier2',
                                             zipfilename=zipfile_template.format(sd=sitedir, s=siteid, g=SUBSET_STR, fy=first_year, ly=last_year, vd=version_data, vp=version_processing))
    zip_manifest_entries.extend(zip_entries)
    csv_manifest_entries.extend(csv_entries)

    # subset T1
    if (first_t1 != 'none'):
        if (first_t1 == 'all') or (int(first_t1) == first_year and int(last_t1) == last_year):
            # ZIP:  filename, fileSize, fileChecksum, fileCount, tier, processor, createDate
            zip_entry = list(zip_entries[0])
            zip_entry[4] = '"tier1"'
            zip_entries = [zip_entry]
            zip_manifest_entries.extend(zip_entries)
        else:
            zip_entries, csv_entries = gen_stats_zip(filename_list=sub_filelist_t1,
                                                     tier='tier1',
                                                     zipfilename=zipfile_template.format(sd=sitedir, s=siteid, g=SUBSET_STR, fy=first_t1, ly=last_t1, vd=version_data, vp=version_processing))
            zip_manifest_entries.extend(zip_entries)
            csv_manifest_entries.extend(csv_entries)

    return csv_manifest_entries, zip_manifest_entries


if __name__ == '__main__':
    sys.exit("ERROR: cannot run independently")
