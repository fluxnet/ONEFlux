# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m


@function
def cpdBootstrapUStarTh20100901(
    t=None,
    NEE=None,
    uStar=None,
    T=None,
    fNight=None,
    fPlot=None,
    cSiteYr=None,
    nBoot=None,
    *args,
    **kwargs,
):
    varargin = cpdBootstrapUStarTh20100901.varargin
    nargin = cpdBootstrapUStarTh20100901.nargin

    # cpdBootstrapUStarTh20100901

    # estimates uStarTh uncertainty for one site-year of data
    # using change-point detection (cpd) methods
    # implemented within the general framework
    # of the Papale et al. (2006) uStarTh algorithm

    # Syntax:

    # [Cp2,Stats2,Cp3,Stats3] = ...
    # cpdBootstrapUStarTh20100901 ...
    # (t,NEE,uStar,T,fNight,fPlot,cSiteYr,nBoot)
    # where:
    # - Cp2 and Cp3 are nW x nT x nBoot matrices containing change-point
    # uStarTh estimates from the 2-parameter operational
    # and 3-parameter diagnostic models
    # - Stats2 and Stats3 are structured records containing the corresponding
    # nW x nT x nBoot matrices of cpd statistics.
    # - t is the time vector
    # - NEE, uStar and T (temperature) are inputs
    # - fNight is a vector specifying day (0) or night (1)
    # - fPlot is a scalar flag that is set high (1) to plot
    # - cSiteYr is a text string used in the plot title
    # - nBoot is the number of bootstraps

    # Relationship to other programs:

    # 1. cpdBootstrapUStarTh20100901
    # - function that implements bootstrapping
    # to estimate uncertainty in annual uStarTh
    # calls
    # 2. CPDEvaluateUStarTh20100901
    # - function that computes uStarTh for one site-year of data
    # with independent uStarTh analyses for each of nW x nT strata
    # (stratified by time of year and temerature)
    # calls
    # 3. cpdFindChangePoint20100901
    # - function for change-point detection
    # applied to individual strata

    # ========================================================================
    # ========================================================================

    # Functions called:

    # cpdEvaluateUStarTh20100901
    # fcx2roevec
    # stats toolbox:  nanmedian

    # Written by Alan Barr 15 Jan 2010.

    # ========================================================================
    # ========================================================================

    # Initializations

    nt = length(t)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:61
    nPerDay = round(1 / nanmedian(diff(t)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:62
    nWindowsN = 4
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:64
    nStrata = 4
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:64
    nBins = 50
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:64
    nPerBin = 5
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:64
    if 24 == nPerDay:
        nPerBin = 3
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:66
    else:
        if 48 == nPerDay:
            nPerBin = 5
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:67

    nPerWindow = dot(dot(nStrata, nBins), nPerBin)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:69
    nInc = dot(0.5, nPerWindow)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:70
    ntN = dot(nWindowsN, nPerWindow)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:71
    iNight = find(fNight)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:73
    uStar[uStar < logical_or(0, uStar) > 4] = NaN
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:74

    itNee = find(logical_not(isnan(NEE + uStar + T)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:76
    itNee = intersect(itNee, iNight)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:76
    ntNee = length(itNee)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:77
    nWindows = ceil(ntNee / nInc) + 1
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:78

    StatsMT = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:80
    StatsMT.n = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:81
    StatsMT.Cp = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:81
    StatsMT.Fmax = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:81
    StatsMT.p = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:81
    StatsMT.b0 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:82
    StatsMT.b1 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:82
    StatsMT.b2 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:82
    StatsMT.c2 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:82
    StatsMT.cib0 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:83
    StatsMT.cib1 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:83
    StatsMT.cic2 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:83
    StatsMT.mt = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:84
    StatsMT.ti = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:84
    StatsMT.tf = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:84
    StatsMT.ruStarVsT = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:85
    StatsMT.puStarVsT = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:85
    StatsMT.mT = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:86
    StatsMT.ciT = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:86
    Cp2 = dot(NaN, ones(nWindows, nStrata, nBoot))
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:88
    Cp3 = dot(NaN, ones(nWindows, nStrata, nBoot))
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:89
    Stats2 = copy(StatsMT)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:91
    Stats3 = copy(StatsMT)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:91
    for iBoot in arange(1, nBoot).reshape(-1):
        for iWindow in arange(1, nWindows).reshape(-1):
            for iStrata in arange(1, nStrata).reshape(-1):
                Stats2[iWindow, iStrata, iBoot] = StatsMT
                # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:95
                Stats3[iWindow, iStrata, iBoot] = StatsMT
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:96

    disp(" ")
    fprintf(
        "cpdBootstrapUStarTh20100901  %s   nObs: %g %g %g %g \n",
        cSiteYr,
        nt,
        sum(logical_not(isnan(concat([NEE, uStar, T])))),
    )
    disp(" ")
    # Bootstrapping.

    if ntNee >= ntN:
        for iBoot in arange(1, nBoot).reshape(-1):
            t0 = copy(now)
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:111
            it = sort(randi(nt, nt, 1))
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:113
            ntNee = sum(ismember(it, itNee))
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:114
            if iBoot > 1:
                fPlot = 0
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:116
            xCp2, xStats2, xCp3, xStats3 = cpdEvaluateUStarTh20100901(
                t[it], NEE[it], uStar[it], T[it], fNight[it], fPlot, cSiteYr, nargout=4
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:118
            nW, nS = size(xCp2, nargout=2)
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:122
            dt = dot(dot(dot((now - t0), 24), 60), 60)
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:123
            fprintf(
                "Bootstrap uStarTh %s:  %g/%g   nObs %g  nWindows %g   Cp2 %4.3f  Cp3 %4.3f   %3.1fs \n",
                cSiteYr,
                iBoot,
                nBoot,
                ntNee,
                nW,
                nanmedian(fcx2rowvec(xCp2)),
                nanmedian(fcx2rowvec(xCp3)),
                dt,
            )
            Cp2[arange(1, nW), arange(), iBoot] = xCp2
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:127
            Stats2[arange(1, nW), arange(), iBoot] = xStats2
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:127
            Cp3[arange(1, nW), arange(), iBoot] = xCp3
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:128
            Stats3[arange(1, nW), arange(), iBoot] = xStats3


# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh20100901.m:128


# ========================================================================
# ========================================================================
