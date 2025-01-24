# standard modules
# 3rd party modules
import numpy
# local modules
from fcNaniqr import fcnaniqr
from fcBin import cpdBin
from myprctile import myprctile

def cpdAssignUStarTh20100901(Stats, fPlot, cSiteYr):
    """
    cpdAssignUStarTh20100901
     aggregates and assigns uStarTh from the Stats* structured records
     as output by cpdBootstrapUStarTh20100901.

    Syntax:

    	[CpA,nA,tW,CpW,cMode,cFailure,fSelect,sSine,FracSig,FracModeD,FracSelect] ...
    = cpdExtractuStarTh20100901 (Stats,fPlot,cSiteYr)
    	where:
    	- Stats is a structured record output by
          cpdBootstrapuStarTh20100901, can be:
          - Stats2 (2-parameter operational change-point model) or
          - Stats3 (3-parameter diagnostic change-point model)
        - fPlot is a flag that is set to 1 for plotting the aggregation analysis
        - cSiteYr is text containing site and year for the fPlot plot

    - CpA is a scalar or vector of annual uStarTh (ChangePoint) means
    - nA is the number of selected change-points in the annual mean
    - CpW and tW are vectors showing seasonal variation in uStarTh
    - cMode is the dominant change-point mode:
      D Deficit (b1>0) or E Excess (b1<0)
    - cFailure is a string containing failure messages
    - fSelect is an array the same size as Stats* that flags the
      selected Cp values for computing CpA and CpW
    - sSine contains the coefficients of an annual sine curve
      fit to tW and CpW
    - FracSig,FracModeD,FracSelect are the fraction of attempted
      change-point detections that are significant, in mode D and
      select.

    The Stats2 or Stats3 records may be 2D (nWindows x nStrata)
    or 3D (nWindows x nStrata x nBoot). If 2D, then CpA
    is a scalar and CpW is averaged across the nStrata temperature strata.
    If 3D, then CpA is a vector of length nBoot and CpW is averaged
    across nBoot bootstraps and nStrata temperature strata.
    Stats input is accepted from both 4Season (nWindows=4)
    and flexible window (nWindows>=7) processing.

    The aggregation process is selective, selecting only:
    - significant change points (p <= 0.05)
    - in the dominant mode (Deficit (b1>0) or Excess (b1<0))
    - after excluding outliers (based on regression stats).
    No assignment is made if the detection failure rate
    is too high.
    Functions called:
     fcBin, fcDatetick, fcEqnAnnualSine, fcNaniqr, fcReadFields
     fcr2Calc, fcx2colvec, fcx2rowvec
    stats toolbox:
     nanmedian, nanmean, nlinfit, prctile

    Written 16 April 2010 by Alan Barr
    Translated to Python by PRI September 2019
    """
    CpA = []
    nA = []
    tW = []
    CpW = []
    fSelect = []
    cMode = ''
    cFailure = ''
    sSine = []
    FracSig = []
    FracModeD = []
    FracSelect = []
    # Compute window sizes etc.
    nBoot = len(Stats.keys())
    nWindows = len(Stats[0].keys())
    nStrata = len(Stats[0][0].keys())
    if nBoot == 1:
        nStrataN = 0.5
    else:
        if nBoot > 1:
            nStrataN = 1.0
        else:
            cFailure = "Stats must be 2D or 3D."
            return CpA, nA, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect
    nWindowsN = 4
    nSelectN = nWindowsN*nStrataN*nBoot
    CpA = numpy.full((nBoot), numpy.nan)
    nA = numpy.full((nBoot), numpy.nan)
    tW = numpy.full((nWindows), numpy.nan)
    CpW = numpy.full((nWindows), numpy.nan)
    # Extract variable arrays from Stats structure.
    # Reassign mt and Cp as x* to retain array shape,
    # then convert the extracted arrays to column vectors.
    mt = numpy.full((nStrata*nWindows*nBoot), numpy.nan)
    xmt = numpy.full((nWindows, nStrata, nBoot), numpy.nan)
    Cp = numpy.full((nStrata*nWindows*nBoot), numpy.nan)
    xCp = numpy.full((nWindows, nStrata, nBoot), numpy.nan)
    b1 = numpy.full((nStrata*nWindows*nBoot), numpy.nan)
    c2 = numpy.full((nStrata*nWindows*nBoot), numpy.nan)
    cib1 = numpy.full((nStrata*nWindows*nBoot), numpy.nan)
    cic2 = numpy.full((nStrata*nWindows*nBoot), numpy.nan)
    p = numpy.full((nStrata*nWindows*nBoot), numpy.nan)
    for boot in range(nBoot):
        for season in range(nWindows):
            for tclass in range(nStrata):
                xmt[season, tclass, boot] = Stats[boot][season][tclass]["mt"]
                xCp[season, tclass, boot] = Stats[boot][season][tclass]["Cp"]
                i = season + tclass*nWindows + boot*nWindows*nStrata
                mt[i] = Stats[boot][season][tclass]["mt"]
                Cp[i] = Stats[boot][season][tclass]["Cp"]
                b1[i] = Stats[boot][season][tclass]["b1"]
                c2[i] = Stats[boot][season][tclass]["c2"]
                cib1[i] = Stats[boot][season][tclass]["cib1"]
                cic2[i] = Stats[boot][season][tclass]["cic2"]
                p[i] = Stats[boot][season][tclass]["p"]
    pSig = 0.05
    fP = numpy.where((p <= pSig), 1, 0)
    # Determine if Stats input is from the operational 2-parameter
    # or diagnostic 3-parameter change-point model
    # and set c2 and cic2 to zero if 2-parameter
    nPar = 3
    if numpy.all(numpy.isnan(c2)):
        nPar = 2
        c2 = float(0)*b1
        cic2 = c2
    # Classify Cp regressions by slopes of b1 and c2 regression coeff:
    #  - NS: not sig, mfP=NaN, p>0.05
    #  - ModeE: atypical significant Cp (b1<c2)
    #  - ModeD: typical significant Cp (b1>=c2)
    iTry = numpy.where(~numpy.isnan(mt))[0]
    nTry = len(iTry)
    # trap nTry == 0
    if nTry == 0:
        #cFailure = "cpdAssignUStarTh: nTry is 0"
        return CpA, nA, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect
    iCp = numpy.where(~numpy.isnan(b1 + c2 + Cp))[0]
    nCp = len(iCp)
    iNS = numpy.where((fP == 0) & (~numpy.isnan(b1 + c2 + Cp)))[0]
    nNS = len(iNS)
    iSig = numpy.where((fP == 1) & (~numpy.isnan(b1 + c2 + Cp)))[0]
    nSig = len(iSig)
    # trap nSig == 0
    if nSig == 0:
        #cFailure = "cpdAssignUStarTh: nSig is 0"
        return CpA, nA, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect
    iModeE = numpy.where((fP == 1) & (b1 < c2))[0]
    nModeE = len(iModeE)
    iModeD = numpy.where((fP == 1) & (b1 >= c2))[0]
    nModeD = len(iModeD)
    # Evaluate and accept primary mode of significant Cps
    if nModeD >= nModeE:
        iSelect = iModeD
        cMode = "D"
    else:
        iSelect = iModeE
        cMode = "E"
    nSelect = len(iSelect)
    fSelect = numpy.zeros(len(fP))
    fSelect[iSelect] = 1
    # convert from number to boolean
    fSelect = fSelect.astype(bool)
    fModeD = numpy.full((len(fP)), numpy.nan)
    fModeD[iModeD] = 1
    fModeE = numpy.full((len(fP)), numpy.nan)
    fModeE[iModeE] = 1
    FracSig = float(nSig) / float(nTry)
    FracModeD = float(nModeD) / float(nSig)
    FracSelect = float(nSelect) / float(nTry)
    # Abort analysis if too few of the regressions produce significant Cps.
    if FracSelect < 0.1:
        cFailure = "Less than 10% successful detections. "
        return CpA, nA, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect
    # Exclude outliers from Select mode based on Cp and regression stats
    if nPar == 2:
        x = numpy.column_stack((Cp, b1, cib1))
        nx = 3
    else:
        if nPar == 3:
            x = numpy.column_stack((Cp, b1, c2, cib1, cic2))
            nx = 5
    mx = numpy.nanmedian(x, axis=0)
    sx = fcnaniqr(x)
    xNorm = x*numpy.nan
    # PRI - I believe the use of x[:, 0] is wrong and it should be x[:, i]
    for i in range(nx):
        xNorm[:, i] = (x[:, 0] - mx[i]) / sx[i]
    xNormX = numpy.nanmax(abs(xNorm), axis=1)
    ns = 5
    fOut = (xNormX > ns)
    iOut = numpy.where(fOut)[0]
    iSelect = numpy.setdiff1d(iSelect, iOut)
    nSelect = len(iSelect)
    fSelect = ~fOut & fSelect
    fModeD[iOut] = numpy.nan
    iModeD = numpy.where(fModeD == 1)[0]
    nModeD = len(iModeD)
    fModeE[iOut] = numpy.nan
    iModeE = numpy.where(fModeE == 1)[0]
    nModeE = len(iModeE)
    iSig = numpy.union1d(iModeD, iModeE)
    nSig = len(iSig)
    FracSig = float(nSig) / float(nTry)
    FracModeD = float(nModeD) / float(nSig)
    FracSelect = float(nSelect) / float(nTry)
    # PRI - the following check seems doomed to failure.  Given the way nSelect
    #       and nSelectN are calculated, we would always expect nSelect<nSelectN.
    #if nSelect<nSelectN; cFailure=sprintf('Too few selected change points: %g/%g',nSelect,nSelectN); return;  end;
    # PRI - however, if we change the definition of nStrata and nBoot at the start
    #       of this script to what I think is correct then the original check
    #       makes sense.  It will return if less than half of the windows give a
    #       change point value that passes all QC checks.
    #       So, having changed the definition of nStrata and nBoot, we will
    #       re-instate the check.
    # PRI - comment out this check for testing purposes only, to match current MATLAB
    #       code.
    #if nSelect < nSelectN:
        #cFailure = "Too few selected change points: " + str(int(nSelect)) + ", " + str(int(nSelectN))
        #print cFailure
        #return CpA, nA, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect
    # Aggregate the values to season and year.
    CpSelect = numpy.full((Cp.shape), numpy.nan)
    CpSelect[iSelect] = Cp[iSelect]
    xCpGF = numpy.reshape(CpSelect,(nWindows, nStrata, nBoot), order='F')
    if nBoot == 1:
        # PRI - needed to reverse order of nanmean/sum and fcx2colvec to get expected
        #       behaviour in Octave when nBoot=1
        # CpA=fcx2colvec(nanmean(xCpGF));
        # nA=fcx2colvec(sum(~isnan(xCpSelect)));
        CpA = numpy.nanmean(xCpGF)
        nA = numpy.sum(~numpy.isnan(xCpGF))
    else:
        # PRI - redundant, left in solely to be consistent with MATLAB code
        # PRI - no, not redundant, PRI is wiser now ...
        # CpA=fcx2colvec(nanmean(reshape(xCpGF,dot(nWindows,nStrata),nBoot)))
        # nA=fcx2colvec(sum(logical_not(isnan(reshape(xCpSelect,dot(nWindows,nStrata),nBoot)))))
        a = numpy.reshape(xCpGF, (nWindows*nStrata, nBoot), order='F')
        CpA = numpy.nanmean(a, axis=0)
        nA = numpy.sum(~numpy.isnan(a), axis=0)
    # Calculate mean tW and CpW for each window based on Select data only.
    # Because the bootstrap varies the number of windows among bootstraps,
    # base on the median number of windows and reshape sorted data.
    a = numpy.reshape(xmt, (nWindows, nStrata*nBoot), order='F')
    nW = numpy.nanmedian(numpy.sum(~numpy.isnan(a), axis=0))
    mtSelect = numpy.sort(mt[iSelect])
    i = numpy.argsort(mt[iSelect])
    CpSelect = Cp[iSelect[i]]
    iprctile = numpy.arange(0, 101, 100/nW)
    xBins = myprctile(mtSelect, iprctile)
    n, tW, CpW = cpdBin(mtSelect, CpSelect, xBins, 0)
    # This is the end of the translated code.
    # The following code to detect seasonal trends is not implemented.
    # Fit annual sine curve
    bSine = numpy.array([1, 1, 1])
    # PRI - unable to get the following code to run in Octave
    #[bSine] = nlinfit(mt(iSelect),Cp(iSelect),'fcEqnAnnualSine',bSine)
    #yHat = fcEqnAnnualSine(bSine, mt(iSelect))
    #r2 = fcr2Calc(Cp(iSelect),yHat)
    #mtHat=sort(mt(iSelect)); CpHat=fcEqnAnnualSine(bSine,mtHat);
    r2 = 1.0
    if bSine[1] < 0:
        bSine[1] = -1.0 * bSine[1]
        bSine[2] = bSine[2] + 365.25 / 2
    bSine[2] = numpy.mod(bSine[2], 365.25)
    sSine = numpy.append(bSine, r2)

