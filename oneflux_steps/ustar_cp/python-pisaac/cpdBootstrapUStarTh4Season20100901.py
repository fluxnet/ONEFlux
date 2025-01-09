# standard modules
import copy
import sys
import time
# 3rd party modules
import numpy
# local modules
from cpdEvaluateUStarTh4Season20100901 import cpdEvaluateUStarTh4Season20100901

def cpdBootstrapUStarTh4Season20100901(t, NEE, uStar, T, fNight, fPlot, cSiteYr, nBoot):
    """
    cpdBootstrapUStarTh4Season20100901

    is a simplified operational version of

    20100901 changes 3A 4I to 2A 3I as sggested by Xiaolan Wang.

    20100408 replaces 20100318, updating ChPt function from:
     FindChangePointMod3LundReeves2002_20100318 to
     FindChangePointMod2A4ILundReeves2002_20100408.
     which: adds back A model, makes a correction to the significance test,
     and adds a comparison of the 4- versus 3-parameter models.
     and adds a comparison of the 4- versus 3-parameter models.

     20100318 new version with small tweaks to FindChangePoint
     also adds mT and ciT to Stats structures.

     is a new working implementation of Alan's u*Th evaluation algorithm
     based on Lund and Reeves' (2002) modified by Wang's (2003) change-point
     detection algorithm.

     Relationship to other programs:

     Called by batchNewNacpEstimateUStarTh_Moving_Mod3LundChPt_20100115
      - script which identifies which sites to process
     Calls newNacpEvaluateUStarTh_MovingStrat_20100114
      - function that processes an individual year of data, using
        FindChangePointMod3LundReeves2002_20091204

     This implementation may supplant all previous versions.

     It uses moving windows of fixed size to evaluate seasonal variation.

     Three combinations of stratification and pooling are implemented.
      - All begin with 2D (time x temperature) stratification
        (moving-window time x n temperature classes within each window).
      - Two (W and A) add normalization and pooling.

     1. Method S (full stratification)
        estimates the change-points for each of the strata
        (nWindows x nTClasses) with no need for normalization.
     2. Method W (pooling within time windows)
        begins with a variant of S but pools the temperature classes
        within each time window before estimating one change-point per window.
        Before pooling, the binned mean NEE data within each temperature class
        are normalized against the 80th NEE percentile for that class.
     3. Method A (pooling to annual)
        further pools the pooled normalized data from W over all time windows
        before estimating a single change-point per year.

     The detailed analysis parameters are output in a Stats structured
     record.

     ========================================================================
     ========================================================================

     Functions called:
      cpdEvaluateUStarTh20100901
      fcx2roevec
      stats toolbox:  nanmedian

     Written by Alan Barr 15 Jan 2010.
     Translated to Python by PRI September 2019.
     ========================================================================
     ========================================================================
    """
    nt = len(t)
    nPerDay = int(round(1 / numpy.median(numpy.diff(t))))
    iNight = numpy.where(fNight == 1)[0]
    iOut = numpy.where((uStar < 0) | (uStar > 4))[0]
    uStar[iOut] = numpy.nan
    nSeasons = 4
    nStrataN = 4
    nStrataX = 8
    nBins = 50
    nPerBin = 5
    if nPerDay == 24:
        nPerBin = 3
    nPerSeason = nStrataN*nBins*nPerBin
    ntN = nSeasons*nPerSeason

    itNee = numpy.where(~numpy.isnan(NEE + uStar + T))[0]
    itNee = numpy.intersect1d(itNee, iNight)
    ntNee = len(itNee)
    Cp2 = numpy.full((nSeasons, nStrataX, nBoot), numpy.nan)
    Cp3 = numpy.full((nSeasons, nStrataX, nBoot), numpy.nan)
    # Stats2 and Stats3 as dictionaries
    stat_labels = ['ciT', 'mt', 'Fmax', 'puStarVsT', 'ruStarVsT', 'mT', 'n', 'p',
                   'cib0', 'cib1', 'b0', 'b1', 'b2', 'ti', 'tf', 'c2', 'Cp', 'cic2']
    Stats2 = {}
    Stats3 = {}
    for iBoot in range(nBoot):
        Stats2[iBoot] = {}
        Stats3[iBoot] = {}
        for iSeason in range(nSeasons):
            Stats2[iBoot][iSeason] = {}
            Stats3[iBoot][iSeason] = {}
            for iStrata in range(nStrataX):
                Stats2[iBoot][iSeason][iStrata] = {}
                Stats3[iBoot][iSeason][iStrata] = {}
                for stat in stat_labels:
                    Stats2[iBoot][iSeason][iStrata][stat] = numpy.nan
                    Stats3[iBoot][iSeason][iStrata][stat] = numpy.nan
    if ntNee >= ntN:
        for iBoot in range(nBoot):
            if iBoot == 0:
                it = numpy.linspace(0, nt-1, nt).astype(int)
            else:
                it = numpy.sort(numpy.random.randint(0, nt, nt))
            if iBoot > 0:
                fPlot = 0

            print "Calling cpdEvaluateUStarTh4Season20100901"
            t0 = time.time()
            xCp2, xStats2, xCp3, xStats3 = cpdEvaluateUStarTh4Season20100901(t[it], NEE[it], uStar[it],
                                                                             T[it], fNight[it],
                                                                             fPlot, cSiteYr)
            print "cpdEvaluateUStarTh4Season20100901 took " + str(time.time() - t0)

            Cp2[:, :, iBoot] = xCp2
            Stats2[iBoot] = xStats2
            Cp3[:, :, iBoot] = xCp3
            Stats3[iBoot] = xStats3
    else:
        print "cpdBootstrapUStarTh4Season: insufficient points"
    return Cp2, Stats2, Cp3, Stats3
