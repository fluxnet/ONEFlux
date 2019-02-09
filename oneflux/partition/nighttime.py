'''
oneflux.partition.nighttime

For license information:
see LICENSE file or headers in oneflux.__init__.py 

From scratch implementation from PV-Wave cleaned-up code, nighttime method

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''
import os
import sys
import logging
import numpy

from datetime import datetime
from scipy.optimize import leastsq
from scipy.stats import rankdata, ttest_ind, f_oneway
from scipy.interpolate import splev, splrep, interp1d, LSQUnivariateSpline

from oneflux import ONEFluxError

from oneflux.partition.compu import compu_qcnee_filter, compu_daylight, compu_daylight_zero, compu_sunrise, compu_sunset, compu_nee_night
from oneflux.partition.ecogeo import lloyd_taylor
from oneflux.partition.auxiliary import compare_col_to_pvwave, FLOAT_PREC, NAN, NAN_TEST, nan, not_nan
from oneflux.partition.library import QC_AUTO_DIR, METEO_PROC_DIR, NEE_PROC_DIR, NT_OUTPUT_DIR, HEADER_SEPARATOR, EXTRA_FILENAME, NT_STR
from oneflux.partition.library import load_output, get_latitude, var, varnum, add_empty_vars, create_data_structures, nomi, newselif, ONEFluxPartitionError
from oneflux.utils.files import check_create_directory

_log = logging.getLogger(__name__)


def partitioning_nt(datadir, siteid, sitedir, prod_to_compare, perc_to_compare, years_to_compare):
    """
    NT partitioning wrapper function.
    Handles all "versions" (percentiles, CUT/VUT, years, etc)
    
    :param datadir: main data directory (full path)
    :type datadir: str
    :param siteid: site flux id to be processed - in format CC-SSS
    :type siteid: str
    :param sitedir: data directory for site (relative path to datadir)
    :type sitedir: str
    :param prod_to_compare: list of products to compare - ['c', 'y']
    :type prod_to_compare: list (of str)
    :param perc_to_compare: list of percentiles to compare - ['1.25', '3.75', ..., '96.25', '98.75']
    :type perc_to_compare: list (of str)
    :param years_to_compare: list of years to compare - [1996, 1997, ... , 2014]
    :type years_to_compare: list (of int)
    """

    _log.info("Started NT partitioning of {s}".format(s=siteid))

    sitedir_full = os.path.join(datadir, sitedir)
    qc_auto_dir = os.path.join(sitedir_full, QC_AUTO_DIR)
    meteo_proc_dir = os.path.join(sitedir_full, METEO_PROC_DIR)
    nee_proc_dir = os.path.join(sitedir_full, NEE_PROC_DIR)
    nt_output_dir = os.path.join(sitedir_full, NT_OUTPUT_DIR)

    # reformat percentiles to compare into data column labels
    percentiles_data_columns = [i.replace('.', HEADER_SEPARATOR) for i in perc_to_compare]

    # check and create output dir if needed
    if os.path.isdir(sitedir_full) and not os.path.isdir(nt_output_dir):
        check_create_directory(directory=nt_output_dir)

    # load meteo proc results
    meteo_proc_f = os.path.join(meteo_proc_dir, '{s}_meteo_hh.csv'.format(s=siteid))
    if not os.path.isfile(meteo_proc_f):
            msg = "Meteo proc file not found '{f}'".format(f=meteo_proc_f)
            _log.critical(msg)
            raise ONEFluxError(msg)
    _log.info("Will now load meteo file '{f}'".format(f=meteo_proc_f))
    whole_dataset_meteo, headers_meteo, timestamp_list_meteo, year_list_meteo = load_output(meteo_proc_f)

    # iterate through UStar threshold types
    for ustar_type in prod_to_compare:
        _log.info("Started processing UStar threshold type '{u}'".format(u=ustar_type))

        # load nee proc results (percentiles file)
        nee_proc_percentiles_f = os.path.join(nee_proc_dir, '{s}_NEE_percentiles_{u}_hh.csv'.format(s=siteid, u=ustar_type))
        if not os.path.isfile(nee_proc_percentiles_f):
            msg = "NEE proc file not found '{f}', trying '{n}'".format(f=nee_proc_percentiles_f, n='{f}')
            nee_proc_percentiles_f = os.path.join(nee_proc_dir, '{s}_NEE_percentiles_{u}.csv'.format(s=siteid, u=ustar_type))
            msg = msg.format(f=nee_proc_percentiles_f)
            _log.info(msg)

            if not os.path.isfile(nee_proc_percentiles_f):
                if ustar_type == 'y':
                    msg = "NEE proc file not found '{f}'".format(f=nee_proc_percentiles_f)
                    _log.critical(msg)
                    raise ONEFluxError(msg)
                elif ustar_type == 'c':
                    msg = "NEE proc file not found '{f}', skipping (CUT not computed?)".format(f=nee_proc_percentiles_f)
                    _log.warning(msg)
                    continue
                else:
                    msg = "Invalid USTAR type '{u}'".format(u=ustar_type)
                    raise ONEFluxError(msg)
        _log.info("Will now load nee percentiles file '{f}'".format(f=nee_proc_percentiles_f))
        whole_dataset_nee, headers_nee, timestamp_list_nee, year_list_nee = load_output(nee_proc_percentiles_f)

        # iterate through each year
        for iteration, year in enumerate(year_list_nee):
            if year not in years_to_compare:
                continue
            _log.info("Started processing year '{y}'".format(y=year))
            qc_auto_nee_f = os.path.join(qc_auto_dir, '{s}_qca_nee_{y}.csv'.format(s=siteid, y=year))
            if not os.path.isfile(qc_auto_nee_f):
                msg = "QC auto file not found '{f}'".format(f=qc_auto_nee_f)
                _log.error(msg)
                continue
            latitude = get_latitude(filename=qc_auto_nee_f)

            # iterate through UStar threshold values
            for percentile in percentiles_data_columns:
                _log.info("Started processing percentile '{p}'".format(p=percentile))
                percentile_print = percentile.replace(HEADER_SEPARATOR, '.')
                output_filename = os.path.join(nt_output_dir, "nee_{t}_{p}_{s}_{y}{extra}.csv".format(t=ustar_type, p=percentile_print, s=siteid, y=year, extra=EXTRA_FILENAME))
                temp_output_filename = os.path.join(nt_output_dir, "nee_{t}_{p}_{s}_{y}{extra}.csv".format(t=ustar_type, p=percentile_print, s=siteid, y=year, extra='{extra}'))
                if os.path.isfile(output_filename):
                    _log.info("Output file found, skipping: '{f}'".format(f=output_filename))
                    continue
                else:
                    _log.debug("Output file missing, will be processed: '{f}'".format(f=output_filename))

                # create masks for current year for both nee and meteo
                year_mask_nee = (whole_dataset_nee['year'] == year)
                year_mask_meteo = (whole_dataset_meteo['year'] == year)

                # account for first entry being from previous year
                if iteration == 0:
                    _log.debug("First site-year available ({y}), removing first midnight entry from meteo only".format(y=year))
                    first_meteo = numpy.where(year_mask_meteo == 1)[0][0]
                    first_nee = None
                    year_mask_meteo[first_meteo] = 0
                else:
                    _log.debug("Regular site-year ({y}), removing first midnight entry from meteo and nee".format(y=year))
                    first_meteo = numpy.where(year_mask_meteo == 1)[0][0]
                    first_nee = numpy.where(year_mask_nee == 1)[0][0]
                    year_mask_meteo[first_meteo] = 0
                    year_mask_nee[first_nee] = 0

                # account for last entry being from next year
                _log.debug("Site-year ({y}), adding first midnight entry from next year for meteo and nee".format(y=year))
                last_meteo = numpy.where(year_mask_meteo == 1)[0][-1] + 1
                last_nee = numpy.where(year_mask_nee == 1)[0][-1] + 1
                year_mask_meteo[last_meteo] = 1
                year_mask_nee[last_nee] = 1

                _log.debug("Site-year {y}: first NEE '{tn}' and first meteo '{tm}'".format(y=year, tn=whole_dataset_nee[year_mask_nee][0]['timestamp_end'], tm=whole_dataset_meteo[year_mask_meteo][0]['timestamp_end']))
                _log.debug("Site-year {y}:  last NEE '{tn}' and  last meteo '{tm}'".format(y=year, tn=whole_dataset_nee[year_mask_nee][-1]['timestamp_end'], tm=whole_dataset_meteo[year_mask_meteo][-1]['timestamp_end']))

                if numpy.sum(year_mask_nee) != numpy.sum(year_mask_meteo):
                    msg = "Incompatible array sizes (nee={n}, meteo={m}) for year '{y}' while processing '{f}'".format(y=year, f=output_filename, n=numpy.sum(year_mask_nee), m=numpy.sum(year_mask_meteo))
                    _log.error(msg)
                    raise ONEFluxError(msg)

                working_year_data = create_data_structures(ustar_type=ustar_type, whole_dataset_nee=whole_dataset_nee, whole_dataset_meteo=whole_dataset_meteo,
                                                           percentile=percentile, year_mask_nee=year_mask_nee, year_mask_meteo=year_mask_meteo, latitude=latitude, part_type=NT_STR)

                # corresponds to partitnioning_nt.pro, line:  compu, set, "QCNEE=0"   # NOTE: removes all information of missing data records!
                compu(data=working_year_data, func=compu_qcnee_filter, columns=['qcnee']) # equivalent to: working_year_data['qcnee'][:] = 0

                # get latitude from data structure
                lat = var(working_year_data, 'lat')

                # call flux_partition
                result_year_data = flux_partition(data=working_year_data, lat=lat[0], tempvar='tair', temp_output_filename=temp_output_filename)

                # save output data file
                _log.debug("Saving output file '{f}".format(f=output_filename))
                numpy.savetxt(fname=output_filename, X=result_year_data, delimiter=',', fmt='%s', header=','.join(result_year_data.dtype.names), comments='')
                _log.debug("Saved output file '{f}".format(f=output_filename))

                _log.info("Finished processing percentile '{p}'".format(p=percentile))
#                sys.exit('EXIT') # TODO: testing only, remove
            _log.info("Finished processing year '{y}'".format(y=year))
        _log.info("Finished processing UStar threshold type '{u}'".format(u=ustar_type))
    _log.info("Finished NT partitioning of {s}".format(s=siteid))



STEP_SIZE = 5         # number of days to slide window by
WINDOW_SIZE = 14      # number of days to include in window
MIN_ENTRIES = 6       # minimum number of entries needed for optimization step
MIN_TRANGE = 5.0      # minimum temperature range (degC) needed for optimization step
DAY_MIN_SW_IN = 10.0  # minimum shortwave radiation (W m-2) to be considered daytime
def flux_partition(data, lat, tempvar='tair', nomsg=False, temp_output_filename=''):
    """
    Main flux partitioning function (for a single dataset)
    
    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param lat: site latitude
    :type lat: float
    :param tempvar: temperature variable to be used (e.g., tair or tsoil)
    :type tempvar: str
    :param nomsg: hide messages flag (not used in this implementation) 
    :type nomsg: boolean
    """
    _log.debug('Started NT flux partition main function')

    _log.debug("Flux partitioning using '{t}' as temperature variable".format(t=tempvar))

    ### day/night time flag
    # daylight flag based on sunrise/sunset times
    if lat > NAN_TEST:
        compu(data=data, func=compu_sunrise, columns=['sunrise', 'julday'], parameters={'lat':lat})
        compu(data=data, func=compu_sunset, columns=['sunset', 'julday'], parameters={'lat':lat})
        compu(data=data, func=compu_daylight, columns=['daylight', 'hr', 'sunrise', 'sunset'])
    else:
        compu(data=data, func=compu_daylight_zero, columns=['daylight'])

    # new NEE night variable
    compu(data=data, func=compu_nee_night, columns=['neenight', 'nee'])

    # nighttime NEE based on daylight flag and short-wave radiation
    # original condition: :Rg: lt 10. and :qcNEE: eq 0 and :daylight: eq 0
    neenight_mask = ((data['rg'] < DAY_MIN_SW_IN) & (data['qcnee'] == 0) & (data['daylight'] == 0))
    data, _, _ = newselif(data=data, condition=neenight_mask, drop=False, columns=['neenight'])


    ###############################################################################################
    ### FIRST OPTIMIZATION FOR FULL YEAR ##########################################################
    # estimate parameters using optimization on full year of data
    _log.debug('Starting full year/long term paramater optimization')
    _, rref, e0, _, _, _, _, _, _, _, _, _ = nlinlts1(data=data)
    add_empty_vars(data=data, records=rref, column='rref_1_from_tair', unit='umolm-2s-1')
    bounded_e0 = (0.0 if e0 < 0.0 else (450.0 if e0 > 450.0 else e0))
    add_empty_vars(data=data, records=bounded_e0, column='e0_1_from_tair', unit='umolm-2s-1')
    _log.debug('Finished full year paramater optimization')
    ### FIRST OPTIMIZATION FOR FULL YEAR ##########################################################
    ###############################################################################################



    ###############################################################################################
    #### SECOND OPTIMIZATION FOR 5 DAY STEPS, 14 DAY WINDOWS ######################################
    _log.debug('Starting windowed/short term paramater optimization')
    juldays = data['julday']                                   ### array of days-of-year
    tair = data[tempvar]                                       ### array of temperatures
    fcn = data['neenight']                                     ### array of nighttime NEE
    julmin, julmax = int(juldays[0]), int(numpy.max(juldays))  ### first/last day of year
    n_regr = 0                                                 ### counter of number of regressions/optimizations

    window_steps = range(julmin, julmax + 1, STEP_SIZE)

    # TODO: (potential) add e0_1_list, e0_2_list, e0_3_list, and corresponding se and idx to track individual

    # lists of results/stats for each step/window with successful execution (okstats structure in original code)
    jday_list, jday_all_list, est_rref_list, est_e0_list, est_rref_se_list, est_e0_se_list, est_residuals_list, est_covariance_matrices_list, ls_status_list, ls_msg_list, pvalue_list, nee_std_list, ta_std_list = [], [], [], [], [], [], [], [], [], [], [], [], []

    # lists of entry indices for each step/window with successful execution
    indices_half_list, indices_first_list, indices_last_list, indices_len_list = [], [], [], []

    for jday in window_steps:
#        print                                  # TODO: remove
#        print '--- jday start: ', jday, ' ---' # TODO: remove
        jday_all_list.append(jday)
        pvalue, nee_std, ta_std, ls_status, ls_msg = 'nan', 'nan', 'nan', -10, '' # selected non-execution status flag and message
        # window (days interval) and non-NA mask to be used in current step
        w_mask = (juldays >= jday) & (juldays < jday + WINDOW_SIZE) & not_nan(fcn) & not_nan(tair) #*****************************
        w_where = numpy.where(w_mask)[0]
        w_len = numpy.sum(w_mask)

        if w_len > MIN_ENTRIES:
            subdata = data[w_mask]
            temp_range = numpy.max(tair[w_mask]) - numpy.min(tair[w_mask])
            if temp_range >= MIN_TRANGE:
                status, rref, e0, rref_se, e0_se, residuals, covariance_matrix, ls_status, ls_msg, pvalue, nee_std, ta_std = nlinlts1(data=subdata)

#                if jday == 301: sys.exit('DEBUG FINISH') # TODO: remove

                if status == 0:
                    jday_list.append(jday)
                    est_rref_list.append(rref)
                    est_e0_list.append(e0)
                    est_rref_se_list.append(rref_se)
                    est_e0_se_list.append(e0_se)
                    est_residuals_list.append(residuals)
                    est_covariance_matrices_list.append(covariance_matrix)
                    indices_half_list.append(w_where[w_len / 2])
                    indices_first_list.append(w_where[0])
                    indices_last_list.append(w_where[-1])
                    indices_len_list.append(w_len)
#                    print '2nOP_doy/n/rref/e0: ', jday, w_len, rref, e0 ### TODO: debug only, remove *********************
                    n_regr += 1 # one more successful regression/optimization
                data['ls_status'][w_where[0]] = ls_status # add status code to output
                data['pvalue'][w_where[0]] = pvalue # add p-value to output
                data['nee_std'][w_where[0]] = nee_std # add std dev of nee code to output
                data['ta_std'][w_where[0]] = ta_std # add std dev of ta code to output
        ls_status_list.append(ls_status)
        ls_msg_list.append(ls_msg.replace('\r', ' ').replace('\n', ' '))
        pvalue_list.append(pvalue)
        nee_std_list.append(nee_std)
        ta_std_list.append(ta_std)
#        print '--- jday start: ', jday, ' ---' # TODO: remove
#        print                                  # TODO: remove
    stats = numpy.zeros(len(jday_list), dtype=[('jday', 'i4'), ('rref', FLOAT_PREC), ('e0', FLOAT_PREC), ('rref_se', FLOAT_PREC), ('e0_se', FLOAT_PREC),
                                               ('indices_half', 'i8'), ('indices_first', 'i8'), ('indices_last', 'i8'), ('indices_len', 'i8'), ])

    # write pvalues, std devs for nee and ta, and optimization status (all jday windows)
    ls_status_output = [','.join([str(j) for j in i]) + '\n' for i in zip(jday_all_list, pvalue_list, nee_std_list, ta_std_list, ls_status_list, ls_msg_list)]
    with open(temp_output_filename.format(extra='__nlr_status_PY'), 'w') as g:
        g.writelines(ls_status_output)
    _log.debug("Wrote NLR status per window output: {f}".format(f=ls_status_output))

    # write e0 estimates (only computed windows)
    stats_e0_output = [','.join([str(j) for j in i]) + '\n' for i in zip(jday_list, est_e0_list)]
    with open(temp_output_filename.format(extra='__e0_all_val_PY'), 'w') as g:
        g.writelines(stats_e0_output)

    # write e0_se estimates (only computed windows)
    stats_e0_se_output = [','.join([str(j) for j in i]) + '\n' for i in zip(jday_list, est_e0_se_list)]
    with open(temp_output_filename.format(extra='__e0_all_se_PY'), 'w') as g:
        g.writelines(stats_e0_se_output)


#    # plots of comparisons to pv_wave
#    compare_col_to_pvwave(py_array=numpy.array(est_e0_list), filename=temp_output_filename.format(extra='__e0_val'), diff=True, save_plot=True, show_plot=False, epsilon=0.1)
#    compare_col_to_pvwave(py_array=numpy.array(est_e0_se_list), filename=temp_output_filename.format(extra='__e0_se'), diff=True, save_plot=True, show_plot=False, epsilon=0.1)

    stats['jday'][:] = jday_list
    stats['rref'][:] = est_rref_list
    stats['e0'][:] = est_e0_list
    stats['rref_se'][:] = est_rref_se_list
    stats['e0_se'][:] = est_e0_se_list
    stats['indices_half'][:] = indices_half_list
    stats['indices_first'][:] = indices_first_list
    stats['indices_last'][:] = indices_last_list
    stats['indices_len'][:] = indices_len_list

    _log.debug('Finished windowed/short term paramater optimization')
    #### SECOND OPTIMIZATION FOR 5 DAY STEPS, 14 DAY WINDOWS ######################################
    ###############################################################################################



    ###############################################################################################
    #### FROM RESULTS OF SECOND OPTIMIZATION, DETERMINE BEST RREF/E0 ##############################
    _log.debug('Finding best windowed/short term rref and e0 versions')
    if len(jday_list) > 0:
        max_e0 = (350.0 + 200.0 if tempvar == 'tsoil' else 350.0)
        e0_within_range_mask = (stats['e0'] > 30.0) & (stats['e0'] < max_e0)
        count = numpy.sum(e0_within_range_mask)
        within_range_idx = numpy.where(e0_within_range_mask)[0]
    else:
        count = 0

    if count > 1:
        e0_sorted_idx = numpy.argsort(stats[e0_within_range_mask]['e0_se'])
        e0_sorted_last = (2 if 2 < (len(e0_sorted_idx) - 1) else (len(e0_sorted_idx) - 1))
        e0_selected_idx = within_range_idx[e0_sorted_idx[0:e0_sorted_last + 1]]

        _log.debug("Selected rref values: {r}   --   selected e0 values: {e}   --   selected e0 idx: {i}".format(r=stats[e0_selected_idx]['rref'], e=stats[e0_selected_idx]['e0'], i=e0_selected_idx))

#        print "jday:", jday_list
#        print "stats['e0']", stats['e0']
#        print "stats['e0_se']", stats['e0_se']
#        print "within_range_idx", within_range_idx
#        print "e0_sorted_idx", e0_sorted_idx
#        sys.exit(0)

        # TODO:
        # save: - e0_selected_idx
        #       - stats[e0_selected_idx]['e0']
        #       - stats[e0_selected_idx]['e0_se']

        # write e0_selected estimates, SE, and IDX
        jday_list_selected = list(stats['jday'][e0_selected_idx])
        e0_selected_val_output = [','.join([str(j) for j in i]) + '\n' for i in zip(jday_list_selected, stats[e0_selected_idx]['e0'])]
        with open(temp_output_filename.format(extra='__e0_selected_val_PY'), 'w') as g:
            g.writelines(e0_selected_val_output)

        e0_selected_se_output = [','.join([str(j) for j in i]) + '\n' for i in zip(jday_list_selected, stats[e0_selected_idx]['e0_se'])]
        with open(temp_output_filename.format(extra='__e0_selected_se_PY'), 'w') as g:
            g.writelines(e0_selected_se_output)

        e0_selected_idx_output = [','.join([str(j) for j in i]) + '\n' for i in zip(jday_list_selected, e0_selected_idx)] # not full array idx, just window idx
        with open(temp_output_filename.format(extra='__e0_selected_idx_PY'), 'w') as g:
            g.writelines(e0_selected_idx_output)


        best_rref = numpy.mean(stats[e0_selected_idx]['rref'])
        best_e0 = numpy.mean(stats[e0_selected_idx]['e0'])
        best_rref_se = numpy.mean(stats[e0_selected_idx]['rref_se'])
        best_e0_se = numpy.mean(stats[e0_selected_idx]['e0_se'])

        add_empty_vars(data=data, records=best_rref, column='rref_2_from_tair', unit='umolm-2s-1')
        add_empty_vars(data=data, records=best_rref_se, column='rref_2_se_from_tair', unit='umolm-2s-1')
        add_empty_vars(data=data, records=best_e0, column='e0_2_from_tair', unit='umolm-2s-1')
        add_empty_vars(data=data, records=best_e0_se, column='e0_2_se_from_tair', unit='umolm-2s-1')

        nonnan_tempvar_mask = not_nan(data[tempvar])
        predicted_reco = lloyd_taylor(ta=data[tempvar], rref=best_rref, e0=best_e0)
        predicted_reco[~nonnan_tempvar_mask] = NAN
        add_empty_vars(data=data, records=predicted_reco, column='reco_2e_from_tair', unit='-')
    else:
        _log.error("No short-term relationship using variable {v}".format(v=tempvar))

        add_empty_vars(data=data, records=data['rref_1_from_tair'], column='rref_2_from_tair', unit='umolm-2s-1')
        add_empty_vars(data=data, records=data['e0_1_from_tair'], column='e0_2_from_tair', unit='umolm-2s-1')
        add_empty_vars(data=data, records=NAN, column='rref_2_se_from_tair', unit='umolm-2s-1')
        add_empty_vars(data=data, records=NAN, column='e0_2_se_from_tair', unit='-')
        add_empty_vars(data=data, records=NAN, column='reco_2e_from_tair', unit='-')
    #### FROM RESULTS OF SECOND OPTIMIZATION, DETERMINE BEST RREF/E0 ##############################
    ###############################################################################################



    ###############################################################################################
    #### FROM RESULTS OF SECOND OPTIMIZATION AND BEST RREF/E0, INTERPOLATE AND SMOOTH E0 ##########
    _log.debug('Interpolating and smoothing parameters')

    if len(jday_list) > 0:
        e0_se_within_range_mask = (stats['e0_se'] < 100.0) & ((stats['e0_se'] / stats['e0']) < 0.5) & (stats['e0'] > 50.0) & (stats['e0'] < 450.0)
        count = numpy.sum(e0_se_within_range_mask)
    else:
        count = 0

    if count > 0:
        e0_3 = numpy.zeros(len(data), dtype=FLOAT_PREC)
        e0_3_se = numpy.zeros(len(data), dtype=FLOAT_PREC)
        e0_3[:] = NAN
        e0_3_se[:] = NAN
        e0_3[stats['indices_half'][e0_se_within_range_mask]] = stats['e0'][e0_se_within_range_mask]
        e0_3_se[stats['indices_half'][e0_se_within_range_mask]] = stats['e0_se'][e0_se_within_range_mask]

#        # write e0_3 estimates, SE, and e0_3_idx (only selected windows)
#        jday_list_selected = list(stats['jday'][e0_se_within_range_mask])
#        e0_3_output = [','.join([str(j) for j in i]) + '\n' for i in zip(jday_list_selected, list(e0_3[e0_3 > -9999]))]
#        with open(temp_output_filename.format(extra='__e0_3_val_PY'), 'w') as g:
#            g.writelines(e0_3_output)
#
#        e0_3_se_output = [','.join([str(j) for j in i]) + '\n' for i in zip(jday_list_selected, list(e0_3_se[e0_3 > -9999]))]
#        with open(temp_output_filename.format(extra='__e0_3_se_PY'), 'w') as g:
#            g.writelines(e0_3_se_output)
#
#        e0_3_idx_output = [','.join([str(j) for j in i]) + '\n' for i in zip(jday_list_selected, list(numpy.where(e0_3 > -9999)[0].astype(FLOAT_PREC)))]
#        with open(temp_output_filename.format(extra='__e0_3_idx_PY'), 'w') as g:
#            g.writelines(e0_3_idx_output)

#        # plot comparisons of e0_3 and e0_3 indexes
#        compare_col_to_pvwave(py_array=numpy.where(e0_3 > -9999)[0].astype(FLOAT_PREC), filename=temp_output_filename.format(extra='__e0_3_idx_PW'), diff=True, save_plot=True, show_plot=False, epsilon=0.1)
#        compare_col_to_pvwave(py_array=e0_3[e0_3 > -9999], filename=temp_output_filename.format(extra='__e0_3_val_PW'), diff=True, save_plot=True, show_plot=False, epsilon=0.1)
#        compare_col_to_pvwave(py_array=e0_3_se[e0_3 > -9999], filename=temp_output_filename.format(extra='__e0_3_se_PW'), diff=True, save_plot=True, show_plot=False, epsilon=0.1)

        # compute rref for windows (compute also reco and reco_trim/rob)
        reanalyse_rref(data=data, e0=data['e0_2_from_tair'], tempvar='tair', step=4, moving_window=8)

        # compute gpp and gpp_trim/rob
        # TODO: check on reco_e and gpp_e; needed?
        # gapfilled
        data['gpp_2'] = NAN
        data['gpp_2rob'] = NAN
        data['gpp_2e'] = NAN

        mask = not_nan(data['nee_f']) & not_nan(data['reco_2'])
        data['gpp_2'][mask] = -data['nee_f'][mask] + data['reco_2'][mask]

        mask = not_nan(data['nee_f']) & not_nan(data['reco_2rob'])
        data['gpp_2rob'][mask] = -data['nee_f'][mask] + data['reco_2rob'][mask]

        mask = not_nan(data['nee_f']) & not_nan(data['reco_2e_from_tair'])
        data['gpp_2e'][mask] = -data['nee_f'][mask] + data['reco_2e_from_tair'][mask]

        # non-gapfilled
        data['gpp_2_nongf'] = NAN
        data['gpp_2rob_nongf'] = NAN
        data['gpp_2e_nongf'] = NAN

        mask = not_nan(data['nee']) & not_nan(data['reco_2'])
        data['gpp_2'][mask] = -data['nee'][mask] + data['reco_2'][mask]

        mask = not_nan(data['nee']) & not_nan(data['reco_2rob'])
        data['gpp_2rob'][mask] = -data['nee'][mask] + data['reco_2rob'][mask]

        mask = not_nan(data['nee']) & not_nan(data['reco_2e_from_tair'])
        data['gpp_2e'][mask] = -data['nee'][mask] + data['reco_2e_from_tair'][mask]

    #### FROM RESULTS OF SECOND OPTIMIZATION AND BEST RREF/E0, INTERPOLATE AND SMOOTH E0 ##########
    ###############################################################################################


    result = data

    _log.debug('Finished NT flux partition main function')
    return result

def reanalyse_rref(data, e0, tempvar='tair', step=4, moving_window=8):
    """
    Estimates reference respiration (rref) values based on fixed
    temperature sensitivity value (e0)  

    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param e0: single value or array of values for e0
    :type e0: float or numpy.ndarray
    :param tempvar: temperature variable to be used (soil or air)
    :type tempvar: str
    :param step: step for each iteration (in days)
    :type step: int
    :param moving_window: window size for each iteration (in days)
    :type moving_window: int
    """
    julday = data['julday'] + (data['hr'] / 24.0)

    # if float or numpy.ndarray, initiallizes e0_array
    e0_array = numpy.zeros(data.size, dtype=FLOAT_PREC)
    e0_array[:] = e0

    # initializes output arrays
    data['rrefoptord'] = NAN
    data['rrefoptord_se'] = NAN
    data['rrefopttrim'] = NAN
    data['rrefopttrim_se'] = NAN

    # compute and iterate over integer day-of-year
    julday_int = (julday + 0.5).astype('i8')
    for j in range(1, int(julday[-1]), step):
        mask = (julday_int >= j) & (julday_int < (j + moving_window)) & (data[tempvar] > -1000.) & (data['neenight'] > -1000.)
        idx = numpy.where(mask)[0]
        count = numpy.sum(mask)

        if count > 2:
            mask2 = (julday_int >= j) & (julday_int < (j + moving_window))
            idx2 = numpy.where(mask2)[0]
            count2 = numpy.sum(mask2)
            #mid = idx2[count2 / 2] # unused step (?)
            mid = int(numpy.average(idx))
            e0_average = numpy.average(e0_array[mask])
            tair_average = numpy.average(data[tempvar][mask])
            reco_average = numpy.average(data['neenight'][mask])
            lloyd_fac = lloyd_taylor(ta=data[tempvar][mask], rref=1.0, e0=e0_average)

            parameters, std_devs, ls_status, ls_msg, residuals, covariance_matrix = least_squares(func=lambda b: ((b * lloyd_fac - data['neenight'][mask]) ** 2).sum(),
                                                                                                  initial_guess=(0.1,),
                                                                                                  entries=len(data['neenight'][mask]),
                                                                                                  iterations=1000 * (len(data['neenight'][mask]) + 1),
                                                                                                  return_residuals_cov_mat=True)

            # oktrim = where(abs(NEENight(ok) - recoAvg) LT pct(abs(NEENight(ok) - recoAvg), 95.) )
            mask_trim = numpy.absolute(data['neenight'][mask] - reco_average) < pct(array=numpy.absolute(data['neenight'][mask] - reco_average), percent=95.0)
            idx_trim = numpy.where(mask_trim)[0]
            parameters_trim, std_devs_trim, ls_status_trim, ls_msg_trim, residuals_trim, covariance_matrix_trim = least_squares(func=lambda b: ((b * lloyd_fac[mask_trim] - data['neenight'][mask][mask_trim]) ** 2).sum(),
                                                                                                                                initial_guess=(0.1,),
                                                                                                                                entries=len(data['neenight'][mask][mask_trim]),
                                                                                                                                iterations=1000 * (len(data['neenight'][mask][mask_trim]) + 1),
                                                                                                                                return_residuals_cov_mat=True)

            # assign calculated rref and rref se, non-trimmed and trimmed, to mid point timestamp
            # also replaces assign_empty_vars calls
            # TODO: compute correct values of SEs (maybe single variable least_squares optimization works differently?)
            data['rrefoptord'][mid] = (parameters[0] if parameters[0] > 1e-6 else 1e-6)
            data['rrefoptord_se'][mid] = numpy.sqrt(std_devs[0])
            data['rrefopttrim'][mid] = (parameters_trim[0] if parameters_trim[0] > 1e-6 else 1e-6)
            data['rrefopttrim_se'][mid] = numpy.sqrt(std_devs_trim[0])

    # start interpolation of all computed variables
    ipolmiss(data=data, variable='rrefoptord')
    ipolmiss(data=data, variable='rrefoptord_se')
    ipolmiss(data=data, variable='rrefopttrim')
    ipolmiss(data=data, variable='rrefopttrim_se')

    # compute reco from current e0 and new rref, non-trimmed and trimmed (uses gap-filled temperature)
    data['reco_2'] = lloyd_taylor(ta=data[tempvar + '_f'], rref=data['rrefoptord'], e0=e0)
    data['reco_2rob'] = lloyd_taylor(ta=data[tempvar + '_f'], rref=data['rrefopttrim'], e0=e0)



def ipolmiss(data, variable):
    """
    Interpolates missing values in data for variable
    (changes data object directly)  

    Note: original code allowed multiple variables to be interpolated
          in a single call to ipolmiss, but only used as a single variable
          at a time; this implementation assumes single variable for
          each call
    
    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param variable: variable to be interpolated
    :type variable: str
    """
    _log.debug("Interpolating variable '{v}'".format(v=variable))

    #order = 2 # always 2 in all calls from original code; means linear interpolation
    method = 'Exact' # always 'Exact' from original code

    if not isinstance(data, numpy.ndarray):
        msg = "ipolmiss ({v}) data object is not ndarray: '{d}'".format(v=variable, d=str(data))
        _log.critical(msg)
        raise ONEFluxError(msg)

    if variable not in data.dtype.names:
        msg = "ipolmiss ({v}) label not in data object".format(v=variable)
        _log.critical(msg)
        raise ONEFluxError(msg)

    mask = not_nan(data[variable])
    count = numpy.sum(mask)

    if (count > 1) and ((count < data.size) or (method == 'LSQ')):
        idx = numpy.where(mask)[0]
        julday = data['julday'] + (data['hr'] / 24.0)
        duration = [i - julday[mask][0] for i in julday[mask]]

        if count < 6:
            _log.error("ipolmiss ({v}) too few elements: {c}".format(v=variable, c=count))

        # create interpolation function
        sp_interp_function = interp1d(duration, data[variable][mask], kind='linear', bounds_error=False, fill_value=numpy.NaN)

        # apply interpolation function to full extent of dataset
        duration_full = [i - julday[mask][0] for i in julday]
        data[variable][:] = sp_interp_function(duration_full)

        # set beginning/end gaps into first/last valid value
        data[variable][:idx[0]] = data[variable][idx[0]]
        data[variable][idx[-1] + 1:] = data[variable][idx[-1]]




def ipolmiss_vector(array, order, exact=True):
    """
    Interpolates array
    (TODO: finish implementation; not used in main branch of processing code) 
    
    :param array: array to be interpolated
    :type array: numpy.ndarray (1D)
    :param order: order of polinomial to be used
    :type order: int
    :param exact: if True, spline interpolation, if False, spline least-squares interpolation
    :type exact: bool
    """
    return
    # TODO: implement and test (not used for main nighttime partitioning variables
#    print
#    print array
    all_indices = numpy.arange(len(array))
    nonnan_mask = not_nan(array)
    nonnan_idx = numpy.where(nonnan_mask)[0]
    if numpy.sum(nonnan_mask) == 0: # all NAN, return all NAN
        return array
    if numpy.sum(nonnan_mask) == 1: # only one non-NAN, return non-NAN value for all elements
        return (array * 0.0) + array(nonnan_mask)[0]

    if exact:
        # order for splrep is one less than for PV-Wave bsinterp
        spline = splrep(x=nonnan_idx, y=array[nonnan_mask], k=(5 if order > 6 else order - 1))
    else:
        # TODO: confirm t=[order] is correct
        weights = numpy.ones(len(nonnan_idx))
        spline = splrep(x=nonnan_idx, y=array[nonnan_mask], w=weights, k=(5 if order > 6 else order - 1), task=-1)
#        print
#        print spline
#        sys.exit('EXIT')

    # apply spline
    ipol_vect = splev(x=all_indices, tck=spline)
    #first and last non-NAs propagated to head/tail of NAs
    ipol_vect[:nonnan_idx[0]] = ipol_vect[nonnan_idx[0]]
    ipol_vect[nonnan_idx[-1]:] = ipol_vect[nonnan_idx[-1]]

    return ipol_vect



BR_PERC = 10.0
def nlinlts1(data, func=lloyd_taylor, depvar='neenight', indepvar='tair', npara=2, xguess=[2.0, 200.0], trim_perc=BR_PERC):
    """
    Main non-linear least-squares driver function
    
    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param func: function to be optimized
    :type func: function
    :param depvar: dependent variable (computed by function)
    :type depvar: str
    :param indepvar: independent variable (parameter to function)
    :type indepvar: str
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
    nonnan_indep_mask = not_nan(data[indepvar])
    if numpy.sum(nonnan_indep_mask) < (npara * 3):
        _log.warning("Not enough data points (independent variable filtered) for optimization: {n}".format(n=numpy.sum(nonnan_indep_mask)))
        status = -1
        return status, -9999.0, -9999.0, -9999.0, -9999.0, None, None, None, None, None, None, None

    # check number of entries for dependent AND independent variable
    nonnan_dep_mask = not_nan(data[depvar])
    nonnan_combined_mask = nonnan_indep_mask & nonnan_dep_mask
    if numpy.sum(nonnan_combined_mask) < (npara * 3):
        _log.warning("Not enough data points (dependent and independent variable filtered) for optimization: {n}".format(n=numpy.sum(nonnan_combined_mask)))
        status = -1
        return status, -9999.0, -9999.0, -9999.0, -9999.0, None, None, None, None, None, None, None

    # "clean" dependent variable so not to use NAs from independent variable
    clean_dep = data[depvar].copy()
    clean_dep[~nonnan_indep_mask] = NAN

#    print
#    print 'NEE:'
#    print clean_dep
#    print
#    print 'TA:'
#    print data[indepvar]
#    print
#    # TODO: remove

    # define inner function to be used for optimization
    def trimmed_residuals(par, nee=clean_dep, temp=data[indepvar], trim_perc=trim_perc):
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
        rref, e0 = par
        prediction = lloyd_taylor(ta=temp, rref=rref, e0=e0)
        residuals = nee - prediction
        nonnan_nee_mask = not_nan(nee)
        residuals[~nonnan_nee_mask] = 0.0

        # NOTE: compareIndex and compindex not used in NT partitioning code

        if trim_perc == 0.0:
            return residuals

        absolute_residuals = numpy.abs(residuals)
        pct_calc = pct(absolute_residuals, 100.0 - trim_perc)
        trim_mask = (absolute_residuals > pct_calc)
        residuals[trim_mask] = 0.0

#        print 'rref/e0/res:', rref, e0, numpy.sum(residuals ** 2)

        return residuals

    parameters, std_devs, ls_status, ls_msg, residuals, covariance_matrix = least_squares(func=trimmed_residuals,
                                                                                          initial_guess=xguess,
                                                                                          entries=len(clean_dep),
                                                                                          iterations=1000 * (len(clean_dep) + 1),
                                                                                          return_residuals_cov_mat=True)
    est_rref, est_e0 = parameters
    est_rref_std, est_e0_std = std_devs

    tvalue, pvalue = ttest_ind(clean_dep, lloyd_taylor(ta=data[indepvar], rref=est_rref, e0=est_e0))
    fvalue, f_pvalue = f_oneway(clean_dep, lloyd_taylor(ta=data[indepvar], rref=est_rref, e0=est_e0))
    nee_std, ta_std = numpy.nanstd(clean_dep), numpy.nanstd(data[indepvar])

#    print "rref:", est_rref
#    print "rref_se:", est_rref_std
#    print "e0:", est_e0
#    print "e0_se:", est_e0_std
#    print "p-value:", pvalue, tvalue
#    print "p-value (f):", f_pvalue, fvalue
#    print
#    # TODO: remove

#    _log.debug("Finished optimization step for period '{ts1}' - '{ts2}'  -  parameters rref: {r} ({rs}), e0: {e} ({es})*********".format(ts1=first_ts.strftime('%Y-%m-%d %H:%M'),
#                                                                                                                                         ts2=last_ts.strftime('%Y-%m-%d %H:%M'),
#                                                                                                                                         r=est_rref, e=est_e0,
#                                                                                                                                         rs=est_rref_std, es=est_e0_std))

    # NOTE: calculation of residuals in the original code used only for graph, so not added here

    # add zeros to residuals, if lenght of residuals less than maximum number of entries for window
    # done to match original code, purpose unclear
    if len(residuals) < 48 * WINDOW_SIZE:
        new_residuals = numpy.zeros(48 * WINDOW_SIZE, dtype=FLOAT_PREC)
        new_residuals[:len(residuals)] = residuals
    else:
        new_residuals = residuals

    # NOTE: if changing return values, also update case for "not enough data points"
    return status, est_rref, est_e0, est_rref_std, est_e0_std, new_residuals, covariance_matrix, ls_status, ls_msg, pvalue, nee_std, ta_std



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
    pars, cov_x, info, msg, success = leastsq(func=func, x0=initial_guess, full_output=True, maxfev=iterations, factor=STEP_BOUND_FACTOR)

    if success != 1:# and (info['nfev'] == iterations):
        if info['nfev'] >= iterations:
            if not stop:
                _log.warning("No convergence (code '{p}'), retrying ({r}-fold limit increase). Least squares message: [[{m}]]".format(p=success, r=NO_CONVERGENCE_RETRY, m=msg.replace('\r', ' ').replace('\n', ' ')))
                return least_squares(func=func, initial_guess=initial_guess, entries=entries, iterations=iterations * NO_CONVERGENCE_RETRY, stop=True, return_residuals_cov_mat=return_residuals_cov_mat)
            else:
                _log.warning("No convergence (code '{p}'), stopping. Least squares message: [[{m}]]".format(p=success, m=msg.replace('\r', ' ').replace('\n', ' ')))
        else:
            _log.debug("Unclean minimization (code '{p}'). Least squares message: [[{m}]]".format(p=success, m=msg.replace('\r', ' ').replace('\n', ' ')))

    # from residuals, get covariance matrix, then variances, then standard deviations
    residuals = info['fvec']
    if entries > len(initial_guess) and cov_x is not None:
        s_squared = (residuals ** 2).sum() / (entries - len(initial_guess))
        cov_matrix = cov_x * s_squared
        variances = [cov_matrix[i][i] for i in range(len(cov_matrix))]
        std_devs = [numpy.sqrt(i) for i in variances]
    else:
        std_devs = [numpy.nan] * len(initial_guess)
        cov_matrix = None

    if return_residuals_cov_mat:
        return (pars, std_devs, success, msg, residuals, cov_matrix)
    else:
        return (pars, std_devs)



def compu(data, func, columns, parameters={}, skip_if_present=False, no_missing=False, new_=False):
    """
    Computes function on columns [1:] of data array, assigning result to first column [0]
    Uses actual functions and not text expressions as in the original PV-Wave code
    
    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param func: function to be called with parameters from column
    :type func: function
    :param columns: list of columns from data array to be used as target and parameters
    :type columns: list (of str)
    :param parameters: dictionary of parameters to be used
    :type parameters: dict
    :param skip_if_present: (optional) if parameter present and variable found, returns without doing anything (NOT USED HERE)
    :type  skip_if_present: bool
    :param no_missing: if parameter True, uses all records, not only non-NAN
    :type no_missing: bool
    :param new_: if parameter False and variable found, removes old variable(s) and returns (NOT USED HERE)
    :type new_: bool
    """

    # check columns and prepare parameters for function
    varnum(data=data, columns=columns)

    # **parameters will convert dictionary into proper parameter list
    if no_missing:
        # extract columns to be used as parameters
        ext_parameters = {col:data[col] for col in columns[1:]}
        ext_parameters.update(parameters)
        data[columns[0]][:] = func(data=data, **ext_parameters)
    else:
        nonnan_data, nonnan_mask, nan_mask = nomi(data=data, columns=columns[1:])
        # extract columns to be used as parameters
        ext_parameters = {col:nonnan_data[col] for col in columns[1:]}
        ext_parameters.update(parameters)
        data[columns[0]][nonnan_mask] = func(data=nonnan_data, **ext_parameters)
        data[columns[0]][nan_mask] = NAN
#        print nonnan_data.size, numpy.sum(nonnan_mask), numpy.sum(nan_mask)
    _log.debug("Computed function '{f}' over ({n}) parameters '{p}' and storing results in column '{c}'".format(f=func.__name__, p=columns[1:], n=len(columns[1:]), c=columns[0]))


def get_first_last_ts(data):
    """
    Retrieves datetime objects for first and last timestamps in data structure for partitioning

    :param data: data structure
    :type data: numpy.ndarray
    """
    first_ts = datetime(int(data['year'][0]), int(data['month'][0]), int(data['day'][0]), int(data['hour'][0]), int(data['minute'][0]))
    last_ts = datetime(int(data['year'][-1]), int(data['month'][-1]), int(data['day'][-1]), int(data['hour'][-1]), int(data['minute'][-1]))
    return first_ts, last_ts



if __name__ == '__main__':
    raise ONEFluxError('Not executable')
