'''
oneflux.partition.daytime

For license information:
see LICENSE file or headers in oneflux.__init__.py 

From scratch implementation from PV-Wave cleaned-up code, daytime method

@author: Gilberto Pastorello and Abdelrahman Elbashandy 
@contact: gzpastorello@lbl.gov & aaelbashandy@lbl.gov
@date: 2017-05-22
'''
import os
import sys
import logging
import numpy

from statsmodels import robust
from datetime import datetime, timedelta
from scipy.optimize import leastsq
from scipy import stats
from scipy.interpolate import splev, splrep, interp1d, LSQUnivariateSpline

from oneflux import ONEFluxError

from oneflux.partition.compu import compu_qcnee_filter, compu_daylight, compu_daylight_zero, compu_sunrise, compu_sunset, compu_nee_night
from oneflux.partition.ecogeo import lloyd_taylor_dt, gpp_vpd
from oneflux.partition.auxiliary import compare_col_to_pvwave, FLOAT_PREC, DOUBLE_PREC, NAN, NAN_TEST, nan, not_nan
from oneflux.partition.library import QC_AUTO_DIR, METEO_PROC_DIR, NEE_PROC_DIR, DT_OUTPUT_DIR, HEADER_SEPARATOR, EXTRA_FILENAME, DT_STR
from oneflux.partition.library import load_output, get_latitude, add_empty_vars, create_data_structures, nomi, newselif, nlinlts2, check_parameters, remove_errored_entries, jacobian, ONEFluxPartitionError
from oneflux.utils.files import check_create_directory
from oneflux.utils.helper_fns import islessthan

from oneflux.graph.compare import plot_comparison

_log = logging.getLogger(__name__)

PARAM_DTYPE = [
        ('year', 'i4'),
        ('i', 'i4'),
        ('day', 'i4'),
        ('i_ok', 'i4'),
        ('ind_begin', 'i4'),
        ('ind_end', 'i4'),
        ('subset_size', 'i4'),
        ('nee_avg', 'f4'),
        ('nee_std', 'f4'),
        ('ta_avg', 'f4'),
        ('ta_std', 'f4'),
        ('rg_avg', 'f4'),
        ('rg_std', 'f4'),
        ('alpha', 'f4'),
        ('beta', 'f4'),
        ('k', 'f4'),
        ('rref', 'f4'),
        ('e0', 'f4')
    ]

class ONEFluxPartitionBrokenOptError(ONEFluxPartitionError):
    """
    Pipeline ONEFlux error - Partitioning specific - DT optimization fail
    
    """
    def __init__(self, message, site_id=None, year=None, day_begin=None, day_end=None, prod=None, perc=None):

        if (site_id is None) or (year is None) or (day_begin is None) or (day_end is None) or (prod is None) or (perc is None):
            msg = 'ONEFluxPartitionBrokenOptError exception called with incomplete parameters: '
            msg += 'siteid: {s}, percentile: {perc}, product: {prod}, year: {year}, day_begin: {b}, day_end: {e}'.format(s=site_id, b=day_begin, e=day_end, perc=perc, prod=prod, year=year)
            raise ONEFluxPartitionError(msg)

        self.site_id = site_id
        self.year = year
        self.day_begin = day_begin
        self.day_end = day_end
        self.prod = prod
        self.perc = perc

        line2add = '{s}_{year}_{prod},{b:.0f},{e:.0f}'.format(s=site_id, b=day_begin, e=day_end, prod=prod, year=year)
        self.line2add = line2add

        msg = 'Broken DT optimization, {m}'.format(m=message)
        msg += ' for {s}, percentile {perc}, product {prod}, year {year}, at window {b}-{e}.'.format(s=site_id, b=day_begin, e=day_end, perc=perc, prod=prod, year=year)
        msg += ' LINE-TO-ADD: {line}'.format(line=line2add)
        super(ONEFluxPartitionBrokenOptError, self).__init__(msg)


