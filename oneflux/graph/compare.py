'''
oneflux.graph.compare

For license information:
see LICENSE file or headers in oneflux.__init__.py

Library for comparing data sets

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''
import sys
import os
import logging
import numpy
import matplotlib
import platform
import datetime

if platform.system() == 'Darwin':
    matplotlib.use('macosx') # N.B.: must come before pyplot import
if os.environ.get('DISPLAY', None) is None:
    matplotlib.use('Agg') # if no display set, change Matplotlib backend; no 'show' capabilities for Matplotlib; N.B.: must come before pyplot import
matplotlib.rcParams['path.simplify'] = False  # removes smoothing, forces plotting all points

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib import pyplot, gridspec, patches, dates
from scipy import stats

from oneflux import ONEFluxError

_log = logging.getLogger(__name__)

def plot_comparison(timestamp_list, data1, data2, label1, label2, title, basename=None, show=True, force_x_lim=False, show_exclusive_gaps=False):
    """
    
    :param timestamp_list: list of timestamps (datetime objects)
    :type timestamp_list: list
    :param data1: data for first data set to be compared
    :type data1: numpy.ndarray
    :param data2: data for second data set to be compared
    :type data2: numpy.ndarray
    :param label1: label for first data set
    :type label1: str
    :param label2: label for second data set
    :type label2: str
    :param title: plot title
    :type title: str
    :param basename: file base name for saving figure (no file saved if None)
    :type basename: str or None
    :param show: if True will show interactive figure
    :type show: bool
    :param force_x_lim: if True will force x axis to start/end matching timestamp_list first/last timestamp 
    :type force_x_lim: bool
    """
    _log.debug("Compare execution environment: platform='{p}', display='{d}', matplotlib-backend='{b}'".format(p=platform.system(), d=os.environ.get('DISPLAY', None), b=matplotlib.get_backend(),))

    ### my code
    #pyplot.plot_date(timestamp_list, data1)
    #pyplot.show()
    #exit()
    ### end of my code

    mask = ~numpy.isnan(data1) & ~numpy.isnan(data2)
    if not numpy.any(mask):
        _log.error("Nothing to plot '{b}', '{l1}', '{l2}'".format(b=basename, l1=label1, l2=label2))
        return

    figure = pyplot.figure()
    #figure.text(.5, .97, var, horizontalalignment='center', fontsize='x-large')
    figure.set_figwidth(16)
    figure.set_figheight(12)
    canvas = FigureCanvasAgg(figure)

    gs = gridspec.GridSpec(18, 3)
    gs.update(left=0.06, right=0.98, top=0.88, bottom=0.05, wspace=0.18, hspace=0.40)

    if ('{l1}' in title) and ('{l2}' in title):
        figure_title = title.format(l1=label1, l2=label2)
    else:
        figure_title = title

    # min/max
    xmin, xmax = numpy.nanmin(data1[(data1 != -numpy.inf) & (data1 != numpy.inf)]), numpy.nanmax(data1[(data1 != -numpy.inf) & (data1 != numpy.inf)])
    ymin, ymax = numpy.nanmin(data2[(data2 != -numpy.inf) & (data2 != numpy.inf)]), numpy.nanmax(data2[(data2 != -numpy.inf) & (data2 != numpy.inf)])

    # main timeseries
    data_ts_dates = dates.date2num(timestamp_list)
    #data_ts_dates = timestamp_list
    #print("len(data_ts_dates)")
    #print(len(data_ts_dates))

    axis_main = pyplot.subplot(gs[0:7, :])
    axis_main.set_title(figure_title, x=0.5, y=1.30)
    axis_main.axhline(linewidth=0.7, linestyle='-', color='#AAAAAA')
    p1, = axis_main.plot_date(data_ts_dates, data1, linewidth=1.0, linestyle='', marker='+', markersize=6, color='#8080ff', markeredgecolor='#8080ff', alpha=1.0)
    p2, = axis_main.plot_date(data_ts_dates, data2, linewidth=1.0, linestyle='', marker='x', markersize=6, color='#ff8080', markeredgecolor='#ff8080', alpha=1.0)
    if force_x_lim:
        axis_main.set_xlim(timestamp_list[0], timestamp_list[-1])
#         p3, = axis_main.plot_date([], [], linewidth=1.0, linestyle='', marker='.', markersize=3, color='green', markeredgecolor='green', alpha=1.0)
#         legend = axis_main.legend([p1, p2, p3], [label1, label2, 'diff'], numpoints=1, markerscale=8.0)
    legend = axis_main.legend([p1, p2], [label1, label2], numpoints=1, markerscale=1.1, fancybox=True)
    legend.get_frame().set_alpha(0.7)
    legend.get_frame().set_edgecolor('none')
    axis_main.xaxis.tick_top()
    for t in axis_main.get_xmajorticklabels():
        t.set(rotation=90)
    props1 = dict(boxstyle='round', facecolor='#d8d8ff', edgecolor='none', alpha=0.7)
    props2 = dict(boxstyle='round', facecolor='#ffe5e5', edgecolor='none', alpha=0.7)
    axis_main.text(0.02, 0.94, '{v}: $mean={a}$  $median={d}$  $std={s}$  $N={n}$'.format(v=label1, a=numpy.nanmean(data1), d=numpy.nanmedian(data1), s=numpy.nanstd(data1), n=numpy.sum(~numpy.isnan(data1))), transform=axis_main.transAxes, fontsize=11, fontweight='bold', color='#8080ff', bbox=props1)
    axis_main.text(0.02, 0.86, '{v}: $mean={a}$  $median={d}$  $std={s}$  $N={n}$'.format(v=label2, a=numpy.nanmean(data2), d=numpy.nanmedian(data2), s=numpy.nanstd(data2), n=numpy.sum(~numpy.isnan(data2))), transform=axis_main.transAxes, fontsize=11, fontweight='bold', color='#ff8080', bbox=props2)

    tmin, tmax = axis_main.get_xlim()

    #print("tmin")
    #print(datetime.date.fromordinal(int(tmin)))
    #print("tmax")
    #print(datetime.date.fromordinal(int(tmax)))

    # gaps
    axis_avail = pyplot.subplot(gs[7, :])
    vmin, vmax = min(xmin, ymin), max(xmax, ymax)

    m1 = numpy.isnan(data1)
    m2 = numpy.isnan(data2)
    m3 = numpy.logical_xor(m1, m2)

    if show_exclusive_gaps == True:
        axis_avail.vlines(timestamp_list, ymin=m3 * vmin, ymax=m3 * vmax, linestyles='solid', color='#000000', alpha=1.0)
    else:
        axis_avail.vlines(timestamp_list, ymin=m1 * vmin, ymax=m1 * vmax, linewidth=0.1, color='blue', alpha=0.5)
        axis_avail.vlines(timestamp_list, ymin=m2 * vmin, ymax=m2 * vmax, linewidth=0.1, color='red', alpha=0.5)
    if force_x_lim:
        axis_avail.set_xlim(timestamp_list[0], timestamp_list[-1])
    axis_avail.set_ylabel('gaps')
    axis_avail.set_ylim(ymin, ymax)
    axis_avail.tick_params(bottom='off', top='off', left='off', right='off', labelleft='off', labelbottom='off')
    if numpy.sum(m1) + numpy.sum(m2) + numpy.sum(m3) == 0:
        axis_avail.text(0.5, 0.25, 'NO GAPS', transform=axis_avail.transAxes, fontsize=16, color='black')
    axis_avail.set_xlim(tmin, tmax)

    '''
    # XOR
    axis_xor = pyplot.subplot(gs[8, :])

    m3 = numpy.logical_xor(m1, m2)

    axis_xor.vlines(timestamp_list, ymin=m3 * vmin, ymax=m3 * vmax, linestyles='solid', color='#000000', alpha=1.0)
    axis_xor.set_ylabel('xor')
    axis_xor.set_ylim(ymin, ymax)
    axis_xor.tick_params(bottom='off', top='off', left='off', right='off', labelleft='off', labelbottom='off')
    if numpy.sum(m3) == 0:
        axis_xor.text(0.5, 0.25, 'NO XOR', transform=axis_xor.transAxes, fontsize=16, color='black')
    axis_xor.set_xlim(tmin, tmax)
    '''

    # difference
    axis_diff = pyplot.subplot(gs[8:11, :])
    axis_diff.axhline(linewidth=0.7, linestyle='-', color='#AAAAAA')
    #p, = axis_diff.plot_date(timestamp_list, data1 - data2, linewidth=1.0, linestyle='', marker='.', markersize=3, color='#559977', markeredgecolor='#559977', alpha=1.0)
    data_zero = numpy.zeros_like(data1)
    data_diff = data1 - data2
    axis_diff.fill_between(timestamp_list, data_zero, data_diff, where=data_diff >= data_zero, color='#8080ff', alpha=1.0)
    axis_diff.fill_between(timestamp_list, data_zero, data_diff, where=data_diff <= data_zero, color='#ff8080', alpha=1.0)
    if force_x_lim:
        axis_diff.set_xlim(timestamp_list[0], timestamp_list[-1])
    axis_diff.set_ylabel('difference')
    axis_diff.tick_params(labelbottom='off')
    axis_diff.set_xlim(tmin, tmax)
    yticks = axis_diff.get_yticks().tolist()
    yticks = [abs(i) for i in yticks]
    axis_diff.set_yticklabels(yticks)


    # regression
    gradient, intercept, r_value, p_value, std_err = stats.linregress(data1[mask], data2[mask])
    rsq = r_value * r_value
    ymin_r, ymax_r = (gradient * xmin + intercept, gradient * xmax + intercept)
#         vmin, vmax = min(xmin, ymin), max(xmax, ymax)
#         print xmin, xmax, ymin, ymax
    diff = (vmax - vmin) * 0.1
    vmin, vmax = vmin - diff, vmax + diff
    axis_regr = pyplot.subplot(gs[11:, 0])
    axis_regr.plot((vmin, vmax), (vmin, vmax), linestyle='-', linewidth=1, marker='', markersize=4, color='black', markeredgecolor='black', alpha=1.0)
    axis_regr.plot(data1, data2, linewidth=1.0, linestyle='', marker='.', markersize=3, color='#559977', markeredgecolor='#559977', alpha=1.0)
    axis_regr.plot((xmin, xmax), (ymin_r, ymax_r), linestyle='-', linewidth=1, marker='', markersize=4, color='red', markeredgecolor='red', alpha=1.0)
    axis_regr.set_xlim(vmin, vmax)
    axis_regr.set_ylim(vmin, vmax)
    axis_regr.set_xlabel(label1)
    axis_regr.set_ylabel(label2)
    axis_regr.text(0.9, 0.96, '1:1', transform=axis_regr.transAxes, fontsize=10, color='black')
    props = dict(boxstyle='round', facecolor='#eae3dd', edgecolor='none', alpha=0.7)
    axis_regr.text(0.04, 0.88, '$y={g:.4f}*x {sig} {i:.4f}$\n$r^2={r:.4f}$'.format(r=rsq, g=gradient, i=abs(intercept), sig=('-' if intercept < 0 else '+')), transform=axis_regr.transAxes, fontsize=12, color='#997755', bbox=props)

    # histogram (density)
    axis_hist = pyplot.subplot(gs[11:, 1])
    hist_range = [vmin, vmax]
    h1, bins1, patches1 = axis_hist.hist(data1, bins=80, histtype='stepfilled', range=hist_range, normed=True, color='blue', edgecolor='none', alpha=0.5, label=label1)
    h2, bins2, patches2 = axis_hist.hist(data2, bins=80, histtype='stepfilled', range=hist_range, normed=True, color='red', edgecolor='none', alpha=0.5, label=label2)
    axis_hist.set_ylabel('probability density')
    legend = axis_hist.legend(fancybox=True)
    legend.get_frame().set_alpha(0.7)
    legend.get_frame().set_edgecolor('none')
    for leg in legend.legendHandles:
        leg.set_edgecolor('none')


    # histogram (cumulative density)
    axis_cumden = pyplot.subplot(gs[11:, 2])
    hist_range = [vmin, vmax]
    h1, bins1, patches1 = axis_cumden.hist(data1, bins=200, cumulative=True, histtype='stepfilled', range=hist_range, normed=True, color='blue', edgecolor='none', alpha=0.5, label=label1)
    h2, bins2, patches2 = axis_cumden.hist(data2, bins=200, cumulative=True, histtype='stepfilled', range=hist_range, normed=True, color='red', edgecolor='none', alpha=0.5, label=label2)
    axis_cumden.set_ylim(0.0, 1.0)
    axis_cumden.set_ylabel('cumulative probability density')
    legend = axis_cumden.legend(loc='lower right', fancybox=True)
    legend.get_frame().set_alpha(0.7)
    legend.get_frame().set_edgecolor('none')
    for leg in legend.legendHandles:
        leg.set_edgecolor('none')


    if basename:
        if ('{l1}' in basename) and ('{l2}' in basename):
            figure_filename = os.path.abspath((basename + '.png').format(l1=label1, l2=label2))
        else:
            figure_filename = os.path.abspath('{b}__{l1}_{l2}.png'.format(b=basename, l1=label1, l2=label2))
        canvas.print_figure(figure_filename, dpi=100)
        _log.info("Saved '{f}'".format(f=figure_filename))

    if show:
        pyplot.show()

    #pyplot.plot_date(timestamp_list, data1)
    #pyplot.show()

    pyplot.close(figure)

    #pyplot.plot_date(timestamp_list, data1)
    #pyplot.show()
    #exit()


def plot_e0_comparison(ge_sum, le_sum, ok_ge_sum, ok_le_sum, nok_ge_sum, nok_le_sum, threshold, title, basename=None, show=True, ymax=None):
    _log.debug("Compare execution environment: platform='{p}', display='{d}', matplotlib-backend='{b}'".format(p=platform.system(), d=os.environ.get('DISPLAY', None), b=matplotlib.get_backend(),))

    figure = pyplot.figure()
    #figure.text(.5, .97, var, horizontalalignment='center', fontsize='x-large')
    figure.set_figwidth(12)
    figure.set_figheight(9)
    canvas = FigureCanvasAgg(figure)

    gs = gridspec.GridSpec(1, 3)
    gs.update(left=0.06, right=0.98, top=0.94, bottom=0.05, wspace=0.18, hspace=0.40)

    # diff totals over/under threshold
    axis_tot = pyplot.subplot(gs[0, 0])
    axis_tot.set_title(title, x=1.70, y=1.02)
    tick_labels = ['Diff <= {t}'.format(t=threshold), 'Diff >= {t}'.format(t=threshold)]
    _ = axis_tot.bar([1, 2], [le_sum, ge_sum], [0.8, 0.8], [0.0, 0.0], color=['#8080ff', '#ff8080'], edgecolor=['#8080ff', '#ff8080'], tick_label=tick_labels)
    top_le_label, top_ge_label = str(le_sum), str(ge_sum)
    if ymax is not None:
        axis_tot.set_ylim(0, ymax)
        total = float(ymax)
        top_le_perc, top_ge_perc = (le_sum / total) * 100., (ge_sum / total) * 100.
        top_le_label += ' ({i:.2f}%)'.format(i=top_le_perc)
        top_ge_label += ' ({i:.2f}%)'.format(i=top_ge_perc)
    axis_tot.text(1, le_sum + 2, top_le_label, color='#8080ff', fontweight='bold', ha='center')
    axis_tot.text(2, ge_sum + 2, top_ge_label, color='#ff8080', fontweight='bold', ha='center')
    axis_tot.set_ylabel('Number of windows')
#    for t in axis_tot.get_xmajorticklabels(): t.set(rotation=90)

    props = dict(boxstyle='round', facecolor='#ffffff', edgecolor='none', alpha=0.7)
    axis_tot.text(0.02, 1.01, 'diff under {t}'.format(t=threshold), transform=axis_tot.transAxes, fontsize=11, fontweight='bold', color='#8080ff', bbox=props)
    axis_tot.text(0.60, 1.01, 'diff over {t}'.format(t=threshold), transform=axis_tot.transAxes, fontsize=11, fontweight='bold', color='#ff8080', bbox=props)

    # diff and NLR status combinations
    axis_stat = pyplot.subplot(gs[0, 1:])
    tick_labels = ['NRL OK\nDiff <= {t}'.format(t=threshold),
                   'NRL not OK\nDiff <= {t}'.format(t=threshold),
                   'NRL not OK\nDiff >= {t}'.format(t=threshold),
                   'NRL OK\nDiff >= {t}'.format(t=threshold), ]
    a1 = axis_stat.bar(1, ok_le_sum, 0.8, 0.0, color='#8080ff', edgecolor='#8080ff', hatch='O')
    a2 = axis_stat.bar(2, nok_le_sum, 0.8, 0.0, color='#8080ff', edgecolor='#8080ff', hatch='//')
    a3 = axis_stat.bar(3, nok_ge_sum, 0.8, 0.0, color='#ff8080', edgecolor='#ff8080', hatch='//')
    a4 = axis_stat.bar(4, ok_ge_sum, 0.8, 0.0, color='#ff8080', edgecolor='#ff8080', hatch='O')
    top_ok_le_label, top_nok_le_label, top_nok_ge_label, top_ok_ge_label = str(ok_le_sum), str(nok_le_sum), str(nok_ge_sum), str(ok_ge_sum)
    if ymax is not None:
        axis_stat.set_ylim(0, ymax)
        total = float(ymax)
        top_ok_le_perc, top_nok_le_perc, top_nok_ge_perc, top_ok_ge_perc = (ok_le_sum / total) * 100., (nok_le_sum / total) * 100., (nok_ge_sum / total) * 100., (ok_ge_sum / total) * 100.
        top_ok_le_label += ' ({i:.2f}%)'.format(i=top_ok_le_perc)
        top_nok_le_label += ' ({i:.2f}%)'.format(i=top_nok_le_perc)
        top_nok_ge_label += ' ({i:.2f}%)'.format(i=top_nok_ge_perc)
        top_ok_ge_label += ' ({i:.2f}%)'.format(i=top_ok_ge_perc)
        props = dict(boxstyle='round', facecolor='#ffffff', edgecolor='none', alpha=0.7)
        axis_stat.text(0.02, 0.96, '{t} (100.0%)'.format(t=int(total)), transform=axis_stat.transAxes, fontsize=11, fontweight='bold', color='#000011', bbox=props)
    axis_stat.text(1, ok_le_sum + 2, top_ok_le_label, color='#8080ff', fontweight='bold', ha='center')
    axis_stat.text(2, nok_le_sum + 2, top_nok_le_label, color='#8080ff', fontweight='bold', ha='center')
    axis_stat.text(3, nok_ge_sum + 2, top_nok_ge_label, color='#ff8080', fontweight='bold', ha='center')
    axis_stat.text(4, ok_ge_sum + 2, top_ok_ge_label, color='#ff8080', fontweight='bold', ha='center')
    axis_stat.set_xticks([1, 2, 3, 4])
    axis_stat.set_xticklabels(tick_labels)
    axis_stat.legend((a1[0], a2[0]), ('NLR OK', 'NRL not OK'))
#    for t in axis_stat.get_xmajorticklabels(): t.set(rotation=90)

    if basename[-4:] != '.png':
        basename = basename + '.png'
    canvas.print_figure(basename, dpi=100)
    _log.info("Saved '{f}'".format(f=basename))

    if show:
        pyplot.show()

    pyplot.close(figure)


def plot_param_diff_vs(param_data, vs_data, highlight_mask=None, param_label='E0', vs_label='unknown', highlight_label='undefined', basename=None, show=False):
    _log.debug("Compare execution environment: platform='{p}', display='{d}', matplotlib-backend='{b}'".format(p=platform.system(), d=os.environ.get('DISPLAY', None), b=matplotlib.get_backend(),))

    mask = ~numpy.isnan(param_data) & ~numpy.isnan(vs_data)
    if not numpy.any(mask):
        _log.error("Nothing to plot {el} vs '{vl}'".format(el=param_label, vl=vs_label))
        return

    figure = pyplot.figure()
    #figure.text(.5, .97, var, horizontalalignment='center', fontsize='x-large')
    figure.set_figwidth(8)
    figure.set_figheight(6)
    canvas = FigureCanvasAgg(figure)

    gs = gridspec.GridSpec(1, 1)
    gs.update(left=0.1, right=0.98, top=0.96, bottom=0.1, wspace=0.18, hspace=0.40)

    # min/max
    xmin, xmax = numpy.nanmin(param_data), numpy.nanmax(param_data)
    ymin, ymax = numpy.nanmin(vs_data), numpy.nanmax(vs_data)
    vmin, vmax = min(xmin, ymin), max(xmax, ymax)

    # regression
    gradient, intercept, r_value, p_value, std_err = stats.linregress(param_data[mask], vs_data[mask])
    rsq = r_value * r_value
    ymin_r, ymax_r = (gradient * xmin + intercept, gradient * xmax + intercept)
#         vmin, vmax = min(xmin, ymin), max(xmax, ymax)
#         print xmin, xmax, ymin, ymax
    diff = (vmax - vmin) * 0.1
    vmin, vmax = vmin - diff, vmax + diff

    xdiff = (xmax - xmin) * 0.1
    xxmin, xxmax = xmin - xdiff, xmax + xdiff

    ydiff = (ymax - ymin) * 0.1
    yymin, yymax = ymin - ydiff, ymax + ydiff

    axis_regr = pyplot.subplot(gs[0, 0])
#    axis_regr.plot((vmin, vmax), (vmin, vmax), linestyle='-', linewidth=1, marker='', markersize=4, color='black', markeredgecolor='black', alpha=1.0)
    axis_regr.plot(param_data, vs_data, linewidth=1.0, linestyle='', marker='o', markersize=6, color='#559977', markeredgecolor='#559977', alpha=1.0)
    if highlight_mask is not None:
        a2 = axis_regr.plot(param_data[highlight_mask], vs_data[highlight_mask], linewidth=1.0, linestyle='', marker='o', markersize=6, color='#985577', markeredgecolor='#985577', alpha=1.0)
        axis_regr.legend((a2[0],), (highlight_label,), loc='upper right')
    axis_regr.plot((xmin, xmax), (ymin_r, ymax_r), linestyle='-', linewidth=1, marker='', markersize=4, color='red', markeredgecolor='red', alpha=1.0)
    axis_regr.set_xlim(xxmin, xxmax)
    axis_regr.set_ylim(yymin, yymax)
    axis_regr.set_xlabel(param_label)
    axis_regr.set_ylabel(vs_label)
#    axis_regr.text(0.9, 0.96, '1:1', transform=axis_regr.transAxes, fontsize=10, color='black')
    props = dict(boxstyle='round', facecolor='#eae3dd', edgecolor='none', alpha=0.7)
    axis_regr.text(0.15, 0.85, '$y={g:.2f}*x {sig} {i:.2f}$\n$r^2={r:.4f}$'.format(r=rsq, g=gradient, i=abs(intercept), sig=('-' if intercept < 0 else '+')), transform=axis_regr.transAxes, fontsize=12, color='#997755', bbox=props)

    if basename:
        if basename[-4:] != '.png':
            basename = basename + '.png'
        canvas.print_figure(basename, dpi=100)
        _log.info("Saved '{f}'".format(f=basename))

    if show:
        pyplot.show()

    pyplot.close(figure)




LOW_VAR_PERC = 25
def compute_plot_param_diffs(py_data, pw_data, filename, param_var_list=['alpha', 'beta', 'k', 'rref', 'e0'], vs_var_list=['nee', 'ta', 'rg'], low_variability_percentile=LOW_VAR_PERC, show=False, normalized=False, site_count=0):

    for param_var in param_var_list:
        for vs_var in vs_var_list:
            param_diff = numpy.abs(py_data[param_var] - pw_data[param_var])

            param_label = ('{v}: |py - pw| / max(|py|, |pw|)'.format(v=param_var) if normalized else '{v}: |py - pw|'.format(v=param_var))
            std_label = 'std({v})'.format(v=vs_var)
            std_var = vs_var + '_std'

            # plot param differences vs vs_var_std
            basename = filename + '__comp_{p}-diff_std-{v}'.format(p=param_var, v=vs_var) + ('_{n}-sites'.format(n=site_count) if site_count else '')

            # find low variability for all other variables
            low_variability_mask = py_data[std_var] > 0.0 # just to get mask with right dimensions
            low_variability_mask[:] = True
            e_vs_var_label = ''
            for e_vs_var in [i for i in vs_var_list if i != vs_var]:
                e_vs_var_std = e_vs_var + '_std'
                low_variability_threshold = numpy.nanpercentile(py_data[e_vs_var_std], low_variability_percentile)
                low_variability_mask = low_variability_mask & (py_data[e_vs_var_std] < low_variability_threshold)
                e_vs_var_label = e_vs_var_label + ' & (std({v})<{t:.2f})'.format(v=e_vs_var, t=low_variability_threshold)
            e_vs_var_label = e_vs_var_label.strip(' &')
            plot_param_diff_vs(param_data=param_diff, vs_data=py_data[std_var], highlight_mask=low_variability_mask, param_label=param_label, vs_label=std_label, highlight_label='{v} ({p}th perc)'.format(v=e_vs_var_label, p=low_variability_percentile), basename=basename, show=show)


def compute_plot_e0_diffs(py_data, pw_data, filename, low_variability_percentile=LOW_VAR_PERC, show=False, normalized=False, site_count=0):

    e0diff = numpy.abs(py_data['e0_all_val'] - pw_data['e0_all_val'])

#    # Does not make sense to normalize NEE and TA, variability effects on model (Lloyd-Taylor respiration) are not site dependent
#    if normalized:
#        e0_label = '|py - pw| / max(|py|, |pw|)'
#        std_ta_label = 'std(TA) / max(std(TA))'
#        std_nee_label = 'std(NEE) / max(std(NEE))'
#    else:
#        e0_label = '|py - pw|'
#        std_ta_label = 'std(TA)'
#        std_nee_label = 'std(NEE)'

    e0_label = ('|py - pw| / max(|py|, |pw|)' if normalized else '|py - pw|')
    std_ta_label = 'std(TA)'
    std_nee_label = 'std(NEE)'

    # plot e0 differences vs pvalue
    basename = filename + '__comp_e0diff-pvalue' + ('_{n}-sites'.format(n=site_count) if site_count else '')
    plot_param_diff_vs(param_data=e0diff, vs_data=py_data['pvalue'], param_label=e0_label, vs_label='p-value', basename=basename, show=show)

    # plot e0 differences vs nee_std
    basename = filename + '__comp_e0diff-std_nee' + ('_{n}-sites'.format(n=site_count) if site_count else '')
    low_variability_threshold = numpy.nanpercentile(py_data['ta_std'], low_variability_percentile)
    highlight_mask = py_data['ta_std'] < low_variability_threshold
    plot_param_diff_vs(param_data=e0diff, vs_data=py_data['nee_std'], highlight_mask=highlight_mask, param_label=e0_label, vs_label=std_nee_label, highlight_label='std(TA)<{v:.2f} ({p}th perc)'.format(v=low_variability_threshold, p=low_variability_percentile), basename=basename, show=show)

    # plot e0 differences vs ta_std
    basename = filename + '__comp_e0diff-std_ta' + ('_{n}-sites'.format(n=site_count) if site_count else '')
    low_variability_threshold = numpy.nanpercentile(py_data['nee_std'], low_variability_percentile)
    highlight_mask = py_data['nee_std'] < low_variability_threshold
    plot_param_diff_vs(param_data=e0diff, vs_data=py_data['ta_std'], highlight_mask=highlight_mask, param_label=e0_label, vs_label=std_ta_label, highlight_label='std(NEE)<{v:.2f} ({p}th perc)'.format(v=low_variability_threshold, p=low_variability_percentile), basename=basename, show=show)

    # plot e0 differences vs nee_std "+" ta_std
    basename = filename + '__comp_e0diff-std_nee-ta' + ('_{n}-sites'.format(n=site_count) if site_count else '')
    std_sum = numpy.sqrt((py_data['nee_std'] * py_data['nee_std']) + (py_data['ta_std'] * py_data['ta_std']))
    plot_param_diff_vs(param_data=e0diff, vs_data=std_sum, param_label=e0_label, vs_label='std(NEE)+std(TA)', basename=basename, show=show)


if __name__ == '__main__':
    raise ONEFluxError('Not executable')
