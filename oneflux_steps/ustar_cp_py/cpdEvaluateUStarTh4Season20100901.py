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
    *varargin,
):
    globals().update(load_all_vars())

    nargin = len(varargin)

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
    itOut = find(logical_or(uStar < 0, uStar > 3))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:79
    uStar[itOut] = NaN
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:79

    itAnnual = find(logical_and(fNight == 1, logical_not(isnan(NEE + uStar + T))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:81
    ntAnnual = length(itAnnual)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:81
    # Initialize outputs.

    Cp2 = matlabarray(dot(NaN, ones(nSeasons, nStrataX)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:85
    Cp3 = matlabarray(dot(NaN, ones(nSeasons, nStrataX)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:86
    StatsMT = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:88
    StatsMT = check_struct(StatsMT)
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

    for iSeason in arange(1, nSeasons).reshape(-1):
        for iStrata in arange(1, nStrataX).reshape(-1):
            try:
                Stats2
            except:
                Stats2 = matlabarray()
            Stats2[iSeason, iStrata] = StatsMT
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:98
            try:
                Stats3
            except:
                Stats3 = matlabarray()
            Stats3[iSeason, iStrata] = StatsMT
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:99

    if ntAnnual < nN:
        return Cp2, Stats2, Cp3, Stats3

    nPerSeason = round(ntAnnual / nSeasons)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:105
    # Move Dec to beginning of year and date as previous year.

    itD = find(m == 12)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:109
    itReOrder = matlabarray([arange(min(itD), nt), arange(1, (min(itD) - 1))])
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:110
    t[itD] = t[itD] - EndDOY
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:111
    t = take(t, itReOrder)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:111
    T = take(T, itReOrder)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:112
    uStar = take(uStar, itReOrder)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:112
    NEE = take(NEE, itReOrder)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:113
    fNight = take(fNight, itReOrder)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:113
    itAnnual = find(logical_and(fNight == 1, logical_not(isnan(NEE + uStar + T))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:115
    ntAnnual = length(itAnnual)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:115
    # Reset nPerSeason and nInc based on actual number of good data.
    # nSeasons is a temporary variable.

    nSeasons = round(ntAnnual / nPerSeason)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:120
    nPerSeason = ntAnnual / nSeasons
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:120
    nPerSeason = round(nPerSeason)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:121
    # Stratify in two dimensions:
    # 1. by time using moving windows
    # 2. by temperature class
    # Then estimate change points Cp2 and Cp3 for each stratum.

    if fPlot == 1:
        fcFigLoc(1, 0.9, 0.9, "MC")
        iPlot = 0
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:128

    for iSeason in arange(1, nSeasons).reshape(-1):
        if 1 == iSeason:
            jtSeason = arange(1, nPerSeason)
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:133
        else:
            if nSeasons == iSeason:
                jtSeason = arange((dot((nSeasons - 1), nPerSeason) + 1), ntAnnual)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:134
            else:
                jtSeason = arange(
                    (dot((iSeason - 1), nPerSeason) + 1), (dot(iSeason, nPerSeason))
                )
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:135
        itSeason = take(itAnnual, jtSeason)
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:137
        ntSeason = length(itSeason)
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:137
        nStrata = floor(ntSeason / (dot(nBins, nPerBin)))
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:138
        if nStrata < nStrataN:
            nStrata = copy(nStrataN)
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:139
        if nStrata > nStrataX:
            nStrata = copy(nStrataX)
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:140
        TTh = prctile(take(T, itSeason), arange(0, 100, (100 / nStrata)))
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:142
        for iStrata in arange(1, nStrata).reshape(-1):
            cPlot = ""
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:145
            if fPlot == 1:
                iPlot = iPlot + 1
                # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:147
                subplot(nSeasons, nStrata, iPlot)
                if logical_and(iSeason == 1, iStrata == 1):
                    cPlot = copy(cSiteYr)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:148
            itStrata = find(
                logical_and(T >= take(TTh, iStrata), T <= take(TTh, iStrata + 1))
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:151
            itStrata = intersect(itStrata, itSeason)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:152
            n, muStar, mNEE = fcBin(
                take(uStar, itStrata),
                take(NEE, itStrata),
                matlabarray([]),
                nPerBin,
                nargout=3,
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:154
            xCp2, xs2, xCp3, xs3 = cpdFindChangePoint20100901(
                muStar, mNEE, fPlot, cPlot, nargout=4
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:156
            n, muStar, mT = fcBin(
                take(uStar, itStrata),
                take(T, itStrata),
                matlabarray([]),
                nPerBin,
                nargout=3,
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:160
            r, p = corrcoef(muStar, mT, nargout=2)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:161
            xs2 = check_struct(xs2)
            xs2.mt = copy(mean(take(t, itStrata)))
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:163
            xs2.ti = copy(take(t, take(itStrata, 1)))
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:163
            xs2.tf = copy(take(t, take(itStrata, end())))
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:163
            xs2.ruStarVsT = copy(take(r, 2, 1))
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:164
            xs2.puStarVsT = copy(take(p, 2, 1))
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:164
            xs2.mT = copy(mean(take(T, itStrata)))
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:165
            xs2.ciT = copy(
                dot(0.5, diff(prctile(take(T, itStrata), matlabarray([2.5, 97.5]))))
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:165
            xs3 = check_struct(xs3)
            xs3.mt = copy(xs2.mt)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:167
            xs3.ti = copy(xs2.ti)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:167
            xs3.tf = copy(xs2.tf)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:167
            xs3.ruStarVsT = copy(xs2.ruStarVsT)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:168
            xs3.puStarVsT = copy(xs2.puStarVsT)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:168
            xs3.mT = copy(xs2.mT)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:169
            xs3.ciT = copy(xs2.ciT)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:169
            Cp2[iSeason, iStrata] = xCp2
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:171
            try:
                Stats2
            except:
                Stats2 = matlabarray()
            Stats2[iSeason, iStrata] = xs2
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:172
            Cp3[iSeason, iStrata] = xCp3
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:174
            try:
                Stats3
            except:
                Stats3 = matlabarray()
            Stats3[iSeason, iStrata] = xs3
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:175

    for i in arange(1, length(varargin)).reshape(-1):
        a = take(varargin, i)
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:182
        if iscell(a) and strcmp(take(a, 1), "jsonencode"):
            for j in arange(2, length(a)).reshape(-1):
                if 2 == take(a, j):
                    Stats2 = jsonencode(Stats2)
                # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:187
                else:
                    if 4 == take(a, j):
                        Stats3 = jsonencode(Stats3)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh4Season20100901.m:189

    return Cp2, Stats2, Cp3, Stats3