## cpdAssignUStarTh20100901.m:200
    ##	=======================================================================
##	=======================================================================

    #if fPlot:
        #FracSelectByWindow=sum(reshape(logical_not(isnan(xCpGF)),nWindows,dot(nStrata,nBoot)),2) / sum(reshape(logical_not(isnan(xmt)),nWindows,dot(nStrata,nBoot)),2)
## cpdAssignUStarTh20100901.m:207
        #mtByWindow=nanmean(reshape(xmt,nWindows,dot(nStrata,nBoot)),2)
## cpdAssignUStarTh20100901.m:208
        #fcFigLoc(1,0.5,0.45,'NE')
        #subplot('position',concat([0.08,0.56,0.6,0.38]))
        #hold('on')
        #box('on')
        #plot(mt,Cp,'r.',mt(iModeE),Cp(iModeE),'b.',mt(iModeD),Cp(iModeD),'g.')
        #nBins=copy(nWindows)
## cpdAssignUStarTh20100901.m:214
        #if nModeD >= dot(nBins,30):
            #n,mx,my=fcBin(mt(iModeD),Cp(iModeD),[],round(nModeD / nBins),nargout=3)
## cpdAssignUStarTh20100901.m:216
            #hold('on')
            #plot(mx,my,'ko-','MarkerFaceColor','y','MarkerSize',8,'LineWidth',2)
        #if nModeE >= dot(nBins,30):
            #n,mx,my=fcBin(mt(iModeE),Cp(iModeE),[],round(nModeE / nBins),nargout=3)
