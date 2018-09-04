'''
Data check plots

For license information:
see LICENSE file or headers in oneflux.__init__.py

NOTES
  - NEE/GPP/RECO one per res (HH, DD, ..), REF, MEAN, all percentile + QC (availability)
  - LE/H original, corr (25+75) (HH)
  - (good to have) NEE with NIGHT/DAY flags (HH and/or DD)
  - (good to have) u* threshold distribution, VUT and CUT
  - (good to have) meteo


@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: Dec 10, 2015
'''

import sys
import os
import logging
import numpy

import matplotlib
matplotlib.rcParams['path.simplify'] = False  # removes smoothing, force plotting all points
#matplotlib.use('macosx')

from datetime import datetime
from scipy import integrate, interpolate, stats, polyfit, polyval
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot, gridspec, dates, ticker

from oneflux import ONEFluxError
from oneflux.pipeline.variables_codes import FULL_D
from oneflux.pipeline.common import RESOLUTION_LIST, PRODFILE_TEMPLATE, PRODFILE_AUX_TEMPLATE, PRODFILE_YEARS_TEMPLATE, PRODFILE_FIGURE_TEMPLATE, INTTEST
from oneflux.pipeline.aux_info_files import load_ustar_cut, load_ustar_vut
from oneflux.pipeline.site_data_product import get_headers

log = logging.getLogger(__name__)

STRTEST_STANDARD = ['TIMESTAMP', 'TIMESTAMP_START', 'TIMESTAMP_END']
INTTEST_STANDARD = {}
NFULL_D = {k.lower():v for k, v in FULL_D.iteritems()}

for res, l in INTTEST.iteritems():
    nl = []
    for item in l:
        nitem = NFULL_D.get(item, None)
        if nitem is not None:
            nl.append(nitem)
    INTTEST_STANDARD[res] = nl

DPI = 100
COLOR_QC = 'lightskyblue'
COLOR_MEAN = 'darkorange'
COLOR_U50 = 'indigo'
COLOR_REF = 'black'
COLOR_RNG = 'grey'
COLOR_NT_U50 = 'yellow'
COLOR_NT_REF = 'maroon'
COLOR_NT_RNG = 'coral'
COLOR_DT_U50 = 'purple'
COLOR_DT_REF = 'navy'
COLOR_DT_RNG = 'steelblue'

def load_years(siteid, sitedir, version_data, version_processing, prodfile_years_template=PRODFILE_YEARS_TEMPLATE):
    prodfile_years = prodfile_years_template.format(s=siteid, sd=sitedir, vd=version_data, vp=version_processing)
    if not os.path.isfile(prodfile_years):
        raise ONEFluxError("{s}: product site years file not found: {f}".format(s=siteid, f=prodfile_years))
    with open(prodfile_years, 'r') as f:
        lines = f.readlines()
    #header = lines[0].strip.split(',')
    first_year, last_year, _, _ = lines[1].strip().split(',')
    first_year, last_year = int(first_year.strip()), int(last_year.strip())

    return first_year, last_year

def get_dtype(variable, resolution):
    for s in STRTEST_STANDARD:
        if s.lower() in variable.lower():
            return 'a25'
    for s in INTTEST_STANDARD[resolution]:
        if s.lower() == variable.lower():
            return 'i8'
    return 'f8'

def get_fill_value(dtype):
    if dtype == 'a25':
        return ''
    elif dtype == 'i8':
        return -9999
    else:
        return numpy.NaN

def load_data_file(filename, resolution):
    log.debug("Loading: {f}".format(f=filename))
    headers = get_headers(filename=filename)
    dtype = [(h, get_dtype(h, resolution)) for h in headers]
    fill_values = [get_fill_value(dtype=d[1]) for d in dtype]
    data = numpy.genfromtxt(fname=filename, dtype=dtype, names=True, delimiter=",", skip_header=0, missing_values='-9999,-9999.0,-6999,-6999.0, ', usemask=True)
    data = numpy.atleast_1d(data)
    return numpy.ma.filled(data, fill_values)

def plot_ustar():
    pass

def plot_nee_unc(hh, dd, ww, mm, yy, title='', width=10, height=25, filename='nee.png', show=False, y_label=''):
    figure = pyplot.figure()
    figure.text(.5, .97, title, horizontalalignment='center', fontsize='x-large')
    figure.set_figwidth(width)
    figure.set_figheight(height)
#         figure.subplots_adjust(left=0.02, right=0.98, bottom=0.04, top=0.98, wspace=None, hspace=None)
    canvas = FigureCanvas(figure)

    gs = gridspec.GridSpec(50, 1)
    gs.update(left=0.10, right=0.96, hspace=0.08, top=0.94, bottom=0.00)

    # HH
    log.debug("Plotting HH for '{f}'".format(f=filename))
    if hh: xmin, xmax = hh['ts'][0], hh['ts'][-1]
    else: xmin, xmax = None, None
    hh_axis = pyplot.subplot(gs[0:8, 0])
    hh_axis.set_ylabel('{l} (HH)'.format(l=y_label))
#    hh_axis.get_xaxis().set_ticks([])
    hh_axis.get_xaxis().tick_top()
    hh_axis.set_xlim([xmin, xmax])
    hh_axis_qc = pyplot.subplot(gs[8, 0])
    hh_axis_qc.set_ylabel('QC')
#    hh_axis_qc.get_xaxis().set_ticks([])
    hh_axis_qc.get_yaxis().set_ticks([])
    hh_axis_qc.set_xlim([xmin, xmax])
    hh_axis_empty = pyplot.subplot(gs[9, 0])
    hh_axis_empty.set_axis_off()
    if hh:
        ts = hh['ts']
        lines = hh['lines']
        ranges = hh['ranges']
        qc = hh['qc']
        for r in ranges:
            hh_axis.fill_between(ts, r['data1'], r['data2'], color=r['color'], facecolor=r['color'], edgecolor=r['color'], alpha=r['alpha'], label=r['label'])
        for l in lines:
            hh_axis.plot_date(ts, l['data'], linestyle='', linewidth=1.5, marker='.', markersize=1, color=l['color'], alpha=r['alpha'], label=l['label'])
        if hh.has_key('ranges2'):
            ranges = hh['ranges2']
            for r in ranges:
                hh_axis.fill_between(ts, r['data1'], r['data2'], color=r['color'], facecolor=r['color'], edgecolor=r['color'], alpha=r['alpha'], label=r['label'])
        if hh.has_key('lines2'):
            lines = hh['lines2']
            for l in lines:
                hh_axis.plot_date(ts, l['data'], linestyle='', linewidth=1.5, marker='.', markersize=1, color=l['color'], alpha=r['alpha'], label=l['label'])
        hh_axis.legend(loc='best', prop={'size':8})
        if qc:
            zeros = numpy.zeros(len(ts), dtype='f8')
            hh_axis_qc.fill_between(ts, zeros, qc['data'], color=qc['color'], facecolor=qc['color'], edgecolor=qc['color'], alpha=qc['alpha'], label=qc['label'])
