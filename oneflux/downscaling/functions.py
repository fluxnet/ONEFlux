import re
import math
import os
import sys
import calendar
import copy
import logging
import numpy as N
import pandas as pd

from scipy import stats
from scipy.optimize import leastsq
from oneflux.downscaling.constantes import *

log = logging.getLogger(__name__)

#-------------------------------------------------------------------------------------------
# function search_index
def search_index(var_name,line):
   i=0
   re_res = re.search(var_name, line[i])
   while not re_res:
      i=i+1
      re_res = re.search(var_name, line[i])
   return i
# end function
#-------------------------------------------------------------------------------------------

#---------------------------------------------------------------------
#- This subroutine computes the solar angle according to the method
#- used by GSWP and developed by J.C. Morill.
#- See for further details :
#- http://www.atmo.arizona.edu/~morrill/swrad.html
def solarang(julian, julian0, lon, lat, one_year):

   pi = 4.*math.atan(1.)
   #- 1) Day angle gamma
   gamma = 2.*pi*(julian-julian0)/one_year

   #- 2) Solar declination (assumed constant for a 24 hour period)  page 7 in radians
   dec = ( 0.006918-0.399912*math.cos(gamma)+0.070257*math.sin(gamma)-0.006758*math.cos(2*gamma)+0.000907*math.sin(2*gamma)-0.002697*math.cos(3*gamma)+0.00148*math.sin(3*gamma))
   decd = dec*(180/pi)
   #- maximum error 0.0006 rad (<3'), leads to error of less than 1/2 degree in zenith angle

   #- 3)  Equation of time  page 11
   et = ( 0.000075+0.001868*math.cos(gamma)-0.032077*math.sin(gamma)-0.014615*math.cos(2*gamma)-0.04089*math.sin(2*gamma))*229.18
   #- Get the time zones for the current time
   gmt = 24.*(julian-int(julian))

   val=time_zone(gmt, lon)
   zone=val[0]
   lhour=val[1]
   #--- 4) Local apparent time  page 13
   #--- 
   #--- ls     standard longitude (nearest 15 degree meridian)
   #--- le     local longtitude
   #--- lhour  local standard time
   #--- latime local apparent time
   #--- lcorr  longitudunal correction (minutes)
   #---
   ls = ((zone-1)*15)-180.
   lcorr = 4.*(ls-lon)*(-1)
   latime = lhour+lcorr/60.+et/60.
   if (latime <  0.):
      latime = latime+24
   if (latime >= 24.):
      latime = latime-24

   #--- 5) Hour angle omega  page 15
   #--- hour angle is zero at noon, positive in the morning
   #--- It ranges from 180 to -180
   #---
   #--- omegad is omega in degrees, omega is in radians
   #---
   omegad = (latime-12.)*(-15.)
   omega  = omegad*pi/180.

   #----- 6)  Zenith angle  page 15
   #----- csang cosine of zenith angle (radians)
   #----- llatd =  local latitude in degrees
   #----- llat  =  local latitude in radians
   llatd = lat
   llat  = llatd*pi/180.
   csang = N.maximum(0.,math.sin(dec)*math.sin(llat)+math.cos(dec)*math.cos(llat)*math.cos(omega))
   return csang
# end function solarang
#-------------------------------------------------------------------------------------------



#-------------------------------------------------------------------------------------------
# function time_zone
def time_zone(gmt, lon):
   #---
   #--- Convert longitude index to longtitude in degrees
   deg = lon
   #---
   #--- Determine into which time zone (15 degree interval) the
   #--- longitude falls.
   i=0
   while i in range(25):
      if (deg < (-187.5+(15*(i+1)))):
         zone = (i+1)
         if (zone == 25):
            zone = 1
         i=24
      i=i+1   
   #---
   #--- Calculate change (in number of hours) from GMT time to
   #--- local hour.  Change will be negative for zones < 13 and
   #--- positive for zones > 13.
   #---
   #--- There is also a correction for lhour < 0 and lhour > 23
   #--- to lhour between 0 and 23.
   if (zone < 13):
      change = zone-13
      lhour = gmt+change
   #---
   if (zone == 13):
      lhour = gmt
   #---
   if (zone > 13):
      change = zone-13
      lhour = gmt+change
   if (lhour <  0):
      lhour = lhour+24
   if (lhour >= 24):
      lhour = lhour-24
   return zone,lhour
