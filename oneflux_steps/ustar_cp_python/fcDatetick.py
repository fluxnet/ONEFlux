from oneflux_steps.ustar_cp_python.utils import *
from oneflux_steps.ustar_cp_python.fcDatevec import *
from oneflux_steps.ustar_cp_python.fcDatenum import mydatenum

import matplotlib.pyplot as plt
import datetime

def fcDatetick(t, sFrequency, iDateStr, fLimits):
    
    # # mimic MATLAB's ability to handle scalar or vector inputs
    # if (hasattr(t, "__len__") and len(t) > 0 and hasattr(t[0], "__len__")):
    #     # Input is 2-Dimensional, so vectorise ourselves
    #     return numpy.vectorize(fcDatetick)(t, sFrequency, iDateStr, fLimits)
    
    y, m, d, h, mn, s = fcDatevec(t)
    iYrs = unique(y)
    iSerMos = dot((y - 1), 12) + m
    iSerMo1 = min(iSerMos)
    iSerMo2 = max(iSerMos)
    nSerMos = iSerMo2 - iSerMo1 + 1
    xDates = matlabarray([])

    match (sFrequency):
      case "Dy":
        xDates = t[::48]

      case "2Dy":
        iYr1 = floor(iSerMo1 / 12) + 1
        iMo1 = mod(iSerMo1, 12)
        
        if iMo1 == 0:
            iMo1 = 12        
            iYr1 = iYr1 - 1
      
        for iDy in arange(1, 29, 2).reshape(-1):
            xDates = [xDates, mydatenum(iYr1, arange(iMo1, (iMo1 + nSerMos)), iDy)]

      case "3Dy":
        iYr1 = floor(iSerMo1 / 12) + 1
        iMo1 = mod(iSerMo1, 12)
        if iMo1 == 0:
            iMo1 = 12
            iYr1 = iYr1 - 1
        for iDy in arange(1, 28, 3).reshape(-1):
            xDates = [xDates, mydatenum(iYr1, arange(iMo1, (iMo1 + nSerMos)), iDy)]
          
      case "5Dy":
        iYr1 = floor(iSerMo1 / 12) + 1
        iMo1 = mod(iSerMo1, 12)
        if iMo1 == 0:
            iMo1 = 12
            iYr1 = iYr1 - 1
        for iDy in arange(1, 26, 5).reshape(-1):
            xDates = [xDates, mydatenum(iYr1, arange(iMo1, (iMo1 + nSerMos)), iDy)]

      case "7Dy":
        iYr1 = floor(iSerMo1 / 12) + 1                   
        iMo1 = mod(iSerMo1, 12)
        if iMo1 == 0:
            iMo1 = 12
            iYr1 = iYr1 - 1
        for iDy in arange(1, 22, 7).reshape(-1):
            xDates = [ xDates, mydatenum(iYr1, arange(iMo1, (iMo1 + nSerMos)), iDy)]

      case "10Dy":
        iYr1 = floor(iSerMo1 / 12) + 1
        iMo1 = mod(iSerMo1, 12)
        if iMo1 == 0:
            iMo1 = 12
            iYr1 = iYr1 - 1
        for iDy in arange(1, 21, 10).reshape(-1):
            xDates = [ xDates, mydatenum(iYr1, arange(iMo1, (iMo1 + nSerMos)), iDy)]
          
        
      case "14Dy":
        iYr1 = floor(iSerMo1 / 12) + 1
        iMo1 = mod(iSerMo1, 12)
        if iMo1 == 0:
            iMo1 = 12
            iYr1 = iYr1 - 1
        for iDy in arange(1, 15, 14).reshape(-1):
            xDates = [xDates, mydatenum(iYr1, arange(iMo1, (iMo1 + nSerMos)), iDy)]                                    


      case "15Dy":
        iYr1 = floor(iSerMo1 / 12) + 1
        iMo1 = mod(iSerMo1, 12)
        if iMo1 == 0:
            iMo1 = 12
            iYr1 = iYr1 - 1
        for iDy in arange(1, 16, 15).reshape(-1):
            xDates = [xDates, mydatenum(iYr1, arange(iMo1, (iMo1 + nSerMos)), iDy)]

      case "Mo":
        iYr1 = floor(iSerMo1 / 12) + 1
        iMo1 = mod(iSerMo1, 12)
        if iMo1 == 0:
            iMo1 = 12
            iYr1 = iYr1 - 1
        xDates = mydatenum(
            iYr1, arange(iMo1, (iMo1 + nSerMos)), 1
        )
        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:36
        # # # 			datestr(xDates)
        # # # 			datestr([min(t) max(t)])
        # # # 			pause;
                                  
      case "2Mo":
        iYr1 = floor(iSerMo1 / 12) + 1
        iMo1 = mod(iSerMo1, 12)
        if iMo1 == 0:
            iMo1 = 12
            iYr1 = iYr1 - 1
        xDates = mydatenum(iYr1, arange(iMo1, (iMo1 + nSerMos), 2), 1)

      case "3Mo":
        iYr1 = floor(iSerMo1 / 12) + 1
        iMo1 = mod(iSerMo1, 12)
        if iMo1 == 0:
            iMo1 = 12
            iYr1 = iYr1 - 1
        xDates = mydatenum(iYr1, arange(iMo1, (iMo1 + nSerMos), 3), 1)


      case "4Mo":
        iYr1 = floor(iSerMo1 / 12) + 1
        iMo1 = mod(iSerMo1, 12)
        if iMo1 == 0:
            iMo1 = 12
            iYr1 = iYr1 - 1
        xDates = mydatenum(iYr1, arange(iMo1, (iMo1 + nSerMos), 4), 1)
        
      case "6Mo":                                              
        iYr1 = floor(iSerMo1 / 12) + 1
        iMo1 = mod(iSerMo1, 12)
        if iMo1 == 0:
            iMo1 = 12
            iYr1 = iYr1 - 1
        xDates = mydatenum(iYr1, arange(iMo1, (iMo1 + nSerMos), 6), 1)

      case "Yr":
        iYr1 = min(iYrs)
        iYr2 = max(iYrs)
        xDates = mydatenum(arange(iYr1, iYr2 + 1), 1, 1)

    xDates = unique(xDates)

    # Set current `x` access to have values given by xDates
    plt.gca().set_xticks(xDates)
    # set label to empty
    plt.gca().set_xticklabels([])
    if iDateStr > 0:
        # compute a datestring for each xDates based on iDateStr
        # TODO: this is different to the original MATLAB code which was
        # cDates = datestr(xDates, iDateStr)

        # convert from a date floating-point
        # ordinal to a datetime object
        cDates = [datetime.datetime.fromordinal(floor(t) + 1).strftime("%Y-%m-%d") for t in xDates]

        plt.gca().set_xticklabels(cDates)

    if fLimits == 1:
        xlim(matlabarray([floor(min(xDates)), ceil(max(xDates))]))
        # Turn on the grid and box using matplotlib
        plt.grid("on")
        plt.box("on")

    return None
