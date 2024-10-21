# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m


@function
def cpdEvaluateUStarTh20100901(
    t=None,
    NEE=None,
    uStar=None,
    T=None,
    fNight=None,
    fPlot=None,
    cSiteYr=None,
    *args,
    **kwargs,
):
    varargin = cpdEvaluateUStarTh20100901.varargin
    nargin = cpdEvaluateUStarTh20100901.nargin

    # cpdEvaluateUStarTh20100901

    # estimates uStarTh for one site-year of data using change-point
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
    # - Stats2 and Stats3 are structured records containing the
    # corresponding nW x nT matrices of cpd statistics.
    # - t is the time vector
    # - NEE, uStar and T (temperature)
    # - fNight is a vector specifying day (0) or night (1)
    # - fPlot is a scalar flag that is set high (1) to plot
    # - cSiteYr is a text string used in the plot title

    # The analysis is based on one year of data.
    # The data are stratified by time of year
    # and temperature into nW by nT strata,
    # each with a fixed number of data.
    # The uStarTh is estimated independently for each stratum,
    # using two separate change-point models:
    # the 2-parameter operational and
    # 3-parameter diagnostic models.

    # The primary modification Papale et al. (2006) is the use of
    # change-point detection (cpd) rather than a moving point test
    # to evaluate the uStarTh.  The cpd method is adopted from
    # Lund and Reeves (2002) and Wang (2003).

    # Relationship to other programs:

    # 1. cpdBootstrapUStarTh20100901
    # - function that implements bootstrapping
    # to estimate uncertainty in annual uStarTh
    # calls
    # 2. CPDEvaluateUStarTh20100901
    # - function that computes uStarTh for one site-year of data
    # with independent uStarTh analyses for each nW x nT strata
    # (after stratifying by time of year and temerature)
    # calls
    # 3. cpdFindChangePoint20100901
    # - function for change-point detection
    # applied to each strata

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

    # Seasonal variation is evaluated using moving windows of 1,000 good
    # points (for 30-min data) or 600 good points (for 60-min data).

    # Within each window, the data are stratified by temperature
    # into 4 equal classes.

    nt = length(t)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:79
    y, m, d = fcDatevec(t, nargout=3)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:79
    iYr = median(y)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:80
    EndDOY = fcDoy(datenum(iYr, 12, 31.5))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:80
    nPerDay = round(1 / nanmedian(diff(t)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:82
    nWindowsN = 4
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:84
    nStrata = 4
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:84
    nBins = 50
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:84
    nPerBin = 5
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:84
    if 24 == nPerDay:
        nPerBin = 3
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:86
    else:
        if 48 == nPerDay:
            nPerBin = 5
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:87

    nPerWindow = dot(dot(nStrata, nBins), nPerBin)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:89
    nInc = dot(0.5, nPerWindow)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:89
    nN = dot(nWindowsN, nPerWindow)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:90
    itOut = find(uStar < logical_or(0, uStar) > 3)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:92
    uStar[itOut] = NaN
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:92

    itAnnual = find(fNight == logical_and(1, logical_not(isnan(NEE + uStar + T))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:94
    ntAnnual = length(itAnnual)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:94
    # Initialize outputs.

    Cp2 = dot(NaN, ones(nWindowsN, nStrata))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:98
    Cp3 = dot(NaN, ones(nWindowsN, nStrata))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:99
    StatsMT = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:101
    StatsMT.n = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:102
    StatsMT.Cp = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:102
    StatsMT.Fmax = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:102
    StatsMT.p = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:102
    StatsMT.b0 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:103
    StatsMT.b1 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:103
    StatsMT.b2 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:103
    StatsMT.c2 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:103
    StatsMT.cib0 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:104
    StatsMT.cib1 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:104
    StatsMT.cic2 = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:104

    StatsMT.mt = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:105
    StatsMT.ti = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:105
    StatsMT.tf = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:105
    StatsMT.ruStarVsT = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:106
    StatsMT.puStarVsT = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:106
    StatsMT.mT = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:107
    StatsMT.ciT = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:107

    Stats2 = copy(StatsMT)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:109
    Stats3 = copy(StatsMT)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:109
    for iWindow in arange(1, nWindowsN).reshape(-1):
        for iStrata in arange(1, nStrata).reshape(-1):
            Stats2[iWindow, iStrata] = StatsMT
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:112
            Stats3[iWindow, iStrata] = StatsMT
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:113

    if ntAnnual < nN:
        return Cp2, Stats2, Cp3, Stats3

    # append wrap-around data to start and end of record;
    # 18 Jan 2010 just need to wrap one end.

    itAdd1 = arange(itAnnual[end() - nInc - 1], nt)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:122

    t = matlabarray(concat([[t[itAdd1] - EndDOY], [t]]))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:124
    T = matlabarray(concat([[T[itAdd1]], [T]]))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:125
    uStar = matlabarray(concat([[uStar[itAdd1]], [uStar]]))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:126
    NEE = matlabarray(concat([[NEE[itAdd1]], [NEE]]))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:127
    fNight = matlabarray(concat([[fNight[itAdd1]], [fNight]]))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:128
    itAnnual = find(fNight == logical_and(1, logical_not(isnan(NEE + uStar + T))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:130
    ntAnnual = length(itAnnual)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:130
    # Reset nPerWindow and nInc based on actual number of good data.
    # nWindows is a temporary variable.

    nWindows = round(ntAnnual / nPerWindow)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:135
    nPerWindow = ntAnnual / nWindows
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:135
    nInc = round(nPerWindow / 2)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:136
    nPerWindow = round(nPerWindow)
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:136
    # Stratify in two dimensions:
    # 1. by time using moving windows
    # 2. by temperature class
    # Then estimate change points Cp2 and Cp3 for each stratum.

    iWindow = 0
    # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:143
    for jt1 in arange(1, (ntAnnual - nInc), nInc).reshape(-1):
        iWindow = iWindow + 1
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:147
        jt2 = jt1 + nPerWindow - 1
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:149
        if jt2 > ntAnnual:
            jt2 = copy(ntAnnual)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:150
            jt1 = ntAnnual - nPerWindow + 1
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:150
        itWindow = itAnnual[arange(jt1, jt2)]
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:151
        TTh = prctile(T[itWindow], arange(0, 100, (100 / nStrata)))
        # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:153
        for iStrata in arange(1, nStrata).reshape(-1):
            itStrata = find(T >= logical_and(TTh[iStrata], T) <= TTh[iStrata + 1])
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:156
            itStrata = intersect(itStrata, itWindow)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:157
            n, muStar, mNEE = fcBin(
                uStar[itStrata], NEE[itStrata], [], nPerBin, nargout=3
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:159
            xCp2, xs2, xCp3, xs3 = cpdFindChangePoint20100901(
                muStar, mNEE, fPlot, cSiteYr, nargout=4
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:161
            n, muStar, mT = fcBin(uStar[itStrata], T[itStrata], [], nPerBin, nargout=3)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:165
            r, p = corrcoef(muStar, mT, nargout=2)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:166
            xs2.mt = copy(mean(t[itStrata]))
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:168
            xs2.ti = copy(t[itStrata[1]])
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:168
            xs2.tf = copy(t[itStrata[end()]])
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:168
            xs2.ruStarVsT = copy(r[2, 1])
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:169
            xs2.puStarVsT = copy(p[2, 1])
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:169
            xs2.mT = copy(mean(T[itStrata]))
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:170
            xs2.ciT = copy(dot(0.5, diff(prctile(T[itStrata], concat([2.5, 97.5])))))
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:170
            xs3.mt = copy(xs2.mt)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:172
            xs3.ti = copy(xs2.ti)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:172
            xs3.tf = copy(xs2.tf)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:172
            xs3.ruStarVsT = copy(xs2.ruStarVsT)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:173
            xs3.puStarVsT = copy(xs2.puStarVsT)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:173
            xs3.mT = copy(xs2.mT)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:174
            xs3.ciT = copy(xs2.ciT)
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:174
            Cp2[iWindow, iStrata] = xCp2
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:176
            Stats2[iWindow, iStrata] = xs2
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:177
            Cp3[iWindow, iStrata] = xCp3
            # oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:179
            Stats3[iWindow, iStrata] = xs3


# oneflux_steps/ustar_cp_refactor_wip/cpdEvaluateUStarTh20100901.m:180


# ========================================================================
# ========================================================================
