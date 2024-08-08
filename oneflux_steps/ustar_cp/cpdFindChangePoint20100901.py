# Generated with SMOP  0.41-beta
from .libsmop import *

# ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m


@function
def cpdFindChangePoint20100901(
    xx=None, yy=None, fPlot=None, cPlot=None, *args, **kwargs
):
    varargin = cpdFindChangePoint20100901.varargin
    nargin = cpdFindChangePoint20100901.nargin

    # cpdFindChangePoint20100901

    # is an operational version of the Lund and Reeves (2002)
    # change-point detection algorithm as modified and
    # implemented by Alan Barr for uStarTh evaluation.

    # Syntax:

    # [Cp2,s2,Cp3,s3] = cpdFindChangePoint20100901(uStar,NEE,fPlot,Txt)

    # - Cp2 changepoint (uStarTh) from operational 2-parameter model,
    # - Cp3 changepoint (uStarTh) from diagnostic 3-parameter model,
    # - s2 structured record containing statistics from Cp2 evaluation,
    # - s3 structured record containing statistics from Cp3 evaluation

    # - xx,yy variables for change-point detection
    # - fPlot flag set to 1 to plot
    # - cPlot text string for plot title

    # Note: The individual variables Cp2 and Cp3 are set to NaN if not significant
    # but the values s2.Cp and s3.Cp are retained even if not significant.

    # 	=======================================================================
    # 	=======================================================================

    # 	Functions called:
    # 	- cpdFmax2pCp2,cpdFmax2pCp3
    # 	from stats toolbox - regress

    # 	Written by Alan Barr, last updated 7 Oct 2010

    # 	=======================================================================
    # 	=======================================================================

    # 	Initialize outputs.

    Cp2 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:39
    Cp3 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:39
    s2 = []
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:41
    s2.n = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:41
    s2.Cp = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:41
    s2.Fmax = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:41
    s2.p = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:41
    s2.b0 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:42
    s2.b1 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:42
    s2.b2 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:42
    s2.c2 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:42
    s2.cib0 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:43
    s2.cib1 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:43
    s2.cic2 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:43
    s3 = copy(s2)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:44
    # 	=======================================================================
    # 	=======================================================================

    # 	Exclude missing data.

    x = reshape(xx, length(xx), 1)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:51
    y = reshape(yy, length(yy), 1)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:51
    iNaN = find(isnan(x + y))
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:52
    x[iNaN] = []
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:52
    y[iNaN] = []
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:52
    n = length(x + y)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:53
    if n < 10:
        return Cp2, s2, Cp3, s3

    # 	Exclude extreme lin reg outliers.

    a = numpy.linalg.solve(concat([ones(n, 1), x]), y)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:57
    yHat = a(1) + dot(a(2), x)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:57
    dy = y - yHat
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:58
    mdy = mean(dy)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:58
    sdy = std(dy)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:58
    ns = 4
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:59
    iOut = find(abs(dy - mdy) > dot(ns, sdy))
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:59
    x[iOut] = []
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:59
    y[iOut] = []
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:59
    n = length(x + y)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:61
    if n < 10:
        return Cp2, s2, Cp3, s3

    # 	Compute statistics of reduced (null hypothesis) models
    # 	for later testing of Cp2 and Cp3 significance.

    yHat2 = mean(y)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:66
    SSERed2 = sum((y - yHat2) ** 2)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:66
    a = numpy.linalg.solve(concat([ones(n, 1), x]), y)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:67
    yHat3 = a(1) + dot(a(2), x)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:67
    SSERed3 = sum((y - yHat3) ** 2)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:67
    nRed2 = 1
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:68
    nFull2 = 2
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:68
    nRed3 = 2
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:68
    nFull3 = 3
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:68
    # 	Compute F score (Fc2 and Fc3) for each data point
    # 	in order to identify Fmax.

    MT = dot(NaN, ones(n, 1))
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:73
    Fc2 = copy(MT)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:73
    Fc3 = copy(MT)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:73
    nEndPtsN = 3
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:75
    nEndPts = floor(dot(0.05, n))
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:75
    if nEndPts < nEndPtsN:
        nEndPts = copy(nEndPtsN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:76

    for i in arange(1, (n - 1)).reshape(-1):
        # fit operational 2 parameter model, with zero slope above Cp2:
        # 2 connected line segments, segment 2 has zero slope
        # parameters b0, b1 and xCp
        iAbv = arange((i + 1), n)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:84
        x1 = copy(x)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:85
        x1[iAbv] = x(i)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:85
        a2 = numpy.linalg.solve(concat([ones(n, 1), x1]), y)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:86
        yHat2 = a2(1) + dot(a2(2), x1)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:87
        SSEFull2 = sum((y - yHat2) ** 2)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:88
        Fc2[i] = (SSERed2 - SSEFull2) / (SSEFull2 / (n - nFull2))
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:89
        # 2 connected line segments with noslope constraints
        # parameters b0, b1, b2 and xCp
        zAbv = zeros(n, 1)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:95
        zAbv[iAbv] = 1
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:95
        x1 = copy(x)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:96
        x2 = multiply((x - x(i)), zAbv)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:96
        a3 = numpy.linalg.solve(concat([ones(n, 1), x1, x2]), y)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:97
        yHat3 = a3(1) + dot(a3(2), x1) + dot(a3(3), x2)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:98
        SSEFull3 = sum((y - yHat3) ** 2)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:99
        Fc3[i] = (SSERed3 - SSEFull3) / (SSEFull3 / (n - nFull3))
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:100

    # 	Assign changepoints from Fc2 and Fc3 maxima.
    # 	Calc stats and test for significance of Fmax scores.

    pSig = 0.05
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:107
    Fmax2, iCp2 = max(Fc2, nargout=2)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:109
    xCp2 = x(iCp2)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:109
    iAbv = arange((iCp2 + 1), n)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:110
    x1 = copy(x)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:110
    x1[iAbv] = xCp2
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:110
    a2, a2int = regress(y, concat([ones(n, 1), x1]), nargout=2)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:111
    yHat2 = a2(1) + dot(a2(2), x1)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:112
    p2 = cpdFmax2pCp2(Fmax2, n)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:113
    Cp2 = copy(xCp2)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:114
    if p2 > pSig:
        Cp2 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:114

    Fmax3, iCp3 = max(Fc3, nargout=2)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:116
    xCp3 = x(iCp3)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:116
    iAbv = arange((iCp3 + 1), n)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:117
    zAbv = zeros(n, 1)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:117
    zAbv[iAbv] = 1
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:117
    x1 = copy(x)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:118
    x2 = multiply((x - xCp3), zAbv)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:118
    a3, a3int = regress(y, concat([ones(n, 1), x1, x2]), nargout=2)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:119
    yHat3 = a3(1) + dot(a3(2), x1) + dot(a3(3), x2)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:120
    p3 = cpdFmax2pCp3(Fmax3, n)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:121
    Cp3 = copy(xCp3)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:122
    if p3 > pSig:
        Cp3 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:122

    # 	Assign values to s2, but only if not too close to end points.

    s2.n = copy(n)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:126
    s3.n = copy(n)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:126
    if iCp2 > logical_and((nEndPts), iCp2) < (n - nEndPts):
        b0 = a2(1)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:130
        cib0 = dot(0.5, diff(a2int(1, arange())))
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:130
        b1 = a2(2)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:131
        cib1 = dot(0.5, diff(a2int(2, arange())))
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:131
        s2.Cp = copy(Cp2)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:133
        s2.Fmax = copy(Fmax2)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:133
        s2.p = copy(p2)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:133
        s2.b0 = copy(b0)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:134
        s2.b1 = copy(b1)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:134
        s2.b2 = copy(NaN)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:134
        s2.c2 = copy(NaN)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:134
        s2.cib0 = copy(cib0)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:135
        s2.cib1 = copy(cib1)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:135
        s2.cic2 = copy(NaN)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:135

    if iCp3 > logical_and((nEndPts), iCp3) < (n - nEndPts):
        b0 = a3(1)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:141
        cib0 = dot(0.5, diff(a3int(1, arange())))
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:141
        b1 = a3(2)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:142
        cib1 = dot(0.5, diff(a3int(2, arange())))
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:142
        b2 = a3(3)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:143
        cic2 = dot(0.5, diff(a3int(3, arange())))
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:143
        c2 = a3(2) + a3(3)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:144
        s3.Cp = copy(xCp3)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:146
        s3.Fmax = copy(Fmax3)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:146
        s3.p = copy(p3)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:146
        s3.b0 = copy(b0)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:147
        s3.b1 = copy(b1)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:147
        s3.b2 = copy(b2)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:147
        s3.c2 = copy(c2)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:147
        s3.cib0 = copy(cib0)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:148
        s3.cib1 = copy(cib1)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:148
        s3.cic2 = copy(cic2)
    # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:148

    # 	=======================================================================
    # 	=======================================================================

    if fPlot == 1:
        cla
        hold("on")
        plot(x, y, "ko", "MarkerFaceColor", "k")
        plot(x, yHat2, "r-", "linewidth", 2)
        plot(x, yHat3, "g-", "linewidth", 2)
        plot(concat([xCp2, xCp2]), concat([min(y), max(y)]), "r-", "linewidth", 2)
        plot(concat([xCp3, xCp3]), concat([min(y), max(y)]), "g-", "linewidth", 2)
        hold("off")
        grid("on")
        box("on")
        if a2(2) > 0:
            cMode = "D"
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:165
        else:
            cMode = "E"
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:165
        title(sprintf("%s %5.3f %s", cPlot, Cp2, cMode))
        xX = dot(max(x), 1.02)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:168
        if xX > 0:
            xlim(concat([0, xX]))
        yN = min(y)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:169
        yX = max(y)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:169
        dy = yX - yN
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:169
        yN = yN - dot(0.02, dy)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:170
        yX = yX + dot(0.02, dy)
        # ../ONEFlux/oneflux_steps/ustar_cp/cpdFindChangePoint20100901.m:170
        if yN < yX:
            ylim(concat([yN, yX]))
        set(gca, "FontSize", 10)

    # 	=======================================================================


# 	=======================================================================
