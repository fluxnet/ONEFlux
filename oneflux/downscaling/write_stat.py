import os
import numpy as N

#from genutil import statistics
from scipy.optimize import leastsq
from scipy import stats
from oneflux.downscaling.constantes import *
from oneflux.downscaling.functions import residuals
from oneflux.downscaling.gap_fill import *

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