# end function time_zone
#-------------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------------------
# function residuals
def residuals(p, y, x):
   err = y-p*x
   return err
# end function residuals
#-------------------------------------------------------------------------------------------

def rmean(binwidth, list):
    """
    Calculates a running mean of a single trace

    Arguments:

    binwidth    -- size of the bin in sampling points (pt).
    Obviously, it should be smaller than the length of the trace.


    Returns:

    A smoothed traced in a new stf window.

    """
    # creates a destination python list to append the data
#    list=N.asarray(list)
    dlist = N.empty((len(list)))

    # running mean algorithm
    for i in range(len(list)):

        if (len(list)-i) > binwidth:
            # append to list the running mean of `binwidth` values
            # N.mean(sweep) calculates the mean of list
            # sweep[p0:p10] takes the values in the vector between p0 and p10 (zero-based)
            dlist[i] = N.mean( list[i:(binwidth+i)] )

        else:
            # use all remaining points for the average:
            dlist[i] = N.mean( list[i:] )
    
    return dlist


# function read_weather
# function reading the weather fields of a yearly eddy-covariance dataset
# argument : file is file name
# returns a vector that contains the different weather fields
def read_weather_papale(path,name,qc,weather_period,year):
   nomfic      = path+'/'+name+'_qca_synth_allvars_'+year+'.csv'
   nb_entete   = 1
   separateur  = ','

   try:
      fic = open(nomfic, 'r')
   except IOError:
      log.debug("The file '{f}' does not exist, will be replaced by missing values".format(f=nomfic))
      length_year=365 + calendar.isleap(int(year))
      """
      test_february = cdtime.reltime(1, 'days since '+year+'-2-28')
      val_test_february=test_february.tocomp(cdtime.GregorianCalendar)
      if(val_test_february.month == 2):
         length_year=366
      else:
         length_year=365
      """
      log.debug('Length of year = {s}'.format(s=length_year))
      Ta_f=N.ones(int(length_year*24/weather_period))*-9999
      Psurf=N.ones(int(length_year*24/weather_period))*-9999
      VPD_f=N.ones(int(length_year*24/weather_period))*-9999
      WS_f=N.ones(int(length_year*24/weather_period))*-9999
      Precip_f=N.ones(int(length_year*24/weather_period))*-9999
      Rg_f=N.ones(int(length_year*24/weather_period))*-9999
      LWin=N.ones(int(length_year*24/weather_period))*-9999
      LWin_calc=N.ones(int(length_year*24/weather_period))*-9999
      Pa_f=N.ones(int(length_year*24/weather_period))*-9999
      WVP=N.ones(int(length_year*24/weather_period))*-9999
   else:
      header=fic.readline()
      colonnes = header.split(separateur)
      #---------------------------------------------------
      # Ta_f     : Air Temperature (C)
      # Precip_f : Precipitation (mm)
      # Rg_f     : Global Radiation (W m-2)
      # VPD_f    : Vapour Pressure Deficit (hPa)
      # WS_f     : Wind horizontal speed (m s-1)
      # LWin     : Incomming Longwave Radiation (W m-2)
      #---------------------------------------------------
      index_Ta_f     = search_index('Ta_f',colonnes)
      index_Precip_f = search_index('Precip_f',colonnes)
      index_Rg_f     = search_index('Rg_f',colonnes)
      index_VPD_f    = search_index('VPD_f',colonnes)
      index_WS_f     = search_index('WS_f',colonnes)
      index_LWin     = search_index('LWin_f',colonnes)
      index_LWin_calc  = search_index('LWin_calc',colonnes)
      index_Pa_f       = search_index('Pa_f',colonnes)

      index_Ta_fqc     = search_index('Ta_fqcOK',colonnes)
      index_Precip_fqc = search_index('Precip_fqcOK',colonnes)
      index_Rg_fqc     = search_index('Rg_fqcOK',colonnes)
      index_VPD_fqc    = search_index('VPD_fqcOK',colonnes)
      index_WS_fqc     = search_index('WS_fqcOK',colonnes)
      index_LWin_fqc   = search_index('LWin_fqcOK',colonnes)
      index_LWin_calcqc= search_index('LWin_calcqcOK',colonnes)
      index_Pa_fqc     = search_index('Pa_fqcOK',colonnes)

      Ta_f      = []
      Precip_f  = []
      Rg_f      = []   
      VPD_f     = []
      WS_f      = []
      LWin      = []
      LWin_calc = []
      Pa_f      = []

      for ligne in fic:
         ligne = ligne.strip()
         colonnes = ligne.split(separateur)

         if((qc==1)and(float(colonnes[index_Ta_fqc])!=1.)):
            Ta_f.append(-9999)
         else:
            Ta_f.append(colonnes[index_Ta_f])

         if((qc==1)and(float(colonnes[index_Precip_fqc])!=1.)):
            Precip_f.append(-9999)
         else:
            Precip_f.append(colonnes[index_Precip_f])

         if((qc==1)and(float(colonnes[index_Rg_fqc])!=1.)):
            Rg_f.append(-9999)
         else:
            Rg_f.append(colonnes[index_Rg_f])

         if((qc==1)and(float(colonnes[index_VPD_fqc])!=1.)):
            VPD_f.append(-9999)
         else:   
            VPD_f.append(colonnes[index_VPD_f])

         if((qc==1)and(float(colonnes[index_WS_fqc])!=1.)):
            WS_f.append(-9999)
         else:         
            WS_f.append(colonnes[index_WS_f])

         if((qc==1)and(float(colonnes[index_LWin_fqc])!=1.)):
            LWin.append(-9999)
         else:
            LWin.append(colonnes[index_LWin])

         if((qc==1)and(float(colonnes[index_LWin_calcqc])!=1.)):
            LWin_calc.append(-9999)
         else:
            LWin_calc.append(colonnes[index_LWin_calc])

         if((qc==1)and(float(colonnes[index_Pa_fqc])!=1.)):
            Pa_f.append(-9999)
         else:         
            Pa_f.append(colonnes[index_Pa_f])


      Ta_f=N.array(Ta_f,float)
      Precip_f=N.array(Precip_f,float)
      Rg_f=N.array(Rg_f,float)
      VPD_f=N.array(VPD_f,float)
      WS_f=N.array(WS_f,float)
      LWin=N.array(LWin,float)   
      LWin_calc=N.array(LWin_calc,float)  
      Pa_f=N.array(Pa_f,float)

      # Correct for abnormal Rg negative values
      Rg_f=N.where(N.logical_and((Rg_f!=-9999), (Rg_f<0.)),0.,Rg_f)
      # Correct for abnormal Precip negative values
      Precip_f=N.where(N.logical_and((Precip_f!=-9999),(Precip_f<0.)),0.,Precip_f)
      # Conversion from kPa to Pa
      Pa_f=N.where(Pa_f!=-9999, Pa_f*1000., Pa_f)
      # Conversion from hPa to Pa
      VPD_f=N.where(VPD_f!=-9999, VPD_f*100., VPD_f)
      # Conversion from Celsius to Kelvin
      Ta_f=N.where(Ta_f!=-9999, Ta_f+273.15, Ta_f)
      # Conversion from "mm per timestep" to "kg m-2 s-1"
      Precip_f=N.where(Precip_f!=-9999, Precip_f/(weather_period*60*60), Precip_f)
      # Conversion from VPD (Vapour Pressure Deficit, Pa) to WVP (Warer Vapor Pressure, Pa)
      WVP=N.ones(len(Ta_f))*-9999
      for i in range(len(VPD_f)):
         if((VPD_f[i] != -9999)and(Ta_f[i]!=-9999)):
            # Magnus Tetens (Murray, 1967) http://cires.colorado.edu/~voemel/vp.html      
            if(Ta_f[i]<273.15):
               eg=c74*N.exp(c70*(Ta_f[i]-273.15)/(Ta_f[i]-c71))
            else:
               eg=c74*N.exp(c72*(Ta_f[i]-273.15)/(Ta_f[i]-c73))

            WVP[i]=(eg-VPD_f[i])
      
      fic.close()
      
   weather= [Ta_f.tolist(), Pa_f.tolist(), VPD_f.tolist(), WS_f.tolist(), Precip_f.tolist(), Rg_f.tolist(), LWin.tolist(),LWin_calc.tolist()]
   
   return weather
# end function
#-------------------------------------------------------------------------------------------
  

def read_ERA5_da_clusterFR(sitecode,year_start=1981,year_end=2022,dir_input_era5='',pixel='',dataset_name=''):
  # importa il file ERA5 scaricato dal clusterFR
  #dir_input_era5 = "/my-drive/My Drive/downscaling_nrt/da_read_climatology"
  log.debug('Dataset name: {s}'.format(s=dataset_name))
  log.debug('Site code: {s}'.format(s=sitecode))
  log.debug('ERA5 input dir: {s}'.format(s=dir_input_era5))
  log.debug('Pixel used for downscaling: {s}'.format(s=pixel))
  dir_input_era5 = os.path.normpath(dir_input_era5)
  era5_file_input_dict = {'file': [],'year': []}
  for root,dirw,files in os.walk(dir_input_era5):
    for f in files:
      #log.debug(f)
      #if not f.endswith('__lon%+d__lat%+d.csv' % (lon_d,lat_d)):
      #  continue
      #if not dataset_name in f:
      #  continue
      # AT-Fue_ERA5_1983.csv
      if not f.startswith(sitecode+'_'):
          continue
      if not pixel == '':
          if not pixel in f:
              continue
      if len(os.path.basename(f).split('_')) == len('AT-Fue_ERA5_1983.csv'.split('_')):
          if (int) (os.path.basename(f).split('_')[2].replace('.csv','')) > year_end:
              continue
          if (int) (os.path.basename(f).split('_')[2].replace('.csv','')) < year_start:
              continue
          year_f = (int) (os.path.basename(f).split('_')[2].replace('.csv',''))
      if len(os.path.basename(f).split('__')) == len('BE-Bra__ERA5__reanalysis-era5-single-levels__1981__lon+0__lat+0.csv'.split('__')):
          if (int) (os.path.basename(f).split('__')[3].replace('.csv','')) > year_end:
              continue
          if (int) (os.path.basename(f).split('__')[3].replace('.csv','')) < year_start:
              continue
          year_f = (int) (os.path.basename(f).split('__')[3].replace('.csv',''))
      era5_file_input_dict['file'].append(str(os.path.join(root,f)))
      era5_file_input_dict['year'].append(year_f)
  
  era5_file_input_dict = pd.DataFrame.from_dict(era5_file_input_dict)
  era5_file_input_dict = era5_file_input_dict.sort_values(by=['year'])

  era5_file_input = era5_file_input_dict['file'].tolist()

  cnt_f = len(era5_file_input)
  clim = []

  if cnt_f == 0:
    raise Exception('ERROR: directory: %s is EMPTY' % dir_input_era5 )

  for f_era5 in era5_file_input:
    # controllo che il range temporale sia coerente
    #BE-Lcr__ERA5__reanalysis-era5-single-levels__2022__lon+0__lat+0
    #if (int) (os.path.basename(f_era5).split('__')[3].replace('.csv','')) > year_end:
    #    continue
    #if (int) (os.path.basename(f_era5).split('__')[3].replace('.csv','')) < year_start:
    #    continue
    if len(os.path.basename(f_era5).split('_')) == len('AT-Fue_ERA5_1983.csv'.split('_')):
        if (int) (os.path.basename(f_era5).split('_')[2].replace('.csv','')) > year_end:
            continue
        if (int) (os.path.basename(f_era5).split('_')[2].replace('.csv','')) < year_start:
            continue
    if len(os.path.basename(f_era5).split('__')) == len('BE-Bra__ERA5__reanalysis-era5-single-levels__1981__lon+0__lat+0.csv'.split('__')):
        if (int) (os.path.basename(f_era5).split('__')[3].replace('.csv','')) > year_end:
            continue
        if (int) (os.path.basename(f_era5).split('__')[3].replace('.csv','')) < year_start:
            continue
    log.debug('Opening file (%d): %s ' % (cnt_f, f_era5))
    cnt_f = cnt_f - 1

    with open(f_era5) as f:
      f_input = f.readlines()
      log.debug('Number of items in ERA5 input file: {s}'.format(s=len(f_input[0].replace('\n','').split(','))))
    # [Ta_f.tolist(), Pa_f.tolist(), VPD_f.tolist(), WS_f.tolist(), Precip_f.tolist(), Rg_f.tolist(), LWin.tolist(),LWin_calc.tolist()]
      if len(clim) == 0:
        for k in range(len(f_input)):
          clim.append(f_input[k].replace('\n','').split(','))
      else:
        for k in range(len(clim)):
          clim[k].extend(f_input[k].replace('\n','').split(','))
     
  for k in range(len(clim)):
    clim[k] = N.array(clim[k],float)

    # Time frequency of clim data (in hours)
    #   climato_period is set when calling read_climatology function
    climato_period = 1
    #weather_period_array = dict_siteinfo['timeres']
    #diff_clim_weather=(int)(climato_period/weather_period_array)

    avg=N.zeros((len(clim)),float)
    climatoshift=N.zeros((len(clim)),float)

    avg[4]=1
    avg[5]=1
    avg[6]=1
    avg[7]=1
    climatoshift[0]=1
    climatoshift[1]=1
    climatoshift[2]=1
    climatoshift[3]=1

    #if(dict_config['format_weather']=='papale'):
    #   id_lwdown_calc=7
    #   id_snow=8
    id_lwdown_calc=7
    id_snow=8

  result_dict = {'clim': clim,'climato_period': climato_period,'avg': avg,'climatoshift': climatoshift,
                 'id_lwdown_calc': id_lwdown_calc,'id_snow': id_snow}
  return result_dict

