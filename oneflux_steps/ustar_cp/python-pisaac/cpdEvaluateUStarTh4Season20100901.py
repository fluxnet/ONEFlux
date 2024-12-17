# standard modules
import copy
import os
import sys
# 3rd party modules
import numpy
from numpy.lib.recfunctions import append_fields
from scipy import stats
import xlwt
# local modules
from fcDatevec import mydatevec
from fcDoy import mydoy
from fcDatenum import mydatenum
from fcBin import cpdBin
from cpdFindChangePoint20100901 import cpdFindChangePoint20100901
from myprctile import myprctile

def cpdEvaluateUStarTh4Season20100901(t, NEE, uStar, T, fNight, fPlot, cSiteYr):
    """
    nacpEvaluateUStarTh4Season20100901
    estimates uStarTh for a site-year of data using change-point
    detection (cpd) methods implemented within the general framework
    of the Papale et al. (2006) uStarTh evaluation method.

    Syntax:
     [Cp2,Stats2,Cp3,Stats3] = ...
      cpdEvaluateUStarTh20100901(t,NEE,uStar,T,fNight,fPlot,cSiteYr)
     where:
      - Cp2 and Cp3 are nW x nT matrices containing change-point
        uStarTh estimates from the 2-parameter operational
        and 3-parameter diagnostic models
      - Stats2 and Stats3 are structured records containing the corresponding
        nW x nT matrices of cpd statistics.
      - t is the time vector
      - NEE, uStar and T (temperature)
      - fNight is a vector specifying day (0) or night (1)
      - fPlot is a scalar flag that is set high (1) to plot
      - cSiteYr is a text string used in the plot title

    The analysis is based on one year of data.  The year is stratified
    by time of year and temperature into nW by nT strata, each with a
    fixed number of data.
    The uStarTh is estimated independently for each stratum, using two
    change-point models: the 2-parameter operational and 3-parameter
    diagnostic models.

    The primary modification Papale et al. (2006) is the use of
    change-point detection (cpd) rather than a moving point test
    to evaluate the uStarTh.  The cpd method is adopted from
    Lund and Reeves (2002) and Wang (2003).

    Relationship to other programs:
        1. cpdBootstrapUStarTh20100901
            - function which processes specified sites including bootstrapping
              and data output.
    calls
        2. CPDEvaluateUStarTh20100901
            - function that processes an individual year of data
    calls
        3. cpdFindChangePoint20100901 (change-point detection function).
    Functions called:
     cpdFindChangePoint20100901
     fcBin, fcDatevec, fcDoy
     stats toolbox:  nanmedian, prctile, regress

    Written by Alan Barr 15 Jan 2010.
    Translated to Python by PRI September 2019.
    """
    # Initializations
    nt = len(t)
    Y, M, D, h, m, s = mydatevec(t)
    # mydatevec returns float because it uses numpy.nan
    iYr = int(numpy.median(Y))
    dn = mydatenum(iYr, 12, 31, 12, 0, 0)
    EndDOY = mydoy(dn)
    nPerDay = int(round(1 / numpy.median(numpy.diff(t))))
    nSeasons = 4
    nStrataN = 4
    nStrataX = 8
    nBins = 50
    nPerBin = 5
    if nPerDay == 24:
        nPerBin = 3
    nPerSeasonN = nStrataN*nBins*nPerBin
    nN = nSeasons*nPerSeasonN
    itOut = numpy.where((uStar[~numpy.isnan(uStar)] < 0) | (uStar[~numpy.isnan(uStar)] > 3))[0]
    uStar[itOut] = numpy.nan
    itAnnual = numpy.where((fNight == 1) & (~numpy.isnan(NEE+uStar+T)))[0]
    ntAnnual = len(itAnnual)
    # Initialize outputs, Cp2 and Cp3 as numpy arrays.
    Cp2 = numpy.full((nSeasons, nStrataX), numpy.nan)
    Cp3 = numpy.full((nSeasons, nStrataX), numpy.nan)
    # Stats2 and Stats3 as dictionaries
    stat_labels = ['ciT', 'mt', 'Fmax', 'puStarVsT', 'ruStarVsT', 'mT', 'n', 'p',
                   'cib0', 'cib1', 'b0', 'b1', 'b2', 'ti', 'tf', 'c2', 'Cp', 'cic2']
    Stats2 = {}
    Stats3 = {}
    for iSeason in range(nSeasons):
        Stats2[iSeason] = {}
        Stats3[iSeason] = {}
        for iStrata in range(nStrataX):
            Stats2[iSeason][iStrata] = {}
            Stats3[iSeason][iStrata] = {}
            for stat in stat_labels:
                Stats2[iSeason][iStrata][stat] = numpy.nan
                Stats3[iSeason][iStrata][stat] = numpy.nan
    if ntAnnual < nN:
        print "cpdEvaluateUStarTh4Season: ntAnnual less than nN ", ntAnnual, nN
        return Cp2, Stats2, Cp3, Stats3
    # Octave has ntAnnual, nSeasons and nPerSeason as floats
    # then round(1040.5) ==> 1041.0
    nPerSeason = round(float(ntAnnual) / float(nSeasons))
    # Move December to beginning of year and date as previous year.
    itD = numpy.where(M == 12)[0]
    itReOrder = numpy.concatenate([range(min(itD), nt), range(0, (min(itD)))])
    # PRI Spetember 2019 - I don't think this works as intended using t as generated
    t[itD] = t[itD] - EndDOY
    t = t[itReOrder]
    T = T[itReOrder]
    uStar = uStar[itReOrder]
    NEE = NEE[itReOrder]
    fNight = fNight[itReOrder]
    itAnnual = numpy.where((fNight == 1) & (~numpy.isnan(NEE + uStar + T)))[0]
    ntAnnual = len(itAnnual)
    # Reset nPerSeason and nInc based on actual number of good data.
    # nSeasons is a temporary variable.
    nSeasons = round(float(ntAnnual) / float(nPerSeason))
    nPerSeason = float(ntAnnual) / nSeasons
    nPerSeason = round(nPerSeason)
    # Stratify in two dimensions:
    # 1. by time using moving windows
    # 2. by temperature class
    # Then estimate change points Cp2 and Cp3 for each stratum.
    xls_out = {"cSiteYr": cSiteYr, "cpdBin_input": {}, "cpdBin_output": {},
               "cpdFindChangePoint_output": {}}
    for iSeason in range(0, int(nSeasons)):
        xls_out["cpdBin_input"][iSeason] = {}
        xls_out["cpdBin_output"][iSeason] = {}
        if iSeason == 0:
            jtSeason = range(0, int(nPerSeason))
        else:
            if iSeason == nSeasons-1:
                jtSeason = range(int((nSeasons - 1)*nPerSeason), int(ntAnnual))
            else:
                jtSeason = range(int(iSeason*nPerSeason), int((iSeason + 1)*nPerSeason))
        itSeason = itAnnual[jtSeason]
        ntSeason = len(itSeason)
        nStrata = numpy.floor(ntSeason / (nBins*nPerBin))
        if nStrata < nStrataN:
            nStrata = nStrataN
        if nStrata > nStrataX:
            nStrata = nStrataX
        bin_range = numpy.arange(0, 101, 100/nStrata)

        xls_out["nSeasons"] = nSeasons
        xls_out["nStrata"] = nStrata

        TTh = myprctile(T[itSeason], bin_range)
        for iStrata in range(0, int(nStrata)):
            xls_out["cpdBin_input"][iSeason][iStrata] = {}
            xls_out["cpdBin_output"][iSeason][iStrata] = {}
            #itStrata = numpy.where((T >= TTh[iStrata]) & (T <= TTh[iStrata + 1]))[0]
            # using numpy.greater_equal() with "where" to suppress NaN warnings
            c1 = numpy.greater_equal(T, TTh[iStrata], where=~numpy.isnan(T))
            c2 = numpy.less_equal(T, TTh[iStrata+1], where=~numpy.isnan(T))
            itStrata = numpy.where(c1 & c2)[0]
            itStrata = numpy.intersect1d(itStrata, itSeason)
            if len(itStrata) == 0:
                print "rseting"

            xls_out["cpdBin_input"][iSeason][iStrata]["itStrata"] = itStrata
            xls_out["cpdBin_input"][iSeason][iStrata]["uStar"] = uStar[itStrata]
            xls_out["cpdBin_input"][iSeason][iStrata]["NEE"] = NEE[itStrata]

            n, muStar, mNEE = cpdBin(uStar[itStrata], NEE[itStrata], [], nPerBin)

            xls_out["cpdBin_output"][iSeason][iStrata]["muStar"] = muStar
            xls_out["cpdBin_output"][iSeason][iStrata]["mNEE"] = mNEE

            xCp2, xs2, xCp3, xs3 = cpdFindChangePoint20100901(muStar, mNEE, iSeason, iStrata)

            n, muStar, mT = cpdBin(uStar[itStrata], T[itStrata], [], nPerBin)
            r, p = stats.pearsonr(muStar, mT)
            xs2["mt"] = numpy.mean(t[itStrata])
            xs2["ti"] = t[itStrata[0]]
            xs2["tf"] = t[itStrata[-1]]
            xs2["ruStarVsT"] = r
            xs2["puStarVsT"] = p
            xs2["mT"] = numpy.mean(T[itStrata])
            xs2["ciT"] = 0.5*numpy.diff(myprctile(T[itStrata], numpy.array([2.5, 97.5])))[0]
            xs2["nSeasons"] = nSeasons
            xs2["nStrata"] = nStrata
            xs3["mt"] = xs2["mt"]
            xs3["ti"] = xs2["ti"]
            xs3["tf"] = xs2["tf"]
            xs3["ruStarVsT"] = xs2["ruStarVsT"]
            xs3["puStarVsT"] = xs2["puStarVsT"]
            xs3["mT"] = xs2["mT"]
            xs3["ciT"] = xs2["ciT"]
            xs3["nSeasons"] = nSeasons
            xs3["nStrata"] = nStrata
            Cp2[iSeason, iStrata] = xCp2
            Stats2[iSeason][iStrata] = xs2
            Cp3[iSeason, iStrata] = xCp3
            Stats3[iSeason][iStrata] = xs3

    xls_out["cpdFindChangePoint_output"]["Cp2"] = Cp2
    xls_out["cpdFindChangePoint_output"]["Cp3"] = Cp3
    xls_out["cpdFindChangePoint_output"]["Stats2"] = Stats2
    xls_out["cpdFindChangePoint_output"]["Stats3"] = Stats3
    #cpdEvaluateUStarTh4Season_xls_output(xls_out)

    return Cp2, Stats2, Cp3, Stats3

