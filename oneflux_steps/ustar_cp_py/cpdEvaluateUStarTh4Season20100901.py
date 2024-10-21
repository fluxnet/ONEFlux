# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m


@function
def cpdEvaluateUStarTh4Season20100901(
    t=None,
    NEE=None,
    uStar=None,
    T=None,
    fNight=None,
    fPlot=None,
    cSiteYr=None,
    varargin=None,
    *args,
    **kwargs,
):
    varargin = cpdEvaluateUStarTh4Season20100901.varargin
    nargin = cpdEvaluateUStarTh4Season20100901.nargin

    # nacpEvaluateUStarTh4Season20100901

    # estimates uStarTh for a site-year of data using change-point
    # detection (cpd) methods implemented within the general framework
    # of the Papale et al. (2006) uStarTh evaluation method.

    # Syntax:
    # [Cp2,Stats2,Cp3,Stats3] = ...
    # cpdEvaluateUStarTh20100901 ...
    # (t,NEE,uStar,T,fNight,fPlot,cSiteYr)
    # where:
    # - Cp2 and Cp3 are nW x nT matrices containing change-point
    # uStarTh estimates from the 2-parameter operational
    # and 3-parameter diagnostic models
    # - Stats2 and Stats3 are structured records containing the corresponding
    # nW x nT matrices of cpd statistics.
    # - t is the time vector
    # - NEE, uStar and T (temperature)
    # - fNight is a vector specifying day (0) or night (1)
    # - fPlot is a scalar flag that is set high (1) to plot
    # - cSiteYr is a text string used in the plot title

    # The analysis is based on one year of data.  The year is stratified
    # by time of year and temperature into nW by nT strata, each with a
    # fixed number of data.
    # The uStarTh is estimated independently for each stratum, using two
    # change-point models: the 2-parameter operational and 3-parameter
    # diagnostic models.

    # The primary modification Papale et al. (2006) is the use of
    # change-point detection (cpd) rather than a moving point test
    # to evaluate the uStarTh.  The cpd method is adopted from
    # Lund and Reeves (2002) and Wang (2003).
    #

    # Relationship to other programs:
    # 1. cpdBootstrapUStarTh20100901
    # - function which processes specified sites including bootstrapping
    # and data output.
    # calls
    # 2. CPDEvaluateUStarTh20100901
    # - function that processes an individual year of data
    # calls
    # 3. cpdFindChangePoint20100901 (change-point detection function).

    # ========================================================================
    # ========================================================================

    # Functions called:

    # cpdFindChangePoint20100901
    # fcBin, fcDatevec, fcDoy
    # stats toolbox:  nanmedian, prctile, regress

    # Written by Alan Barr 15 Jan 2010.

    # ========================================================================
    # ========================================================================

    # Initializations

    nt = length(t)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:66
    y, m, d = fcDatevec(t, nargout=3)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:66
    iYr = median(y)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:67
    EndDOY = fcDoy(datenum(iYr, 12, 31.5))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:67
    nPerDay = round(1 / nanmedian(diff(t)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:69
    nSeasons = 4
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:71
    nStrataN = 4
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:71
    nStrataX = 8
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:71
    nBins = 50
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:71
    nPerBin = 5
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:71
    if 24 == nPerDay:
        nPerBin = 3
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:73
    else:
        if 48 == nPerDay:
            nPerBin = 5
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:74

    nPerSeasonN = dot(dot(nStrataN, nBins), nPerBin)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:76
    nN = dot(nSeasons, nPerSeasonN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:77
    itOut = find(uStar < logical_or(0, uStar) > 3)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:79
    uStar[itOut] = NaN
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:79

    itAnnual = find(fNight == logical_and(1, logical_not(isnan(NEE + uStar + T))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:81
    ntAnnual = length(itAnnual)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:81
    # Initialize outputs.

    Cp2 = dot(NaN, ones(nSeasons, nStrataX))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:85
    Cp3 = dot(NaN, ones(nSeasons, nStrataX))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:86
    StatsMT = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:88
    StatsMT.n = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:89
    StatsMT.Cp = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:89
    StatsMT.Fmax = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:89
    StatsMT.p = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:89
    StatsMT.b0 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:90
    StatsMT.b1 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:90
    StatsMT.b2 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:90
    StatsMT.c2 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:90
    StatsMT.cib0 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:91
    StatsMT.cib1 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:91
    StatsMT.cic2 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:91

    StatsMT.mt = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:92
    StatsMT.ti = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:92
    StatsMT.tf = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:92
    StatsMT.ruStarVsT = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:93
    StatsMT.puStarVsT = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:93
    StatsMT.mT = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:94
    StatsMT.ciT = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:94

    Stats2 = copy(StatsMT)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:96
    Stats3 = copy(StatsMT)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:96
    for iSeason in arange(1, nSeasons).reshape(-1):
        for iStrata in arange(1, nStrataX).reshape(-1):
            Stats2[iSeason, iStrata] = StatsMT
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:99
            Stats3[iSeason, iStrata] = StatsMT
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:100

    if ntAnnual < nN:
        return Cp2, Stats2, Cp3, Stats3

    nPerSeason = round(ntAnnual / nSeasons)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:106
    # Move Dec to beginning of year and date as previous year.

    itD = find(m == 12)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:110
    itReOrder = matlabarray(concat([arange(min(itD), nt), arange(1, (min(itD) - 1))]))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:111
    t[itD] = t[itD] - EndDOY
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:112
    t = t[itReOrder]
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:112
    T = T[itReOrder]
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:113
    uStar = uStar[itReOrder]
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:113
    NEE = NEE[itReOrder]
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:114
    fNight = fNight[itReOrder]
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:114
    itAnnual = find(fNight == logical_and(1, logical_not(isnan(NEE + uStar + T))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:116
    ntAnnual = length(itAnnual)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:116
    # Reset nPerSeason and nInc based on actual number of good data.
    # nSeasons is a temporary variable.

    nSeasons = round(ntAnnual / nPerSeason)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:121
    nPerSeason = ntAnnual / nSeasons
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:121
    nPerSeason = round(nPerSeason)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:122
    # Stratify in two dimensions:
    # 1. by time using moving windows
    # 2. by temperature class
    # Then estimate change points Cp2 and Cp3 for each stratum.

    if fPlot == 1:
        fcFigLoc(1, 0.9, 0.9, "MC")
        iPlot = 0
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:129

    for iSeason in arange(1, nSeasons).reshape(-1):
        if 1 == iSeason:
            jtSeason = arange(1, nPerSeason)
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:134
        else:
            if nSeasons == iSeason:
                jtSeason = arange((dot((nSeasons - 1), nPerSeason) + 1), ntAnnual)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:135
            else:
                jtSeason = arange(
                    (dot((iSeason - 1), nPerSeason) + 1), (dot(iSeason, nPerSeason))
                )
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:136
        itSeason = itAnnual[jtSeason]
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:138
        ntSeason = length(itSeason)
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:138
        nStrata = floor(ntSeason / (dot(nBins, nPerBin)))
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:139
        if nStrata < nStrataN:
            nStrata = copy(nStrataN)
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:140
        if nStrata > nStrataX:
            nStrata = copy(nStrataX)
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:141
        TTh = prctile(T[itSeason], arange(0, 100, (100 / nStrata)))
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:143
        for iStrata in arange(1, nStrata).reshape(-1):
            cPlot = ""
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:146
            if fPlot == 1:
                iPlot = iPlot + 1
                # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:148
                subplot(nSeasons, nStrata, iPlot)
                if iSeason == logical_and(1, iStrata) == 1:
                    cPlot = copy(cSiteYr)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:149
            itStrata = find(T >= logical_and(TTh[iStrata], T) <= TTh[iStrata + 1])
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:152
            itStrata = intersect(itStrata, itSeason)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:153
            n, muStar, mNEE = fcBin(
                uStar[itStrata], NEE[itStrata], [], nPerBin, nargout=3
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:155
            xCp2, xs2, xCp3, xs3 = cpdFindChangePoint20100901(
                muStar, mNEE, fPlot, cPlot, nargout=4
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:157
            n, muStar, mT = fcBin(uStar[itStrata], T[itStrata], [], nPerBin, nargout=3)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:161
            r, p = corrcoef(muStar, mT, nargout=2)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:162
            xs2.mt = copy(mean(t[itStrata]))
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:164
            xs2.ti = copy(t[itStrata[1]])
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:164
            xs2.tf = copy(t[itStrata[end()]])
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:164
            xs2.ruStarVsT = copy(r[2, 1])
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:165
            xs2.puStarVsT = copy(p[2, 1])
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:165
            xs2.mT = copy(mean(T[itStrata]))
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:166
            xs2.ciT = copy(dot(0.5, diff(prctile(T[itStrata], concat([2.5, 97.5])))))
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:166
            xs3.mt = copy(xs2.mt)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:168
            xs3.ti = copy(xs2.ti)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:168
            xs3.tf = copy(xs2.tf)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:168
            xs3.ruStarVsT = copy(xs2.ruStarVsT)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:169
            xs3.puStarVsT = copy(xs2.puStarVsT)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:169
            xs3.mT = copy(xs2.mT)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:170
            xs3.ciT = copy(xs2.ciT)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:170
            Cp2[iSeason, iStrata] = xCp2
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:172
            Stats2[iSeason, iStrata] = xs2
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:173
            Cp3[iSeason, iStrata] = xCp3
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:175
            Stats3[iSeason, iStrata] = xs3
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:176

    if size(varargin) > 0:
        Stats2 = jsonencode(Stats2)
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:183
        Stats3 = jsonencode(Stats3)


# oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:184

# ========================================================================
# ========================================================================
