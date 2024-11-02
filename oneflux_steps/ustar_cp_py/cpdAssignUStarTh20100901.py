# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m


@function
def cpdAssignUStarTh20100901(Stats=None, fPlot=None, cSiteYr=None, *varargin):
    globals().update(load_all_vars())

    nargin = len(varargin)

    # cpdAssignUStarTh20100901
    # aggregates and assigns uStarTh from the Stats* structured records
    # as output by cpdBootstrapUStarTh20100901.

    # Syntax:

    # [CpA,nA,tW,CpW,cMode,cFailure,fSelect,sSine,FracSig,FracModeD,FracSelect] ...
    # = cpdExtractuStarTh20100901 (Stats,fPlot,cSiteYr)

    # where:

    # -	Stats is a structured record output by
    # cpdBootstrapuStarTh20100901, can be:
    # - Stats2 (2-parameter operational change-point model) or
    # - Stats3 (3-parameter diagnostic change-point model)
    # -	fPlot is a flag that is set to 1 for plotting
    # the aggregation analysis
    # -	cSiteYr is text containing site and year for the fPlot plot

    # -	CpA is a scalar or vector of annual uStarTh (ChangePoint) means
    # -	nA is the number of selected change-points in the annual mean
    # -	CpW and tW are vectors showing seasonal variation in uStarTh
    # -	cMode is the dominant change-point mode:
    # D Deficit (b1>0) or E Excess (b1<0)
    # -	cFailure is a string containing failure messages
    # -	fSelect is an array the same size as Stats* that flags the
    # selected Cp values for computing CpA and CpW
    # -	sSine contains the coefficients of an annual sine curve
    # fit to tW and CpW
    # -	FracSig,FracModeD,FracSelect are the fraction of attempted
    # change-point detections that are significant, in mode D and
    # select.

    # The Stats2 or Stats3 records may be 2D (nWindows x nStrata)
    # or 3D (nWindows x nStrata x nBoot). If 2D, then CpA
    # is a scalar and CpW is averaged across the nStrata temperature strata.
    # If 3D, then CpA is a vector of length nBoot and CpW is averaged
    # across nBoot bootstraps and nStrata temperature strata.
    # Stats input is accepted from both 4Season (nWindows=4)
    # and flexible window (nWindows>=7) processing.

    # The aggregation process is selective, selecting only:
    # - significant change points (p <= 0.05)
    # - in the dominant mode (Deficit (b1>0) or Excess (b1<0))
    # - after excluding outliers (based on regression stats).
    # No assignment is made if the detection failure rate
    # is too high.

    # ========================================================================
    # ========================================================================

    # Functions called:

    # fcBin, fcDatetick, fcEqnAnnualSine, fcNaniqr, fcReadFields
    # fcr2Calc, fcx2colvec, fcx2rowvec
    # stats toolbox:  nanmedian, nanmean, nlinfit, prctile

    # Written 16 April 2010 by Alan Barr

    # =======================================================================
    # =======================================================================

    for i in arange(1, length(varargin)).reshape(-1):
        a = take(varargin, i)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:67
        if iscell(a) and strcmp(take(a, 1), "jsondecode"):
            for j in arange(2, length(a)).reshape(-1):
                if 1 == take(a, j):
                    Stats = jsondecode(Stats)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:72

    CpA = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:78
    nA = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:78
    tW = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:78
    CpW = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:78
    fSelect = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:78
    cMode = ""
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:78
    cFailure = ""
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:78
    sSine = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:78
    FracSig = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:79
    FracModeD = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:79
    FracSelect = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:79
    # Compute window sizes etc.

    nDim = ndims(Stats)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:83
    if 2 == nDim:
        nWindows, nBoot = size(Stats, nargout=2)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:85
        nStrata = 1
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:85
        nStrataN = 0.5
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:85
    else:
        if 3 == nDim:
            nWindows, nStrata, nBoot = size(Stats, nargout=3)
            # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:86
            nStrataN = 1
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:86
        else:
            cFailure = "Stats must be 2D or 3D."
            # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:87
            return (
                CpA,
                nA,
                tW,
                CpW,
                cMode,
                cFailure,
                fSelect,
                sSine,
                FracSig,
                FracModeD,
                FracSelect,
            )

    nWindowsN = 4
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:89
    nSelectN = dot(dot(nWindowsN, nStrataN), nBoot)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:89
    CpA = dot(NaN, ones(nBoot, 1))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:91
    nA = dot(NaN, ones(nBoot, 1))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:91
    tW = dot(NaN, ones(nWindows, 1))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:91
    CpW = dot(NaN, ones(nWindows, 1))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:91
    # Extract variable arrays from Stats structure.
    # Reassign mt and Cp as x* to retain array shape,
    # then convert the extracted arrays to column vectors.

    cVars = cellarray(["mt", "Cp", "b1", "c2", "cib1", "cic2", "p"])
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:97
    nVars = length(cVars)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:97
    for i in arange(1, nVars).reshape(-1):
        cv = char(cVars[i])
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:99
        eval(cv + "=fcReadFields(Stats," " + cv + " ");")
        if "mt" == cv:
            xmt = copy(mt)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:101
        else:
            if "Cp" == cv:
                xCp = copy(Cp)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:102
        eval(cv + "=fcx2colvec(" + cv + ");")

    pSig = 0.05
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:107
    fP = p <= pSig
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:107
    # Determine if Stats input is from the operational 2-parameter
    # or diagnostic 3-parameter change-point model
    # and set c2 and cic2 to zero if 2-parameter

    nPar = 3
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:113
    if sum(logical_not(isnan(c2))) == 0:
        nPar = 2
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:113
        c2 = dot(0, b1)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:113
        cic2 = copy(c2)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:113

    # Classify Cp regressions by slopes of b1 and c2 regression coeff:
    # - NS: not sig, mfP=NaN, p>0.05
    # - ModeE: atypical significant Cp (b1<c2)
    # - ModeD: typical significant Cp (b1>=c2)

    iTry = find(logical_not(isnan(mt)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:120
    nTry = length(iTry)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:120
    iCp = find(logical_not(isnan(b1 + c2 + Cp)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:121
    nCp = length(iCp)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:121
    iNS = find(logical_and(fP == 0, logical_not(isnan(b1 + c2 + Cp))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:122
    nNS = length(iNS)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:122
    iSig = find(logical_and(fP == 1, logical_not(isnan(b1 + c2 + Cp))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:123
    nSig = length(iSig)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:123
    iModeE = find(logical_and(fP == 1, b1 < c2))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:124
    nModeE = length(iModeE)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:124
    iModeD = find(logical_and(fP == 1, b1 >= c2))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:125
    nModeD = length(iModeD)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:125
    # Evaluate and accept primary mode of significant Cps

    if nModeD >= nModeE:
        iSelect = copy(iModeD)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:129
        cMode = "D"
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:129
    else:
        iSelect = copy(iModeE)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:129
        cMode = "E"
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:129

    nSelect = length(iSelect)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:129
    fSelect = matlabarray(zeros(size(fP)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:130
    fSelect[iSelect] = 1
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:130
    fSelect = logical(fSelect)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:130
    fModeD = matlabarray(dot(NaN, ones(size(fP))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:131
    fModeD[iModeD] = 1
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:131
    fModeE = matlabarray(dot(NaN, ones(size(fP))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:132
    fModeE[iModeE] = 1
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:132
    FracSig = nSig / nTry
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:134
    FracModeD = nModeD / nSig
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:134
    FracSelect = nSelect / nTry
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:134
    # Abort analysis if too few of the regressions produce significant Cps.

    if FracSelect < 0.1:
        cFailure = "Less than 10% successful detections. "
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:138
        return (
            CpA,
            nA,
            tW,
            CpW,
            cMode,
            cFailure,
            fSelect,
            sSine,
            FracSig,
            FracModeD,
            FracSelect,
        )

    # Exclude outliers from Select mode based on Cp and regression stats

    if 2 == nPar:
        x = matlabarray(concat([Cp, b1, cib1]))
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:143
        nx = 3
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:143
    else:
        if 3 == nPar:
            x = matlabarray(concat([Cp, b1, c2, cib1, cic2]))
            # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:144
            nx = 5
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:144

    mx = nanmedian(x)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:147
    sx = fcNaniqr(x)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:147
    xNorm = matlabarray(dot(NaN, x))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:148
    for i in arange(1, nx).reshape(-1):
        xNorm[:, i] = (x[:, 1] - take(mx, i)) / take(sx, i)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:148

    xNormX = max(abs(xNorm), [], 2)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:149
    ns = 5
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:150
    fOut = xNormX > ns
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:150
    iOut = find(fOut)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:150
    iSelect = setdiff(iSelect, iOut)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:151
    nSelect = length(iSelect)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:151
    fSelect = logical_and(logical_not(fOut), fSelect)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:152
    fModeD[iOut] = NaN
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:153
    iModeD = find(fModeD == 1)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:153
    nModeD = length(iModeD)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:153
    fModeE[iOut] = NaN
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:154
    iModeE = find(fModeE == 1)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:154
    nModeE = length(iModeE)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:154
    iSig = union(iModeD, iModeE)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:155
    nSig = length(iSig)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:155
    FracSig = nSig / nTry
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:157
    FracModeD = nModeD / nSig
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:157
    FracSelect = nSelect / nTry
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:157
    if nSelect < nSelectN:
        cFailure = sprintf("Too few selected change points: %g/%g", nSelect, nSelectN)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:159
        return (
            CpA,
            nA,
            tW,
            CpW,
            cMode,
            cFailure,
            fSelect,
            sSine,
            FracSig,
            FracModeD,
            FracSelect,
        )

    # Aggregate the values to season and year.

    xCpSelect = matlabarray(dot(NaN, xCp))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:163
    xCpSelect[iSelect] = xCp(iSelect)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:163
    xCpGF = copy(xCpSelect)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:163
    if 2 == nDim:
        CpA = fcx2colvec(nanmean(xCpGF))
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:165
        nA = fcx2colvec(sum(logical_not(isnan(xCpSelect))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:166
    else:
        if 3 == nDim:
            CpA = fcx2colvec(nanmean(reshape(xCpGF, dot(nWindows, nStrata), nBoot)))
            # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:167
            nA = fcx2colvec(
                sum(
                    logical_not(
                        isnan(reshape(xCpSelect, dot(nWindows, nStrata), nBoot))
                    )
                )
            )
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:168

    # Calculate mean tW and CpW for each window based on Select data only.
    # Because the bootstrap varies the number of windows among bootstraps,
    # base on the median number of windows and reshape sorted data.

    nW = nanmedian(sum(logical_not(isnan(reshape(xmt, nWindows, dot(nStrata, nBoot))))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:175
    mtSelect, i = sort(mt(iSelect), nargout=2)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:176
    CpSelect = Cp(take(iSelect, i))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:176
    xBins = prctile(mtSelect, arange(0, 100, (100 / nW)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:177
    n, tW, CpW = fcBin(mtSelect, CpSelect, xBins, 0, nargout=3)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:178
    # Fit annual sine curve

    bSine = matlabarray(concat([1, 1, 1]))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:182
    bSine = nlinfit(mt(iSelect), Cp(iSelect), "fcEqnAnnualSine", bSine)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:183
    yHat = fcEqnAnnualSine(bSine, mt(iSelect))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:184
    r2 = fcr2Calc(Cp(iSelect), yHat)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:184
    mtHat = sort(mt(iSelect))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:185
    CpHat = fcEqnAnnualSine(bSine, mtHat)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:185
    if bSine[2] < 0:
        bSine[2] = -bSine[2]
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:187
        bSine[3] = bSine[3] + 365.25 / 2
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:187

    bSine[3] = mod(bSine[3], 365.25)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:188
    sSine = matlabarray(concat([fcx2rowvec(bSine), r2]))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:189
    # =======================================================================
    # =======================================================================

    if fPlot:
        FracSelectByWindow = sum(
            reshape(logical_not(isnan(xCpGF)), nWindows, dot(nStrata, nBoot)), 2
        ) / sum(reshape(logical_not(isnan(xmt)), nWindows, dot(nStrata, nBoot)), 2)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:196
        mtByWindow = nanmean(reshape(xmt, nWindows, dot(nStrata, nBoot)), 2)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:197
        fcFigLoc(1, 0.5, 0.45, "NE")
        subplot("position", concat([0.08, 0.56, 0.6, 0.38]))
        hold("on")
        box("on")
        plot(mt, Cp, "r.", mt(iModeE), Cp(iModeE), "b.", mt(iModeD), Cp(iModeD), "g.")
        nBins = copy(nWindows)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:203
        if nModeD >= dot(nBins, 30):
            n, mx, my = fcBin(
                mt(iModeD), Cp(iModeD), [], round(nModeD / nBins), nargout=3
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:205
            hold("on")
            plot(mx, my, "ko-", "MarkerFaceColor", "y", "MarkerSize", 8, "LineWidth", 2)
        if nModeE >= dot(nBins, 30):
            n, mx, my = fcBin(
                mt(iModeE), Cp(iModeE), [], round(nModeE / nBins), nargout=3
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:209
            hold("on")
            plot(mx, my, "bo-", "MarkerFaceColor", "c", "MarkerSize", 8, "LineWidth", 2)
        fcDatetick(mt, "Mo", 4, 1)
        ylabel("Cp")
        ylabel("Raw Cp Modes D (green) E (red)")
        ylim(concat([0, prctile(Cp, 99.9)]))
        hold("off")
        title(
            sprintf(
                "%s  Stats%g  Mode%s  nSelect/nTry: %g/%g  uStarTh: %5.3f (%5.3f) ",
                cSiteYr,
                nPar,
                cMode,
                nSelect,
                nTry,
                nanmedian(Cp(iSelect)),
                dot(0.5, diff(prctile(Cp(iSelect), concat([2.5, 97.5])))),
            )
        )
        subplot("position", concat([0.08, 0.06, 0.6, 0.38]))
        hold("on")
        box("on")
        if "G" == cMode:
            c = "g"
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:220
        else:
            if "L" == cMode:
                c = "b"
            # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:220
            else:
                c = "k"
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:220
        plot(mt(iSelect), Cp(iSelect), c + ".", mtHat, CpHat, "r-", "LineWidth", 3)
        plot(tW, CpW, "ro", "MarkerFaceColor", "y", "MarkerSize", 9, "LineWidth", 2)
        fcDatetick(mt(iSelect), "Mo", 4, 1)
        ylabel("Select Cp")
        ylim(concat([0, prctile(Cp(iSelect), 99)]))
        title(sprintf("Cp = %5.3f + %5.3f sin(wt - %3.0f) (r^2 = %5.3f) ", bSine, r2))
        subplot("position", concat([0.76, 0.56, 0.22, 0.38]))
        hist(CpA, 30)
        grid("on")
        box("on")
        xlim(concat([min(CpA), max(CpA)]))
        xlabel("Annual \itu_*^{Th}")
        ylabel("Frequency")
        title(
            sprintf(
                "Median (CI): %5.3f (%5.3f) ",
                nanmedian(CpA),
                dot(0.5, diff(prctile(CpA, concat([2.5, 97.5])))),
            )
        )
        subplot("position", concat([0.76, 0.06, 0.22, 0.38]))
        plot(mtByWindow, FracSelectByWindow, "o-")
        fcDatetick(mtByWindow, "Mo", 4, 1)
        ylabel("FracSelectByWindow")
        ylim(concat([0, 1]))

    # =======================================================================
    # =======================================================================

    return (
        CpA,
        nA,
        tW,
        CpW,
        cMode,
        cFailure,
        fSelect,
        sSine,
        FracSig,
        FracModeD,
        FracSelect,
    )