def cpdEvaluateUStarTh4Season_xls_output(xls_out):
    """
    Purpose:
     Write the intermediate results from cpdBin and cpdFindChangePoint20100901
     to an Excel file.
    Author: PRI
    Date: October 2019
    """
    out_path = "/home/peter/Python/cpd/tests/output/"
    out_path = os.path.join(out_path, xls_out["cSiteYr"])
    if not os.path.isdir(out_path):
        os.makedirs(out_path)
    out_name = os.path.join(out_path, "py_cpdEvaluateUStarTh4Season_output.xls")
    out_book = xlwt.Workbook()
    # add a sheet for the Cp2 results
    cp2_sheet = out_book.add_sheet("Cp2")
    Cp2 = xls_out["cpdFindChangePoint_output"]["Cp2"]
    rows, cols = Cp2.shape
    for row in range(rows):
        cp2_sheet.write(row+1, 0, row)
        for col in range(cols):
            if row == 0:
                cp2_sheet.write(0, col+1, col)
            cp2_sheet.write(row+1, col+1, Cp2[row, col])
    # add a sheet for the Cp3 results
    cp3_sheet = out_book.add_sheet("Cp3")
    Cp3 = xls_out["cpdFindChangePoint_output"]["Cp3"]
    rows, cols = Cp3.shape
    for row in range(rows):
        cp3_sheet.write(row+1, 0, row)
        for col in range(cols):
            if row == 0:
                cp3_sheet.write(0, col+1, col)
            cp3_sheet.write(row+1, col+1, Cp3[row, col])
    # output the contents of Stats3
    stats2_sheet = out_book.add_sheet("Stats2")
    Stats2 = xls_out["cpdFindChangePoint_output"]["Stats2"]
    for s, season in enumerate(sorted(Stats2.keys())):
        # season
        for t, tclass in enumerate(sorted(Stats2[season].keys())):
            # T class
            col = s*len(Stats2[season]) + t
            for row, stat in enumerate(sorted(Stats2[season][tclass].keys())):
                if row == 0:
                    column_heading = str(season) + "," + str(tclass)
                    stats2_sheet.write(0, col+1, column_heading)
                if s == 0 and t == 0:
                    stats2_sheet.write(row+1, 0, stat)
                stats2_sheet.write(row+1, col+1, Stats2[season][tclass][stat])
    # output the contents of Stats3
    stats3_sheet = out_book.add_sheet("Stats3")
    Stats3 = xls_out["cpdFindChangePoint_output"]["Stats3"]
    for s, season in enumerate(sorted(Stats3.keys())):
        # season
        for t, tclass in enumerate(sorted(Stats3[season].keys())):
            # T class
            col = s*len(Stats3[season]) + t
            for row, stat in enumerate(sorted(Stats3[season][tclass].keys())):
                if row == 0:
                    column_heading = str(season) + "," + str(tclass)
                    stats3_sheet.write(0, col+1, column_heading)
                if s == 0 and t == 0:
                    stats3_sheet.write(row+1, 0, stat)
                stats3_sheet.write(row+1, col+1, Stats3[season][tclass][stat])
    # output the cpdBin input data
    cpdBin_input_sheet = out_book.add_sheet("cpdBin (input)")
    cpdBin_input = xls_out["cpdBin_input"]
    items = ["itStrata", "uStar", "NEE"]
    for s, season in enumerate(sorted(cpdBin_input.keys())):
        for t, tclass in enumerate(sorted(cpdBin_input[s].keys())):
            for i, item in enumerate(items):
                col = s*len(cpdBin_input[s])*len(items) + t*len(items) + i
                for row in range(len(cpdBin_input[s][t][item])):
                    if row == 0:
                        column_heading = str(season) + "," + str(tclass)
                        cpdBin_input_sheet.write(row, col, column_heading)
                        cpdBin_input_sheet.write(row+1, col, item)
                    cpdBin_input_sheet.write(row+2, col, cpdBin_input[s][t][item][row])
    # output the cpdBin output data
    cpdBin_output_sheet = out_book.add_sheet("cpdBin (output)")
    cpdBin_output = xls_out["cpdBin_output"]
    items = ["muStar", "mNEE"]
    for s, season in enumerate(sorted(cpdBin_output.keys())):
        for t, tclass in enumerate(sorted(cpdBin_output[s].keys())):
            for i, item in enumerate(items):
                col = s*len(cpdBin_output[s])*len(items) + t*len(items) + i
                for row in range(len(cpdBin_output[s][t][item])):
                    if row == 0:
                        column_heading = str(season) + "," + str(tclass)
                        cpdBin_output_sheet.write(row, col, column_heading)
                        cpdBin_output_sheet.write(row+1, col, item)
                    cpdBin_output_sheet.write(row+2, col, cpdBin_output[s][t][item][row])

    out_book.save(out_name)
    return