## cpdAssignUStarTh20100901.m:220
            #hold('on')
            #plot(mx,my,'bo-','MarkerFaceColor','c','MarkerSize',8,'LineWidth',2)
        #fcDatetick(mt,'Mo',4,1)
        #ylabel('Cp')
        #ylabel('Raw Cp Modes D (green) E (red)')
        #ylim(concat([0,prctile(Cp,99.9)]))
        #hold('off')
        #title(sprintf('%s  Stats%g  Mode%s  nSelect/nTry: %g/%g  uStarTh: %5.3f (%5.3f) ',cSiteYr,nPar,cMode,nSelect,nTry,nanmedian(Cp(iSelect)),dot(0.5,diff(prctile(Cp(iSelect),concat([2.5,97.5]))))))
        #subplot('position',concat([0.08,0.06,0.6,0.38]))
        #hold('on')
        #box('on')
        #if 'G' == cMode:
            #c='g'
## cpdAssignUStarTh20100901.m:231
        #else:
            #if 'L' == cMode:
                #c='b'
## cpdAssignUStarTh20100901.m:231
            #else:
                #c='k'
## cpdAssignUStarTh20100901.m:231
        #plot(mt(iSelect),Cp(iSelect),concat([c,'.']),mtHat,CpHat,'r-','LineWidth',3)
        #plot(tW,CpW,'ro','MarkerFaceColor','y','MarkerSize',9.T,'LineWidth',2)
        #fcDatetick(mt(iSelect),'Mo',4,1)
        #ylabel('Select Cp')
        #ylim(concat([0,prctile(Cp(iSelect),99)]))
        #title(sprintf('Cp = %5.3f + %5.3f sin(wt - %3.0f) (r^2 = %5.3f) ',bSine,r2))
        #subplot('position',concat([0.76,0.56,0.22,0.38]))
        #hist(CpA,30)
        #grid('on')
        #box('on')
        #xlim(concat([min(CpA),max(CpA)]))
        #xlabel('Annual \\itu_*^{Th}')
        #ylabel('Frequency')
        #title(sprintf('Median (CI): %5.3f (%5.3f) ',nanmedian(CpA),dot(0.5,diff(prctile(CpA,concat([2.5,97.5]))))))
        #subplot('position',concat([0.76,0.06,0.22,0.38]))
        #plot(mtByWindow,FracSelectByWindow,'o-')
        #fcDatetick(mtByWindow,'Mo',4,1)
        #ylabel('FracSelectByWindow')
        #ylim(concat([0,1]))

    ##	=======================================================================
##	=======================================================================

    return CpA, nA, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect
