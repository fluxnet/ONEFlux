import numpy as N
import logging

from scipy.optimize import leastsq
from scipy import stats
from oneflux.downscaling.functions import solarang, time_zone, residuals
from oneflux.downscaling.constantes import * 

log = logging.getLogger(__name__)

#-------------------------------------------------------------------------------------------
# function gap_fill_func gapfills the meteorlogical data
# argument1 : the weather dataset (weather)
# argument2 : the climatology dataset (clim)
# argument3 : the ratio between clim and weather time steps (diff_clim_weather)
# argument4 : the weather time step
# argument5 : the clim time step
# argument6 : vector of julian days
# argument7 : length of the year
# argument8 : longitude
# argument9 : latitude
# argument10: maximum length of gap below which we linearly interpolated
# argument11: vector of flags indicating whether the field is averaged or instantaneous
# argument12: vector of time step shifted needed for putting in agreement weather and climate datasets
# argument13: vector of time step shifted needed for accounting for time zone adjustment
 
# returns a vector that contains the weather dataset gapfilled
def gap_fill_func(weather,clim,diff_clim_weather,weather_period,climato_period,julian,year_length,lon,lat,gapmax,avg,climatoshift,timeshift):
   weather_clim_period=[]
   weather_clim_period_test=[]

   weather_clim_period_nogap=[]
   clim_nogap=[]
   weather_clim_period_gapfill=[]
   weather_clim_period_all_gapfill=[]
   weather_gapfill=[]
   weather_all_gapfill=[]
   clim_weather_period=[]

   if(timeshift==-9999):
      timezone=time_zone(0,lon)
      # east of Greenwich => timeshift>0
      # west of Greenwich => timeshift<0
      if(timezone[1]<13):
         timeshift=timezone[1]
      else:
         timeshift=timezone[1]-24

   stat_vec=[]

   log.debug('shift to UTC time = {t} hours'.format(t=timeshift))


   for k in range(len(weather)):
   
      #weather_clim_period.append(N.zeros(int(len(weather[k])/diff_clim_weather), dtype='float', 0))
      weather_clim_period.append(N.zeros(int(len(weather[k])/diff_clim_weather), dtype=float))
      if(k==id_precip):
         #freq_precip=N.zeros(len(weather[k])/diff_clim_weather, float, 0)
         freq_precip=N.zeros(int(len(weather[k])/diff_clim_weather), float)
      #weather_clim_period_test.append(N.zeros(len(weather[k])/diff_clim_weather, float, 0))
      weather_clim_period_test.append(N.zeros(int(len(weather[k])/diff_clim_weather), dtype=float))


      # climatoshift indicates to which time step or time period
      # unit is fraction of a time period (between 2 consecutive time steps)
      # a climatic field value corresponds to
      # for field that is a mean value (avg=1)
      #    climatoshift=0 when the mean value is calculated from one time step to the next one
      #    climatoshift=-0.5 when the mean value is centered on one time step
      # for field that is an instantaneous value (avg=0)
      #    climatoshift=0 when the value correspond to the current time step
      #    climatoshift=1 when the value corresponds to the next time step
      totalshift=timeshift+climatoshift[k]*climato_period
      log.debug('Variable being processed: {v}'.format(v=label_fig[k]))
      for t in range(len(weather[k])):
         tshift=t-(float)(totalshift)/weather_period
         goodcell=int(tshift/diff_clim_weather)
         if((tshift>=0)and(tshift<len(weather[k]))):
            # in case of a mean value calculation, we sum all weather element within each element of weather_clim_period
            # if one weather element equals -9999, the related weather_clim_period is equal to -9999
            if (avg[k]==1):
               if((weather[k][t] != -9999) and (weather_clim_period[k][goodcell] != -9999)):
                  weather_clim_period[k][goodcell]+=weather[k][t]/diff_clim_weather
               else:
                  weather_clim_period[k][goodcell]=-9999
               weather_clim_period_test[k][goodcell]=1

               if(k==id_precip):
                  if((weather[k][t] != -9999) and (freq_precip[goodcell] != -9999)):
                     if(weather[k][t]>0):
                        freq_precip[goodcell]+=1./diff_clim_weather
                  else:
                     freq_precip[goodcell]=-9999
               
            # in case of a instantaneaous calculation, each weather_clim_period element corresponds
            # to the first weather element associated to this weather_clim_period element
            else:
               if(weather_clim_period_test[k][goodcell] == 0):
                  if((weather[k][t] != -9999)):
                     weather_clim_period[k][goodcell]=weather[k][t]
                  else:
                     weather_clim_period[k][goodcell]=-9999
                  weather_clim_period_test[k][goodcell]=1
      # in case of a mean value calculcation (avg==1)
      # elements of weather_clim_period that have been partly filled (at the beginning or at the end)
      # are set to -9999
      if (avg[k]==1):
         if(totalshift%climato_period !=0):
            if(totalshift>0):
               goodcellmissing=int((len(weather[k])-1-(float)(totalshift)/weather_period)/diff_clim_weather)
               weather_clim_period[k][goodcellmissing]=-9999
            else:
               if(totalshift<0):
                  goodcellmissing=int((-(float)(totalshift)/weather_period)/diff_clim_weather)
                  weather_clim_period[k][goodcellmissing]=-9999
      # elements of weather_clim_period that have NOT been filled (at the beginning or at the end)
      # are set to -9999          
      weather_clim_period[k]=N.where(weather_clim_period_test[k]==1,weather_clim_period[k],-9999)
               

      weather_clim_period_nogap.append([])
      clim_nogap.append([])
      for t in range(len(weather_clim_period[k])):
         if(weather_clim_period[k][t] != -9999):
            weather_clim_period_nogap[k].append(weather_clim_period[k][t])
            clim_nogap[k].append(clim[k][t])


      weather_clim_period_nogap[k]=N.array(weather_clim_period_nogap[k],float)
      clim_nogap[k]=N.array(clim_nogap[k],float)



      # Evaluate the correlation
      # between clim_nogap and weather_clim_period_nogap
      # intercept and slope of the relation
      # will be used for correcting clim data when filling gaps
      a=clim_nogap[k]
      b=weather_clim_period_nogap[k]

      if((k==id_swdown)or(k==id_ws)):
         if(len(a)==0):
            stat=N.zeros(2)
            stat[0]='nan'
         else:
            stat1=leastsq(residuals,1.,args=(b,a))
            stat=N.zeros(2, dtype=float)
            #stat=N.array(stat[0], dtype=float)
            stat[0]=stat1[0][0]
            stat[1]=0
      elif(k==id_precip):
         stat=N.zeros(2, dtype=float)
         if(len(a)==0):
            stat[0]='nan'
            stat[1]=0
         else:
            stat[0]=sum(b)/sum(a)
            stat[1]=0
      else:
         if(len(a)==0):
            stat=N.zeros(2, dtype=float)
            stat[0]='nan'
         else:
            #stat=statistics.linearregression(b,x=a)
            slope, intercept, r, p, std_err = stats.linregress(a, b)
            stat=N.zeros(2)
            stat[0] = slope
            stat[1] = intercept 
      if(str(stat[0])!='nan'):
         slope=stat[0]
         intercept=stat[1]
      else:
         slope=1
         intercept=0

      stat_vec.append([slope,intercept])
      log.debug('Slope of the linear relation in-situ VS reanalysis={s}'.format(s=slope))
      log.debug('Intercept of the linear relation in-situ VS reanalysis={s}'.format(s=intercept))
      if(str(stat[0])!='nan'):
         log.debug('RMSE without correction={s}'.format(s=rms(a,b)))
         log.debug('RMSE with correction={s}'.format(s=rms(a*slope+intercept,b)))
         

      weather_clim_period_gapfill.append([])
      weather_clim_period_gapfill[k]=N.where(weather_clim_period[k]==-9999, slope*clim[k]+intercept, weather_clim_period[k])

      weather_clim_period_all_gapfill.append([])
      weather_clim_period_all_gapfill[k]=slope*clim[k]+intercept

      weather_all_gapfill.append([])
      clim_weather_period.append([])
 
      weather_gapfill.append([])
      mean_csang=0.
      if(k==id_precip):
         freq_precip_nogap=N.ma.masked_values(freq_precip,-9999)
         freq_precip_nogap_nonull=N.ma.masked_values(freq_precip_nogap,0.)
         if(freq_precip_nogap_nonull.count()!=0):
            freq_precip_scalar=freq_precip_nogap_nonull.mean()
            number_precip_per_diff_clim_weather=round(freq_precip_scalar*diff_clim_weather)
         else:
            number_precip_per_diff_clim_weather=diff_clim_weather
      for t in range(len(weather[k])):
         tshift=t-(float)(totalshift)/weather_period
         goodcell=int(tshift/diff_clim_weather)
         if(k==id_swdown):
            if((t-(float)(timeshift)/weather_period)<(len(weather[k])-(diff_clim_weather-1))):
               if(tshift%diff_clim_weather==0):
                  mean_csang=0.
                  for l in range(diff_clim_weather):
                     goodcellsolar=int((t-(float)(timeshift)/weather_period)+l)
                     mean_csang+=solarang(julian[goodcellsolar],0,lon,lat,year_length[int(tshift)])/diff_clim_weather
               if(mean_csang == 0.):
                  ratio=0.
               else:
                  goodcellratio=int((t-(float)(timeshift)/weather_period))
                  ratio=solarang(julian[goodcellratio],0,lon,lat,year_length[goodcellratio])/mean_csang
            else:
               ratio=1
         if(k==id_lwdown):
            ratio=1
         if(k==id_precip):
            if(t%diff_clim_weather+1<=number_precip_per_diff_clim_weather):
               ratio=diff_clim_weather/number_precip_per_diff_clim_weather
            else:
               ratio=0.

         # if the current value is -9999, we have to fill the gap
         if(weather[k][t] == -9999):
            # if gapmax is > 0
            # for short gap, we will try to interpolate
            # between the last and the next
            # defined values in the weather dataset
            active_linear=1
            if(gapmax>0):
               tlow=t-1
               while((tlow>=0)and(weather[k][tlow]==-9999)and((t-tlow)<=gapmax)):
                  tlow=tlow-1
               tup=t+1
               while((tup<len(weather[k]))and(weather[k][tup]==-9999)and((tup-t)<=gapmax)):
                  tup=tup+1
               # if the last and the next defined values are not too far
               # we linearly interpolate with the weather dataset
               if(tup-tlow<=gapmax+1):
                  if(tlow<0):
                     weather_gapfill[k].append(weather[k][tup])
                  elif(tup>=len(weather[k])):
                     weather_gapfill[k].append(weather[k][tlow])
                  else:
                     step=(float)(t-tlow)/(tup-tlow)
                     weather_gapfill[k].append(weather[k][tlow]*(1-step)+weather[k][tup]*step)
               else:
                  active_linear=0
            # if gapmax == 0 or
            # if the last and the next defined values are too far each other
            # we use the clim dataset for filling the gap
            if((gapmax==0)or(not active_linear)):   
               if (avg[k]==0):
                  step=(float)(tshift%diff_clim_weather)/diff_clim_weather
                  if(tshift<0.):
                     weather_gapfill[k].append(weather_clim_period_gapfill[k][0])
                  elif((tshift/diff_clim_weather+1)>=(len(weather_clim_period_gapfill[k]))):
                     weather_gapfill[k].append(weather_clim_period_gapfill[k][len(weather_clim_period_gapfill[k])-1])
                  else:
                     weather_gapfill[k].append(weather_clim_period_gapfill[k][goodcell]*(1-step)+weather_clim_period_gapfill[k][goodcell+1]*step)
               else:
                  if(tshift<0.):
                     weather_gapfill[k].append(weather_clim_period_gapfill[k][0]*ratio)
                  elif((tshift/diff_clim_weather)>=(len(weather_clim_period_gapfill[k]))):
                     weather_gapfill[k].append(weather_clim_period_gapfill[k][len(weather_clim_period_gapfill[k])-1]*ratio)
                  else:
                     weather_gapfill[k].append(weather_clim_period_gapfill[k][goodcell]*ratio)
         else:
            weather_gapfill[k].append(weather[k][t])

         if (avg[k]==0):
            step=(float)(tshift%diff_clim_weather)/diff_clim_weather
            if(tshift<0.):
               weather_all_gapfill[k].append(weather_clim_period_all_gapfill[k][0])
               clim_weather_period[k].append(clim[k][0])
            elif((tshift/diff_clim_weather+1)>=(len(weather_clim_period_all_gapfill[k]))):
               weather_all_gapfill[k].append(weather_clim_period_all_gapfill[k][len(weather_clim_period_all_gapfill[k])-1])
               clim_weather_period[k].append(clim[k][len(clim[k])-1])
            else:
               weather_all_gapfill[k].append(weather_clim_period_all_gapfill[k][goodcell]*(1-step)+weather_clim_period_all_gapfill[k][goodcell+1]*step)
               clim_weather_period[k].append(clim[k][goodcell]*(1-step)+clim[k][goodcell+1]*step)
         else:
            if(tshift<0.):
               weather_all_gapfill[k].append(weather_clim_period_all_gapfill[k][0]*ratio)
               clim_weather_period[k].append(clim[k][0]*ratio)
            elif((tshift/diff_clim_weather)>=(len(weather_clim_period_all_gapfill[k]))):
               weather_all_gapfill[k].append(weather_clim_period_all_gapfill[k][len(weather_clim_period_all_gapfill[k])-1]*ratio)
               clim_weather_period[k].append(clim[k][len(clim[k])-1]*ratio)
            else:
               weather_all_gapfill[k].append(weather_clim_period_all_gapfill[k][goodcell]*ratio)
               clim_weather_period[k].append(clim[k][goodcell]*ratio)

   return clim_weather_period,weather_all_gapfill,weather_gapfill,weather_clim_period_gapfill,weather_clim_period_nogap,weather_clim_period,clim_nogap,stat_vec
# end function
#-------------------------------------------------------------------------------------------
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