def partitioning_dt(datadir, siteid, sitedir, prod_to_compare, perc_to_compare, years_to_compare):
    """
    DT partitioning wrapper function.
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

    _log.info("Started DT partitioning of {s}".format(s=siteid))

    sitedir_full = os.path.join(datadir, sitedir)
    qc_auto_dir = os.path.join(sitedir_full, QC_AUTO_DIR)
    meteo_proc_dir = os.path.join(sitedir_full, METEO_PROC_DIR)
    nee_proc_dir = os.path.join(sitedir_full, NEE_PROC_DIR)
    dt_output_dir = os.path.join(sitedir_full, DT_OUTPUT_DIR)

    # reformat percentiles to compare into data column labels
    percentiles_data_columns = [i.replace('.', HEADER_SEPARATOR) for i in perc_to_compare]

    # check and create output dir if needed
    if os.path.isdir(sitedir_full) and not os.path.isdir(dt_output_dir):
        check_create_directory(directory=dt_output_dir)

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
                output_filename = os.path.join(dt_output_dir, "nee_{t}_{p}_{s}_{y}{extra}.csv".format(t=ustar_type, p=percentile_print, s=siteid, y=year, extra=EXTRA_FILENAME))
                temp_output_filename = os.path.join(dt_output_dir, "nee_{t}_{p}_{s}_{y}{extra}.csv".format(t=ustar_type, p=percentile_print, s=siteid, y=year, extra='{extra}'))
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

                #### Get a cleaned-up organized numpy version of the data
                working_year_data = create_data_structures(ustar_type=ustar_type, whole_dataset_nee=whole_dataset_nee, whole_dataset_meteo=whole_dataset_meteo,
                                                           percentile=percentile, year_mask_nee=year_mask_nee, year_mask_meteo=year_mask_meteo, latitude=latitude, part_type=DT_STR)

                #### Remove entries that fall into specified error-ranges
                working_year_data = remove_errored_entries(ustar_type=ustar_type, site=siteid, site_dir=sitedir_full, year=year, working_year_data=working_year_data)

                name_out = str(siteid) + "_" + str(year) + "_" + str(ustar_type)

                name_file = "nee_" + str(ustar_type) + "_" + str(percentile) + "_" + str(siteid) + "_" + str(year)

                #### call flux_part_gl2010 for day time (main partitioning process)
                result_year_data = flux_part_gl2010(data=working_year_data, name_file=name_file, name_out=name_out, dt_output_dir=dt_output_dir, site_id=siteid, ustar_type=ustar_type, percentile_num=percentile, year=year)

                if result_year_data is None:
                    _log.error("Error processing output file '{f}".format(f=output_filename))
                else:
                    # save output data file
                    _log.debug("Saving output file '{f}".format(f=output_filename))
                    numpy.savetxt(fname=output_filename, X=result_year_data, delimiter=',', fmt='%s', header=','.join(result_year_data.dtype.names), comments='')
                    _log.debug("Saved output file '{f}".format(f=output_filename))

                _log.info("Finished processing percentile '{p}'".format(p=percentile))
            _log.info("Finished processing year '{y}'".format(y=year))
        _log.info("Finished processing UStar threshold type '{u}'".format(u=ustar_type))
    _log.info("Finished DT partitioning of {s}".format(s=siteid))


def flux_part_gl2010(data, name_file, name_out, dt_output_dir, site_id, ustar_type, percentile_num, year):
    """

    :Task:  Main flux partitioning function (for day time)

    :Explanation:   This is the main function that handles the main processing
                    of the data. 
                    
                    - We handle filling tha gaps in the 'NEE' variable using
                    'uncert_via_gapFill'.
                    - Call estimate_params to get the best parameters or weights
                    to get the most suitable model.
                    - Call compute_flux to calculate the Reco and GPP variables.


    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param name_file: conventional leading name to be added to beginneing ofeach file generated
    :type name_file: string
    :param name_out: name for output file
    :type name_out: string
    :param dt_output_dir: data structure for partitioning
    :type dt_output_dir: numpy.ndarray
    :param site_id: Site id
    :type site_id: string
    :param ustar_type: ustar type (y or c)
    :type ustar_type: string
    :param percentile_num: percentile number
    :type percentile_num: string
    :param year: year being processed
    :type year: int
    """
    _log.info("Starting flux_part_gl2010 for daytime for nee_{u}_{p}_{s}_{y}".format(u=ustar_type, p=percentile_num, s=site_id, y=year))

    add_empty_vars(data=data, records=data['vpd'], column='vpd_f', unit='-')

    h_data = numpy.copy(data)

    # initiating defaults for both the gap filling and optimization (estimate_params) functions
    #################################################
    max_miss_frac = 0.4
    winsize = 4
    trimperc = 0.0
    fguess = [0.01, 30.0, 0.0, 5.0, 100.0]
    #################################################

    n_data = h_data.shape[0]

    # Imaginary step to drop specific column names. Remove anything that ends with 'unc'
    # drop(data, '##unc')

    #print(data.dtype.names)
    #print("----------")
    #print("\n".join(s for s in data.dtype.names if "day".lower() in s.lower()))

    #compare_results_pv_py(py_data=h_data, pvwave_file_path='../test_before_uncert_gapfill.csv', var='NEE')

    # Compute uncertainties via gap filling
    uncert_via_gapFill(data=h_data, var='NEE'.lower(), nomsg=True, maxMissFrac=1.0)

    #pvwave_file_path = '../test_after_uncert_gapfill.csv'
    #file_basename = 'after_gapfill_1999_y'
    #compare_results_pv_py(py_data=h_data, pvwave_file_path=pvwave_file_path, var='NEE_f_unc', file_basename=file_basename, save_csv=True, show_diff_index=True, show_diff_thresh=0.01)
    #compare_results_pv_py(py_data=h_data, pvwave_file_path=pvwave_file_path, var='NEE_fmet_unc', file_basename=file_basename, save_csv=True, show_diff_index=True, show_diff_thresh=0.01)
    #compare_results_pv_py(py_data=h_data, pvwave_file_path=pvwave_file_path, var='NEE_fwin_unc', file_basename=file_basename, save_csv=True, show_diff_index=True, show_diff_thresh=0.01)
    #compare_results_pv_py(py_data=h_data, pvwave_file_path=pvwave_file_path, var='NEE_fn_unc', file_basename=file_basename, save_csv=True, show_diff_index=True, show_diff_thresh=0.01)
    #compare_results_pv_py(py_data=h_data, pvwave_file_path=pvwave_file_path, var='NEE_fs_unc', file_basename=file_basename, save_csv=True, show_diff_index=True, show_diff_thresh=0.01)
    #compare_results_pv_py(py_data=h_data, pvwave_file_path=pvwave_file_path, var='NEE_fsrob_unc', file_basename=file_basename, save_csv=True, show_diff_index=True, show_diff_thresh=0.01)
    #compare_results_pv_py(py_data=h_data, pvwave_file_path=pvwave_file_path, var='NEE_fmed_unc', file_basename=file_basename, save_csv=True, show_diff_index=True, show_diff_thresh=0.01)
    #compare_results_pv_py(py_data=h_data, pvwave_file_path=pvwave_file_path, var='NEE_fqc_unc', file_basename=file_basename, save_csv=True, show_diff_index=True, show_diff_thresh=0.01)
    #compare_results_pv_py(py_data=h_data, pvwave_file_path=pvwave_file_path, var='NEE_fqcOK_unc', file_basename=file_basename, save_csv=True, show_diff_index=True, show_diff_thresh=0.01)

    ind = numpy.arange(n_data)
    add_empty_vars(data=h_data, records=ind, column=str("ind"))

    NEE_fqcok = (h_data['nee_f'] > -999).astype(int) * h_data['nee_fqcok']
    add_empty_vars(data=h_data, records=NEE_fqcok, column=str("nee_fqcok"))

    #### Calling estimate_parasets to get the best model for
    #### the NEE data
    params, whichmodel, JTJ_inv, res_cor, p_correl_return = estimate_parasets(data=h_data, winsize=winsize, fguess=fguess, trimperc=trimperc, name_out=name_out, dt_output_dir=dt_output_dir, site_id=site_id, ustar_type=ustar_type, percentile_num=percentile_num, year=year)

    paramsOK = numpy.where(params == -9999)


#    print("paramsOK")
#    print(paramsOK)
#    print("paramsOK")
#    print(paramsOK[1] * paramsOK[0] + paramsOK[0])
#    print("params.size")
#    print(params.size)


    if len(paramsOK[0]) == params.size:
        return

    #### Calling compute_flux to calculate the Reco and GPP variables
    reco_flux, gpp_flux, pf_flux1, pf_flux2 = compute_flux(data=h_data, params=params, dt_output_dir=dt_output_dir, site_id=site_id, ustar_type=ustar_type, percentile_num=percentile_num, year=year)

    #### Calling compute_var to get the predicted variable by specifying
    #### the model we used in estimate_params
    varGPP = compute_var(data=h_data, params=params, whichmodel=whichmodel, JTJ_inv=JTJ_inv, res_cor=res_cor)

    #print("flux")
    #print(flux)
    #print("varGPP")
    #print(varGPP)

    if reco_flux.size == 0 or gpp_flux.size == 0:
        return

    i_se = numpy.isnan(pf_flux1)
    j_se = numpy.isinf(pf_flux1)

    pf_flux1[i_se] = NAN
    pf_flux1[j_se] = NAN

    add_empty_vars(data=h_data, records=reco_flux, column='reco_hblr')
    add_empty_vars(data=h_data, records=gpp_flux, column='gpp_hblr')

    #### Check if predicted model has values
    if varGPP.size == 0:
        h_data['se_gpp_hblr'] = NAN
    else:
        add_empty_vars(data=h_data, records=numpy.sqrt(varGPP), column='se_gpp_hblr')

    nee = reco_flux - gpp_flux
    add_empty_vars(data=h_data, records=nee, column='nee_hblr')
    add_empty_vars(data=h_data, records=pf_flux1, column='p_flag1')
    add_empty_vars(data=h_data, records=pf_flux2, column='p_flag2')

    index = params[12, :]
    '''
    print("index")
    print(index)
    '''
    h_data['rb'][index.astype(int)] = params[3, :]
    h_data['beta'][index.astype(int)] = params[1, :]
    h_data['k'][index.astype(int)] = params[2, :]
    h_data['e0'][params[10, :].astype(int)] = params[4, :]
    h_data['alpha'][params[11, :].astype(int)] = params[0, :]

    h_data['flag_sum'] = pf_flux1 + pf_flux2

    _log.info("Finished flux_part_gl2010 of daytime for nee_{u}_{p}_{s}_{y}".format(u=ustar_type, p=percentile_num, s=site_id, y=year))

    return h_data


def compute_flux(data, params, dt_output_dir, site_id, ustar_type, percentile_num, year):
    """
    :Task:  This function is responsible to calculate the Reco and GPP values

    :Explanation:   We iterate over the "okay" parameters we got from estimate_params.
                    Then we get the data in each window while keeping in mind
                    the position of each window. i.e we handle the data of
                    the first window and the last window. We're trying to 
                    figure out the range we're covering within each window.
                    In params, we saved the value day_begin of each window in the 
                    the last column. That's why we're linking params[n_params - 1, ...].
                    "day_begin" of the last window to the "day_begin" of the next
                    window; and that's the range we're covering.

                    Lets keep in mind that these are only the "okay" parameters,
                    so if a specific window was "not-okay", then we might be connecting
                    a larger ranged window with the algorithm mentioned. For example,
                    if the previous day_begin window was at 100 and each window size is 
                    100, and there are no "not-okay" windows, then we are covering
                    the range from data-point 100 to data-point 200. But if there were
                    "not-okay" windows, then we might see a window with a range from
                    data-point 100 to data-point 300, as the window at data-point 200
                    is "not-okay".

                    Finally, we iterate over each data-point "j" in the whole dataset.
                    i.e j could represent around 17,000 data points. For each 
                    data-point "j", there could be up to two windows that have 
                    covered this data-point "j", as the windows are overlapped. 
                    So we check how many windows have covered it. If there are two 
                    windows covering this data-point "j", then we are going
                    to assign weights to each window and multiply the Reco and GPP
                    values we got previously with it's assigned weight. We get the
                    final Reco and GPP values by adding the multiplied values together.
                    If there is only one window covering this data-point "j", then
                    we are going to assign the final Reco and GPP values to the 
                    previously calculated Reco and GPP.


    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param params: The most suitable "okay" parameters we got from estimate_params ("params_ok")
    :type params: numpy.ndarray
    :param dt_output_dir: data structure for partitioning
    :type dt_output_dir: numpy.ndarray
    :param site_id: Site id
    :type site_id: string
    :param ustar_type: ustar type (y or c)
    :type ustar_type: string
    :param percentile_num: percentile number
    :type percentile_num: string
    :param year: year being processed
    :type year: int
    """
    _log.info("Starting compute_flux of daytime for nee_{u}_{p}_{s}_{y}".format(u=ustar_type, p=percentile_num, s=site_id, y=year))
    filename_range = 'nee_' + ustar_type + '_' + str(percentile_num) + '_' + site_id + '_' + str(year) + '_params_after_es_python.csv'

    n_params = len(params[:, 0])
    n_parasets = len(params[0, :])
    n_set = len(data['nee_f'])
    Reco_mat = numpy.empty((n_parasets, n_set))
    Reco_mat.fill(NAN)
    Reco = numpy.zeros(n_set, dtype=FLOAT_PREC)
    GPP_mat = numpy.empty((n_parasets, n_set))
    GPP_mat.fill(NAN)
    GPP = numpy.zeros(n_set, dtype=FLOAT_PREC)
    partition_flag1 = numpy.zeros(n_set, dtype=FLOAT_PREC)
    partition_flag2 = numpy.zeros(n_set, dtype=FLOAT_PREC)

    reco_gpp_orig = numpy.zeros((10, n_set), dtype=FLOAT_PREC)

    '''
    print("n_params")
    print(n_params)
    print("n_parasets")
    print(n_parasets)
    print("n_set")
    print(n_set)
    '''

    #### We iterate over the "okay" parameters we got from estimate_params
    for i in range(n_parasets):
        sub = None

        #### Getting the data in each window while keeping in mind
        #### the position of each window. i.e we handle the data of
        #### the first window and the last window.
        if i == 0:
            ind_begin = 0
            ind_end = params[n_params - 1, i + 1]
            sub_mask = ((data['ind'] >= ind_begin) & (data['ind'] < ind_end))
            sub, _, _ = newselif(data=data, condition=sub_mask, drop=True)
        elif i == (n_parasets - 1):
            ind_begin = params[n_params - 1, i - 1]
            ind_end = numpy.max(data['ind'])
            sub_mask = ((data['ind'] >= ind_begin) & (data['ind'] <= ind_end))
            sub, _, _ = newselif(data=data, condition=sub_mask, drop=True)
        else:
            ind_begin = params[n_params - 1, i - 1]
            ind_end = params[n_params - 1, i + 1]
            sub_mask = ((data['ind'] >= ind_begin) & (data['ind'] < ind_end))
            sub, _, _ = newselif(data=data, condition=sub_mask, drop=True)

            '''
            #if i == 15:
            if i >= 13 and i <= 24:
                print("i")
                print(i)
                print("ind_begin")
                print(ind_begin)
                print("ind_end")
                print(ind_end)
                print("rref")
                print(params[3, i])
                print("e0")
                print(params[4, i])
                print("sub['tair_f'].size")
                print(sub['tair_f'].size)
                #if i == 24:
                #    exit()
            '''

        #### We apply the best parameters we got on the right model
        #### functions to estimate the Reco and GPP. We do this by fitting
        #### the right paramters, applied at the data in each window.
        Reco_mat[i, sub['ind'].astype(int)] = lloyd_taylor_dt(ta_f=sub['tair_f'], parameter=params[3:4 + 1, i])
        GPP_mat[i, sub['ind'].astype(int)] = gpp_vpd(rg_f=sub['rg_f'], vpd_f=sub['vpd_f'], parameter=numpy.transpose(params[0:2 + 1, i]))

        '''
        if i == 15:
            #print("sub['ind'][392]")
            #print(sub['ind'][392])
            #print("sub['tair_f'][392]")
            #print(sub['tair_f'][392])
            print("params[3:4+1, i]")
            print(params[3:4+1, i])
            #print("Reco_mat[i, sub['ind'][392].astype(int)]")
            #print(Reco_mat[i, sub['ind'][392].astype(int)])
        '''

    #end for i


    #### We iterate over each data point in the whole dataset.
    #### i.e j could represent around 17,000 data points.
    for j in range(n_set):

        #### For each data-point "j", there could be up to two windows
        #### that have covered this data-point "j". So we check how many
        #### windows have covered it and save the number in count.
        Reco_ind = numpy.where(Reco_mat[:, j] > NAN)[0]
        count = len(Reco_ind)

        #### If there are two windows covering this data-point "j", then we are going
        #### to assign weights to each window and multiply the Reco and GPP
        #### values we got previously with it's assigned weight. We get the
        #### final Reco and GPP values by adding the multiplied values together.
        if count > 1:
            weight1 = (params[n_params - 1, Reco_ind[1]] - j) / (params[n_params - 1, Reco_ind[1]] - params[n_params - 1, Reco_ind[0]])
            weight2 = (j - params[n_params - 1, Reco_ind[0]]) / (params[n_params - 1, Reco_ind[1]] - params[n_params - 1, Reco_ind[0]])
            Reco[j] = Reco_mat[Reco_ind[0], j] * weight1 + Reco_mat[Reco_ind[1], j] * weight2
            GPP[j] = GPP_mat[Reco_ind[0], j] * weight1 + GPP_mat[Reco_ind[1], j] * weight2
            partition_flag1[j] = numpy.abs(params[n_params - 1, Reco_ind[1]] - j)
            partition_flag2[j] = numpy.abs(j - params[n_params - 1, Reco_ind[0]])

            # my code
            reco_gpp_orig[0, j] = j
            reco_gpp_orig[1, j] = data['year'][j]
            reco_gpp_orig[2, j] = data['month'][j]
            reco_gpp_orig[3, j] = data['day'][j]
            reco_gpp_orig[4, j] = data['hr'][j]
            reco_gpp_orig[5, j] = data['julday'][j]
            reco_gpp_orig[6, j] = Reco_mat[Reco_ind[0], j]
            reco_gpp_orig[7, j] = Reco_mat[Reco_ind[1], j]
            reco_gpp_orig[8, j] = GPP_mat[Reco_ind[0], j]
            reco_gpp_orig[9, j] = GPP_mat[Reco_ind[1], j]

            '''
            if j == 1952:
                print("j")
                print(j)
                print("count")
                print(count)
                print("Reco_ind[0]")
                print(Reco_ind[0])
                print("Reco_ind[1]")
                print(Reco_ind[1])
                print("weight1")
                print(weight1)
                print("weight2")
                print(weight2)
                print("params[n_params - 1, Reco_ind[0]]")
                print(params[n_params - 1, Reco_ind[0]])
                print("params[n_params - 1, Reco_ind[1]]")
                print(params[n_params - 1, Reco_ind[1]])
                print("Reco_mat[Reco_ind[0], j]")
                print(Reco_mat[Reco_ind[0], j])
                print("Reco_mat[Reco_ind[1], j]")
                print(Reco_mat[Reco_ind[1], j])
                print("GPP_mat[Reco_ind[0], j]")
                print(GPP_mat[Reco_ind[0], j])
                print("GPP_mat[Reco_ind[1], j]")
                print(GPP_mat[Reco_ind[1], j])
                print("Reco[j]")
                print(Reco[j])
                print("GPP[j]")
                print(GPP[j])

                #if j == 1952:
                #    exit()

                #if j == 8840:
                 #   exit()
            '''

                #end code

        #### If there is only one window covering this data-point "j", then
        #### we are going to assign the final Reco and GPP values
        #### to the previously calculated Reco and GPP.
        elif count == 1:
            Reco[j] = Reco_mat[Reco_ind[0], j]
            GPP[j] = GPP_mat[Reco_ind[0], j]
            partition_flag1[j] = numpy.abs(params[n_params - 1, Reco_ind[0]] - j)

            if Reco_ind[0] == 0:
                partition_flag2[j] = j
            else:
                partition_flag2[j] = n_set - 1 - j

            '''
            if j == 5605:
                print("j")
                print(j)
                print("count")
                print(count)
                print("Reco_ind[0]")
                print(Reco_ind[0])
                print("Reco_mat[Reco_ind[0], j]")
                print(Reco_mat[Reco_ind[0], j])
                print("GPP_mat[Reco_ind[0], j]")
                print(GPP_mat[Reco_ind[0], j])
                print("Reco[j]")
                print(Reco[j])
                print("GPP[j]")
                print(GPP[j])

                #if j == 8840:
                #    exit()
            '''

        #### If there is no window covering this data-point "j", then exit.
        else: # TODO: investigate and replace behavior (same as broken opt error?)
            msg = "DT EXIT EXCEPTION: no window covering data point j"
            _log.critical(msg)
            raise ONEFluxPartitionError(msg)
    #### end "for j"

    #print("Reco")
    #print(Reco)
    #print("GPP")
    #print(GPP)
    #print("partition_flag1")
    #print(partition_flag1)
    #print("partition_flag2")
    #print(partition_flag2)

    #exit()

    #return numpy.concatenate((Reco, GPP, partition_flag1, partition_flag2), axis=0)

    #### Saving the previously calculated Reco and GPP values of the overlapped windows.
    var_names_reco_gpp = "j,year,month,day,hr,julday,reco_first,reco_second,gpp_first,gpp_second"

    filename_reco = 'nee_' + ustar_type + '_' + str(percentile_num) + '_' + site_id + '_' + str(year) + '_reco_before_weights_python.csv'
    numpy.savetxt(os.path.join(dt_output_dir, filename_reco), numpy.transpose(reco_gpp_orig), delimiter=',', fmt='%s', header=var_names_reco_gpp, comments='')
    #exit()

    _log.info("Finished compute_flux of daytime for nee_{u}_{p}_{s}_{y}".format(u=ustar_type, p=percentile_num, s=site_id, y=year))

    return Reco, GPP, partition_flag1, partition_flag2


def compute_var(data, params, whichmodel, JTJ_inv, res_cor):
    """
    :Task:  Get the predicted values of a variable for all windows covered in the model.

    :Explanation:   We get the predicted values of a varialbe by specifying
                    the model we used in 'estimate_params', applying 'whichmodel'.
                    We iterate over each parameter list and it's window and pass it
                    to the model in it's specified window by calling 'varpred'.

    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param params: parameters to be applied to the model
    :type params: numpy.ndarray
    :param whichmodel: integer specifying the model type.
    :type whichmodel: int
    :param JTJ_inv: 
    :type JTJ_inv: numpy.ndarray
    :param res_cor: 
    :type res_cor: numpy.ndarray
    """
    _log.info("Starting compute_var of daytime")

    n_params = len(params[:, 0])
    n_parasets = len(params[0, :])
    n_set = len(data['nee_f'])
    var_GPP_mat = numpy.empty((n_parasets, n_set))
    var_GPP_mat.fill(NAN)
    var_GPP = numpy.zeros(n_set, dtype=DOUBLE_PREC)

    '''
    print("n_params")
    print(n_params)
    print("n_parasets")
    print(n_parasets)
    print("n_set")
    print(n_set)
    '''

    #### Iterate over each parameter
    for i in range(n_parasets):
        sub = None
        if i == 0:
            ind_begin = 0
            ind_end = params[n_params - 1, i + 1]
            sub_mask = ((data['ind'] >= ind_begin) & (data['ind'] < ind_end))
            sub, _, _ = newselif(data=data, condition=sub_mask, drop=True)
        elif i == (n_parasets - 1):
            ind_begin = params[n_params - 1, i - 1]
            ind_end = numpy.max(data['ind'])
            sub_mask = ((data['ind'] >= ind_begin) & (data['ind'] <= ind_end))
            sub, _, _ = newselif(data=data, condition=sub_mask, drop=True)
        else:
            ind_begin = params[n_params - 1, i - 1]
            ind_end = params[n_params - 1, i + 1]
            sub_mask = ((data['ind'] >= ind_begin) & (data['ind'] < ind_end))
            sub, _, _ = newselif(data=data, condition=sub_mask, drop=True)

        #print("sub['ind'].size")
        #print(sub['ind'].size)

        #print("i")
        #print(i)

        #### params_filled_arr is just a replicated array filled with
        #### the value of E0 of the current window
        params_filled_arr = numpy.empty(sub['ind'].size)
        params_filled_arr.fill(params[4, i])

        #### params_filled_arr2 is just a replicated array filled with
        #### the value of alpha of the current window
        params_filled_arr2 = numpy.empty(sub['ind'].size)
        params_filled_arr2.fill(params[0, i])

        #### Based on the model we picked, we use it to get the predicted values.
        if whichmodel[i] == 0:
            #print("params[0:3+1, i]")
            #print(params[0:3+1, i])
            var_GPP_mat[i, sub['ind'].astype(int)] = varpred(func="HLRC_LloydVPD", data=sub, params_filled_arr=params_filled_arr, JTJ_inv=JTJ_inv[i, :, :],
                                                optpara=params[0:3 + 1, i], res=res_cor[i])
        elif whichmodel[i] == 1:
            var_GPP_mat[i, sub['ind'].astype(int)] = varpred(func="HLRC_Lloyd", data=sub, params_filled_arr=params_filled_arr, JTJ_inv=JTJ_inv[i, 0:2 + 1, 0:2 + 1],
                                                optpara=[params[0, i], params[1, i], params[3, i]], res=res_cor[i])
        elif whichmodel[i] == 2:
            var_GPP_mat[i, sub['ind'].astype(int)] = varpred(func="HLRC_Lloyd_afix", data=sub, params_filled_arr=params_filled_arr, params_filled_arr2=params_filled_arr2, JTJ_inv=JTJ_inv[i, 0:1 + 1, 0:1 + 1],
                                                optpara=[params[1, i], params[3, i]], res=res_cor[i])
        elif whichmodel[i] == 3:
            var_GPP_mat[i, sub['ind'].astype(int)] = varpred(func="HLRC_LloydVPD_afix", data=sub, params_filled_arr=params_filled_arr, params_filled_arr2=params_filled_arr2, JTJ_inv=JTJ_inv[i, 0:2 + 1, 0:2 + 1],
                                                optpara=params[1:3 + 1, i], res=res_cor[i])
        elif whichmodel[i] == 4:
            #print("var_GPP_mat.shape")
            #print(var_GPP_mat.shape)
            #print("sub['ind'].shape")
            #print(sub['ind'].shape)
            #print("var_GPP_mat[i, sub['ind'].astype(int)].shape")
            #print(var_GPP_mat[i, sub['ind'].astype(int)].shape)
            var_GPP_mat[i, sub['ind'].astype(int)] = varpred(func="LloydT_E0fix", data=sub, params_filled_arr=params_filled_arr, JTJ_inv=JTJ_inv[i, 0, 0],
                                                optpara=params[3, i], res=res_cor[i])
            #if i == 2:
            #    exit()

    #end for i

    #### Weight the predicted values and sum the values
    for j in range(n_set):
        GPP_ind = numpy.where(var_GPP_mat[:, j] > NAN)[0]
        count = len(GPP_ind)
        if count > 1:
            weight1 = (params[n_params - 1, GPP_ind[1]] - j) / (params[n_params - 1, GPP_ind[1]] - params[n_params - 1, GPP_ind[0]])
            weight2 = (j - params[n_params - 1, GPP_ind[0]]) / (params[n_params - 1, GPP_ind[1]] - params[n_params - 1, GPP_ind[0]])
            var_GPP[j] = var_GPP_mat[GPP_ind[0], j] * (weight1 * weight1) + var_GPP_mat[GPP_ind[1], j] * (weight2 * weight2)
        elif count == 1:
            var_GPP[j] = var_GPP_mat[GPP_ind[0], j]
        else:
            var_GPP[j] = NAN
    #end for j

    #print("var_GPP")
    #print(var_GPP)
    #exit()

    _log.info("Finished compute_var of daytime")

    return var_GPP


def varpred(func, data, JTJ_inv, optpara, res, params_filled_arr, params_filled_arr2=None):
    """
    :Task:  Get the predicted values of a variable.

    :Explanation:   We get the predicted values of a varialbe by specifying
                    the model function we used in 'estimate_params'.


    :param func: function model to use
    :type func: str
    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param JTJ_inv: 
    :type JTJ_inv: numpy.ndarray
    :param optpara: optimized parameters to be applied to the model
    :type optpara: numpy.ndarray
    :param res: 
    :type res: numpy.ndarray
    :param params_filled_arr: Array of replicated E0 values
    :type params_filled_arr: numpy.ndarray
    :param params_filled_arr2: Array of replicated alpha values
    :type params_filled_arr2: numpy.ndarray
    """
    #_log.info("Starting varpred of daytime")

    #### Calculate the jacobian matrix
    jac = jacobian(func=func, data=data, params_filled_arr=params_filled_arr, params_filled_arr2=params_filled_arr2, params=optpara)

    '''
    print("jac.shape")
    print(jac.shape)
    print("jac.size")
    print(jac.size)

    #print("JTJ_inv.shape")
    #print(JTJ_inv.shape)
    #print("JTJ_inv.size")
    #print(JTJ_inv.size)
    #print("JTJ_inv")
    #print(JTJ_inv)
    '''

    varY = None
    if JTJ_inv.size == 1:
        #print("JTJ_inv.size == 1")
        # in pvwave multiplying an array with it's transpose is like
        # multiplying it without the transpose
        #varY = (jac) * JTJ_inv * numpy.transpose(jac) * res
        varY = (jac) * JTJ_inv * (jac) * res
    else:
        #print("JTJ_inv.size != 1")
        x = numpy.dot(numpy.transpose(jac), JTJ_inv)
        y = numpy.dot(x, jac)
        #print("y")
        #print(y * res)
        varY = numpy.diagonal(y * res)

    #print("varY")
    #print(varY)

    #print("varY.shape")
    #print(varY.shape)

    #print("varY.size")
    #print(varY.size)

    #exit()

    #_log.info("Finished varpred of daytime")

    return varY


def estimate_parasets(data, winsize, fguess, trimperc, name_out, dt_output_dir, site_id, ustar_type, percentile_num, year):
    """
    :Task:  This function is responsible to find the best parameters to 
            represent the model that will fit the data the most.

    :Explanation:   To understand this function we have to know the terms ok and nok
                    for okay and not-okay. Basically the algorithm is about iterating
                    through a range of days (The days are calculated and being saved 
                    to day_begin and day_end); each range represents a window.

                    We go through a process of parameter evaluation and based
                    on the retrieved parameters, we decide if they're okay or not okay,
                    and save them to the proper arrays, whether it's params_ok or params_nok.

                    To effectively come up with the closely best parameters, we try 
                    3 different guesses in the "for j" loop. After trying the 3 different
                    guesses and find the most suiltable parameters of the 3, we validate
                    them by calling the function "check_parameters".

                    Based on specified conditions, we decide which model function to 
                    use to come up with the proper parameters (e.g lloyd_taylor, hlrc_lloydvpd, etc).


    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param winsize: window size to get best parameters within each window
    :type winsize: int
    :param fguess: the initial guesses for the optimization function to start with
    :type fguess: array of floats
    :param trimperc: percentage to trim
    :type trimperc: float
    """

    _log.info("Starting estimate_parasets of daytime for nee_{u}_{p}_{s}_{y}".format(u=ustar_type, p=percentile_num, s=site_id, y=year))


    ###############################################
    #### self note: pvwave dimensions are reversed,
    #### row and col and flipped in translation
    ###############################################

    #### Creating the arrays we're going to use
    n_parasets = long(365 / winsize) * 2
    params = numpy.zeros((3, 2 * len(fguess), n_parasets), dtype=FLOAT_PREC)
    params_ok = numpy.zeros((2 * len(fguess), n_parasets), dtype=FLOAT_PREC)
    params_nok = numpy.zeros((2 * len(fguess), n_parasets), dtype=FLOAT_PREC)
    rmse = numpy.zeros(3, dtype=FLOAT_PREC)
    #ind = fltarr(n_parasets, 3, 3)
    ind = numpy.zeros((3, 3, n_parasets), dtype=FLOAT_PREC)
    ind_ok = numpy.zeros((3, n_parasets), dtype=FLOAT_PREC)
    p_cor = numpy.zeros((3, 6, n_parasets), dtype=FLOAT_PREC)
    p_cor_ok = numpy.zeros((6, n_parasets), dtype=FLOAT_PREC)

    JTJ_inv_ok = numpy.zeros((n_parasets, len(fguess) - 1, len(fguess) - 1), dtype=DOUBLE_PREC)
    whichmodel = numpy.zeros(3, dtype=int)
    whichmodel_ok = numpy.zeros(n_parasets, dtype=int)
    res_cor = numpy.zeros(3, dtype=DOUBLE_PREC)
    res_cor_ok = numpy.zeros(n_parasets, dtype=DOUBLE_PREC)

    params_all = numpy.zeros((2 * len(fguess), n_parasets), dtype=FLOAT_PREC)
    params_all_timestamp = numpy.zeros((n_parasets, 2 * len(fguess) + 2), dtype=FLOAT_PREC)

    # my code
    new_dtype = PARAM_DTYPE
    ### intitalize extra diagnostics output
    params_all_for_ranges = numpy.zeros(n_parasets, dtype=new_dtype)
    params_all_for_ranges['year'] = int(year)
    params_all_for_ranges['nee_avg'] = NAN
    params_all_for_ranges['ta_avg'] = NAN
    params_all_for_ranges['rg_avg'] = NAN
    params_all_for_ranges['nee_std'] = NAN
    params_all_for_ranges['ta_std'] = NAN
    params_all_for_ranges['rg_std'] = NAN
    #end of my code

    '''
    n_parasets = long(365 / winsize) * 2
    params = fltarr(n_parasets, 2 * n_elements(fguess), 3)
    params_ok = fltarr(n_parasets, 2 * n_elements(fguess))
    params_nok = fltarr(n_parasets, 2 * n_elements(fguess))
    rmse = fltarr(3)
    ind = fltarr(n_parasets, 3, 3)
    ind_ok = fltarr(n_parasets, 3)
    p_cor = fltarr(n_parasets, 6, 3)
    p_cor_ok = fltarr(n_parasets, 6)

    JTJ_inv_ok = dblarr(n_elements(fguess) - 1, n_elements(fguess) - 1, n_parasets)
    whichmodel = intarr(3)
    whichmodel_ok = intarr(n_parasets)
    res_cor = dblarr(3)
    res_cor_ok = dblarr(n_parasets)


        JTJ_inv = dblarr(n_elements(fguess) - 1, n_elements(fguess) - 1, 3)
    '''


    #;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #;;; whichmodel: choice of model  ;;;
    #;;; 0: HLRC_LloydVPD             ;;;
    #;;; 1: HLRC_Lloyd                ;;;
    #;;; 2: HLRC_Lloyd_afix           ;;;
    #;;; 3: HLRC_LloydVPD_afix        ;;;
    #;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    i_ok = 0
    i_nok = 0
    betafac = [0.5, 1, 2]

    lloydtemp_e0 = None
    lloydtemp_e0_se = None

    #numpy.savetxt(fname='../dt_set_before_es_2013_y_python.csv', X=data, delimiter=',', fmt='%s', header=','.join(data.dtype.names), comments='')
    #exit()

    #### Iterate through each parameter set to create this set
    for i in range(n_parasets):
        JTJ_inv = numpy.zeros((3, len(fguess) - 1, len(fguess) - 1), dtype=DOUBLE_PREC)
        #JTJ_inv = numpy.zeros((len(fguess) - 1, 3, len(fguess) - 1), dtype=DOUBLE_PREC)

        #### Defining the range of window of data we're going
        #### to use for optimization
        day_begin = i * winsize / 2.0
        day_end = day_begin + winsize

        day_begin2 = 0
        day_end2 = numpy.amax(data['julday'])

        if i > 1:
            day_begin2 = (i - 2) * winsize / 2.0
        if i < n_parasets - 2:
            day_end2 = (i + 2) * winsize / 2.0 + winsize

#        print("#######################################################################")
#        print("#######################################################################")
#        print("#######################################################################")
#
#        print("i")
#        print(i)
#        print("i_ok")
#        print(i_ok)
#        print("day_begin")
#        print(day_begin)
#        print("day_end")
#        print(day_end)
#        print("day_begin2")
#        print(day_begin2)
#        print("day_end2")
#        print(day_end2)


        #### Creating the masks of the data. We'll be using
        #### these masks to select the data that fits certain
        #### conditions for processing
        sub_mask = ((data['julday'] > day_begin) & (data['julday'] <= day_end) & (data['nee_fqc'] == 0))
        subn_mask = ((data['julday'] > day_begin2) & (data['julday'] <= day_end2) & (data['nee_fqc'] == 0) & (data['rg'] <= 4))
        subd_mask = ((data['julday'] > day_begin) & (data['julday'] <= day_end) & (data['nee_fqc'] == 0) & (data['rg'] > 4))

        #### Get the data that correspond to the masks in the previous step
        sub, _, _ = newselif(data=data, condition=sub_mask, drop=True)
        subn, _, _ = newselif(data=data, condition=subn_mask, drop=True)
        subd, _, _ = newselif(data=data, condition=subd_mask, drop=True)


        '''
        print("name_out, day_begin2, day_end2")
        print("name_out, " + str(day_begin2) + ", " + str(day_end2))
        print("long((day_begin + winsize / 2.0) * 48.0)")
        print(long((day_begin + winsize / 2.0) * 48.0))
        '''

        #ind[i][:][:] = long((day_begin + winsize / 2.0) * 48.0)
        #ind[i, :, :] = long((day_begin + winsize / 2.0) * 48.0)

        #### Calculate the first index of the window we're using now
        ind[:, :, i] = long((day_begin + winsize / 2.0) * 48.0)

        '''
        #print("ind[:, :, i]")
        #print(ind[:, :, i])
        #exit()

        print("numpy.any(subn_mask)")
        print(numpy.any(subn_mask))
        print("numpy.any(subd_mask)")
        print(numpy.any(subd_mask))
        #print("subn['nee_fs_unc']")
        #print(subn['nee_fs_unc'])
        print("subd['nee_fs_unc']")
        print(subd['nee_fs_unc'])

        #if i == 45:
        #    exit()
        '''

        if numpy.amin(subn['nee_fs_unc']) < 0:
            subn['nee_fs_unc'][:] = 1

        if numpy.amin(subd['nee_fs_unc']) < 0:
            subd['nee_fs_unc'][:] = 1

        '''
        if i == 173:
            print("subn['nee_f'].shape")
            print(subn['nee_f'].shape)
        '''

        E0set = 0
        #### If the data in subn within the window is <= 10, then use
        #### the lloydtemp_e0 from the previous window
        if subn['nee_f'].shape[0] <= 10 and i_ok > 0 and lloydtemp_e0 != None:
            lloydtemp_e0 = params_ok[4, i_ok - 1]
            lloydtemp_e0_se = params_ok[9, i_ok - 1]
            #ind[i][0][:] = ind_ok[i_ok - 1][0]
            ind[:, 0, i] = ind_ok[0, i_ok - 1]
            E0set = 1

            '''
            print("lloydtemp_e0")
            print(lloydtemp_e0)
            print("lloydtemp_e0_se")
            print(lloydtemp_e0_se)
            '''

        '''
        print("i")
        print(i)
        print("i_ok")
        print(i_ok)
        print("subn['nee_f'].shape[0]")
        print(subn['nee_f'].shape[0])
        print("E0set")
        print(E0set)
        '''

        #### Chech if the data is suitable for optimization (to find the model)
        if (subn['nee_f'].shape[0] > 10 or E0set == 1) and subd['nee_f'].shape[0] > 10:
            #### Calling percentiles_fn to get the values of the chosen
            #### percentiles from the "nee_f" data array after sorting it
            percs = percentiles_fn(data=sub, columns=['nee_f'], values=[0.03, 0.97])
            #### Setting initial value for beta amplitude of NEE
            beta = abs(percs[0] - percs[1])

            #### Setting initial value for rb to be the average
            #### of the "nee_f" data
            rb = numpy.average(subn['nee_f'])
            fguess[3] = rb

            if E0set == 0:
                # estimate temperature sensitivity from data
                '''
                print("****************************")
                print("Starting LloydTemp")
                print("****************************")
                '''
                #status, rref, e0, rref_se, e0_se, residuals, covariance_matrix, cor_matrix, lt_rmse, ls_status = nlinlts2(data=subn, lts_func="LloydTemp", depvar='nee_f', indepvar_arr=['tair_f'], npara=2, xguess=fguess[3:4+1], mprior=numpy.array(fguess[3:4+1], dtype=FLOAT_PREC), sigm=numpy.array([800, 1000]), sigd=subn['nee_fs_unc'])

                #### Starting the optimization using the "LloyedTemp" function
                lloyedTemp_result = nlinlts2(data=subn, lts_func="LloydTemp", depvar='nee_f', indepvar_arr=['tair_f'], npara=2, xguess=fguess[3:4 + 1], mprior=numpy.array(fguess[3:4 + 1], dtype=FLOAT_PREC), sigm=numpy.array([800, 1000]), sigd=subn['nee_fs_unc'])

                #### Setting the returned model parameters
                status = lloyedTemp_result['status']
                rref = lloyedTemp_result['rref']
                e0 = lloyedTemp_result['e0']
                rref_se = lloyedTemp_result['rref_std_error']
                e0_se = lloyedTemp_result['e0_std_error']
                residuals = lloyedTemp_result['residuals']
                covariance_matrix = lloyedTemp_result['cov_matrix']
                cor_matrix = lloyedTemp_result['cor_matrix']
                lt_rmse = lloyedTemp_result['rmse']
                ls_status = lloyedTemp_result['ls_status']

                lloydtemp_e0 = e0
                lloydtemp_e0_se = e0_se

                if covariance_matrix is None or cor_matrix is None:
                    raise ONEFluxPartitionBrokenOptError('LloydTemp', site_id=site_id, year=year, day_begin=day_begin2, day_end=day_end2, prod=ustar_type, perc=percentile_num)

                '''
                print("fguess")
                print(fguess)
                print("fguess[3:4+1]")
                print(fguess[3:4+1])
                print("status")
                print(status)
                print("rref")
                print(rref)
                print("e0")
                print(e0)
                print("rref_se")
                print(rref_se)
                print("e0_se")
                print(e0_se)
                print("residuals")
                print(residuals)
                print("covariance_matrix")
                print(covariance_matrix)
                print("cor_matrix")
                print(cor_matrix)
                print("ls_status")
                print(ls_status)
                '''

                #### Check that the returned e0 is within range
                #### if not, then get the e0 set from the previous
                #### parameter set; if this doesn't work, set it to the limits.
                if e0 < 50 or e0 > 400:
                    if i_ok > 0:
                        e0 = params_ok[4, i_ok - 1]
                        e0_se = params_ok[9, i_ok - 1]
                        #ind[i][0][:] = ind_ok[i_ok - 1][0]
                        ind[:, 0, i] = ind_ok[0, i_ok - 1]
                    elif e0 < 50:
                        e0 = 50
                        e0_se = NAN
                    elif e0 > 400:
                        e0 = 400
                        e0_se = NAN
                #end if
            #end if

            subd['e0_1_from_tair'][:] = e0

            #### Finding slope of three different initial guess values
            #### and choose the best of three
            for j in range(2 + 1):
                '''
                print("===========")
                print("j")
                print(j)
                print("===========")
                '''

                #### Change second value of fguess to
                #### beta * (half initial guess, initial guess and double initial guess)
                fguess[1] = beta * betafac[j]

                # estimate parameters of the HLRC with fixed E0
                '''
                print("****************************")
                print("Starting HLRC_LloydVPD")
                print("****************************")
                '''
                #numpy.savetxt(fname="dt_subd_2005_y_i_91_python.csv", X=subd, delimiter=',', fmt='%s', header=','.join(subd.dtype.names), comments='')

                #### Starting the optimization using the "HLRC_LloydVPD" function
                hlrclvpd_results = nlinlts2(data=subd, lts_func="HLRC_LloydVPD", depvar='nee_f', indepvar_arr=['rg_f', 'tair_f', 'e0_1_from_tair', 'vpd_f'], npara=4, xguess=fguess[0:3 + 1], mprior=numpy.array(fguess[0:3 + 1], dtype=FLOAT_PREC), sigm=numpy.array([10, 600, 50, 80]), sigd=subd['nee_fs_unc'])

                #print(nlinlts2(data=subd, lts_func="HLRC_LloydVPD", depvar='nee_f', indepvar_arr=['rg_f', 'tair_f', 'e0_1_from_tair', 'vpd_f'], npara=4, xguess=fguess[0:3+1], mprior=numpy.array(fguess[0:3+1], dtype=FLOAT_PREC), sigm=numpy.array([10, 600, 50, 80]), sigd=subd['nee_fs_unc']))
                #hlrclvpd_status, hlrclvpd_alpha, hlrclvpd_beta, hlrclvpd_k, hlrclvpd_rref, hlrclvpd_alpha_se, hlrclvpd_beta_se, hlrclvpd_k_se, hlrclvpd_rref_se, hlrclvpd_residuals, hlrclvpd_cov_matrix, hlrclvpd_cor_matrix, hlrclvpd_rmse, hlrclvpd_ls_status = nlinlts2(data=subd, lts_func="HLRC_LloydVPD", depvar='nee_f', indepvar_arr=['rg_f', 'tair_f', 'e0_1_from_tair', 'vpd_f'], npara=4, xguess=fguess[0:3+1], mprior=numpy.array(fguess[0:3+1], dtype=FLOAT_PREC), sigm=numpy.array([10, 600, 50, 80]), sigd=subd['nee_fs_unc'])

                #### Setting the returned model parameters
                hlrclvpd_status = hlrclvpd_results['status']
                hlrclvpd_alpha = hlrclvpd_results['alpha']
                hlrclvpd_beta = hlrclvpd_results['beta']
                hlrclvpd_k = hlrclvpd_results['k']
                hlrclvpd_rref = hlrclvpd_results['rref']
                hlrclvpd_alpha_se = hlrclvpd_results['alpha_std_error']
                hlrclvpd_beta_se = hlrclvpd_results['beta_std_error']
                hlrclvpd_k_se = hlrclvpd_results['k_std_error']
                hlrclvpd_rref_se = hlrclvpd_results['rref_std_error']
                hlrclvpd_residuals = hlrclvpd_results['residuals']
                hlrclvpd_cov_matrix = hlrclvpd_results['cov_matrix']
                hlrclvpd_cor_matrix = hlrclvpd_results['cor_matrix']
                hlrclvpd_rmse = hlrclvpd_results['rmse']
                hlrclvpd_ls_status = hlrclvpd_results['ls_status']

                if hlrclvpd_cov_matrix is None or hlrclvpd_cor_matrix is None:
                    raise ONEFluxPartitionBrokenOptError('HLRC_LloydVPD', site_id=site_id, year=year, day_begin=day_begin2, day_end=day_end2, prod=ustar_type, perc=percentile_num)

                '''
                if hlrclvpd_residuals == None:
                    # Handle error
                '''

                '''
                print("fguess[0:3+1]")
                print(fguess[0:3+1])
                print("hlrclvpd_alpha")
                print(hlrclvpd_alpha)
                print("hlrclvpd_beta")
                print(hlrclvpd_beta)
                print("hlrclvpd_k")
                print(hlrclvpd_k)
                print("hlrclvpd_rref")
                print(hlrclvpd_rref)

                print("hlrclvpd_alpha_se")
                print(hlrclvpd_alpha_se)
                print("hlrclvpd_beta_se")
                print(hlrclvpd_beta_se)
                print("hlrclvpd_k_se")
                print(hlrclvpd_k_se)
                print("hlrclvpd_rref_se")
                print(hlrclvpd_rref_se)

                print("====================")
                print("hlrclvpd_residuals")
                print(hlrclvpd_residuals)
                print("hlrclvpd_cov_matrix")
                print(hlrclvpd_cov_matrix)
                print("hlrclvpd_cor_matrix")
                print(hlrclvpd_cor_matrix)

                print("len(hlrclvpd_residuals)")
                print(len(hlrclvpd_residuals))
                '''

                #### Specifying which model we chose for this iteration (j -> modified fguess)
                whichmodel[j] = 0

                res_cor[j] = (hlrclvpd_residuals ** 2).sum() / (len(hlrclvpd_residuals) * (1.0 - trimperc / 100.0) - 4)

                #### Setting the parameters of this iteration (j -> modified fguess)
                params[j, :, i] = numpy.array([hlrclvpd_alpha, hlrclvpd_beta, hlrclvpd_k, hlrclvpd_rref, e0, hlrclvpd_alpha_se, hlrclvpd_beta_se, hlrclvpd_k_se, hlrclvpd_rref_se, e0_se])

                if params[j, 2, i] == 0:
                    whichmodel[j] = 1

                p_cor[j, :, i] = numpy.array([hlrclvpd_cor_matrix[0][1], hlrclvpd_cor_matrix[0][2], hlrclvpd_cor_matrix[0][3], hlrclvpd_cor_matrix[1][2], hlrclvpd_cor_matrix[1][3], hlrclvpd_cor_matrix[2][3]])

                rmse[j] = hlrclvpd_rmse

                JTJ_inv[j, :, :] = numpy.copy(hlrclvpd_cov_matrix)

                #### Check if parameter "k" is zero
                if params[j, 2, i] == 0:
                    JTJ_inv_temp = numpy.zeros((len(fguess) - 1, len(fguess) - 1), dtype=DOUBLE_PREC)
                    whichmodel[j] = 1

                    JTJ_inv_temp[0][0] = hlrclvpd_cov_matrix[0][0]
                    JTJ_inv_temp[0][1] = hlrclvpd_cov_matrix[0][1]
                    JTJ_inv_temp[1][0] = hlrclvpd_cov_matrix[1][0]
                    JTJ_inv_temp[1][1] = hlrclvpd_cov_matrix[1][1]

                    JTJ_inv_temp[0][2] = hlrclvpd_cov_matrix[0][3]
                    JTJ_inv_temp[1][2] = hlrclvpd_cov_matrix[1][3]
                    JTJ_inv_temp[2][2] = hlrclvpd_cov_matrix[3][3]
                    JTJ_inv_temp[2][0] = hlrclvpd_cov_matrix[3][0]
                    JTJ_inv_temp[2][1] = hlrclvpd_cov_matrix[3][1]

                    JTJ_inv[j, :, :] = numpy.copy(JTJ_inv_temp)


                #;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
                #;; check k, if less than zero estimate parameters without VPD effect      ;;
                #;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
                if params[j, 2, i] < 0:
                    '''
                    print("****************************")
                    print("Starting HLRC_Lloyd")
                    print("****************************")
                    '''

                    #hlrcl_status, hlrcl_alpha, hlrcl_beta, hlrcl_rref, hlrcl_alpha_se, hlrcl_beta_se, hlrcl_rref_se, hlrcl_residuals, hlrcl_cov_matrix, hlrcl_cor_matrix, hlrcl_rmse, hlrcl_ls_status = nlinlts2(data=subd, lts_func="HLRC_Lloyd", depvar='nee_f', indepvar_arr=['rg_f', 'tair_f', 'e0_1_from_tair'], npara=3, xguess=numpy.array([fguess[0], fguess[1], fguess[3]]), mprior=numpy.array([fguess[0], fguess[1], fguess[3]], dtype=FLOAT_PREC), sigm=numpy.array([10, 600, 80]), sigd=subd['nee_fs_unc'])

                    #### Starting the optimization using the "HLRC_Lloyd" function
                    hlrcl_results = nlinlts2(data=subd, lts_func="HLRC_Lloyd", depvar='nee_f', indepvar_arr=['rg_f', 'tair_f', 'e0_1_from_tair'], npara=3, xguess=numpy.array([fguess[0], fguess[1], fguess[3]]), mprior=numpy.array([fguess[0], fguess[1], fguess[3]], dtype=FLOAT_PREC), sigm=numpy.array([10, 600, 80]), sigd=subd['nee_fs_unc'])

                    #### Setting the returned model parameters
                    hlrcl_status = hlrcl_results['status']
                    hlrcl_alpha = hlrcl_results['alpha']
                    hlrcl_beta = hlrcl_results['beta']
                    hlrcl_rref = hlrcl_results['rref']
                    hlrcl_alpha_se = hlrcl_results['alpha_std_error']
                    hlrcl_beta_se = hlrcl_results['beta_std_error']
                    hlrcl_rref_se = hlrcl_results['rref_std_error']
                    hlrcl_residuals = hlrcl_results['residuals']
                    hlrcl_cov_matrix = hlrcl_results['cov_matrix']
                    hlrcl_cor_matrix = hlrcl_results['cor_matrix']
                    hlrcl_rmse = hlrcl_results['rmse']
                    hlrcl_ls_status = hlrcl_results['ls_status']

                    if hlrcl_cov_matrix is None or hlrcl_cor_matrix is None:
                        raise ONEFluxPartitionBrokenOptError('HLRC_Lloyd', site_id=site_id, year=year, day_begin=day_begin2, day_end=day_end2, prod=ustar_type, perc=percentile_num)

                    '''
                    print("numpy.array([fguess[0], fguess[1], fguess[3]])")
                    print(numpy.array([fguess[0], fguess[1], fguess[3]]))
                    print("hlrcl_alpha")
                    print(hlrcl_alpha)
                    print("hlrcl_beta")
                    print(hlrcl_beta)
                    print("hlrcl_rref")
                    print(hlrcl_rref)

                    print("hlrcl_alpha_se")
                    print(hlrcl_alpha_se)
                    print("hlrcl_beta_se")
                    print(hlrcl_beta_se)
                    print("hlrcl_rref_se")
                    print(hlrcl_rref_se)

                    print("====================")
                    print("hlrcl_residuals")
                    print(hlrcl_residuals)
                    print("hlrcl_cov_matrix")
                    print(hlrcl_cov_matrix)
                    print("hlrcl_cor_matrix")
                    print(hlrcl_cor_matrix)

                    print("len(hlrcl_residuals)")
                    print(len(hlrcl_residuals))
                    '''

                    #### Specifying which model we chose for this iteration (j -> modified fguess)
                    whichmodel[j] = 1

                    res_cor[j] = (hlrcl_residuals ** 2).sum() / (len(hlrcl_residuals) * (1.0 - trimperc / 100.0) - 3)

                    #### Setting the parameters of this iteration (j -> modified fguess)
                    params[j, :, i] = numpy.array([hlrcl_alpha, hlrcl_beta, 0, hlrcl_rref, e0, hlrcl_alpha_se, hlrcl_beta_se, 0, hlrcl_rref_se, e0_se])

                    p_cor[j, :, i] = numpy.array([hlrcl_cor_matrix[0][1], NAN, hlrcl_cor_matrix[0][2], NAN, hlrcl_cor_matrix[1][2], NAN])

                    rmse[j] = hlrcl_rmse

                    JTJ_inv[j, 0:3, 0:3] = numpy.copy(hlrcl_cov_matrix)


                    #;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
                    #;; check alpha, if less than zero estimate parameters with fixed alpha of last window and without VPD effect ;;
                    #;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
                    if (params[j, 0, i] > 0.22) and i_ok > 0:
                        if params_ok[0, i_ok - 1] > 0:
                            alpha = params_ok[0, i_ok - 1]
                            subd['alpha_1_from_tair'][:] = alpha
                            ind[j, 1, i] = ind_ok[1, i_ok - 1]

                            #hlrcl_status_afix, hlrcl_beta_afix, hlrcl_rref_afix, hlrcl_beta_se_afix, hlrcl_rref_se_afix, hlrcl_residuals_afix, hlrcl_cov_matrix_afix, hlrcl_cor_matrix_afix, hlrcl_rmse_afix, hlrcl_ls_status_afix = nlinlts2(data=subd, lts_func="HLRC_Lloyd_afix", depvar='nee_f', indepvar_arr=['rg_f', 'tair_f', 'e0_1_from_tair', 'alpha_1_from_tair'], npara=2, xguess=numpy.array([fguess[1], fguess[3]]), mprior=numpy.array([fguess[1], fguess[3]], dtype=FLOAT_PREC), sigm=numpy.array([600, 80]), sigd=subd['nee_fs_unc'])

                            #### Starting the optimization using the "HLRC_Lloyd_afix" function
                            hlrcl_results_afix = nlinlts2(data=subd, lts_func="HLRC_Lloyd_afix", depvar='nee_f', indepvar_arr=['rg_f', 'tair_f', 'e0_1_from_tair', 'alpha_1_from_tair'], npara=2, xguess=numpy.array([fguess[1], fguess[3]]), mprior=numpy.array([fguess[1], fguess[3]], dtype=FLOAT_PREC), sigm=numpy.array([600, 80]), sigd=subd['nee_fs_unc'])

                            #### Setting the returned model parameters
                            hlrcl_status_afix = hlrcl_results_afix['status']
                            hlrcl_beta_afix = hlrcl_results_afix['beta']
                            hlrcl_rref_afix = hlrcl_results_afix['rref']
                            hlrcl_beta_se_afix = hlrcl_results_afix['beta_std_error']
                            hlrcl_rref_se_afix = hlrcl_results_afix['rref_std_error']
                            hlrcl_residuals_afix = hlrcl_results_afix['residuals']
                            hlrcl_cov_matrix_afix = hlrcl_results_afix['cov_matrix']
                            hlrcl_cor_matrix_afix = hlrcl_results_afix['cor_matrix']
                            hlrcl_rmse_afix = hlrcl_results_afix['rmse']
                            hlrcl_ls_status_afix = hlrcl_results_afix['ls_status']

                            if hlrcl_cov_matrix_afix is None or hlrcl_cor_matrix_afix is None:
                                raise ONEFluxPartitionBrokenOptError('HLRC_Lloyd_afix', site_id=site_id, year=year, day_begin=day_begin2, day_end=day_end2, prod=ustar_type, perc=percentile_num)

                            '''
                            print("numpy.array([fguess[1], fguess[3]])")
                            print(numpy.array([fguess[1], fguess[3]]))
                            print("hlrcl_beta_afix")
                            print(hlrcl_beta_afix)
                            print("hlrcl_rref_afix")
                            print(hlrcl_rref_afix)

                            print("hlrcl_beta_se_afix")
                            print(hlrcl_beta_se_afix)
                            print("hlrcl_rref_se_afix")
                            print(hlrcl_rref_se_afix)

                            print("====================")
                            print("hlrcl_residuals_afix")
                            print(hlrcl_residuals_afix)
                            print("hlrcl_cov_matrix_afix")
                            print(hlrcl_cov_matrix_afix)
                            print("hlrcl_cor_matrix_afix")
                            print(hlrcl_cor_matrix_afix)

                            print("len(hlrcl_residuals_afix)")
                            print(len(hlrcl_residuals_afix))
                            '''

                            #### Specifying which model we chose for this iteration (j -> modified fguess)
                            whichmodel[j] = 2

                            res_cor[j] = (hlrcl_residuals_afix ** 2).sum() / (len(hlrcl_residuals_afix) * (1.0 - trimperc / 100.0) - 2)

                            #### Setting the parameters of this iteration (j -> modified fguess)
                            params[j, :, i] = numpy.array([alpha, hlrcl_beta_afix, 0, hlrcl_rref_afix, e0, NAN, hlrcl_beta_se_afix, 0, hlrcl_rref_se_afix, e0_se])

                            p_cor[j, :, i] = numpy.array([NAN, NAN, NAN, NAN, hlrcl_cor_matrix_afix[0][1], NAN])

                            rmse[j] = hlrcl_rmse_afix

                            JTJ_inv[j, 0:2, 0:2] = numpy.copy(hlrcl_cov_matrix_afix)


                #;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
                #;; check alpha, if gt 0.22 estimate parameters with fixed alpha of last window                   ;;
                #;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
                elif (params[j, 0, i] > 0.22) and (i_ok > 0):
                    if params_ok[0, i_ok - 1] > 0:
                        alpha = params_ok[0, i_ok - 1]
                        subd['alpha_1_from_tair'][:] = alpha
                        ind[j, 1, i] = ind_ok[1, i_ok - 1]

                        '''
                        print("****************************")
                        print("Starting HLRC_LloydVPD_afix")
                        print("****************************")
                        '''
                        #hlrclvpd_status_afix, hlrclvpd_beta_afix, hlrclvpd_k_afix, hlrclvpd_rref_afix, hlrclvpd_beta_se_afix, hlrclvpd_k_se_afix, hlrclvpd_rref_se_afix, hlrclvpd_residuals_afix, hlrclvpd_cov_matrix_afix, hlrclvpd_cor_matrix_afix, hlrclvpd_rmse_afix, hlrclvpd_ls_status_afix = nlinlts2(data=subd, lts_func="HLRC_LloydVPD_afix", depvar='nee_f', indepvar_arr=['rg_f', 'tair_f', 'e0_1_from_tair', 'vpd_f', 'alpha_1_from_tair'], npara=3, xguess=numpy.array([fguess[1], fguess[2], fguess[3]]), mprior=numpy.array([fguess[1], fguess[2], fguess[3]], dtype=FLOAT_PREC), sigm=numpy.array([600, 50, 80]), sigd=subd['nee_fs_unc'])

                        #### Starting the optimization using the "HLRC_LloydVPD_afix" function
                        hlrclvpd_results = nlinlts2(data=subd, lts_func="HLRC_LloydVPD_afix", depvar='nee_f', indepvar_arr=['rg_f', 'tair_f', 'e0_1_from_tair', 'vpd_f', 'alpha_1_from_tair'], npara=3, xguess=numpy.array([fguess[1], fguess[2], fguess[3]]), mprior=numpy.array([fguess[1], fguess[2], fguess[3]], dtype=FLOAT_PREC), sigm=numpy.array([600, 50, 80]), sigd=subd['nee_fs_unc'])

                        #### Setting the returned model parameters
                        hlrclvpd_status_afix = hlrclvpd_results['status']
                        hlrclvpd_beta_afix = hlrclvpd_results['beta']
                        hlrclvpd_k_afix = hlrclvpd_results['k']
                        hlrclvpd_rref_afix = hlrclvpd_results['rref']
                        hlrclvpd_beta_se_afix = hlrclvpd_results['beta_std_error']
                        hlrclvpd_k_se_afix = hlrclvpd_results['k_std_error']
                        hlrclvpd_rref_se_afix = hlrclvpd_results['rref_std_error']
                        hlrclvpd_residuals_afix = hlrclvpd_results['residuals']
                        hlrclvpd_cov_matrix_afix = hlrclvpd_results['cov_matrix']
                        hlrclvpd_cor_matrix_afix = hlrclvpd_results['cor_matrix']
                        hlrclvpd_rmse_afix = hlrclvpd_results['rmse']
                        hlrclvpd_ls_status_afix = hlrclvpd_results['ls_status']

                        if hlrclvpd_cov_matrix_afix is None or hlrclvpd_cor_matrix_afix is None:
                            raise ONEFluxPartitionBrokenOptError('HLRC_LloydVPD_afix', site_id=site_id, year=year, day_begin=day_begin2, day_end=day_end2, prod=ustar_type, perc=percentile_num)

                        '''
                        print("numpy.array([fguess[1], fguess[2], fguess[3]])")
                        print(numpy.array([fguess[1], fguess[2], fguess[3]]))
                        print("hlrclvpd_beta_afix")
                        print(hlrclvpd_beta_afix)
                        print("hlrclvpd_k_afix")
                        print(hlrclvpd_k_afix)
                        print("hlrclvpd_rref_afix")
                        print(hlrclvpd_rref_afix)

                        print("hlrclvpd_beta_se_afix")
                        print(hlrclvpd_beta_se_afix)
                        print("hlrclvpd_k_se_afix")
                        print(hlrclvpd_k_se_afix)
                        print("hlrclvpd_rref_se_afix")
                        print(hlrclvpd_rref_se_afix)

                        print("====================")
                        print("hlrclvpd_residuals_afix")
                        print(hlrclvpd_residuals_afix)
                        print("hlrclvpd_cov_matrix_afix")
                        print(hlrclvpd_cov_matrix_afix)
                        print("hlrclvpd_cor_matrix_afix")
                        print(hlrclvpd_cor_matrix_afix)

                        print("len(hlrclvpd_residuals_afix)")
                        print(len(hlrclvpd_residuals_afix))
                        '''

                        #### Specifying which model we chose for this iteration (j -> modified fguess)
                        whichmodel[j] = 3

                        res_cor[j] = (hlrclvpd_residuals_afix ** 2).sum() / (len(hlrclvpd_residuals_afix) * (1.0 - trimperc / 100.0) - 3)

                        #### Setting the parameters of this iteration (j -> modified fguess)
                        params[j, :, i] = numpy.array([alpha, hlrclvpd_beta_afix, hlrclvpd_k_afix, hlrclvpd_rref_afix, e0, 0, hlrclvpd_beta_se_afix, hlrclvpd_k_se_afix, hlrclvpd_rref_se_afix, e0_se])

                        p_cor[j, :, i] = numpy.array([NAN, NAN, NAN, hlrclvpd_cor_matrix_afix[0][1], hlrclvpd_cor_matrix_afix[0][2], hlrclvpd_cor_matrix_afix[1][2]])

                        rmse[j] = hlrclvpd_rmse_afix

                        JTJ_inv[j, 0:3, 0:3] = numpy.copy(hlrclvpd_cov_matrix_afix)

                        #### Check if parameter "k" is 0
                        if params[j, 2, i] == 0:
                            JTJ_inv_temp = numpy.zeros((len(fguess) - 1, len(fguess) - 1), dtype=DOUBLE_PREC)
                            whichmodel[j] = 2

                            JTJ_inv_temp[0][0] = hlrclvpd_cov_matrix_afix[0][0]
                            JTJ_inv_temp[0][1] = hlrclvpd_cov_matrix_afix[2][0]
                            JTJ_inv_temp[1][0] = hlrclvpd_cov_matrix_afix[0][2]
                            JTJ_inv_temp[1][1] = hlrclvpd_cov_matrix_afix[2][2]

                            JTJ_inv[j, :, :] = numpy.copy(JTJ_inv_temp)


                        #;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
                        #;; check k, if less than zero estimate parameters without VPD effect and with fixed alpha of last window ;;
                        #;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
                        if params[j, 2, i] < 0:
                            '''
                            print("****************************")
                            print("Starting HLRC_Lloyd_afix")
                            print("****************************")
                            '''
                            #hlrcl_status_afix, hlrcl_beta_afix, hlrcl_rref_afix, hlrcl_beta_se_afix, hlrcl_rref_se_afix, hlrcl_residuals_afix, hlrcl_cov_matrix_afix, hlrcl_cor_matrix_afix, hlrcl_rmse_afix, hlrcl_ls_status_afix = nlinlts2(data=subd, lts_func="HLRC_Lloyd_afix", depvar='nee_f', indepvar_arr=['rg_f', 'tair_f', 'e0_1_from_tair', 'alpha_1_from_tair'], npara=2, xguess=numpy.array([fguess[1], fguess[3]]), mprior=numpy.array([fguess[1], fguess[3]], dtype=FLOAT_PREC), sigm=numpy.array([600, 80]), sigd=subd['nee_fs_unc'])

                            #### Starting the optimization using the "HLRC_Lloyd_afix" function
                            hlrcl_results_afix = nlinlts2(data=subd, lts_func="HLRC_Lloyd_afix", depvar='nee_f', indepvar_arr=['rg_f', 'tair_f', 'e0_1_from_tair', 'alpha_1_from_tair'], npara=2, xguess=numpy.array([fguess[1], fguess[3]]), mprior=numpy.array([fguess[1], fguess[3]], dtype=FLOAT_PREC), sigm=numpy.array([600, 80]), sigd=subd['nee_fs_unc'])

                            #### Setting the returned model parameters
                            hlrcl_status_afix = hlrcl_results_afix['status']
                            hlrcl_beta_afix = hlrcl_results_afix['beta']
                            hlrcl_rref_afix = hlrcl_results_afix['rref']
                            hlrcl_beta_se_afix = hlrcl_results_afix['beta_std_error']
                            hlrcl_rref_se_afix = hlrcl_results_afix['rref_std_error']
                            hlrcl_residuals_afix = hlrcl_results_afix['residuals']
                            hlrcl_cov_matrix_afix = hlrcl_results_afix['cov_matrix']
                            hlrcl_cor_matrix_afix = hlrcl_results_afix['cor_matrix']
                            hlrcl_rmse_afix = hlrcl_results_afix['rmse']
                            hlrcl_ls_status_afix = hlrcl_results_afix['ls_status']

                            if hlrcl_cov_matrix_afix is None or hlrcl_cor_matrix_afix is None:
                                raise ONEFluxPartitionBrokenOptError('HLRC_Lloyd_afix', site_id=site_id, year=year, day_begin=day_begin2, day_end=day_end2, prod=ustar_type, perc=percentile_num)

                            '''
                            print("numpy.array([fguess[1], fguess[3]])")
                            print(numpy.array([fguess[1], fguess[3]]))
                            print("hlrcl_beta_afix")
                            print(hlrcl_beta_afix)
                            print("hlrcl_rref_afix")
                            print(hlrcl_rref_afix)

                            print("hlrcl_beta_se_afix")
                            print(hlrcl_beta_se_afix)
                            print("hlrcl_rref_se_afix")
                            print(hlrcl_rref_se_afix)

                            print("====================")
                            print("hlrcl_residuals_afix")
                            print(hlrcl_residuals_afix)
                            print("hlrcl_cov_matrix_afix")
                            print(hlrcl_cov_matrix_afix)
                            print("hlrcl_cor_matrix_afix")
                            print(hlrcl_cor_matrix_afix)

                            print("len(hlrcl_residuals_afix)")
                            print(len(hlrcl_residuals_afix))
                            '''

                            #### Specifying which model we chose for this iteration (modified fguess)
                            whichmodel[j] = 2

                            res_cor[j] = (hlrcl_residuals_afix ** 2).sum() / (len(hlrcl_residuals_afix) * (1.0 - trimperc / 100.0) - 2)

                            #### Setting the parameters of this iteration (j -> modified fguess)
                            params[j, :, i] = numpy.array([alpha, hlrcl_beta_afix, 0, hlrcl_rref_afix, e0, 0, hlrcl_beta_se_afix, 0, hlrcl_rref_se_afix, e0_se])

                            p_cor[j, :, i] = numpy.array([NAN, NAN, NAN, NAN, hlrcl_cor_matrix_afix[0][1], NAN])

                            rmse[j] = hlrcl_rmse_afix

                            JTJ_inv[j, 0:2, 0:2] = numpy.copy(hlrcl_cov_matrix_afix)


                #;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
                #;; check if alpha or beta less than 0, if yes set to 0                                                 ;;
                #;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
                if params[j, 0, i] < 0 or params[j, 1, i] < 0:
                    '''
                    print("****************************")
                    print("Starting LloydT_E0fix")
                    print("****************************")
                    '''
                    #lt_status_e0fix, lt_rref_e0fix, lt_rref_se_e0fix, lt_residuals_e0fix, lt_cov_matrix_e0fix, lt_cor_matrix_e0fix, lt_rmse_e0fix, lt_ls_status_e0fix = nlinlts2(data=subd, lts_func="LloydT_E0fix", depvar='nee_f', indepvar_arr=['tair_f', 'e0_1_from_tair'], npara=1, xguess=numpy.array([fguess[3]]), mprior=numpy.array([fguess[3]], dtype=FLOAT_PREC), sigm=numpy.array([80]), sigd=subd['nee_fs_unc'])

                    #### Starting the optimization using the "LloydT_E0fix" function
                    lt_results_e0fix = nlinlts2(data=subd, lts_func="LloydT_E0fix", depvar='nee_f', indepvar_arr=['tair_f', 'e0_1_from_tair'], npara=1, xguess=numpy.array([fguess[3]]), mprior=numpy.array([fguess[3]], dtype=FLOAT_PREC), sigm=numpy.array([80]), sigd=subd['nee_fs_unc'])

                    #### Setting the returned model parameters
                    lt_status_e0fix = lt_results_e0fix['status']
                    lt_rref_e0fix = lt_results_e0fix['rref']
                    lt_rref_se_e0fix = lt_results_e0fix['rref_std_error']
                    lt_residuals_e0fix = lt_results_e0fix['residuals']
                    lt_cov_matrix_e0fix = lt_results_e0fix['cov_matrix']
                    lt_cor_matrix_e0fix = lt_results_e0fix['cor_matrix']
                    lt_rmse_e0fix = lt_results_e0fix['rmse']
                    lt_ls_status_e0fix = lt_results_e0fix['ls_status']

                    if lt_cov_matrix_e0fix is None or lt_cor_matrix_e0fix is None:
                        raise ONEFluxPartitionBrokenOptError('LloydT_E0fix', site_id=site_id, year=year, day_begin=day_begin2, day_end=day_end2, prod=ustar_type, perc=percentile_num)

                    '''
                    print("numpy.array([fguess[3]])")
                    print(numpy.array([fguess[3]]))
                    print("lt_rref_e0fix")
                    print(lt_rref_e0fix)

                    print("lt_rref_se_e0fix")
                    print(lt_rref_se_e0fix)

                    print("====================")
                    print("lt_residuals_e0fix")
                    print(lt_residuals_e0fix)
                    print("lt_cov_matrix_e0fix")
                    print(lt_cov_matrix_e0fix)
                    print("lt_cor_matrix_e0fix")
                    print(lt_cor_matrix_e0fix)

                    print("len(lt_residuals_e0fix)")
                    print(len(lt_residuals_e0fix))
                    '''

                    #### Specifying which model we chose for this iteration (j -> modified fguess)
                    whichmodel[j] = 4

                    res_cor[j] = (lt_residuals_e0fix ** 2).sum() / (len(lt_residuals_e0fix) * (1.0 - trimperc / 100.0) - 1)

                    #### Setting the parameters of this iteration (j -> modified fguess)
                    params[j, :, i] = numpy.array([0, 0, 0, lt_rref_e0fix, e0, 0, 0, 0, lt_rref_se_e0fix, e0_se])

                    p_cor[j, :, i] = numpy.array([NAN, NAN, NAN, NAN, NAN, NAN])

                    rmse[j] = lt_rmse_e0fix

                    JTJ_inv[j, 0, 0] = numpy.copy(lt_cov_matrix_e0fix)


                is_pars_ok = check_parameters(params=params[j, :, i], fguess=fguess)
                if is_pars_ok == 0:
                    rmse[j] = 9999.0

            # end of "for j"

        #### Find which iteration "j" that resulted in the most minimum rmse
        jmin = numpy.where(rmse == numpy.min(numpy.abs(rmse)))
        jmin = jmin[0]

        '''
        print("rmse")
        print(rmse)
        print("numpy.abs(rmse)")
        print(numpy.abs(rmse))
        print("numpy.min(numpy.abs(rmse))")
        print(numpy.min(numpy.abs(rmse)))
        print("jmin")
        print(jmin)
        print("jmin[0]")
        print(jmin[0])
        '''

        #### Check if the paramters chosen of the current set are valid
        is_pars_ok = check_parameters(params=params[jmin[0], :, i], fguess=fguess)

        '''
        print("i")
        print(i)
        print("is_pars_ok")
        print(is_pars_ok)

        #if i == 12:
        #    exit()
        '''

        #### This if statement is weird but it's in the pvwave code
        if ind[jmin[0], 1, i] == 6616: # TODO: investigate and replace statement
            msg = "DT EXIT EXCEPTION: exact number of indices"
            _log.critical(msg)
            raise ONEFluxPartitionError(msg)

        #### If the current set of parameters is valid
        #### then we choose it for the current window
        if is_pars_ok == 1:
            # my code
            '''
            if i >= 16 and i <= 28:
                print("###***###***###***#")
                print("i")
                print(i)
                print("i_ok")
                print(i_ok)
                print("whichmodel[jmin[0]]")
                print(whichmodel[jmin[0]])
                print("jmin")
                print(jmin)
                print("ind[jmin[0], :, i]")
                print(ind[jmin[0], :, i])
                print("###***###***###***#")
                #if i == 28:
                #    exit()
            '''
            params_all_for_ranges['i'][i] = i
            params_all_for_ranges['day'][i] = i * 4 + 1 - i * 2
            params_all_for_ranges['i_ok'][i] = i_ok
            params_all_for_ranges['alpha'][i] = params[jmin[0], 0, i]
            params_all_for_ranges['beta'][i] = params[jmin[0], 1, i]
            params_all_for_ranges['k'][i] = params[jmin[0], 2, i]
            params_all_for_ranges['rref'][i] = params[jmin[0], 3, i]
            params_all_for_ranges['e0'][i] = params[jmin[0], 4, i]
            #end of code

            params_ok[:, i_ok] = params[jmin[0], :, i]
            ind_ok[:, i_ok] = ind[jmin[0], :, i]
            p_cor_ok[:, i_ok] = p_cor[jmin[0], :, i]
            whichmodel_ok[i_ok] = whichmodel[jmin[0]]
            JTJ_inv_ok[i_ok, :, :] = JTJ_inv[jmin[0], :, :]
            res_cor_ok[i_ok] = res_cor[jmin[0]]
            i_ok = i_ok + 1

        #### else this window won't work and we will use the
        #### previous window
        else:
            # my code
            '''
            if i == 21:
                print("###***###***###***")
                print("i")
                print(i)
                print("i_nok")
                print(i_nok)
                print("###***###***###***")
                #exit()
            '''

            params_all_for_ranges['i'][i] = i
            params_all_for_ranges['day'][i] = i * 4 + 1 - i * 2
            params_all_for_ranges['i_ok'][i] = -9999
            params_all_for_ranges['alpha'][i] = -9999.0
            params_all_for_ranges['beta'][i] = -9999.0
            params_all_for_ranges['k'][i] = -9999.0
            params_all_for_ranges['rref'][i] = -9999.0
            params_all_for_ranges['e0'][i] = -9999.0
            #end of code

            params_nok[:, i_nok] = params[jmin[0], :, i]
            i_nok = i_nok + 1

        params_all[:, i] = params[jmin[0], :, i]
        params_all_timestamp[i, :] = numpy.append([is_pars_ok, day_begin], numpy.transpose(params[jmin[0], :, i]))
    # end of "for i"

    #### Setting the final valid parameters to be returned
    if i_ok > 0:
        params_return = params_ok[:, 0:i_ok]
        ind_return = ind_ok[:, 0:i_ok]
        p_correl_return = p_cor_ok[:, 0:i_ok]
        whichmodel_return = whichmodel_ok[0:i_ok]
        JTJ_inv_return = JTJ_inv_ok[0:i_ok, :, :]
        res_cor_return = res_cor_ok[0:i_ok]
    else:
        nan_arr = numpy.empty(len(fguess) + 3)
        nan_arr.fill(NAN)
        return nan_arr, None, None, None, None

    # My code (not in pvwave)
    i_ok_temp = 0
    for i in range(n_parasets):
        if params_all_for_ranges['i_ok'][i] >= 0:
            if i_ok_temp == 0:
                index_begin, index_end = 0, int(ind_return[2, i_ok_temp + 1])
#                print("index [ 0]: ", index_begin, index_end)
                params_all_for_ranges['ind_begin'][i] = index_begin
                params_all_for_ranges['ind_end'][i] = index_end
                params_all_for_ranges['subset_size'][i] = params_all_for_ranges['ind_end'][i] - params_all_for_ranges['ind_begin'][i]
                ### populate variability (STD) for input data
#                print("****STD [ 0]: ", index_begin, index_end, numpy.nanstd(data['nee_f'][data['nee_fqc'] == 0][index_begin:index_end]), numpy.nanstd(data['tair'][index_begin:index_end]), numpy.nanstd(data['rg'][index_begin:index_end]))
                params_all_for_ranges['nee_avg'][i] = numpy.nanmean(data['nee_f'][data['nee_fqc'] == 0][index_begin:index_end])
                params_all_for_ranges['ta_avg'][i] = numpy.nanmean(data['tair'][index_begin:index_end])
                params_all_for_ranges['rg_avg'][i] = numpy.nanmean(data['rg'][index_begin:index_end])
                params_all_for_ranges['nee_std'][i] = numpy.nanstd(data['nee_f'][data['nee_fqc'] == 0][index_begin:index_end])
                params_all_for_ranges['ta_std'][i] = numpy.nanstd(data['tair'][index_begin:index_end])
                params_all_for_ranges['rg_std'][i] = numpy.nanstd(data['rg'][index_begin:index_end])
            elif i_ok_temp == (i_ok - 1):
                index_begin, index_end = int(ind_return[2, i_ok_temp - 1]), int(numpy.max(data['ind']))
#                print("index [-1]: ", index_begin, index_end)
                params_all_for_ranges['ind_begin'][i] = index_begin
                params_all_for_ranges['ind_end'][i] = index_end
                params_all_for_ranges['subset_size'][i] = params_all_for_ranges['ind_end'][i] - params_all_for_ranges['ind_begin'][i]
                ### populate variability (STD) for input data
#                print("****STD [-1]: ", index_begin, index_end, numpy.nanstd(data['nee_f'][data['nee_fqc'] == 0][index_begin:index_end]), numpy.nanstd(data['tair'][index_begin:index_end]), numpy.nanstd(data['rg'][index_begin:index_end]))
                params_all_for_ranges['nee_avg'][i] = numpy.nanmean(data['nee_f'][data['nee_fqc'] == 0][index_begin:index_end])
                params_all_for_ranges['ta_avg'][i] = numpy.nanmean(data['tair'][index_begin:index_end])
                params_all_for_ranges['rg_avg'][i] = numpy.nanmean(data['rg'][index_begin:index_end])
                params_all_for_ranges['nee_std'][i] = numpy.nanstd(data['nee_f'][data['nee_fqc'] == 0][index_begin:index_end])
                params_all_for_ranges['ta_std'][i] = numpy.nanstd(data['tair'][index_begin:index_end])
                params_all_for_ranges['rg_std'][i] = numpy.nanstd(data['rg'][index_begin:index_end])

            elif i_ok_temp >= i_ok:
                index_begin, index_end = -9999, -9999
#                print("index [>=]: ", index_begin, index_end)
                params_all_for_ranges['ind_begin'][i] = index_begin
                params_all_for_ranges['ind_end'][i] = index_end
                params_all_for_ranges['subset_size'][i] = -9999
                ### populate variability (STD) for input data
#                print("****STD [>=]: ", index_begin, index_end, numpy.nanstd(data['nee_f'][data['nee_fqc'] == 0][index_begin:index_end]), numpy.nanstd(data['tair'][index_begin:index_end]), numpy.nanstd(data['rg'][index_begin:index_end]))
                params_all_for_ranges['nee_avg'][i] = NAN
                params_all_for_ranges['ta_avg'][i] = NAN
                params_all_for_ranges['rg_avg'][i] = NAN
                params_all_for_ranges['nee_std'][i] = NAN
                params_all_for_ranges['ta_std'][i] = NAN
                params_all_for_ranges['rg_std'][i] = NAN
            else:
                index_begin, index_end = int(ind_return[2, i_ok_temp - 1]), int(ind_return[2, i_ok_temp + 1])
#                print("index [el]: ", index_begin, index_end)
                params_all_for_ranges['ind_begin'][i] = index_begin
                params_all_for_ranges['ind_end'][i] = index_end
                params_all_for_ranges['subset_size'][i] = params_all_for_ranges['ind_end'][i] - params_all_for_ranges['ind_begin'][i]
                ### populate variability (STD) for input data
#                print("****STD [el]: ", index_begin, index_end, numpy.nanstd(data['nee_f'][data['nee_fqc'] == 0][index_begin:index_end]), numpy.nanstd(data['tair'][index_begin:index_end]), numpy.nanstd(data['rg'][index_begin:index_end]))
                params_all_for_ranges['nee_avg'][i] = numpy.nanmean(data['nee_f'][data['nee_fqc'] == 0][index_begin:index_end])
                params_all_for_ranges['ta_avg'][i] = numpy.nanmean(data['tair'][index_begin:index_end])
                params_all_for_ranges['rg_avg'][i] = numpy.nanmean(data['rg'][index_begin:index_end])
                params_all_for_ranges['nee_std'][i] = numpy.nanstd(data['nee_f'][data['nee_fqc'] == 0][index_begin:index_end])
                params_all_for_ranges['ta_std'][i] = numpy.nanstd(data['tair'][index_begin:index_end])
                params_all_for_ranges['rg_std'][i] = numpy.nanstd(data['rg'][index_begin:index_end])
            i_ok_temp = i_ok_temp + 1
        else:
            params_all_for_ranges['ind_begin'][i] = -9999
            params_all_for_ranges['ind_end'][i] = -9999
            params_all_for_ranges['subset_size'][i] = -9999

    var_names = 'alpha,beta,k,rref,e0,alpha_se,beta_se,k_se,rref_se,e0_se'
    var_names_timestamp = 'ok,day_begin,alpha,beta,k,rref,e0,alpha_se,beta_se,k_se,rref_se,e0_se'

    var_names_index = 'alpha,beta,k,rref,e0,alpha_se,beta_se,k_se,rref_se,e0_se,index1,index2,index3'

    #numpy.savetxt('test_es_python_before.csv', numpy.transpose(params_return), delimiter=',', fmt='%s')
    #numpy.savetxt('test_es_params_all_python.csv', numpy.transpose(params_all), delimiter=',', fmt='%s')
    #numpy.savetxt('test_es_params_all_python.csv', numpy.transpose(params_all), delimiter=',', header=var_names, fmt='%s')
    #numpy.savetxt('test_es_params_all_timestamp_python.csv', params_all_timestamp, delimiter=',', fmt='%s')
    #numpy.savetxt('test_es_params_all_timestamp_python.csv', params_all_timestamp, delimiter=',', header=var_names_timestamp, fmt='%s')

    #numpy.savetxt('test_es_params_index_all_timestamp_python.csv', numpy.transpose(numpy.concatenate((params_all, ind_ok), axis=0)), delimiter=',', header=var_names_index, fmt='%s')

    filename_range = 'nee_' + ustar_type + '_' + str(percentile_num) + '_' + site_id + '_' + str(year) + '_params_after_es_python.csv'
    numpy.savetxt(os.path.join(dt_output_dir, filename_range), params_all_for_ranges, delimiter=',', header=','.join(params_all_for_ranges.dtype.names), fmt='%s')
    #exit()
    # end of code

    _log.info("Finished estimate_parasets of daytime for nee_{u}_{p}_{s}_{y}".format(u=ustar_type, p=percentile_num, s=site_id, y=year))

    return numpy.concatenate((params_return, ind_return), axis=0), whichmodel_return, JTJ_inv_return, res_cor_return, p_correl_return
    #end of estimate_parasets

def percentiles_fn(data, columns, values=[0.0, 0.25, 0.5, 0.75, 1.0], remove_missing=False):
    """
    Task:   Get the data values corresponding to the percentile chosen at
            the "values" (array of percentiles) after sorting the data.

            return -1 if no data was found

    :param data: data structure for partitioning
    :type data: numpy.ndarray
    :param columns: columns or variable names of the data to be used
    :type columns: str array
    :param values: percentile values to be processed
    :type values: float array
    :param remove_missing: flag to remove missing values
    :type remove_missing: boolean
    """
    result = -1
    n_elements = data[columns[0]].shape[0]

    if n_elements <= 0:
        return result

    if remove_missing:
        data = nomi(data, columns)

    n_elements = data[columns[0]].shape[0]

    values = numpy.array(values)
    if max(values) > 1.0:
        values = values * 0.01

    #### Get an array of indices of the sorted data
    sorted_index_arr = numpy.argsort(data[columns[0]])

    ind = None
    #### Iterate through each percentile and get the corresponding
    #### value at that percentile of the sorted data
    for i in range(len(values)):
        if (values[i] < 0.0) or (values[i] > 1.0):
            return -1

        #### Setting ind to the percentile wanted
        if values[i] <= 0.5:
            ind = long(values[i] * n_elements)
        else:
            ind = long(values[i] * (n_elements + 1))

        if ind >= n_elements:
            ind = n_elements - long(1)

        if i == 0:
            result = data[columns[0]][sorted_index_arr[ind]]
        else:
            result = numpy.append(result, data[columns[0]][sorted_index_arr[ind]])

    return result



def uncert_via_gapFill(data, var, del_flag=False , nomsg=False, maxMissFrac=1.0, longestMarginalgap=60):
    """
    :Task: fill gaps of the chosen varname or column (for day time)

    :Explanation:   We fill the gaps by picking all the nulls in a certain window and
                    average the non gapped values in that window to fill the gaps in 
                    that window with the calculated average value.
                    We do this 6 times. Each time we cover certain conditions to fill
                    the gaps with (e.g TA_TOLERANCE, etc).
    
    :param data: data structure for partitioning
    :type data: numpy.ndarray
    """
    _log.debug("Starting uncert_gap_fill of daytime")

    # Setting defaults for Rg, Ta and VPD
    RG_TOLERANCE = 50.0
    TA_TOLERANCE = 2.5
    VPD_TOLERANCE = 5.0
    # window size
    t_window_orig = 14
    t_window = t_window_orig

    var = var.lower()

    # checking if data is hourly or half hourly data
    nperday = 24
    if data['hr'][1] - data['hr'][0] < 0.9:
        nperday = 48

    # initiating arrays to fill the gaps
    rg = numpy.copy(data['rg'])
    ta = numpy.copy(data['tair'])
    vpd = numpy.copy(data['vpd'])
    hr = numpy.copy(data['hr'].astype(float))
    tofill = numpy.copy(data[var])

    n = tofill.size
    filled_val = numpy.empty(n)
    filled_val.fill(NAN)

    filled_n = numpy.empty(n)
    filled_n.fill(NAN)

    filled_s = numpy.empty(n)
    filled_s.fill(NAN)

    filled_srob = numpy.empty(n)
    filled_srob.fill(NAN)

    filled_med = numpy.empty(n)
    filled_med.fill(NAN)

    fillMethod = numpy.zeros(n)
    fillWindow = numpy.zeros(n)
    tofill_orig = numpy.copy(tofill)
    tofill[:] = NAN

    largemarginGap = numpy.zeros(n)
    nnn = tofill.size
    oookkk = tofill_orig > NAN_TEST
    count = oookkk.sum()

    # "where" return 2 arrays, I am getting the 1st one with the indices
    # of the non null values
    oookkk = numpy.where(tofill_orig > NAN_TEST)[0]
    if oookkk.size == 0:
        firstvalid = -1
        lastvalid = -1
    else:
        firstvalid = numpy.amin(oookkk)
        lastvalid = numpy.amax(oookkk)

    # Checking if the consecutive gaps size in the beginning is too large
    if firstvalid > (48 * longestMarginalgap):
        largemarginGap[:(firstvalid + 1 - (48 * longestMarginalgap))] = 1
    # Checking if the consecutive gaps size in the end is too large
    if lastvalid < (nnn - (48 * longestMarginalgap)):
        largemarginGap[(lastvalid + (48 * longestMarginalgap)):] = 1

    def finalize_results():
        """
        internal function to append the gap filled variables to the main data array
        """
        _log.debug("uncert_gap_fill: Finalize Results")
        if del_flag:
            data[var][:] = filled_val
        else:
            add_empty_vars(data=data, records=filled_val, column=str(var + "_f_unc"))

        add_empty_vars(data=data, records=fillMethod, column=str(var + "_fmet_unc"))
        add_empty_vars(data=data, records=fillWindow, column=str(var + "_fwin_unc"))
        add_empty_vars(data=data, records=filled_n, column=str(var + "_fn_unc"))
        add_empty_vars(data=data, records=filled_s, column=str(var + "_fs_unc"))
        add_empty_vars(data=data, records=filled_srob, column=str(var + "_fsrob_unc"))
        add_empty_vars(data=data, records=filled_med, column=str(var + "_fmed_unc"))

        #toogapy = ((fillMethod == 1) & (fillWindow > 28)) | ((fillMethod == 2) & (fillWindow > 14)) | (fillMethod == 3)

        fillQC = (fillMethod > 0).astype(int) + \
                (((fillMethod == 1) & (fillWindow > 14)) | ((fillMethod == 2) & (fillWindow > 14)) | ((fillMethod == 3) & (fillWindow > 1))).astype(int) + \
                (((fillMethod == 1) & (fillWindow > 56)) | ((fillMethod == 2) & (fillWindow > 28)) | ((fillMethod == 3) & (fillWindow > 5))).astype(int)

        add_empty_vars(data=data, records=fillQC, column=str(var + "_fqc_unc"))
        add_empty_vars(data=data, records=(fillQC <= 1).astype(int), column=str(var + "_fqcok_unc"))


    # Check if gap percentage is too big
    if (float(count) / n) < (1.0 - maxMissFrac):
        filled_val = tofill_orig
        fillMethod[:] = 4
        fillWindow[:] = 9999.0
        filled_n[:] = NAN
        filled_s[:] = NAN
        finalize_results()
        return
    else:
        it_num = 0

        # Filling using meteorological look-up (Rg, Tair, VPD), window <=28 days (Cat. A)
        _log.debug("uncert_gap_fill: Starting loop #1")
        while True:
            #### Getting the indices of the nulls that are between
            #### the firstvalid and lastvalid (if the consecutive gaps are too big at both ends)
            ko = numpy.where((tofill < NAN_TEST) & (largemarginGap == 0))[0]
            count = len(ko)

            t_window = (it_num + 1) * t_window_orig

            #### Check if there are no gaps
            if count == 0:
                finalize_results()
                return

            #### Iterate through each index that needs to be filled
            for index in ko:
                #### w: Window of gaps to be covered
                w = numpy.append(index - numpy.arange(t_window / 2.0 * nperday), index + numpy.arange(t_window / 2.0 * nperday - 1) + 1)
                #### Clip all the indices in the window to be confined to the limits
                numpy.clip(w, 0, n - 1, out=w)
                w = w.astype(int)

                #### Get all the indices of the non gapped values for averaging
                ok4avg = numpy.where(tofill_orig[w] > NAN_TEST)[0]
                count = len(ok4avg)

                #### We need more than 9 non gapped values to be able to continue
                #### this process of averaging
                if count > 9:
                    #### Get all the non gapped values only
                    w = w[ok4avg]
                    #### Get all the indices of the non gapped values that
                    #### fit a certain condition or limits (e.g TA_TOLERANCE, etc)
                    ok4avg = numpy.where((abs(ta[w] - ta[index]) < TA_TOLERANCE) &
                                        (abs(rg[w] - rg[index]) < max(min(RG_TOLERANCE, rg[index]), 20)) &
                                        (abs(vpd[w] - vpd[index]) < VPD_TOLERANCE) &
                                        (rg[w] > NAN_TEST) &
                                        (vpd[w] > NAN_TEST) &
                                        (ta[w] > NAN_TEST))[0]
                    count2 = len(ok4avg)


                    # ok4avg = numpy.where((abs(ta[w] - ta[index]) < TA_TOLERANCE) &
                    #                     (~numpy.isclose(abs(ta[w] - ta[index]), TA_TOLERANCE, rtol=1e-07, atol=0.0)) &
                    #                     (abs(rg[w] - rg[index]) < max(min(RG_TOLERANCE, rg[index]), 20)) &
                    #                     (~numpy.isclose(abs(rg[w] - rg[index]), max(min(RG_TOLERANCE, rg[index]), 20), rtol=1e-07, atol=0.0)) &
                    #                     (abs(vpd[w] - vpd[index]) < VPD_TOLERANCE) &
                    #                     (~numpy.isclose(abs(vpd[w] - vpd[index]), VPD_TOLERANCE, rtol=1e-07, atol=0.0)) &
                    #                     (rg[w] > NAN_TEST) &
                    #                     (vpd[w] > NAN_TEST) &
                    #                     (ta[w] > NAN_TEST))[0]

                    #### Still checking if we have more than 9 non gapped values
                    if count2 > 9:
                        #### Get all the stats related to those non gapped values
                        mean_value = stats.tmean(tofill_orig[w[ok4avg]])
                        counts_value = tofill_orig[w[ok4avg]].size
                        std_value = stats.tstd(tofill_orig[w[ok4avg]])
                        median_value = numpy.median(tofill_orig[w[ok4avg]])
                        srob_value = robust.scale.mad(tofill_orig[w[ok4avg]])

                        #### Fill the gaps with the mean of the non gapped values
                        #### and save the other stats in new columns
                        filled_val[index] = mean_value
                        filled_n[index] = counts_value
                        filled_s[index] = std_value
                        filled_med[index] = median_value
                        filled_srob[index] = srob_value
                        fillMethod[index] = 1
                        fillWindow[index] = (it_num + 1) * t_window_orig

            #### Update tofill with all the newly filled indices
            tofill[:] = filled_val
            it_num = it_num + 1
            if it_num > 1: break
        # End of while loop

        t_window = t_window_orig

        #### Filling with meteorological drivers LUT (only Rg)
        #### Filling using meteoroligical look-up (Rg only), window <=14 days (Cat. A)
        tofill[:] = filled_val

        #pvwave_file_path = '../pvwave_NEE_f_1.csv'
        #file_basename = 'after_loop_1_1999_y'
        #var_name = 'NEE_fqc_unc'
        #compare_results_pv_py(py_data=data, pvwave_file_path=pvwave_file_path, var=var_name, file_basename=file_basename, single_array=fillMethod, save_csv=True, show_diff_index=True, show_diff_thresh=0.5)
        #exit()

        it_num = 0

        _log.debug("uncert_gap_fill: Starting loop #2")
        while True:
            t_window = (it_num + 1) * t_window_orig
            #### Getting the indices of the nulls that are between
            #### the firstvalid and lastvalid (if the consecutive gaps are too big at both ends)
            ko = numpy.where((tofill < NAN_TEST) & (largemarginGap == 0))[0]
            count = len(ko)

            #### Check if there are no gaps
            if count == 0:
                finalize_results()
                return

            #### Iterate through each index that needs to be filled
            for index in ko:
                #### w: Window of gaps to be covered
                w = numpy.append(index - numpy.arange(t_window / 2.0 * nperday), index + numpy.arange(t_window / 2.0 * nperday - 1) + 1)
                #### Clip all the indices in the window to be confined to the limits
                numpy.clip(w, 0, n - 1, out=w)
                w = w.astype(int)

                #### Get all the indices of the non gapped values for averaging.
                #### Also get all the indices of the non gapped values that
                #### fit a certain condition or limits (e.g TA_TOLERANCE, etc).
                ok4avg = numpy.where((abs(rg[w] - rg[index]) < max(min(RG_TOLERANCE, rg[index]), 20)) &
                                    (tofill_orig[w] > NAN_TEST) &
                                    (rg[w] > NAN_TEST))[0]

                '''ok4avg = numpy.where((abs(rg[w] - rg[index]) < max(min(RG_TOLERANCE, rg[index]), 20)) &
                                    (~numpy.isclose(abs(rg[w] - rg[index]), max(min(RG_TOLERANCE, rg[index]), 20), rtol=1e-07, atol=0.0)) &
                                    (tofill_orig[w] > NAN_TEST) &
                                    (rg[w] > NAN_TEST))[0]
                                    '''
                count = len(ok4avg)

                #### We need more than 9 non gapped values to be able to continue
                #### this process of averaging
                if count > 9:
                    #### Get all the stats related to those non gapped values
                    mean_value = stats.tmean(tofill_orig[w[ok4avg]])
                    counts_value = tofill_orig[w[ok4avg]].size
                    std_value = stats.tstd(tofill_orig[w[ok4avg]])
                    median_value = numpy.median(tofill_orig[w[ok4avg]])
                    srob_value = robust.scale.mad(tofill_orig[w[ok4avg]])

                    #### Fill the gaps with the mean of the non gapped values
                    #### and save the other stats in new columns
                    filled_val[index] = mean_value
                    filled_n[index] = counts_value
                    filled_s[index] = std_value
                    filled_med[index] = median_value
                    filled_srob[index] = srob_value
                    fillMethod[index] = 2
                    fillWindow[index] = (it_num + 1) * t_window_orig

            #### Update tofill with all the newly filled indices
            tofill[:] = filled_val
            it_num = it_num + 1
            if it_num > 0: break
        # End of while loop

        t_window_orig_half = 1

        #### still missing values then fill with average diurnal values, and increase time_window until all is filled
        #### Still missing values filled with average diurnal values +-1 hour, window 1 day (Cat. A)
        tofill[:] = filled_val
        it_num = 0

        #pvwave_file_path = '../pvwave_NEE_f_2.csv'
        #file_basename = 'after_loop_2_1999_y'
        #var_name = 'NEE_fqc_unc'
        #compare_results_pv_py(py_data=data, pvwave_file_path=pvwave_file_path, var=var_name, file_basename=file_basename, single_array=fillMethod, save_csv=True, show_diff_index=True, show_diff_thresh=0.5)
        #exit()

        _log.debug("uncert_gap_fill: Starting loop #3")
        while True:
            #### Getting the indices of the nulls that are between
            #### the firstvalid and lastvalid (if the consecutive gaps are too big at both ends)
            ko = numpy.where((tofill < NAN_TEST) & (largemarginGap == 0))[0]
            count = len(ko)

            t_window = (2 * it_num + 1) * t_window_orig_half

            #### Check if there are no gaps
            if count == 0:
                finalize_results()
                return

            #### Iterate through each index that needs to be filled
            for index in ko:
                #### w: Window of gaps to be covered
                w = numpy.append(index - numpy.arange(t_window / 2.0 * nperday), index + numpy.arange(t_window / 2.0 * nperday - 1) + 1)
                #### Clip all the indices in the window to be confined to the limits
                numpy.clip(w, 0, n - 1, out=w)
                w = w.astype(int)

                #### Get all the indices of the non gapped values for averaging.
                #### Also get all the indices of the non gapped values that
                #### fit a certain condition or limits (e.g TA_TOLERANCE, etc).
                ok4avg = numpy.where((abs(hr[w] - hr[index]) < 1.1) &
                                    (tofill_orig[w] > NAN_TEST))[0]
                count = len(ok4avg)

                #### We need more than 9 non gapped values to be able to continue
                #### this process of averaging
                if count > 9:
                    #### Get all the stats related to those non gapped values
                    mean_value = stats.tmean(tofill_orig[w[ok4avg]])
                    counts_value = tofill_orig[w[ok4avg]].size
                    std_value = stats.tstd(tofill_orig[w[ok4avg]])
                    median_value = numpy.median(tofill_orig[w[ok4avg]])
                    srob_value = robust.scale.mad(tofill_orig[w[ok4avg]])

                    #### Fill the gaps with the mean of the non gapped values
                    #### and save the other stats in new columns
                    filled_val[index] = mean_value
                    filled_n[index] = counts_value
                    filled_s[index] = std_value
                    filled_med[index] = median_value
                    filled_srob[index] = srob_value
                    fillMethod[index] = 3
                    fillWindow[index] = t_window

            #### Update tofill with all the newly filled indices
            tofill[:] = filled_val
            it_num = it_num + 1
            if it_num > 2: break
        # End of while loop

        #*********** Values that are filled until here are best filled, since itnum was always small
        #*********** Except for method 3 where the qc=2 would already be reached
        #**** now next iteration
        #### Filling with meteorological drivers LUT (all met)
        #### Filling using meteorological look-up (Rg, Tair, VPD), window >=28 days (Cat. B)
        it_num = 2

        #pvwave_file_path = '../pvwave_NEE_f_3.csv'
        #file_basename = 'after_loop_3_1999_y'
        #var_name = 'NEE_fqc_unc'
        #compare_results_pv_py(py_data=data, pvwave_file_path=pvwave_file_path, var=var_name, file_basename=file_basename, single_array=fillMethod, save_csv=True, show_diff_index=True, show_diff_thresh=0.5)
        #exit()

        _log.debug("uncert_gap_fill: Starting loop #4")
        while True:
            #### Getting the indices of the nulls that are between
            #### the firstvalid and lastvalid (if the consecutive gaps are too big at both ends)
            ko = numpy.where((tofill < NAN_TEST) & (largemarginGap == 0))[0]
            count = len(ko)

            t_window = (it_num + 1) * t_window_orig

            #### Check if there are no gaps
            if count == 0:
                finalize_results()
                return

            #### Iterate through each index that needs to be filled
            for index in ko:
                #### w: Window of gaps to be covered
                w = numpy.append(index - numpy.arange(t_window / 2.0 * nperday), index + numpy.arange(t_window / 2.0 * nperday - 1) + 1)
                #### Clip all the indices in the window to be confined to the limits
                numpy.clip(w, 0, n - 1, out=w)
                w = w.astype(int)

                #### Get all the indices of the non gapped values for averaging
                ok4avg = numpy.where(tofill_orig[w] > NAN_TEST)[0]
                count = len(ok4avg)

                #### We need more than 9 non gapped values to be able to continue
                #### this process of averaging
                if count > 9:
                    #### Get all the non gapped values only
                    w = w[ok4avg]
                    #### Get all the indices of the non gapped values that
                    #### fit a certain condition or limits (e.g TA_TOLERANCE, etc)
                    ok4avg = numpy.where((abs(ta[w] - ta[index]) < TA_TOLERANCE) &
                                        (abs(rg[w] - rg[index]) < max(min(RG_TOLERANCE, rg[index]), 20)) &
                                        (abs(vpd[w] - vpd[index]) < VPD_TOLERANCE) &
                                        (rg[w] > NAN_TEST) &
                                        (vpd[w] > NAN_TEST) &
                                        (ta[w] > NAN_TEST))[0]

                    '''ok4avg = numpy.where((abs(ta[w] - ta[index]) < TA_TOLERANCE) &
                                        (~numpy.isclose(abs(ta[w] - ta[index]), TA_TOLERANCE, rtol=1e-07, atol=0.0)) &
                                        (abs(rg[w] - rg[index]) < max(min(RG_TOLERANCE, rg[index]), 20)) &
                                        (~numpy.isclose(abs(rg[w] - rg[index]), max(min(RG_TOLERANCE, rg[index]), 20), rtol=1e-07, atol=0.0)) &
                                        (abs(vpd[w] - vpd[index]) < VPD_TOLERANCE) &
                                        (~numpy.isclose(abs(vpd[w] - vpd[index]), VPD_TOLERANCE, rtol=1e-07, atol=0.0)) &
                                        (rg[w] > NAN_TEST) &
                                        (vpd[w] > NAN_TEST) &
                                        (ta[w] > NAN_TEST))[0]
                                        '''

                    count2 = len(ok4avg)

                    #### Still checking if we have more than 9 non gapped values
                    if count2 > 9:
                        #### Get all the stats related to those non gapped values
                        mean_value = stats.tmean(tofill_orig[w[ok4avg]])
                        counts_value = tofill_orig[w[ok4avg]].size
                        std_value = stats.tstd(tofill_orig[w[ok4avg]])
                        median_value = numpy.median(tofill_orig[w[ok4avg]])
                        srob_value = robust.scale.mad(tofill_orig[w[ok4avg]])

                        #### Fill the gaps with the mean of the non gapped values
                        #### and save the other stats in new columns
                        filled_val[index] = mean_value
                        filled_n[index] = counts_value
                        filled_s[index] = std_value
                        filled_med[index] = median_value
                        filled_srob[index] = srob_value
                        fillMethod[index] = 1
                        fillWindow[index] = (it_num + 1) * t_window_orig

            #### Update tofill with all the newly filled indices
            tofill[:] = filled_val
            it_num = it_num + 1
            if it_num > 10: break
        # End of while loop

        t_window = t_window_orig

        #### Filling with meteorological drivers LUT (only Rg)
        #### Filling using meteorological look-up (Rg only), window >=14 days (Cat. B)
        tofill[:] = filled_val
        it_num = 1

        #pvwave_file_path = '../pvwave_NEE_f_4.csv'
        #file_basename = 'after_loop_4_1999_y'
        #var_name = 'NEE_fqc_unc'
        #compare_results_pv_py(py_data=data, pvwave_file_path=pvwave_file_path, var=var_name, file_basename=file_basename, single_array=fillMethod, save_csv=True, show_diff_index=True, show_diff_thresh=0.5)
        #exit()

        _log.debug("uncert_gap_fill: Starting loop #5")
        while True:
            t_window = (it_num + 1) * t_window_orig
            #### Getting the indices of the nulls that are between
            #### the firstvalid and lastvalid (if the consecutive gaps are too big at both ends)
            ko = numpy.where((tofill < NAN_TEST) & (largemarginGap == 0))[0]
            count = len(ko)

            #### Check if there are no gaps
            if count == 0:
                finalize_results()
                return

            #### Iterate through each index that needs to be filled
            for index in ko:
                #### w: Window of gaps to be covered
                w = numpy.append(index - numpy.arange(t_window / 2.0 * nperday), index + numpy.arange(t_window / 2.0 * nperday - 1) + 1)
                #### Clip all the indices in the window to be confined to the limits
                numpy.clip(w, 0, n - 1, out=w)
                w = w.astype(int)

                #### Get all the indices of the non gapped values for averaging.
                #### Also get all the indices of the non gapped values that
                #### fit a certain condition or limits (e.g TA_TOLERANCE, etc).
                ok4avg = numpy.where((abs(rg[w] - rg[index]) < max(min(RG_TOLERANCE, rg[index]), 20)) &
                                    (tofill_orig[w] > NAN_TEST) &
                                    (rg[w] > NAN_TEST))[0]

                '''ok4avg = numpy.where((abs(rg[w] - rg[index]) < max(min(RG_TOLERANCE, rg[index]), 20)) &
                                    (~numpy.isclose(abs(rg[w] - rg[index]), max(min(RG_TOLERANCE, rg[index]), 20), rtol=1e-07, atol=0.0)) &
                                    (tofill_orig[w] > NAN_TEST) &
                                    (rg[w] > NAN_TEST))[0]'''
                count = len(ok4avg)

                #### We need more than 9 non gapped values to be able to continue
                #### this process of averaging
                if count > 9:
                    #### Get all the stats related to those non gapped values
                    mean_value = stats.tmean(tofill_orig[w[ok4avg]])
                    counts_value = tofill_orig[w[ok4avg]].size
                    std_value = stats.tstd(tofill_orig[w[ok4avg]])
                    median_value = numpy.median(tofill_orig[w[ok4avg]])
                    srob_value = robust.scale.mad(tofill_orig[w[ok4avg]])

                    #### Fill the gaps with the mean of the non gapped values
                    #### and save the other stats in new columns
                    filled_val[index] = mean_value
                    filled_n[index] = counts_value
                    filled_s[index] = std_value
                    filled_med[index] = median_value
                    filled_srob[index] = srob_value
                    fillMethod[index] = 2
                    fillWindow[index] = (it_num + 1) * t_window_orig

            #### Update tofill with all the newly filled indices
            tofill[:] = filled_val
            it_num = it_num + 1
            if it_num > 10: break
        # End of while loop

        #**** still missing values then fill with average diurnal values, and increase time_window until all is filled
        #if not KEYWORD_SET(nomsg) THEN msg, /inf, 'Still missing values filled with average diurnal values +-1 hour, window 7-210 days (Cat. C)'
        t_window_orig_half = t_window_orig * 0.5
        t_window = t_window_orig_half

        tofill[:] = filled_val
        it_num = 0

        #pvwave_file_path = '../pvwave_NEE_f_5.csv'
        #file_basename = 'after_loop_5_1999_y'
        #var_name = 'NEE_fqc_unc'
        #compare_results_pv_py(py_data=data, pvwave_file_path=pvwave_file_path, var=var_name, file_basename=file_basename, single_array=fillMethod, save_csv=True, show_diff_index=True, show_diff_thresh=0.5)
        #exit()

        _log.debug("uncert_gap_fill: Starting loop #6")
        while True:
            #### Getting the indices of the nulls that are between
            #### the firstvalid and lastvalid (if the consecutive gaps are too big at both ends)
            ko = numpy.where((tofill < NAN_TEST) & (largemarginGap == 0))[0]
            count = len(ko)

            t_window = (it_num + 1) * t_window_orig_half

            #### Check if there are no gaps
            if count == 0:
                finalize_results()
                return

            #### Iterate through each index that needs to be filled
            for index in ko:
                #### w: Window of gaps to be covered
                w = numpy.append(index - numpy.arange(t_window / 2.0 * nperday), index + numpy.arange(t_window / 2.0 * nperday - 1) + 1)
                #### Clip all the indices in the window to be confined to the limits
                numpy.clip(w, 0, n - 1, out=w)
                w = w.astype(int)

                #### Get all the indices of the non gapped values for averaging.
                #### Also get all the indices of the non gapped values that
                #### fit a certain condition or limits (e.g TA_TOLERANCE, etc).
                ok4avg = numpy.where((abs(hr[w] - hr[index]) < 1.1) &
                                    (tofill_orig[w] > NAN_TEST))[0]
                count = len(ok4avg)

                #### We need more than 9 non gapped values to be able to continue
                #### this process of averaging
                if count > 9:
                    #### Get all the stats related to those non gapped values
                    mean_value = stats.tmean(tofill_orig[w[ok4avg]])
                    counts_value = tofill_orig[w[ok4avg]].size
                    std_value = stats.tstd(tofill_orig[w[ok4avg]])
                    median_value = numpy.median(tofill_orig[w[ok4avg]])
                    srob_value = robust.scale.mad(tofill_orig[w[ok4avg]])

                    #### Fill the gaps with the mean of the non gapped values
                    #### and save the other stats in new columns
                    filled_val[index] = mean_value
                    filled_n[index] = counts_value
                    filled_s[index] = std_value
                    filled_med[index] = median_value
                    filled_srob[index] = srob_value
                    fillMethod[index] = 3
                    fillWindow[index] = t_window

            #### Update tofill with all the newly filled indices
            tofill[:] = filled_val
            it_num = it_num + 1
            if it_num > 60: break

        # End of while loop

        #pvwave_file_path = '../pvwave_NEE_f_6.csv'
        #file_basename = 'after_loop_6_1999_y'
        #var_name = 'NEE_fqc_unc'
        #compare_results_pv_py(py_data=data, pvwave_file_path=pvwave_file_path, var=var_name, file_basename=file_basename, single_array=fillMethod, save_csv=True, show_diff_index=True, show_diff_thresh=0.5)

        #print("After the 6 loops")
        finalize_results()

        _log.debug("Finished uncert_gap_fill of daytime")
        return


'''
#### For testing purposes
def compare_results_pv_py(py_data, pvwave_file_path, var, file_basename, single_array=[], save_csv=False, show_diff_index=False, show_diff_thresh=0.001):
    print("Entering compare_results_pv_py")

    timestamp_list_temp =[]
    for i in range(len(py_data['year'])):
        year_value = int(py_data['year'][i])
        month_value = int(py_data['month'][i])
        day_value = int(py_data['day'][i])
        hour_value = int(py_data['hour'][i])
        minute_value = int(py_data['minute'][i])

        timestamp_list_temp.append(datetime(year=year_value,month=month_value,day=day_value,hour=hour_value,minute=minute_value))

    #pvwave_file_path = '../test_pv_dt_mms_error_range.csv'
    pvwave_data = numpy.genfromtxt(pvwave_file_path, delimiter=",", names=True)

    #var = 'NEE'
    #file_basename = 'file_generated_absho_1999_y'
    #file_basename = 'file_generated_before_gapfill_1999_y'
    figure_basename = file_basename + '__' + var

    if len(single_array) == 0:
        plot_comparison(timestamp_list=timestamp_list_temp, data1=py_data[var.lower()], data2=pvwave_data[var], label1='Python', label2='PV-Wave', title=var + " Data preparation comparison between pv-wave and python after error range", basename=figure_basename, show=False)
        if save_csv:
            numpy.savetxt(str(file_basename + '.csv'), numpy.column_stack((py_data[var.lower()], pvwave_data[var])), delimiter=',', fmt='%s')

        if show_diff_index:
            print("Big difference Indices between the 2 arrays:")
            print(numpy.where(abs(py_data[var.lower()] - pvwave_data[var]) > show_diff_thresh)[0])
    else:
        plot_comparison(timestamp_list=timestamp_list_temp, data1=single_array, data2=pvwave_data[var], label1='Python', label2='PV-Wave', title=var + " Data preparation comparison between pv-wave and python after error range", basename=figure_basename, show=False)
        if save_csv:
            numpy.savetxt(str(file_basename + '.csv'), numpy.column_stack((single_array, pvwave_data[var])), delimiter=',', fmt='%s')
        
        if show_diff_index:
            print("Big difference Indices between the 2 arrays:")
            print(numpy.where(abs(single_array - pvwave_data[var]) > show_diff_thresh)[0])



'''
