# Generated with SMOP  0.41-beta
from .libsmop import *

# ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m


@function
def cpdBootstrapUStarTh4Season20100901(
    t=None,
    NEE=None,
    uStar=None,
    T=None,
    fNight=None,
    fPlot=None,
    cSiteYr=None,
    nBoot=None,
    *args,
    **kwargs
):
    varargin = cpdBootstrapUStarTh4Season20100901.varargin
    nargin = cpdBootstrapUStarTh4Season20100901.nargin

    # 	cpdBootstrapUStarTh4Season20100901

    # 	is a simplified operational version of

    # 	20100901 changes 3A 4I to 2A 3I as sggested by Xiaolan Wang.

    # 	20100408 replaces 20100318, updating ChPt function from:
    # 	FindChangePointMod3LundReeves2002_20100318 to
    # 	FindChangePointMod2A4ILundReeves2002_20100408.
    # 	which: adds back A model, makes a correction to the significance test,
    # 	and adds a comparison of the 4- versus 3-parameter models.
    # 	and adds a comparison of the 4- versus 3-parameter models.

    # 	20100318 new version with small tweaks to FindChangePoint
    # 	also adds mT and ciT to Stats structures.

    # 	is a new working implementation of Alan's u*Th evaluation algorithm
    # 	based on Lund and Reeves' (2002) modified by Wang's (2003) change-point
    # 	detection algorithm.

    # 	Relationship to other programs:

    # 	Called by batchNewNacpEstimateUStarTh_Moving_Mod3LundChPt_20100115
    # 		- script which identifies which sites to process
    # 	Calls newNacpEvaluateUStarTh_MovingStrat_20100114
    # 		- function that processes an individual year of data, using
    # 		  FindChangePointMod3LundReeves2002_20091204
    #
    # 	This implementation may supplant all previous versions.

    # 	It uses moving windows of fixed size to evaluate seasonal variation.

    # 	Three combinations of stratification and pooling are implemented.
    # 	 - All begin with 2D (time x temperature) stratification
    # 	   (moving-window time x n temperature classes within each window).
    # 	 - Two (W and A) add normalization and pooling.

    # 	1. Method S (full stratification)
    # 		estimates the change-points for each of the strata
    # 		(nWindows x nTClasses) with no need for normalization.
    # 	2. Method W (pooling within time windows)
    # 		begins with a variant of S but pools the temperature classes
    # 		within each time window before estimating one change-point per window.
    # 		Before pooling, the binned mean NEE data within each temperature class
    # 		are normalized against the 80th NEE percentile for that class.
    # 	3. Method A (pooling to annual)
    # 		further pools the pooled normalized data from W over all time windows
    # 		before estimating a single change-point per year.
    #
    # 	The detailed analysis parameters are output in a Stats structured
    # 	record.

    # 	========================================================================
    # 	========================================================================

    # 	Functions called:

    # 		cpdEvaluateUStarTh20100901
    # 		fcx2roevec
    # 		stats toolbox:  nanmedian

    # 	Written by Alan Barr 15 Jan 2010.

    # 	========================================================================
    # 	========================================================================

    nt = length(t)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:71
    nPerDay = round(1 / nanmedian(diff(t)))
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:72
    iNight = find(fNight)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:74
    iOut = find(uStar < logical_or(0, uStar) > 4)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:75
    uStar[iOut] = NaN
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:75
    nSeasons = 4
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:77
    nStrataN = 4
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:77
    nStrataX = 8
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:77
    nBins = 50
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:77
    nPerBin = 5
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:77
    if 24 == nPerDay:
        nPerBin = 3
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:80
    else:
        if 48 == nPerDay:
            nPerBin = 5
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:81

    nPerSeason = dot(dot(nStrataN, nBins), nPerBin)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:83
    ntN = dot(nSeasons, nPerSeason)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:84
    # 	===================================================================
    # 	===================================================================

    itNee = find(logical_not(isnan(NEE + uStar + T)))
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:89
    itNee = intersect(itNee, iNight)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:90
    ntNee = length(itNee)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:90
    StatsMT = []
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:92
    StatsMT.n = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:93
    StatsMT.Cp = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:93
    StatsMT.Fmax = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:93
    StatsMT.p = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:93
    StatsMT.b0 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:94
    StatsMT.b1 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:94
    StatsMT.b2 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:94
    StatsMT.c2 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:94
    StatsMT.cib0 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:95
    StatsMT.cib1 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:95
    StatsMT.cic2 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:95
    StatsMT.mt = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:96
    StatsMT.ti = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:96
    StatsMT.tf = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:96
    StatsMT.ruStarVsT = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:97
    StatsMT.puStarVsT = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:97
    StatsMT.mT = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:98
    StatsMT.ciT = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:98
    Cp2 = dot(NaN, ones(nSeasons, nStrataX, nBoot))
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:100
    Cp3 = dot(NaN, ones(nSeasons, nStrataX, nBoot))
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:101
    Stats2 = copy(StatsMT)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:103
    Stats3 = copy(StatsMT)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:103
    for iBoot in arange(1, nBoot).reshape(-1):
        for iSeason in arange(1, nSeasons).reshape(-1):
            for iStrata in arange(1, nStrataX).reshape(-1):
                Stats2[iSeason, iStrata, iBoot] = StatsMT
                # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:107
                Stats3[iSeason, iStrata, iBoot] = StatsMT
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:108

    # disp(' ');
    # fprintf('cpdBootstrapUStarTh4Season20100901  #s   nObs: #g #g #g #g \n',cSiteYr,nt,sum(~isnan([NEE uStar T])));
    # disp(' ');

    if ntNee >= ntN:
        for iBoot in arange(1, nBoot).reshape(-1):
            t0 = copy(now)
            # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:124
            it = sort(randi(nt, nt, 1))
            # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:126
            ntNee = sum(ismember(it, itNee))
            # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:127
            if iBoot > 1:
                fPlot = 0
            # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:129
            xCp2, xStats2, xCp3, xStats3 = cpdEvaluateUStarTh4Season20100901(
                t(it), NEE(it), uStar(it), T(it), fNight(it), fPlot, cSiteYr, nargout=4
            )
            # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:131
            dt = dot(dot(dot((now - t0), 24), 60), 60)
            # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:135
            # fprintf('Bootstrap uStarTh #s:  #g/#g   nObs #g  Cp2 #4.3f  Cp3 #4.3f   #3.1fs \n', ...
            # 	cSiteYr,iBoot,nBoot,ntNee,nanmedian(fcx2rowvec(xCp2)),nanmedian(fcx2rowvec(xCp3)),dt);
            Cp2[arange(), arange(), iBoot] = xCp2
            # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:140
            Stats2[arange(), arange(), iBoot] = xStats2
            # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:140
            Cp3[arange(), arange(), iBoot] = xCp3
            # ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:141
            Stats3[arange(), arange(), iBoot] = xStats3


# ../ONEFlux/oneflux_steps/ustar_cp/cpdBootstrapUStarTh4Season20100901.m:141
