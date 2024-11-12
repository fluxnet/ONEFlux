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
        exec_(cv + "=fcReadFields(Stats,'" + cv + "')", globals(), locals())
        if "mt" == cv:
            xmt = copy(mt)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:102
        else:
            if "Cp" == cv:
                xCp = copy(Cp)
            # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:103
            else:
                if "c2" == cv:
                    xc2 = copy(c2)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:104
        exec_(cv + "=fcx2colvec(" + cv + ");", globals(), locals())

    pSig = 0.05
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:109
    fP = p <= pSig
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:109
    # Determine if Stats input is from the operational 2-parameter
    # or diagnostic 3-parameter change-point model
    # and set c2 and cic2 to zero if 2-parameter

    nPar = 3
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:115
    if sum(logical_not(isnan(xc2))) == 0:
        nPar = 2
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:115
        xc2 = dot(0, b1)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:115
        cic2 = copy(xc2)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:115

    # Classify Cp regressions by slopes of b1 and c2 regression coeff:
    # - NS: not sig, mfP=NaN, p>0.05
    # - ModeE: atypical significant Cp (b1<c2)
    # - ModeD: typical significant Cp (b1>=c2)

    iTry = find(logical_not(isnan(mt)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:122
    nTry = length(iTry)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:122
    iCp = find(logical_not(isnan(b1 + xc2 + Cp)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:123
    nCp = length(iCp)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:123
    iNS = find(logical_and(fP == 0, logical_not(isnan(b1 + xc2 + Cp))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:124
    nNS = length(iNS)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:124
    iSig = find(logical_and(fP == 1, logical_not(isnan(b1 + xc2 + Cp))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:125
    nSig = length(iSig)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:125
    iModeE = find(logical_and(fP == 1, b1 < xc2))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:126
    nModeE = length(iModeE)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:126
    iModeD = find(logical_and(fP == 1, b1 >= xc2))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:127
    nModeD = length(iModeD)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:127
    # Evaluate and accept primary mode of significant Cps

    if nModeD >= nModeE:
        iSelect = copy(iModeD)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:131
        cMode = "D"
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:131
    else:
        iSelect = copy(iModeE)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:131
        cMode = "E"
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:131

    nSelect = length(iSelect)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:131
    fSelect = matlabarray(zeros(size(fP)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:132
    fSelect[iSelect] = 1
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:132
    fSelect = logical(fSelect)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:132
    fModeD = matlabarray(dot(NaN, ones(size(fP))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:133
    fModeD[iModeD] = 1
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:133
    fModeE = matlabarray(dot(NaN, ones(size(fP))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:134
    fModeE[iModeE] = 1
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:134
    FracSig = nSig / nTry
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:136
    FracModeD = nModeD / nSig
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:136
    FracSelect = nSelect / nTry
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:136
    # Abort analysis if too few of the regressions produce significant Cps.

    if FracSelect < 0.1:
        cFailure = "Less than 10% successful detections. "
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:140
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
        x = concat([Cp, b1, cib1])
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:145
        nx = 3
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:145
    else:
        if 3 == nPar:
            x = concat([Cp, b1, xc2, cib1, cic2])
            # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:146
            nx = 5
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:146

    mx = nanmedian(x)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:149
    sx = fcNaniqr(x)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:149
    xNorm = matlabarray(dot(NaN, x))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:150
    for i in arange(1, nx).reshape(-1):
        xNorm[:, i] = (x[:, 1] - take(mx, i)) / take(sx, i)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:150

    xNormX = max(abs(xNorm), matlabarray([]), 2)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:151
    ns = 5
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:152
    fOut = xNormX > ns
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:152
    iOut = find(fOut)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:152
    iSelect = setdiff(iSelect, iOut)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:153
    nSelect = length(iSelect)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:153
    fSelect = logical_and(logical_not(fOut), fSelect)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:154
    fModeD[iOut] = NaN
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:155
    iModeD = find(fModeD == 1)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:155
    nModeD = length(iModeD)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:155
    fModeE[iOut] = NaN
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:156
    iModeE = find(fModeE == 1)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:156
    nModeE = length(iModeE)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:156
    iSig = union(iModeD, iModeE)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:157
    nSig = length(iSig)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:157
    FracSig = nSig / nTry
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:159
    FracModeD = nModeD / nSig
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:159
    FracSelect = nSelect / nTry
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:159
    if nSelect < nSelectN:
        cFailure = sprintf("Too few selected change points: %g/%g", nSelect, nSelectN)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:161
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
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:165
    xCpSelect[iSelect] = xCp(iSelect)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:165
    xCpGF = copy(xCpSelect)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:165
    if 2 == nDim:
        CpA = fcx2colvec(nanmean(xCpGF))
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:167
        nA = fcx2colvec(sum(logical_not(isnan(xCpSelect))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:168
    else:
        if 3 == nDim:
            CpA = fcx2colvec(nanmean(reshape(xCpGF, dot(nWindows, nStrata), nBoot)))
            # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:169
            nA = fcx2colvec(
                sum(
                    logical_not(
                        isnan(reshape(xCpSelect, dot(nWindows, nStrata), nBoot))
                    )
                )
            )
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:170

    # Calculate mean tW and CpW for each window based on Select data only.
    # Because the bootstrap varies the number of windows among bootstraps,
    # base on the median number of windows and reshape sorted data.

    nW = nanmedian(sum(logical_not(isnan(reshape(xmt, nWindows, dot(nStrata, nBoot))))))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:177
    mtSelect, i = sort(mt(iSelect), nargout=2)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:178
    CpSelect = Cp(take(iSelect, i))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:178
    xBins = prctile(mtSelect, arange(0, 100, (100 / nW)))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:179
    n, tW, CpW = fcBin(mtSelect, CpSelect, xBins, 0, nargout=3)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:180
    # Fit annual sine curve

    bSine = concat([1, 1, 1])
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:184
    bSine = nlinfit(mt(iSelect), Cp(iSelect), "fcEqnAnnualSine", bSine)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:185
    yHat = fcEqnAnnualSine(bSine, mt(iSelect))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:186
    r2 = fcr2Calc(Cp(iSelect), yHat)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:186
    mtHat = sort(mt(iSelect))
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:187
    CpHat = fcEqnAnnualSine(bSine, mtHat)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:187
    if bSine[2] < 0:
        bSine[2] = -bSine[2]
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:189
        bSine[3] = bSine[3] + 365.25 / 2
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:189

    bSine[3] = mod(bSine[3], 365.25)
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:190
    sSine = concat([fcx2rowvec(bSine), r2])
    # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:191
    # =======================================================================
    # =======================================================================

    if fPlot:
        FracSelectByWindow = sum(
            reshape(logical_not(isnan(xCpGF)), nWindows, dot(nStrata, nBoot)), 2
        ) / sum(reshape(logical_not(isnan(xmt)), nWindows, dot(nStrata, nBoot)), 2)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:198
        mtByWindow = nanmean(reshape(xmt, nWindows, dot(nStrata, nBoot)), 2)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:199
        fcFigLoc(1, 0.5, 0.45, "NE")
        subplot("position", concat([0.08, 0.56, 0.6, 0.38]))
        hold("on")
        box("on")
        plot(mt, Cp, "r.", mt(iModeE), Cp(iModeE), "b.", mt(iModeD), Cp(iModeD), "g.")
        nBins = copy(nWindows)
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:205
        if nModeD >= dot(nBins, 30):
            n, mx, my = fcBin(
                mt(iModeD),
                Cp(iModeD),
                matlabarray([]),
                round(nModeD / nBins),
                nargout=3,
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:207
            hold("on")
            plot(mx, my, "ko-", "MarkerFaceColor", "y", "MarkerSize", 8, "LineWidth", 2)
        if nModeE >= dot(nBins, 30):
            n, mx, my = fcBin(
                mt(iModeE),
                Cp(iModeE),
                matlabarray([]),
                round(nModeE / nBins),
                nargout=3,
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:211
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
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:222
        else:
            if "L" == cMode:
                c = "b"
            # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:222
            else:
                c = "k"
        # oneflux_steps/ustar_cp_refactor_wip/cpdAssignUStarTh20100901.m:222
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
