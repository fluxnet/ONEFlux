'''
oneflux.downscaling.run_downscaling

For license information:
see LICENSE file or headers in oneflux.__init__.py

Main running code for downscaling. Applies downscaling starting from
folder 02__qc_auto. Also creates the two files with the statistics
and min/max for the inputs

@author: Nicolas Vuichard, Carlo Trotta, Gilberto Pastorello
@contact: nicolas.vuichard@lsce.ipsl.fr, trottacarlo@unitus.it, gzpastorello@lbl.gov
@date: 2024-11-05
'''
import os
import zipfile
import shutil
import sys
import datetime
import numpy as np
import pandas as pd
import datetime
import logging
import argparse

from oneflux.pipeline.common import ERA_FIRST_YEAR, ERA_LAST_YEAR
from oneflux.downscaling.gapfilling_prep import read_config, gapfilling
from oneflux import ONEFluxError, log_config

log = logging.getLogger(__name__)

DEFAULT_LOGGING_FILENAME = 'oneflux_downscaling.log'

ERA_FIRST_YEAR_INT = int(ERA_FIRST_YEAR)
ERA_LAST_YEAR_INT = int(ERA_LAST_YEAR)

def get_all_files(path='.', recursive=False):
    files = []
    sizes = []
    for root, dirs, filenames in os.walk(path):
        for fn in filenames:
            ffn = os.path.join(root, fn)
            files.append(ffn)
            sizes.append(os.path.getsize(ffn)/1000)
            if not recursive:
                break
    return (files, sizes)


def create_config(dir_files, file_config_name, pixel, dir_meteo_era, era_first_year, era_last_year, dir_input, dir_output):
    '''
    Use on of the *qca_meteo* files in dir_files to generate the downscaling configurations

    INPUT:
        dir_files: data directory containing 02_qc_auto directory
        file_config_name: name for the configuration file
    '''
    # import and parse one qca_meteo file
    for root1,dir1,file1 in os.walk(os.path.join(dir_files, dir_input)):
        for ff in file1:
            if not 'qca_meteo' in ff:
                continue
            if ff.endswith('.zip'):
                continue
            log.debug('Create configuration from file: %s' % os.path.join(root1,ff))
            with open(os.path.join(root1,ff)) as fm:
                for line in fm.readlines():
                    line = line.replace('\n','').replace('\r','')
                    if line.startswith('site,'):
                        site_code = line.split(',')[1]
                    if line.startswith('lat,'):
                        site_lat = line.split(',')[1]
                    if line.startswith('lon,'):
                        site_lon = line.split(',')[1]
                    if line.startswith('timezone,'):
                        site_timezone = line.split(',')[2]
                    if line.startswith('timeres,'):
                        site_timeres = '0.5' if line.split(',')[1] == 'halfhourly' else '1'
                    if line.startswith('TIMESTAMP'):
                        break
            break
        break

    with open(file_config_name,'w') as fo:
        str_config = [
            '# directory dove trovo i file *_qca_synth_allvars_*.csv',
            'name_path_weather  = %s' % os.path.join(dir_files, dir_input),
            '# directory dove trovo i file da ERA']
        str_config.append('name_path_reanalysis = %s' % dir_meteo_era)
        str_config.append('# directory di output')
        # str_config.append('name_path_out = %s' % os.path.join(dir_files,'06_meteo_era_new_monthly_%s' % pixel))
        str_config.append('name_path_out = %s' % os.path.join(dir_files, dir_output))
        str_config.append('gapmax = 6')
        str_config.append('# Info del sito')
        str_config.append('Site = %s' % site_code)
        str_config.append('FirstY = %d' % era_first_year)
        str_config.append('LastY = %d' % era_last_year)
        str_config.append('Lat = %s' % site_lat)
        str_config.append('Lon = %s' % site_lon)
        str_config.append('UTCtime = %s' % site_timezone)
        str_config.append('timeres = %s' % site_timeres)
        str_config.append('pixel = %s' % pixel)
        fo.write('\n'.join(str_config))
                 
    log.debug('Wrote file: %s' % file_config_name)


def run(dir_era5_co, dir_input, dir_output, era_first_year=ERA_FIRST_YEAR_INT, era_last_year=ERA_LAST_YEAR_INT):
    '''
    Main downscaling run function

    INPUT:
        dir_era5_co: directory with reanalysis data (ERA5) extracted for site pixel
        dir_input: site directory with site specific data to be used for downscaling (usually ending 02_qc_auto)
        dir_output: site directory where the downscaled results will be saved (usually ending in 06_meteo_era)
    '''

    start_run = datetime.datetime.now()
    
    # # directory degli input ERA5 da COPERNICUS
    # dir_era5_co = r'./ERA5_global_nc_for_downscaling_monthly' # r'f:\test_downscaling\input_era_CO'
    
    # # directory dove sposto i risultati del downscaling
    # dir_output = '/home/c.trotta/output_downscaling_2023/'
    
    # # directory dove trovo i file per qc_auto
    # # la struttura della cartella e':
    # #   dir_input_00\ <directory del sito\>\00_fp_dataset\
    # # ad esempio:
    # #   f:\test_downscaling\input_file_qcauto\SE-Svb_ex202310100833\00_fp_dataset\
    # dir_input = r'./input_file_qcauto_L2'# r'f:\test_downscaling\input_file_qcauto'
    # #dir_input_00 = r'./input_file_qcauto'# r'f:\test_downscaling\input_file_qcauto'

    stat_summary_file = os.path.join(dir_output, 'stat_summary_L2.csv')
    data02_max_min_file = os.path.join(dir_output, 'data_max_min_L2.csv')

    # pixel che uso per il downscaling
    combi_pixel = []
    for lat_d in [0]:#[-1,0,1]:
        for lon_d in [0]:#[-1,0,1]:
            combi_pixel.append('lon%+d__lat%+d' % (lon_d,lat_d))
    log.debug('Combi pixel selected: %s' % combi_pixel)
    # applico qc_auto a tutti i dataset scaricati con FPcreator
    # prima di qc_auto applico i range scaricati dalla tabella SQL

    # creo il file di configurazione e lancio il downscaling    
    lista_dir_ok = set()
    list_all_file, list_all_file_size = get_all_files(dir_input, recursive=True)
    for fname in list_all_file:
        if '_qca_meteo_' in fname:
            if os.path.basename(os.path.dirname(os.path.dirname(fname))) in dir_input: 
                lista_dir_ok.add(os.path.dirname(os.path.dirname(fname)))
    
    lista_dir_ok = list(lista_dir_ok)
    log.debug('Directories with results: {s}'.format(s=lista_dir_ok))
    
    item_gap_filling = []
    item_gap_filling_nook = []

    df_stat_t = pd.DataFrame()

    for ff in lista_dir_ok:
        sitecode = os.path.basename(ff).split('_')[0]
        log.debug('Found site code ({s}) in path ({p})'.format(s=sitecode, p=ff))
        for pixel in combi_pixel:                
            # controllo il numero di file ERA5
            nr_y = 1
            for y in range(era_first_year, era_last_year + 1):
                fn = os.path.join(dir_era5_co,
                    '%s__ERA5__reanalysis-era5-single-levels__%d__%s.csv' % (sitecode,y,pixel) )
                fnT = os.path.join(dir_era5_co,
                    '%s__ERA5T__reanalysis-era5-single-levels__%d__%s.csv' % (sitecode,y,pixel) )
                if os.path.exists(fn):
                    if os.path.exists(fnT):
                        os.remove(fnT)

                nr_y = nr_y * ((os.path.exists(fn)or(os.path.exists(fnT))))
                
                if nr_y == 0:
                    msg = 'Missing path: %s' % fn
                    log.critical(msg)
                    item_gap_filling_nook.append(msg)
                    raise ONEFluxError(msg)
            if nr_y == 0:
                continue
            file_config_name = os.path.join(ff,'config_%s%s.txt' % (
                  sitecode, '_%s' % pixel))
            #if not os.path.exists(file_config_name):
            create_config(ff, file_config_name, pixel, dir_era5_co,
                          era_first_year=era_first_year, era_last_year=era_last_year,
                          dir_input=dir_input, dir_output=dir_output)
            dict_config = read_config(file_config_name)
            # if not os.path.exists(os.path.join(dict_config['name_path_out'],
            #                                    'stat_%s.txt' % dict_config['Site'])):
                #create_config(ff,file_config_name,pixel)
            #gapfilling(file_config_name)
            #raise Exception('EXIT')
            item_gap_filling.append([file_config_name])
            
            # log.debug(os.path.join(dict_config['name_path_out'],'stat_%s.txt' % dict_config['Site']))
            # df_stat = pd.read_csv(os.path.join(dict_config['name_path_out'],'stat_%s.txt' % dict_config['Site']))
            # df_stat['Site'] = dict_config['Site']
            # df_stat['pixel'] = dict_config['pixel']
            # for col in df_stat.columns:
            #     df_stat.loc[(df_stat[col] == '-'),col] = N.nan
            # df_stat_t = pd.concat([df_stat_t,df_stat],ignore_index=True)
            # #f:\xONEflux\AT-Inn_ex202308301031_test_downscaling_2023_eraFR_ok\06_meteo_era_new_monthly_lon-1__lat-1\stat_AT-Inn.txt

    if len(item_gap_filling) == 1:
        log.debug('Configs for gapfilling: {d}'.format(d=item_gap_filling))
        gapfilling(file_config= item_gap_filling[0][0])
    elif len(item_gap_filling) > 1:
        msg = 'Multiple sites/files ({n}) to gapfill in single-site execution mode:'.format(n=len(item_gap_filling))
        log.critical(msg)
        raise ONEFluxError(msg)
    else: 
        msg = 'Incorrect number of items ({n}) to gapfill:'.format(n=len(item_gap_filling))
        log.critical(msg)
        raise ONEFluxError(msg)
                
    # df_stat_t.to_csv(os.path.join(dir_main,'stat_summary.csv'),index=False)
    # log.debugnew_monthly('\nwrite file: %s' % os.path.join(dir_main,'stat_summary.csv'))

    log.debug('Number of files downscaled: {d}, and NOT downscaled: {n}'.format(d=len(item_gap_filling), n=len(item_gap_filling_nook)))

    # raccolgo le statistiche in un unico file
    stat06 = []
    data02_max_min = []
    for root1,dir1,file1 in os.walk(dir_input): # r'f:\test_downscaling\input_file_qcauto'
        for dd in dir1:
            log.debug('Directory to be searched for files: {s}'.format(s=dd))
            for root2,dir2,file2 in os.walk(os.path.join(dir_input,dd)):
                for dd2 in dir2:
                    # esporto le statisriche ('06_meteo')
                    if dir_output in dd2:
                        if dd2 == '06_meteo_era_new_monthly_lon+0__lat+0':
                            if not os.path.exists( os.path.join(dir_input,dd,dd2.replace('_new_monthly_lon+0__lat+0','')) ):
                                shutil.copytree(
                                    os.path.join(dir_input,dd,dd2),
                                    os.path.join(dir_input,dd,dd2.replace('_new_monthly_lon+0__lat+0',''))
                                )
                                log.debug('copy {s1} as {s2}'.format(
                                    os.path.join(dir_input,dd,dd2),
                                    os.path.join(dir_input,dd,dd2.replace('_new_monthly_lon+0__lat+0',''))
                                ))
                        for root3,dir3,file3 in os.walk(os.path.join(dir_input,dd,dd2)):
                            for ff in file3:
                                if 'stat_' in ff:
                                    df = pd.read_csv(os.path.join(dir_input,dd,dd2,ff))
                                    df['file_name'] = ff
                                    df['site_directory'] = dd
                                    df['sitecode'] = dd.split('_')[0]
                                    df['dir06'] = dd2
                                    if '__lat' in dd2:
                                        df['lat_d'] = dd2.split('_')[-1]
                                        df['lon_d'] = dd2.split('_')[-3]
                                        df['pixel'] = '__'.join([dd2.split('_')[-1],dd2.split('_')[-3]])
                                    else:
                                        df['lat_d'] = ''
                                        df['lon_d'] = ''
                                        df['pixel'] = ''
                                    for col in df.columns:
                                        df.loc[(df[col] == '-'),col] = np.nan
                                    stat06.append(df)
                            break
                    # esporto max/min degli input ('02_qc_auto')
                    if dir_input in dd2:
                        for root3,dir3,file3 in os.walk(os.path.join(dir_input,dd,dd2)):
                            for ff in file3:
                                if not '_qca_synth_allvars_' in ff:
                                    continue
                                log.debug('Get min/max file: %s' % os.path.join(dir_input,dd,dd2,ff))
                                df_ff = pd.read_csv(os.path.join(dir_input,dd,dd2,ff))
                                df_dict = {'path_completa': [], 'var_name': [],'min_v': [],'max_v': []}
                                for col in df_ff.columns:
                                    if 'qcOK' in col:
                                        continue
                                    df_ff_valid = df_ff.loc[(df_ff[col + 'qcOK']==1)]
                                    df_dict['path_completa'].append(os.path.join(dir_input,dd,dd2,ff))
                                    df_dict['var_name'].append(col)
                                    df_dict['min_v'].append(df_ff_valid[col].min())
                                    df_dict['max_v'].append(df_ff_valid[col].max())
                                df_dict = pd.DataFrame.from_dict(df_dict)
                                data02_max_min.append(df_dict)
                    
                break
        break

    if stat06:
        stat06 = pd.concat(stat06,ignore_index=True)
        stat06.to_csv(stat_summary_file, index = False)

    if data02_max_min:
        data02_max_min = pd.concat(data02_max_min,ignore_index=True)
        data02_max_min.to_csv(data02_max_min_file, index=False)

    end_run = datetime.datetime.now()
    elapsed_time = end_run - start_run

    log.debug('%d files downscaled' % len(item_gap_filling))
    log.debug('%d files NOT downscaled' % len(item_gap_filling_nook))
    log.debug('Wrote file: %s' % stat_summary_file)
    log.debug('Wrote file: %s' % data02_max_min_file)
    log.debug('Run time: Start: %s, finish: %s, total runtime: %s' % (start_run, end_run, elapsed_time))