#-------------------------------------------------------------------------------------------
# function write_csv
def write_csv(weather_gapfill,year_start,year_end,weather_period,name,path):
   weather_out=copy.deepcopy(weather_gapfill)

   for k in range(len(weather_out)):
      weather_out[k]=N.array(weather_out[k],float)

   # Conversion from Pa to kPa
   weather_out[id_psurf]= weather_out[id_psurf]/1000.
   # Conversion from Pa to hPa
   weather_out[id_vpd]= weather_out[id_vpd]/100.
   # Conversion from Kelvin to Celsius
   weather_out[id_tair]= weather_out[id_tair]-273.15
   # Conversion from "kg m-2 s-1" to "mm per timestep"
   weather_out[id_precip]= weather_out[id_precip]*weather_period*60*60

   line_end=os.linesep
   ind=0
#   print 'dans write_csv'
#   print 'year_start=',year_start
   for j in range(year_end-year_start+1):
      year=year_start+j
      #print(os.path.join(path,name+'_'+str(year)+'.csv'))
      fic = open(os.path.join(path,name+'_'+str(year)+'.csv'), 'w')
      for i in range(len(weather_out)-1):
         fic.write("%s," % (label_text[i]))
      fic.write("%s" % (label_text[len(weather_out)-1]))
      fic.write("\n")