#            hh_axis_qc.bar(left=ts, height=qc['data'], width=4000.0 / len(qc['data']), align='center', color=qc['color'], edgecolor=qc['color'], alpha=qc['alpha'])
        hh_axis_qc.set_ylim([0.0, 1.0])

    # DD
    log.debug("Plotting DD for '{f}'".format(f=filename))
    if dd: xmin, xmax = dd['ts'][0], dd['ts'][-1]
    else: xmin, xmax = None, None
    dd_axis = pyplot.subplot(gs[10:18, 0])
    dd_axis.set_ylabel('{l} (DD)'.format(l=y_label))
    dd_axis.get_xaxis().set_ticks([])
    dd_axis.set_xlim([xmin, xmax])
    dd_axis_qc = pyplot.subplot(gs[18, 0])
    dd_axis_qc.set_ylabel('QC')
#    dd_axis_qc.get_xaxis().set_ticks([])
    dd_axis_qc.get_yaxis().set_ticks([])
    dd_axis_qc.set_xlim([xmin, xmax])
    dd_axis_empty = pyplot.subplot(gs[19, 0])
    dd_axis_empty.set_axis_off()
    if dd:
        ts = dd['ts']
        lines = dd['lines']
        ranges = dd['ranges']
        qc = dd['qc']
        for r in ranges:
            dd_axis.fill_between(ts, r['data1'], r['data2'], color=r['color'], facecolor=r['color'], edgecolor=r['color'], alpha=r['alpha'], label=r['label'])
        for l in lines:
            dd_axis.plot_date(ts, l['data'], linestyle='', linewidth=1.5, marker='.', markersize=2, color=l['color'], alpha=r['alpha'], label=l['label'])
        if dd.has_key('ranges2'):
            ranges = dd['ranges2']
            for r in ranges:
                dd_axis.fill_between(ts, r['data1'], r['data2'], color=r['color'], facecolor=r['color'], edgecolor=r['color'], alpha=r['alpha'], label=r['label'])
        if dd.has_key('lines2'):
            lines = dd['lines2']
            for l in lines:
                dd_axis.plot_date(ts, l['data'], linestyle='', linewidth=1.5, marker='.', markersize=2, color=l['color'], alpha=r['alpha'], label=l['label'])
        dd_axis.legend(loc='best', prop={'size':8})
        if qc:
            zeros = numpy.zeros(len(ts), dtype='f8')
            dd_axis_qc.fill_between(ts, zeros, qc['data'], color=qc['color'], facecolor=qc['color'], edgecolor=qc['color'], alpha=qc['alpha'], label=qc['label'])
#            dd_axis_qc.bar(left=ts, height=qc['data'], width=4000.0 / len(qc['data']), align='center', color=qc['color'], edgecolor=qc['color'], alpha=qc['alpha'])
        dd_axis_qc.set_ylim([0.0, 1.0])

    # WW
    log.debug("Plotting WW for '{f}'".format(f=filename))
    if ww: xmin, xmax = ww['ts'][0], ww['ts'][-1]
    else: xmin, xmax = None, None
    ww_axis = pyplot.subplot(gs[20:28, 0])
    ww_axis.set_ylabel('{l} (WW)'.format(l=y_label))
    ww_axis.get_xaxis().set_ticks([])
    ww_axis.set_xlim([xmin, xmax])
    ww_axis_qc = pyplot.subplot(gs[28, 0])
    ww_axis_qc.set_ylabel('QC')
#    ww_axis_qc.get_xaxis().set_ticks([])
    ww_axis_qc.get_yaxis().set_ticks([])
    ww_axis_qc.set_xlim([xmin, xmax])
    ww_axis_empty = pyplot.subplot(gs[29, 0])
    ww_axis_empty.set_axis_off()
    if ww:
        ts = ww['ts']
        lines = ww['lines']
        ranges = ww['ranges']
        qc = ww['qc']
        for r in ranges:
            ww_axis.fill_between(ts, r['data1'], r['data2'], color=r['color'], facecolor=r['color'], edgecolor=r['color'], alpha=r['alpha'], label=r['label'])
        for l in lines:
            ww_axis.plot_date(ts, l['data'], linestyle='-', linewidth=1.5, marker='', markersize=2, color=l['color'], alpha=r['alpha'], label=l['label'])
        if ww.has_key('ranges2'):
            ranges = ww['ranges2']
            for r in ranges:
                ww_axis.fill_between(ts, r['data1'], r['data2'], color=r['color'], facecolor=r['color'], edgecolor=r['color'], alpha=r['alpha'], label=r['label'])
        if ww.has_key('lines2'):
            lines = ww['lines2']
            for l in lines:
                ww_axis.plot_date(ts, l['data'], linestyle='-', linewidth=1.5, marker='', markersize=2, color=l['color'], alpha=r['alpha'], label=l['label'])
        ww_axis.legend(loc='best', prop={'size':8})
        if qc:
            zeros = numpy.zeros(len(ts), dtype='f8')
            ww_axis_qc.fill_between(ts, zeros, qc['data'], color=qc['color'], facecolor=qc['color'], edgecolor=qc['color'], alpha=qc['alpha'], label=qc['label'])
#            ww_axis_qc.bar(left=ts, height=qc['data'], width=4000.0 / len(qc['data']), align='center', color=qc['color'], edgecolor=qc['color'], alpha=qc['alpha'])
        ww_axis_qc.set_ylim([0.0, 1.0])

    # MM
    log.debug("Plotting MM for '{f}'".format(f=filename))
    if mm: xmin, xmax = mm['ts'][0], mm['ts'][-1]
    else: xmin, xmax = None, None
    mm_axis = pyplot.subplot(gs[30:38, 0])
    mm_axis.set_ylabel('{l} (MM)'.format(l=y_label))
    mm_axis.get_xaxis().set_ticks([])
    mm_axis.set_xlim([xmin, xmax])
    mm_axis_qc = pyplot.subplot(gs[38, 0])
    mm_axis_qc.set_ylabel('QC')