if __name__ == "__main__":

    # cli arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('eradir', metavar="ERA-DIR", help="Absolute path to ERA pixel extracted data directory", type=str)
    parser.add_argument('datadir', metavar="DATA-DIR", help="Absolute path to general data directory", type=str)
    parser.add_argument('sitedir', metavar="SITE-DIR", help="Relative path to site data directory (within data-dir)", type=str)
    parser.add_argument('-q', '--qc_auto_dir', help="Relative path to 02_qc_auto equivalent directory", type=str, dest='qcautodir', default='02_qc_auto')
    parser.add_argument('-m', '--meteo_era_dir', help="Relative path to 06_meteo_era equivalent directory", type=str, dest='meteoeradir', default='06_meteo_era')
    parser.add_argument('-l', '--logfile', help="Logging file path", type=str, dest='logfile', default=DEFAULT_LOGGING_FILENAME)
    args = parser.parse_args()

    # setup logging file and stdout
    log_config(level=logging.DEBUG, filename=args.logfile, std=True, std_level=logging.DEBUG)

    start_process = datetime.datetime.now()

    dir_input = os.path.join(args.datadir, args.sitedir, args.qcautodir)
    dir_output = os.path.join(args.datadir, args.sitedir, args.meteoeradir)
    run(dir_era5_co=args.eradir, dir_input=dir_input, dir_output=dir_output)

    end_process = datetime.datetime.now()
    elap_process = end_process - start_process
    log.debug('Process time: Start: %s, finish: %s, total runtime: %s' % (start_process, end_process, elap_process))
    