#      print path+name+str(year)+'.txt'
      length_year=365 + calendar.isleap(int(year))
      """
      test_february = cdtime.reltime(1, 'days since '+str(year)+'-2-28')
      val_test_february=test_february.tocomp(cdtime.GregorianCalendar)
      if(val_test_february.month == 2):
         length_year=366
      else:
         length_year=365
      """
      for day in range(int(length_year*24/weather_period)):
         for i in range(len(weather_out)-1):
            fic.write("%f," % (weather_out[i][ind]))
         fic.write("%f" % (weather_out[len(weather_out)-1][ind]))
         fic.write("\n")
         ind=ind+1

      fic.close() 


#-------------------------------------------------------------------------------------------
# funzioni da genutil
def rms(x, y, weights=None, centered=0, biased=1):
    """
    Function: __rms
    Description of function:
        Does the main computation for returning rms. See documentation
        of rms() for details.
    """

    return std(x - y, centered=centered, biased=biased, weights=weights)

def std(x, weights=None, centered=1, biased=1):
    """
    Function: __std
    Description of function:
        Does the main computation for returning standard deviation. See
        documentation of std() for details.
    """
    return N.ma.sqrt(variance(x, weights=weights,
                                    centered=centered, biased=biased))

def variance(x, weights=None, centered=1, biased=1):
    """
    Function: __variance
    Description of function:
        Does the main computation for returning variance. See documentation
        of variance() for details.
    """
    return covariance(x, x, weights=weights,
                        centered=centered, biased=biased)

def covariance(x, y, weights=None, centered=1, biased=1):
    """
    Function: __covariance
    Description of function:
        Does the main computation for returning covariance. See documentation
        of covariance() for details.
    """
    if weights is not None and biased != 1:
        raise Exception(
            'Error in covariance, you cannot have weights and unbiased together')

    if centered == 1:
        xmean = N.ma.average(x, weights=weights, axis=0)
        ymean = N.ma.average(y, weights=weights, axis=0)
        x = x - xmean
        y = y - ymean
        del(xmean)
        del(ymean)
    #
    if weights is None:
        weights = N.ma.ones(x.shape, dtype=x.dtype.char)
    # if not ((x.mask is None) or (x.mask is MV2.nomask)):
    #     weights = N.ma.masked_where(x.mask, weights)
    if biased == 1:
        cov = N.ma.sum(x * y * weights, axis=0) / \
            N.ma.sum(weights, axis=0)
    else:
        cov = N.ma.sum(x * y, axis=0) / (N.ma.count(x * y, axis=0) - 1)

    return cov

def correlation(x, y, weights=None, centered=1, biased=1):
    """
    Function: __correlation
    Description of function:
        Does the main computation for returning correlation. See documentation
        of correlation() for details.
    """
    cov = covariance(x, y, weights=weights, centered=centered, biased=biased)
    sx = std(x, weights=weights, centered=centered, biased=biased)
    sy = std(y, weights=weights, centered=centered, biased=biased)
    return cov / (sx * sy)

#-------------------------------------------------------------------------------------------
# functions previously in write_stat.py
def write_stat(weather,clim_nogap,weather_clim_period_nogap,timeshift,weather_period,path,name):
    #fic=open(path+'stat_'+name+'.txt', 'w')
    fic=open(os.path.join(path,'stat_'+name+'.txt'), 'w')

    fic.write("Var,Unit,Percentage of Gaps,Slope,Intercept,RMSEbc,RMSEac,Corr,Mean,Std,MAEbc,MAEac\n")


    for k in range(len(weather)):
      val1=(1-(N.ma.masked_values(weather[k],-9999).count()/float(len(weather[k]))))*100

      if(k==id_psurf):
          # Conversion from Pa to kPa
          a=clim_nogap[k]/1000.
          b=weather_clim_period_nogap[k]/1000.
      elif(k==id_vpd):
          # Conversion from Pa to hPa
          a=clim_nogap[k]/100.
          b=weather_clim_period_nogap[k]/100.          
      elif(k==id_tair):
          # Conversion from Kelvin to Celsius
          a=clim_nogap[k]-273.15
          b=weather_clim_period_nogap[k]-273.15
      elif(k==id_precip):
          # Conversion from "kg m-2 s-1" to "mm per timestep"
          a=clim_nogap[k]*weather_period*60*60
          b=weather_clim_period_nogap[k]*weather_period*60*60
      else:
          a=clim_nogap[k]
          b=weather_clim_period_nogap[k]
          
      if((k==id_swdown)or(k==id_ws)):
         if(len(a)==0):
            stat=N.zeros(2,float)
            stat[0]='nan'
         else:
            #stat=leastsq(residuals,1.,args=(b,a))
            stat1=leastsq(residuals,1.,args=(b,a))
            stat=N.zeros(2, dtype=float)
            #stat=N.array(stat[0], dtype=float)
            stat[0]=stat1[0][0]
            stat[1]=0
            #stat=N.array(stat,float)
            #stat[1]=0
      elif(k==id_precip):
         stat=N.zeros(2,float)
         if(len(a)==0):
            stat[0]='nan'
            stat[1]=0
         else:
            stat[0]=sum(b)/sum(a)
            stat[1]=0
      else:
          if(len(a)==0):
            stat=N.zeros(2,float)
            stat[0]='nan'
          else:
            # stat=statistics.linearregression(b,x=a)
            # stat=linearregression(b,x=a)
            slope, intercept, r, p, std_err = stats.linregress(a, b)
            stat=N.zeros(2,float)
            stat[0] = slope
            stat[1] = intercept

      if(str(stat[0])!='nan'):
         slope=stat[0]
         intercept=stat[1]
      else:
         slope=1
         intercept=0


      fic.write("%s," % label_var_fluxnet[k])
      fic.write("%s," % label_units_fluxnet[k])
      fic.write("%4.2f," % val1)
      if(val1 < 100):
          valmean=b.mean()
          valstd=b.std()
          fic.write("%4.2f," % float(slope))
          if(k!=id_precip):
              # val2=statistics.rms(a,b)
              # val3=statistics.rms(a*slope+intercept,b)
              # val4=statistics.correlation(a,b)
              val2=rms(a,b)
              val3=rms(a*slope+intercept,b)
              val4=correlation(a,b)

              fic.write("%4.2f," % float(intercept))
              fic.write("%4.2f," % val2)
              fic.write("%4.2f," % val3)
              fic.write("%4.2f," % val4)
              fic.write("%4.2f," % valmean)
              fic.write("%4.2f," % valstd)
              fic.write("%4.2f," % N.mean(abs(a-b)))
              fic.write("%4.2f\n" % N.mean(abs((a*slope+intercept)-b)))
          else:
              fic.write("-,-,-,-,")
              fic.write("%4.2f," % valmean)
              fic.write("%4.2f," % valstd)
              fic.write("-,-\n")
      else:
          fic.write("-,-,-,-,-,-,-,-,-\n")
    fic.close()