#    mm_axis_qc.get_xaxis().set_ticks([])
    mm_axis_qc.get_yaxis().set_ticks([])
    mm_axis_qc.set_xlim([xmin, xmax])
    mm_axis_empty = pyplot.subplot(gs[39, 0])
    mm_axis_empty.set_axis_off()
    if mm:
        ts = mm['ts']
        lines = mm['lines']
        ranges = mm['ranges']
        qc = mm['qc']
        for r in ranges:
            mm_axis.fill_between(ts, r['data1'], r['data2'], color=r['color'], facecolor=r['color'], edgecolor=r['color'], alpha=r['alpha'], label=r['label'])
        for l in lines:
            mm_axis.plot_date(ts, l['data'], linestyle='-', linewidth=1.5, marker='', markersize=4, color=l['color'], alpha=r['alpha'], label=l['label'])
        if mm.has_key('ranges2'):
            ranges = mm['ranges2']
            for r in ranges:
                mm_axis.fill_between(ts, r['data1'], r['data2'], color=r['color'], facecolor=r['color'], edgecolor=r['color'], alpha=r['alpha'], label=r['label'])
        if mm.has_key('lines2'):
            lines = mm['lines2']
            for l in lines:
                mm_axis.plot_date(ts, l['data'], linestyle='-', linewidth=1.5, marker='', markersize=4, color=l['color'], alpha=r['alpha'], label=l['label'])
        mm_axis.legend(loc='best', prop={'size':8})
        if qc:
            zeros = numpy.zeros(len(ts), dtype='f8')
            mm_axis_qc.fill_between(ts, zeros, qc['data'], color=qc['color'], facecolor=qc['color'], edgecolor=qc['color'], alpha=qc['alpha'], label=qc['label'])
#            mm_axis_qc.bar(left=ts, height=qc['data'], width=3000.0 / len(qc['data']), align='center', color=qc['color'], edgecolor=qc['color'], alpha=qc['alpha'])
        mm_axis_qc.set_ylim([0.0, 1.0])

    # YY
    log.debug("Plotting YY for '{f}'".format(f=filename))
    if yy: xmin, xmax = yy['ts'][0], yy['ts'][-1]
    else: xmin, xmax = None, None
    yy_axis = pyplot.subplot(gs[40:48, 0])
    yy_axis.set_ylabel('{l} (YY)'.format(l=y_label))
    yy_axis.get_xaxis().set_ticks([])
    yy_axis.set_xlim([xmin, xmax])
    yy_axis_qc = pyplot.subplot(gs[48, 0])
    yy_axis_qc.set_ylabel('QC')
    yy_axis_qc.set_xlim([xmin, xmax])
#    yy_axis_qc.get_xaxis().set_ticks([])
    yy_axis_qc.get_xaxis().set_major_locator(matplotlib.dates.YearLocator())
    yy_axis_qc.get_xaxis().set_major_formatter(matplotlib.dates.DateFormatter('%Y'))
    yy_axis_qc.get_yaxis().set_ticks([])
    yy_axis_empty = pyplot.subplot(gs[49, 0])
    yy_axis_empty.set_axis_off()
    if yy:
        ts = yy['ts']
        lines = yy['lines']
        ranges = yy['ranges']
        qc = yy['qc']
        for r in ranges:
            yy_axis.fill_between(ts, r['data1'], r['data2'], color=r['color'], facecolor=r['color'], edgecolor=r['color'], alpha=r['alpha'], label=r['label'])
        for l in lines:
            yy_axis.plot_date(ts, l['data'], linestyle='-', linewidth=1.5, marker='', markersize=4, color=l['color'], alpha=r['alpha'], label=l['label'])
        if yy.has_key('ranges2'):
            ranges = yy['ranges2']
            for r in ranges:
                yy_axis.fill_between(ts, r['data1'], r['data2'], color=r['color'], facecolor=r['color'], edgecolor=r['color'], alpha=r['alpha'], label=r['label'])
        if yy.has_key('lines2'):
            lines = yy['lines2']
            for l in lines:
                yy_axis.plot_date(ts, l['data'], linestyle='-', linewidth=1.5, marker='', markersize=4, color=l['color'], alpha=r['alpha'], label=l['label'])
        yy_axis.legend(loc='best', prop={'size':8})
        if qc:
            zeros = numpy.zeros(len(ts), dtype='f8')
            yy_axis_qc.fill_between(ts, zeros, qc['data'], color=qc['color'], facecolor=qc['color'], edgecolor=qc['color'], alpha=qc['alpha'], label=qc['label'])
#            yy_axis_qc.bar(left=ts, height=qc['data'], width=4000.0 / len(qc['data']), align='center', color=qc['color'], edgecolor=qc['color'], alpha=qc['alpha'])
        yy_axis_qc.set_ylim([0.0, 1.0])

    if filename:
        canvas.print_figure(filename, dpi=DPI)
        log.debug("Saved '{f}'".format(f=filename))

    if show:
        pyplot.show()

    pyplot.close(figure)


def gen_site_plots(siteid, sitedir, version_data, version_processing, pipeline=None):
    log.info("Generation of plots for site {s} started".format(s=siteid))

    if pipeline is None:
        prodfile_template = PRODFILE_TEMPLATE
        prodfile_figure_template = PRODFILE_FIGURE_TEMPLATE
        prodfile_years_template = PRODFILE_YEARS_TEMPLATE
    else:
        prodfile_template = pipeline.prodfile_template
        prodfile_figure_template = pipeline.prodfile_figure_template
        prodfile_years_template = pipeline.prodfile_years_template

    first_year, last_year = load_years(siteid=siteid, sitedir=sitedir, version_data=version_data, version_processing=version_processing, prodfile_years_template=prodfile_years_template)
    year_range = range(int(first_year), int(last_year) + 1)

    hh_filename = prodfile_template.format(s=siteid, sd=sitedir, g='FULLSET', r='HH', fy=first_year, ly=last_year, vd=version_data, vp=version_processing)
    if not os.path.isfile(hh_filename):
        hh_filename = prodfile_template.format(s=siteid, sd=sitedir, g='FULLSET', r='HR', fy=first_year, ly=last_year, vd=version_data, vp=version_processing)
        if not os.path.isfile(hh_filename):
            raise ONEFluxError("{s}: data file not found: {f}".format(s=siteid, f=hh_filename))
    dd_filename = prodfile_template.format(s=siteid, sd=sitedir, g='FULLSET', r='DD', fy=first_year, ly=last_year, vd=version_data, vp=version_processing)
    if not os.path.isfile(dd_filename):
        raise ONEFluxError("{s}: data file not found: {f}".format(s=siteid, f=dd_filename))
    ww_filename = prodfile_template.format(s=siteid, sd=sitedir, g='FULLSET', r='WW', fy=first_year, ly=last_year, vd=version_data, vp=version_processing)
    if not os.path.isfile(ww_filename):
        raise ONEFluxError("{s}: data file not found: {f}".format(s=siteid, f=ww_filename))
    mm_filename = prodfile_template.format(s=siteid, sd=sitedir, g='FULLSET', r='MM', fy=first_year, ly=last_year, vd=version_data, vp=version_processing)
    if not os.path.isfile(mm_filename):
        raise ONEFluxError("{s}: data file not found: {f}".format(s=siteid, f=mm_filename))
    yy_filename = prodfile_template.format(s=siteid, sd=sitedir, g='FULLSET', r='YY', fy=first_year, ly=last_year, vd=version_data, vp=version_processing)
    if not os.path.isfile(yy_filename):
        raise ONEFluxError("{s}: data file not found: {f}".format(s=siteid, f=yy_filename))

#    ### subject to bug caused by sites with first site year removed
#    ### (CUT USTAR file cannot be located, first year is not the same as year on first file of data)
#    ### see code for fixing first_year before calls to load_ustar_cut and load_ustar_vut
#    ### on file fpp.execution.aux_info_files
#    ustar_cut = load_ustar_cut(siteid=siteid, sitedir=sitedir, first_year=first_year, last_year=last_year)
#    ustar_vut = load_ustar_vut(siteid=siteid, sitedir=sitedir, year_range=year_range)

    hh_data = load_data_file(filename=hh_filename, resolution='hh')
    hh_timestamps = [datetime.strptime(e, "%Y%m%d%H%M") for e in hh_data['TIMESTAMP_END']]
#    print 'HH', hh_timestamps[0], hh_timestamps[1], hh_timestamps[-2], hh_timestamps[-1]

    dd_data = load_data_file(filename=dd_filename, resolution='dd')
    dd_timestamps = [datetime.strptime(e, "%Y%m%d") for e in dd_data['TIMESTAMP']]
#    print 'DD:', dd_timestamps[0], dd_timestamps[1], dd_timestamps[-2], dd_timestamps[-1]

    ww_data = load_data_file(filename=ww_filename, resolution='ww')
    ww_timestamps = [datetime.strptime(e, "%Y%m%d") for e in ww_data['TIMESTAMP_END']]
#    print 'WW:', ww_timestamps[0], ww_timestamps[1], ww_timestamps[-2], ww_timestamps[-1]

    mm_data = load_data_file(filename=mm_filename, resolution='mm')
    mm_timestamps = [datetime.strptime(e, "%Y%m") for e in mm_data['TIMESTAMP']]
#    print 'MM:', mm_timestamps[0], mm_timestamps[1], mm_timestamps[-2], mm_timestamps[-1]

    yy_data = load_data_file(filename=yy_filename, resolution='yy')
    yy_timestamps = [datetime.strptime(e, "%Y") for e in yy_data['TIMESTAMP']]
