#!/usr/bin/env python
# command line to run:
#   python gapfilling.py config_all.txt    
import sys
import re
import numpy as N
import os
import logging

from oneflux import ONEFluxError
from oneflux.downscaling.functions import search_index, solarang, time_zone, residuals, rmean, \
                                          read_weather_papale, read_ERA5_da_clusterFR,write_csv
from oneflux.downscaling.gap_fill import *
from oneflux.downscaling.write_stat import *

log = logging.getLogger(__name__)

def read_config(file_config):
    # importo il file di configurazione
    with open(file_config) as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            line = line.strip()
            if len(line) == 0:
                continue
            line = line.split('#')[0]
            if len(line) == 0:
                continue
            line = line.split('=')
            line[0] = line[0].strip()
            line[1] = line[1].strip()
            log.debug('Config file entries: {l1} = {l2}'.format(l1=line[0], l2=line[1]))
            if line[0] == 'name_path_weather':
                name_path_weather = line[1]
            if line[0] == 'name_path_reanalysis':
                name_path_reanalysis = line[1]
            if line[0] == 'name_path_out':
                name_path_out = line[1]
            if line[0] == 'gapmax':
                gapmax = float(line[1])
            if line[0] == 'Site':
                name = line[1]
            if line[0] == 'FirstY':
                year_start = int(line[1])
            if line[0] == 'LastY':
                year_end = int(line[1])
            if line[0] == 'Lat':
                lat = float(line[1])
            if line[0] == 'Lon':
                lon = float(line[1])
            if line[0] == 'UTCtime':
                timeshift = float(line[1])
            if line[0] == 'timeres':
                weather_period = float(line[1])
            if line[0] == 'pixel':
                pixel = line[1]
                
    return {'name_path_weather': name_path_weather,
         'name_path_reanalysis': name_path_reanalysis,
         'name_path_out': name_path_out,
         'gapmax': gapmax,
         'Site': name,
         'FirstY': year_start,
         'LastY': year_end,
         'Lat': lat,
         'Lon': lon,
         'UTCtime': timeshift,
         'timeres': weather_period,
         'pixel': pixel
        }
def gapfilling(file_config):

    dict_config = read_config(file_config)
    id_lwdown_calc=7
    id_snow=8
    
    log.debug('Treatment for site: {s}'.format(s=dict_config['Site']))
    for k,v in dict_config.items():
        log.debug('Entry [{k}] = {v}'.format(k=k, v=v))

    clim_dict = read_ERA5_da_clusterFR(dict_config['Site'],year_start=dict_config['FirstY'],year_end=dict_config['LastY'],
                                       dir_input_era5=dict_config['name_path_reanalysis'],pixel=dict_config['pixel'])
                                       #lon_d = 0,lat_d=0,
                                       #dataset_name=''):
    clim = clim_dict['clim']
    log.debug('clim: {s}'.format(s=clim))
    climato_period = clim_dict['climato_period']
    avg = clim_dict['avg']
    climatoshift = clim_dict['climatoshift']
    
    for k in range(len(clim)):
       clim[k]=N.array(clim[k],float)
    # Time frequency of clim data (in hours)
    #   climato_period is set when calling read_climatology function
    diff_clim_weather=(int)(climato_period/dict_config['timeres'])
    
    #------------------------------------------------------------------------------------------- 
    # Download of the weather variables from FLUXNET dataset
    # for the i_th site stored in the site TXT file
    year=dict_config['FirstY']
    filename=dict_config['name_path_weather']+dict_config['Site']+'_'+str(year)+'_synth_hourly_allvars.csv'
    weather=read_weather_papale(dict_config['name_path_weather'],dict_config['Site'],1,dict_config['timeres'],str(year))
    julian=[]
    year_length=[]
    julian.extend((range(len(weather[0]))+N.ones(1)/2.)/N.array(24./dict_config['timeres']))
    year_length.extend(range(len(weather[0]))*N.array(0.)+N.array(len(weather[0])/(24./dict_config['timeres'])))
    
    for j in range(dict_config['LastY']-dict_config['FirstY']):
       year=dict_config['FirstY']+j+1
       filename=dict_config['name_path_weather']+dict_config['Site']+'_'+str(year)+'_synth_hourly_allvars.csv'
       weather_year=read_weather_papale(dict_config['name_path_weather'],dict_config['Site'],1,dict_config['timeres'],str(year))
       for k in range(len(weather_year)):      
          weather[k].extend(weather_year[k])
       julian.extend((range(len(weather_year[0]))+N.ones(1)/2.)/N.array(24./dict_config['timeres']))
       year_length.extend(range(len(weather_year[0]))*N.array(0.)+len(weather_year[0])/(24./dict_config['timeres']))
    
    for k in range(len(weather)):
       weather[k]=N.array(weather[k],float)
       
    julian=N.array(julian)
    year_length=N.array(year_length)
    
    weather_qc=N.array(weather)
    weather_qc=N.where(weather_qc==-9999,0,1)
    
    if (len(weather[0])/len(clim[0]) != (climato_period/dict_config['timeres'])):
       log.debug('For {s}'.format(s=dict_config['Site']))
       msg = 'Timelength of Clim and Weather datasets do not match'
       log.critical(msg)
       raise ONEFluxError(msg)
    
    
    #-------------------------------------------------------------------------------------------
    # Fill the gaps in the meteorological fields
    [clim_weather_period,weather_all_gapfill,weather_gapfill,weather_clim_period_gapfill,weather_clim_period_nogap,
     weather_clim_period,clim_nogap,stat]=gap_fill_func(weather,clim,diff_clim_weather,dict_config['timeres'],climato_period,
                                                        julian,year_length,dict_config['Lon'],dict_config['Lat'],dict_config['gapmax'],avg,climatoshift,dict_config['UTCtime'])
    
    if not os.path.exists(dict_config['name_path_out']):
        os.makedirs(dict_config['name_path_out'])
    
    write_stat(weather,clim_nogap,weather_clim_period_nogap,dict_config['UTCtime'],dict_config['timeres'],dict_config['name_path_out'],dict_config['Site'])
    
    write_stat_30min(weather,weather_all_gapfill,dict_config['UTCtime'],dict_config['timeres'],dict_config['name_path_out'],dict_config['Site'])
    write_stat_30min(weather,clim_weather_period,dict_config['UTCtime'],dict_config['timeres'],dict_config['name_path_out'],dict_config['Site']+'_nocorr')
    
    write_csv(weather_all_gapfill,dict_config['FirstY'],dict_config['LastY'],dict_config['timeres'],dict_config['Site'],dict_config['name_path_out'])
    
    write_csv(clim_weather_period,dict_config['FirstY'],dict_config['LastY'],dict_config['timeres'],dict_config['Site']+'_nocorr',dict_config['name_path_out'])

    log.debug(dict_config['name_path_out'])


def main(argv):
    args = argv[1:]
    log.debug(args)
    #start_process_total = datetime.datetime.now()
    gapfilling(args[0])
    #end_process_total = datetime.datetime.now()
    #elap_process_total = end_process_total - start_process_total           


if __name__ == "__main__":
    log.debug(sys.argv)
    main(sys.argv)