def write_stat_30min(weather,weather_gapfill,timeshift,weather_period,path,name):
    #fic=open(path+'stat30_'+name+'.txt', 'w')
    fic=open(os.path.join(path,'stat30_'+name+'.txt'), 'w')

    fic.write("Var,Unit,Percentage of Gaps,Slope,Intercept,RMSE,Corr\n")


    for k in range(len(weather)):
      data=N.ma.masked_values(weather[k],-9999)
      model_temp=N.where(weather[k]==-9999,-9999,weather_gapfill[k])
      model=N.ma.masked_values(model_temp,-9999)

      val1=(1-(N.ma.masked_values(weather[k],-9999).count()/float(len(weather[k]))))*100

      if(k==id_psurf):
          # Conversion from Pa to kPa
          a=model/1000.
          b=data/1000.
      elif(k==id_vpd):
          # Conversion from Pa to hPa
          a=model/100.
          b=data/100.          
      elif(k==id_tair):
          # Conversion from Kelvin to Celsius
          a=model-273.15
          b=data-273.15
      elif(k==id_precip):
          # Conversion from "kg m-2 s-1" to "mm per timestep"
          a=model*weather_period*60*60
          b=data*weather_period*60*60
      else:
          a=model
          b=data
          
#      if(k==id_swdown):
#         if(len(a)==0):
#            stat=N.zeros(2)
#            stat[0]='nan'
#         else:
#            stat=leastsq(residuals,1.,args=(b,a))
#            stat=N.array(stat)
#            stat[1]=0
#      elif(k==id_precip):
#         stat=N.zeros(2)
#         if(len(a)==0):
#            stat[0]='nan'
#            stat[1]=0
#         else:
#            stat[0]=sum(b)/sum(a)
#            stat[1]=0
#      else:
      # stat=statistics.linearregression(b,x=a)
      #stat=linearregression(b,x=a)
      try:
        slope, intercept, r, p, std_err = stats.linregress(a, b)
        stat=N.zeros(2)
        stat[0] = slope
        stat[1] = intercept
      except ValueError:
        stat=N.zeros(2)
        stat[0] = N.nan

      if(str(stat[0])!='nan'):
         slope=stat[0]
         intercept=stat[1]
      else:
         slope=1
         intercept=0
           
      fic.write("%s," % label_var_fluxnet[k])
      fic.write("%s," % label_units_fluxnet[k])
      fic.write("%4.2f," % val1)
      if(val1 < 100):
          fic.write("%4.2f," % float(slope))
          if(k!=id_precip):
              # val2=statistics.rms(a,b)
              # val4=statistics.correlation(a,b)
              val2=rms(a,b)
              val4=correlation(a,b)

              fic.write("%4.2f," % float(intercept))
              fic.write("%4.2f," % val2)
              fic.write("%4.2f\n" % val4)
          else:
              fic.write("-,-,-,-\n")
      else:
          fic.write("-,-,-,-\n")
    fic.close()