#    print 'YY:', yy_timestamps[0], yy_timestamps[1], yy_timestamps[-2], yy_timestamps[-1]

    ### NEE
    hh = {'ts': hh_timestamps,
          'lines': [#{'label':'NEE_VUT_MEAN', 'data':hh_data['NEE_VUT_MEAN'], 'color':COLOR_MEAN, 'alpha':1},
                    #{'label':'NEE_VUT_U50', 'data':hh_data['NEE_VUT_USTAR50'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'NEE_VUT_REF', 'data':hh_data['NEE_VUT_REF'], 'color':COLOR_REF, 'alpha':1},
                    ],
          'ranges': [{'label':'NEE_VUT_05-95', 'data1':hh_data['NEE_VUT_05'], 'data2':hh_data['NEE_VUT_95'], 'color':COLOR_RNG, 'alpha':0.45},
                     {'label':'NEE_VUT_16-84', 'data1':hh_data['NEE_VUT_16'], 'data2':hh_data['NEE_VUT_84'], 'color':COLOR_RNG, 'alpha':0.45},
                     {'label':'NEE_VUT_25-75', 'data1':hh_data['NEE_VUT_25'], 'data2':hh_data['NEE_VUT_75'], 'color':COLOR_RNG, 'alpha':0.45},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':hh_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }
#    hh = {}
    dd = {'ts': dd_timestamps,
          'lines': [#{'label':'NEE_VUT_MEAN', 'data':dd_data['NEE_VUT_MEAN'], 'color':COLOR_MEAN, 'alpha':1},
                    #{'label':'NEE_VUT_U50', 'data':dd_data['NEE_VUT_USTAR50'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'NEE_VUT_REF', 'data':dd_data['NEE_VUT_REF'], 'color':COLOR_REF, 'alpha':1},
                    ],
          'ranges': [{'label':'NEE_VUT_05-95', 'data1':dd_data['NEE_VUT_05'], 'data2':dd_data['NEE_VUT_95'], 'color':COLOR_RNG, 'alpha':0.45},
                     {'label':'NEE_VUT_16-84', 'data1':dd_data['NEE_VUT_16'], 'data2':dd_data['NEE_VUT_84'], 'color':COLOR_RNG, 'alpha':0.45},
                     {'label':'NEE_VUT_25-75', 'data1':dd_data['NEE_VUT_25'], 'data2':dd_data['NEE_VUT_75'], 'color':COLOR_RNG, 'alpha':0.45},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':dd_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }
#    dd = {}
    ww = {'ts': ww_timestamps,
          'lines': [#{'label':'NEE_VUT_MEAN', 'data':ww_data['NEE_VUT_MEAN'], 'color':COLOR_MEAN, 'alpha':1},
                    #{'label':'NEE_VUT_U50', 'data':ww_data['NEE_VUT_USTAR50'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'NEE_VUT_REF', 'data':ww_data['NEE_VUT_REF'], 'color':COLOR_REF, 'alpha':1},
                    ],
          'ranges': [{'label':'NEE_VUT_05-95', 'data1':ww_data['NEE_VUT_05'], 'data2':ww_data['NEE_VUT_95'], 'color':COLOR_RNG, 'alpha':0.45},
                     {'label':'NEE_VUT_16-84', 'data1':ww_data['NEE_VUT_16'], 'data2':ww_data['NEE_VUT_84'], 'color':COLOR_RNG, 'alpha':0.45},
                     {'label':'NEE_VUT_25-75', 'data1':ww_data['NEE_VUT_25'], 'data2':ww_data['NEE_VUT_75'], 'color':COLOR_RNG, 'alpha':0.45},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':ww_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }
#    ww = {}
    mm = {'ts': mm_timestamps,
          'lines': [{'label':'NEE_VUT_MEAN', 'data':mm_data['NEE_VUT_MEAN'], 'color':COLOR_MEAN, 'alpha':1},
                    {'label':'NEE_VUT_U50', 'data':mm_data['NEE_VUT_USTAR50'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'NEE_VUT_REF', 'data':mm_data['NEE_VUT_REF'], 'color':COLOR_REF, 'alpha':1},
                    ],
          'ranges': [{'label':'NEE_VUT_05-95', 'data1':mm_data['NEE_VUT_05'], 'data2':mm_data['NEE_VUT_95'], 'color':COLOR_RNG, 'alpha':0.45},
                     {'label':'NEE_VUT_16-84', 'data1':mm_data['NEE_VUT_16'], 'data2':mm_data['NEE_VUT_84'], 'color':COLOR_RNG, 'alpha':0.45},
                     {'label':'NEE_VUT_25-75', 'data1':mm_data['NEE_VUT_25'], 'data2':mm_data['NEE_VUT_75'], 'color':COLOR_RNG, 'alpha':0.45},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':mm_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }
    yy = {'ts': yy_timestamps,
          'lines': [{'label':'NEE_VUT_MEAN', 'data':yy_data['NEE_VUT_MEAN'], 'color':COLOR_MEAN, 'alpha':1},
                    {'label':'NEE_VUT_U50', 'data':yy_data['NEE_VUT_USTAR50'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'NEE_VUT_REF', 'data':yy_data['NEE_VUT_REF'], 'color':COLOR_REF, 'alpha':1},
                    ],
          'ranges': [{'label':'NEE_VUT_05-95', 'data1':yy_data['NEE_VUT_05'], 'data2':yy_data['NEE_VUT_95'], 'color':COLOR_RNG, 'alpha':0.45},
                     {'label':'NEE_VUT_16-84', 'data1':yy_data['NEE_VUT_16'], 'data2':yy_data['NEE_VUT_84'], 'color':COLOR_RNG, 'alpha':0.45},
                     {'label':'NEE_VUT_25-75', 'data1':yy_data['NEE_VUT_25'], 'data2':yy_data['NEE_VUT_75'], 'color':COLOR_RNG, 'alpha':0.45},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':yy_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }

    plot_nee_unc(hh=hh, dd=dd, ww=ww, mm=mm, yy=yy,
                 title="{s} - NEE".format(s=siteid),
                 y_label='NEE',
                 filename=prodfile_figure_template.format(s=siteid, sd=sitedir, f='NEE', fy=first_year, ly=last_year, vd=version_data, vp=version_processing),
                 show=False)


    ### RECO
    hh = {'ts': hh_timestamps,
          'lines': [
#                    {'label':'RECO_NT_VUT_U50', 'data':hh_data['RECO_NT_VUT_USTAR50'], 'color':COLOR_NT_U50, 'alpha':1},
                    {'label':'RECO_NT_VUT_REF', 'data':hh_data['RECO_NT_VUT_REF'], 'color':COLOR_NT_REF, 'alpha':1},
                    ],
          'lines2': [
#                    {'label':'RECO_DT_VUT_U50', 'data':hh_data['RECO_DT_VUT_USTAR50'], 'color':COLOR_DT_U50, 'alpha':1},
                    {'label':'RECO_DT_VUT_REF', 'data':hh_data['RECO_DT_VUT_REF'], 'color':COLOR_DT_REF, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'RECO_NT_VUT_05-95', 'data1':hh_data['RECO_NT_VUT_05'], 'data2':hh_data['RECO_NT_VUT_95'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'RECO_NT_VUT_16-84', 'data1':hh_data['RECO_NT_VUT_16'], 'data2':hh_data['RECO_NT_VUT_84'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'RECO_NT_VUT_25-75', 'data1':hh_data['RECO_NT_VUT_25'], 'data2':hh_data['RECO_NT_VUT_75'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     ],
          'ranges2': [
                     {'label':'RECO_DT_VUT_05-95', 'data1':hh_data['RECO_DT_VUT_05'], 'data2':hh_data['RECO_DT_VUT_95'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'RECO_DT_VUT_16-84', 'data1':hh_data['RECO_DT_VUT_16'], 'data2':hh_data['RECO_DT_VUT_84'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'RECO_DT_VUT_25-75', 'data1':hh_data['RECO_DT_VUT_25'], 'data2':hh_data['RECO_DT_VUT_75'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':hh_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }
    dd = {'ts': dd_timestamps,
          'lines': [
#                    {'label':'RECO_NT_VUT_U50', 'data':dd_data['RECO_NT_VUT_USTAR50'], 'color':COLOR_NT_U50, 'alpha':1},
                    {'label':'RECO_NT_VUT_REF', 'data':dd_data['RECO_NT_VUT_REF'], 'color':COLOR_NT_REF, 'alpha':1},
                    ],
          'lines2': [
#                    {'label':'RECO_DT_VUT_U50', 'data':dd_data['RECO_DT_VUT_USTAR50'], 'color':COLOR_DT_U50, 'alpha':1},
                    {'label':'RECO_DT_VUT_REF', 'data':dd_data['RECO_DT_VUT_REF'], 'color':COLOR_DT_REF, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'RECO_NT_VUT_05-95', 'data1':dd_data['RECO_NT_VUT_05'], 'data2':dd_data['RECO_NT_VUT_95'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'RECO_NT_VUT_16-84', 'data1':dd_data['RECO_NT_VUT_16'], 'data2':dd_data['RECO_NT_VUT_84'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'RECO_NT_VUT_25-75', 'data1':dd_data['RECO_NT_VUT_25'], 'data2':dd_data['RECO_NT_VUT_75'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     ],
          'ranges2': [
                     {'label':'RECO_DT_VUT_05-95', 'data1':dd_data['RECO_DT_VUT_05'], 'data2':dd_data['RECO_DT_VUT_95'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'RECO_DT_VUT_16-84', 'data1':dd_data['RECO_DT_VUT_16'], 'data2':dd_data['RECO_DT_VUT_84'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'RECO_DT_VUT_25-75', 'data1':dd_data['RECO_DT_VUT_25'], 'data2':dd_data['RECO_DT_VUT_75'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':dd_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }
    ww = {'ts': ww_timestamps,
          'lines': [
#                    {'label':'RECO_NT_VUT_U50', 'data':ww_data['RECO_NT_VUT_USTAR50'], 'color':COLOR_NT_U50, 'alpha':1},
                    {'label':'RECO_NT_VUT_REF', 'data':ww_data['RECO_NT_VUT_REF'], 'color':COLOR_NT_REF, 'alpha':1},
                    ],
          'lines2': [
#                    {'label':'RECO_DT_VUT_U50', 'data':ww_data['RECO_DT_VUT_USTAR50'], 'color':COLOR_DT_U50, 'alpha':1},
                    {'label':'RECO_DT_VUT_REF', 'data':ww_data['RECO_DT_VUT_REF'], 'color':COLOR_DT_REF, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'RECO_NT_VUT_05-95', 'data1':ww_data['RECO_NT_VUT_05'], 'data2':ww_data['RECO_NT_VUT_95'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'RECO_NT_VUT_16-84', 'data1':ww_data['RECO_NT_VUT_16'], 'data2':ww_data['RECO_NT_VUT_84'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'RECO_NT_VUT_25-75', 'data1':ww_data['RECO_NT_VUT_25'], 'data2':ww_data['RECO_NT_VUT_75'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     ],
          'ranges2': [
                     {'label':'RECO_DT_VUT_05-95', 'data1':ww_data['RECO_DT_VUT_05'], 'data2':ww_data['RECO_DT_VUT_95'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'RECO_DT_VUT_16-84', 'data1':ww_data['RECO_DT_VUT_16'], 'data2':ww_data['RECO_DT_VUT_84'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'RECO_DT_VUT_25-75', 'data1':ww_data['RECO_DT_VUT_25'], 'data2':ww_data['RECO_DT_VUT_75'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':ww_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }
    mm = {'ts': mm_timestamps,
          'lines': [
#                    {'label':'RECO_NT_VUT_U50', 'data':mm_data['RECO_NT_VUT_USTAR50'], 'color':COLOR_NT_U50, 'alpha':1},
                    {'label':'RECO_NT_VUT_REF', 'data':mm_data['RECO_NT_VUT_REF'], 'color':COLOR_NT_REF, 'alpha':1},
                    ],
          'lines2': [
#                    {'label':'RECO_DT_VUT_U50', 'data':mm_data['RECO_DT_VUT_USTAR50'], 'color':COLOR_DT_U50, 'alpha':1},
                    {'label':'RECO_DT_VUT_REF', 'data':mm_data['RECO_DT_VUT_REF'], 'color':COLOR_DT_REF, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'RECO_NT_VUT_05-95', 'data1':mm_data['RECO_NT_VUT_05'], 'data2':mm_data['RECO_NT_VUT_95'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'RECO_NT_VUT_16-84', 'data1':mm_data['RECO_NT_VUT_16'], 'data2':mm_data['RECO_NT_VUT_84'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'RECO_NT_VUT_25-75', 'data1':mm_data['RECO_NT_VUT_25'], 'data2':mm_data['RECO_NT_VUT_75'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     ],
          'ranges2': [
                     {'label':'RECO_DT_VUT_05-95', 'data1':mm_data['RECO_DT_VUT_05'], 'data2':mm_data['RECO_DT_VUT_95'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'RECO_DT_VUT_16-84', 'data1':mm_data['RECO_DT_VUT_16'], 'data2':mm_data['RECO_DT_VUT_84'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'RECO_DT_VUT_25-75', 'data1':mm_data['RECO_DT_VUT_25'], 'data2':mm_data['RECO_DT_VUT_75'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':mm_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }
    yy = {'ts': yy_timestamps,
          'lines': [
                    {'label':'RECO_NT_VUT_U50', 'data':yy_data['RECO_NT_VUT_USTAR50'], 'color':COLOR_NT_U50, 'alpha':1},
                    {'label':'RECO_NT_VUT_REF', 'data':yy_data['RECO_NT_VUT_REF'], 'color':COLOR_NT_REF, 'alpha':1},
                    ],
          'lines2': [
                    {'label':'RECO_DT_VUT_U50', 'data':yy_data['RECO_DT_VUT_USTAR50'], 'color':COLOR_DT_U50, 'alpha':1},
                    {'label':'RECO_DT_VUT_REF', 'data':yy_data['RECO_DT_VUT_REF'], 'color':COLOR_DT_REF, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'RECO_NT_VUT_05-95', 'data1':yy_data['RECO_NT_VUT_05'], 'data2':yy_data['RECO_NT_VUT_95'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'RECO_NT_VUT_16-84', 'data1':yy_data['RECO_NT_VUT_16'], 'data2':yy_data['RECO_NT_VUT_84'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'RECO_NT_VUT_25-75', 'data1':yy_data['RECO_NT_VUT_25'], 'data2':yy_data['RECO_NT_VUT_75'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     ],
          'ranges2': [
                     {'label':'RECO_DT_VUT_05-95', 'data1':yy_data['RECO_DT_VUT_05'], 'data2':yy_data['RECO_DT_VUT_95'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'RECO_DT_VUT_16-84', 'data1':yy_data['RECO_DT_VUT_16'], 'data2':yy_data['RECO_DT_VUT_84'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'RECO_DT_VUT_25-75', 'data1':yy_data['RECO_DT_VUT_25'], 'data2':yy_data['RECO_DT_VUT_75'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':yy_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }

    plot_nee_unc(hh=hh, dd=dd, ww=ww, mm=mm, yy=yy,
                 title="{s} - RECO".format(s=siteid),
                 y_label='RECO',
                 filename=prodfile_figure_template.format(s=siteid, sd=sitedir, f='RECO', fy=first_year, ly=last_year, vd=version_data, vp=version_processing),
                 show=False)

    ### GPP
    hh = {'ts': hh_timestamps,
          'lines': [
#                    {'label':'GPP_NT_VUT_U50', 'data':hh_data['GPP_NT_VUT_USTAR50'], 'color':COLOR_NT_U50, 'alpha':1},
                    {'label':'GPP_NT_VUT_REF', 'data':hh_data['GPP_NT_VUT_REF'], 'color':COLOR_NT_REF, 'alpha':1},
                    ],
          'lines2': [
#                    {'label':'GPP_DT_VUT_U50', 'data':hh_data['GPP_DT_VUT_USTAR50'], 'color':COLOR_DT_U50, 'alpha':1},
                    {'label':'GPP_DT_VUT_REF', 'data':hh_data['GPP_DT_VUT_REF'], 'color':COLOR_DT_REF, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'GPP_NT_VUT_05-95', 'data1':hh_data['GPP_NT_VUT_05'], 'data2':hh_data['GPP_NT_VUT_95'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'GPP_NT_VUT_16-84', 'data1':hh_data['GPP_NT_VUT_16'], 'data2':hh_data['GPP_NT_VUT_84'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'GPP_NT_VUT_25-75', 'data1':hh_data['GPP_NT_VUT_25'], 'data2':hh_data['GPP_NT_VUT_75'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     ],
          'ranges2': [
                     {'label':'GPP_DT_VUT_05-95', 'data1':hh_data['GPP_DT_VUT_05'], 'data2':hh_data['GPP_DT_VUT_95'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'GPP_DT_VUT_16-84', 'data1':hh_data['GPP_DT_VUT_16'], 'data2':hh_data['GPP_DT_VUT_84'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'GPP_DT_VUT_25-75', 'data1':hh_data['GPP_DT_VUT_25'], 'data2':hh_data['GPP_DT_VUT_75'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':hh_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }
    dd = {'ts': dd_timestamps,
          'lines': [
#                    {'label':'GPP_NT_VUT_U50', 'data':dd_data['GPP_NT_VUT_USTAR50'], 'color':COLOR_NT_U50, 'alpha':1},
                    {'label':'GPP_NT_VUT_REF', 'data':dd_data['GPP_NT_VUT_REF'], 'color':COLOR_NT_REF, 'alpha':1},
                    ],
          'lines2': [
#                    {'label':'GPP_DT_VUT_U50', 'data':dd_data['GPP_DT_VUT_USTAR50'], 'color':COLOR_DT_U50, 'alpha':1},
                    {'label':'GPP_DT_VUT_REF', 'data':dd_data['GPP_DT_VUT_REF'], 'color':COLOR_DT_REF, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'GPP_NT_VUT_05-95', 'data1':dd_data['GPP_NT_VUT_05'], 'data2':dd_data['GPP_NT_VUT_95'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'GPP_NT_VUT_16-84', 'data1':dd_data['GPP_NT_VUT_16'], 'data2':dd_data['GPP_NT_VUT_84'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'GPP_NT_VUT_25-75', 'data1':dd_data['GPP_NT_VUT_25'], 'data2':dd_data['GPP_NT_VUT_75'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     ],
          'ranges2': [
                     {'label':'GPP_DT_VUT_05-95', 'data1':dd_data['GPP_DT_VUT_05'], 'data2':dd_data['GPP_DT_VUT_95'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'GPP_DT_VUT_16-84', 'data1':dd_data['GPP_DT_VUT_16'], 'data2':dd_data['GPP_DT_VUT_84'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'GPP_DT_VUT_25-75', 'data1':dd_data['GPP_DT_VUT_25'], 'data2':dd_data['GPP_DT_VUT_75'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':dd_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }
    ww = {'ts': ww_timestamps,
          'lines': [
#                    {'label':'GPP_NT_VUT_U50', 'data':ww_data['GPP_NT_VUT_USTAR50'], 'color':COLOR_NT_U50, 'alpha':1},
                    {'label':'GPP_NT_VUT_REF', 'data':ww_data['GPP_NT_VUT_REF'], 'color':COLOR_NT_REF, 'alpha':1},
                    ],
          'lines2': [
#                    {'label':'GPP_DT_VUT_U50', 'data':ww_data['GPP_DT_VUT_USTAR50'], 'color':COLOR_DT_U50, 'alpha':1},
                    {'label':'GPP_DT_VUT_REF', 'data':ww_data['GPP_DT_VUT_REF'], 'color':COLOR_DT_REF, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'GPP_NT_VUT_05-95', 'data1':ww_data['GPP_NT_VUT_05'], 'data2':ww_data['GPP_NT_VUT_95'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'GPP_NT_VUT_16-84', 'data1':ww_data['GPP_NT_VUT_16'], 'data2':ww_data['GPP_NT_VUT_84'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'GPP_NT_VUT_25-75', 'data1':ww_data['GPP_NT_VUT_25'], 'data2':ww_data['GPP_NT_VUT_75'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     ],
          'ranges2': [
                     {'label':'GPP_DT_VUT_05-95', 'data1':ww_data['GPP_DT_VUT_05'], 'data2':ww_data['GPP_DT_VUT_95'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'GPP_DT_VUT_16-84', 'data1':ww_data['GPP_DT_VUT_16'], 'data2':ww_data['GPP_DT_VUT_84'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'GPP_DT_VUT_25-75', 'data1':ww_data['GPP_DT_VUT_25'], 'data2':ww_data['GPP_DT_VUT_75'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':ww_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }
    mm = {'ts': mm_timestamps,
          'lines': [
#                    {'label':'GPP_NT_VUT_U50', 'data':mm_data['GPP_NT_VUT_USTAR50'], 'color':COLOR_NT_U50, 'alpha':1},
                    {'label':'GPP_NT_VUT_REF', 'data':mm_data['GPP_NT_VUT_REF'], 'color':COLOR_NT_REF, 'alpha':1},
                    ],
          'lines2': [
#                    {'label':'GPP_DT_VUT_U50', 'data':mm_data['GPP_DT_VUT_USTAR50'], 'color':COLOR_DT_U50, 'alpha':1},
                    {'label':'GPP_DT_VUT_REF', 'data':mm_data['GPP_DT_VUT_REF'], 'color':COLOR_DT_REF, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'GPP_NT_VUT_05-95', 'data1':mm_data['GPP_NT_VUT_05'], 'data2':mm_data['GPP_NT_VUT_95'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'GPP_NT_VUT_16-84', 'data1':mm_data['GPP_NT_VUT_16'], 'data2':mm_data['GPP_NT_VUT_84'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'GPP_NT_VUT_25-75', 'data1':mm_data['GPP_NT_VUT_25'], 'data2':mm_data['GPP_NT_VUT_75'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     ],
          'ranges2': [
                     {'label':'GPP_DT_VUT_05-95', 'data1':mm_data['GPP_DT_VUT_05'], 'data2':mm_data['GPP_DT_VUT_95'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'GPP_DT_VUT_16-84', 'data1':mm_data['GPP_DT_VUT_16'], 'data2':mm_data['GPP_DT_VUT_84'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'GPP_DT_VUT_25-75', 'data1':mm_data['GPP_DT_VUT_25'], 'data2':mm_data['GPP_DT_VUT_75'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':mm_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }
    yy = {'ts': yy_timestamps,
          'lines': [
                    {'label':'GPP_NT_VUT_U50', 'data':yy_data['GPP_NT_VUT_USTAR50'], 'color':COLOR_NT_U50, 'alpha':1},
                    {'label':'GPP_NT_VUT_REF', 'data':yy_data['GPP_NT_VUT_REF'], 'color':COLOR_NT_REF, 'alpha':1},
                    ],
          'lines2': [
                    {'label':'GPP_DT_VUT_U50', 'data':yy_data['GPP_DT_VUT_USTAR50'], 'color':COLOR_DT_U50, 'alpha':1},
                    {'label':'GPP_DT_VUT_REF', 'data':yy_data['GPP_DT_VUT_REF'], 'color':COLOR_DT_REF, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'GPP_NT_VUT_05-95', 'data1':yy_data['GPP_NT_VUT_05'], 'data2':yy_data['GPP_NT_VUT_95'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'GPP_NT_VUT_16-84', 'data1':yy_data['GPP_NT_VUT_16'], 'data2':yy_data['GPP_NT_VUT_84'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     {'label':'GPP_NT_VUT_25-75', 'data1':yy_data['GPP_NT_VUT_25'], 'data2':yy_data['GPP_NT_VUT_75'], 'color':COLOR_NT_RNG, 'alpha':0.40},
                     ],
          'ranges2': [
                     {'label':'GPP_DT_VUT_05-95', 'data1':yy_data['GPP_DT_VUT_05'], 'data2':yy_data['GPP_DT_VUT_95'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'GPP_DT_VUT_16-84', 'data1':yy_data['GPP_DT_VUT_16'], 'data2':yy_data['GPP_DT_VUT_84'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     {'label':'GPP_DT_VUT_25-75', 'data1':yy_data['GPP_DT_VUT_25'], 'data2':yy_data['GPP_DT_VUT_75'], 'color':COLOR_DT_RNG, 'alpha':0.40},
                     ],
          'qc': {'label':'NEE_VUT_MEAN_QC', 'data':yy_data['NEE_VUT_MEAN_QC'], 'color':COLOR_QC, 'alpha':1}
    }

    plot_nee_unc(hh=hh, dd=dd, ww=ww, mm=mm, yy=yy,
                 title="{s} - GPP".format(s=siteid),
                 y_label='GPP',
                 filename=prodfile_figure_template.format(s=siteid, sd=sitedir, f='GPP', fy=first_year, ly=last_year, vd=version_data, vp=version_processing),
                 show=False)


    ### LE
    hh = {'ts': hh_timestamps,
          'lines': [
                    {'label':'LE_F_MDS', 'data':hh_data['LE_F_MDS'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'LE_CORR', 'data':hh_data['LE_CORR'], 'color':COLOR_MEAN, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'LE_CORR_25-75', 'data1':hh_data['LE_CORR_25'], 'data2':hh_data['LE_CORR_75'], 'color':COLOR_RNG, 'alpha':0.40},
                     ],
          'qc': {}
    }
    dd = {'ts': dd_timestamps,
          'lines': [
                    {'label':'LE_F_MDS', 'data':dd_data['LE_F_MDS'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'LE_CORR', 'data':dd_data['LE_CORR'], 'color':COLOR_MEAN, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'LE_CORR_25-75', 'data1':dd_data['LE_CORR_25'], 'data2':dd_data['LE_CORR_75'], 'color':COLOR_RNG, 'alpha':0.40},
                     ],
          'qc': {}
    }
    ww = {'ts': ww_timestamps,
          'lines': [
                    {'label':'LE_F_MDS', 'data':ww_data['LE_F_MDS'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'LE_CORR', 'data':ww_data['LE_CORR'], 'color':COLOR_MEAN, 'alpha':1},
                    ],
          'ranges': [],
          'qc': {}
    }
    mm = {'ts': mm_timestamps,
          'lines': [
                    {'label':'LE_F_MDS', 'data':mm_data['LE_F_MDS'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'LE_CORR', 'data':mm_data['LE_CORR'], 'color':COLOR_MEAN, 'alpha':1},
                    ],
          'ranges': [],
          'qc': {}
    }
    yy = {'ts': yy_timestamps,
          'lines': [
                    {'label':'LE_F_MDS', 'data':yy_data['LE_F_MDS'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'LE_CORR', 'data':yy_data['LE_CORR'], 'color':COLOR_MEAN, 'alpha':1},
                    ],
          'ranges': [],
          'qc': {}
    }

    plot_nee_unc(hh=hh, dd=dd, ww=ww, mm=mm, yy=yy,
                 title="{s} - LE".format(s=siteid),
                 y_label='LE',
                 filename=prodfile_figure_template.format(s=siteid, sd=sitedir, f='LE', fy=first_year, ly=last_year, vd=version_data, vp=version_processing),
                 show=False)


    ### H
    hh = {'ts': hh_timestamps,
          'lines': [
                    {'label':'H_F_MDS', 'data':hh_data['H_F_MDS'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'H_CORR', 'data':hh_data['H_CORR'], 'color':COLOR_MEAN, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'H_CORR_25-75', 'data1':hh_data['H_CORR_25'], 'data2':hh_data['H_CORR_75'], 'color':COLOR_RNG, 'alpha':0.50},
                     ],
          'qc': {}
    }
    dd = {'ts': dd_timestamps,
          'lines': [
                    {'label':'H_F_MDS', 'data':dd_data['H_F_MDS'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'H_CORR', 'data':dd_data['H_CORR'], 'color':COLOR_MEAN, 'alpha':1},
                    ],
          'ranges': [
                     {'label':'H_CORR_25-75', 'data1':dd_data['H_CORR_25'], 'data2':dd_data['H_CORR_75'], 'color':COLOR_RNG, 'alpha':0.50},
                     ],
          'qc': {}
    }
    ww = {'ts': ww_timestamps,
          'lines': [
                    {'label':'H_F_MDS', 'data':ww_data['H_F_MDS'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'H_CORR', 'data':ww_data['H_CORR'], 'color':COLOR_MEAN, 'alpha':1},
                    ],
          'ranges': [],
          'qc': {}
    }
    mm = {'ts': mm_timestamps,
          'lines': [
                    {'label':'H_F_MDS', 'data':mm_data['H_F_MDS'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'H_CORR', 'data':mm_data['H_CORR'], 'color':COLOR_MEAN, 'alpha':1},
                    ],
          'ranges': [],
          'qc': {}
    }
    yy = {'ts': yy_timestamps,
          'lines': [
                    {'label':'H_F_MDS', 'data':yy_data['H_F_MDS'], 'color':COLOR_U50, 'alpha':1},
                    {'label':'H_CORR', 'data':yy_data['H_CORR'], 'color':COLOR_MEAN, 'alpha':1},
                    ],
          'ranges': [],
          'qc': {}
    }

    plot_nee_unc(hh=hh, dd=dd, ww=ww, mm=mm, yy=yy,
                 title="{s} - H".format(s=siteid),
                 y_label='H',
                 filename=prodfile_figure_template.format(s=siteid, sd=sitedir, f='H', fy=first_year, ly=last_year, vd=version_data, vp=version_processing),
                 show=False)
    log.info("Generation of plots for site {s} finished".format(s=siteid))

if __name__ == '__main__':
    sys.exit("ERROR: cannot run independently")

