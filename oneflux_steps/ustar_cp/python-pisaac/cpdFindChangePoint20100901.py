# standard modules
# 3rd party modules
import numpy
import scipy.stats
import statsmodels.api as sm
# local modules
from cpdFmax2pCp2 import *
from cpdFmax2pCp3 import *

def cpdFindChangePoint20100901(xx, yy, iSeason, iStrata):
    """
    cpdFindChangePoint20100901

    is an operational version of the Lund and Reeves (2002)
    change-point detection algorithm as modified and
    implemented by Alan Barr for uStarTh evaluation.

    Syntax:
     [Cp2,s2,Cp3,s3] = cpdFindChangePoint20100901(uStar,NEE,fPlot,Txt)
      - Cp2 changepoint (uStarTh) from operational 2-parameter model,
      - Cp3 changepoint (uStarTh) from diagnostic 3-parameter model,
      - s2 structured record containing statistics from Cp2 evaluation,
      - s3 structured record containing statistics from Cp3 evaluation
      - xx,yy variables for change-point detection
      - fPlot flag set to 1 to plot
      - cPlot text string for plot title
    Note: The individual variables Cp2 and Cp3 are set to NaN if not significant
          but the values s2.Cp and s3.Cp are retained even if not significant.
    Functions called:
     - cpdFmax2pCp2,cpdFmax2pCp3
    from stats toolbox - regress
    Written by Alan Barr, last updated 7 Oct 2010
    Translated to Python by PRI, September 2019
    """
    # Initialize outputs.
    Cp2 = numpy.nan
    Cp3 = numpy.nan
    # s2 and s3 as dictionaries
    s2 = {}
    s3 = {}
    for item in ["n", "Cp", "Fmax", "p", "b0", "b1", "b2", "c2", "cib0", "cib1", "cic2"]:
        s2[item] = numpy.nan
        s3[item] = numpy.nan
    # Copy inputs
    x = numpy.array(xx)
    y = numpy.array(yy)
    # Exclude missing data (nan)
    x = x[~numpy.isnan(xx) & ~numpy.isnan(yy)]
    y = y[~numpy.isnan(xx) & ~numpy.isnan(yy)]
    # number of points left
    n = len(x)
    # return if less than 10 points
    if n < 10:
        return Cp2, s2, Cp3, s3
    # Exclude extreme outliers.
    # scipy.stats.linregress is 6 times faster than numpy.polyval!
    a = scipy.stats.linregress(x, y)
    yHat = a[1] + a[0]*x
    dy = y - yHat
    mdy = numpy.mean(dy)
    sdy = numpy.std(dy, ddof=1)
    ns = 4
    x = x[numpy.abs(dy - mdy) <= ns*sdy]
    y = y[numpy.abs(dy - mdy) <= ns*sdy]
    n = len(x)
    if n < 10:
        return Cp2, s2, Cp3, s3
    # Compute statistics of reduced (null hypothesis) models
    # for later testing of Cp2 and Cp3 significance.
    yHat2 = numpy.mean(y)
    SSERed2 = numpy.sum((y - yHat2) ** 2)
    a = scipy.stats.linregress(x, y)
    yHat3 = a[1] + a[0]*x
    SSERed3 = numpy.sum((y - yHat3) ** 2)
    nFull2 = 2
    nFull3 = 3
    # Compute F score (Fc2 and Fc3) for each data point in order to identify Fmax.
    Fc2 = numpy.full(n, numpy.nan)
    Fc3 = numpy.full(n, numpy.nan)
    nEndPtsN = 3
    nEndPts = numpy.floor(0.05*n)
    if nEndPts < nEndPtsN:
        nEndPts = nEndPtsN
    for i in numpy.arange(0, n-1):
        # fit operational 2 parameter model, with zero slope above Cp2:
        # 2 connected line segments, segment 2 has zero slope
        # parameters b0, b1 and xCp
        iAbv = numpy.arange(i, n)
        x1 = numpy.array(x)
        x1[iAbv] = x[i]
        x1a = numpy.column_stack((numpy.ones(len(x1)), x1))
        # we use numpy.linalg.lstsq to duplicate the matrix left divide
        # used in the original MATLAB code.
        a2 = numpy.linalg.lstsq(x1a, y, rcond=None)[0]
        yHat2 = a2[0] + a2[1]*x1
        SSEFull2 = numpy.sum((y - yHat2) ** 2)
        Fc2[i] = (SSERed2 - SSEFull2) / (SSEFull2 / (n - nFull2))
        # 2 connected line segments with noslope constraints
        # parameters b0, b1, b2 and xCp
        zAbv = numpy.zeros(n)
        zAbv[iAbv] = 1
        x1 = numpy.array(x)
        x2 = numpy.multiply((x - x[i]), zAbv)
        X = numpy.column_stack((numpy.ones(len(x1)), x1, x2))
        # we use numpy.linalg.lstsq to duplicate the matrix left divide
        # used in the original MATLAB code.
        a3 = numpy.linalg.lstsq(X, y, rcond=None)[0]
        yHat3 = a3[0] + a3[1]*x1 + a3[2]*x2
        SSEFull3 = numpy.sum((y - yHat3) ** 2)
        Fc3[i] = (SSERed3 - SSEFull3) / (SSEFull3 / (n - nFull3))
    # Assign changepoints from Fc2 and Fc3 maxima.
    # Calc stats and test for significance of Fmax scores.
    pSig = 0.05
    # 2 parameter model
    iCp2 = numpy.argmax(Fc2[~numpy.isnan(Fc2)])
    Fmax2 = Fc2[iCp2]
    xCp2 = x[iCp2]
    iAbv = numpy.arange((iCp2 + 1), n)
    x1 = numpy.array(x)
    x1[iAbv] = xCp2
    # if OLS can't find a solution, a2.params only has 1 element not 2
    # this is trapped below
    a2 = sm.OLS(y, sm.add_constant(x1)).fit()
    p2 = cpdFmax2pCp2(Fmax2, n)
    Cp2 = xCp2
    if p2 > pSig:
        Cp2 = numpy.nan
    # 3 parameter model
    iCp3 = numpy.argmax(Fc3[~numpy.isnan(Fc3)])
    Fmax3 = Fc3[iCp3]
    xCp3 = x[iCp3]
    iAbv = numpy.arange((iCp3 + 1), n)
    zAbv = numpy.zeros(n)
    zAbv[iAbv] = 1
    x1 = numpy.array(x)
    x2 = numpy.multiply((x - xCp3), zAbv)
    X = numpy.column_stack((numpy.ones(len(x1)), x1, x2))
    # if OLS can't find a solution, a3.params only has 1 element not 3
    # this is trapped below
    a3 = sm.OLS(y, X).fit()
    p3 = cpdFmax2pCp3(Fmax3, n)
    Cp3 = xCp3
    if p3 > pSig:
        Cp3 = numpy.nan
    # Assign values to s2, but only if not too close to end points.
    s2["n"] = n
    s3["n"] = n
    if (iCp2 > nEndPts - 1) and (iCp2 < (n - nEndPts - 1)):
        if len(a2.params) == 2:
            s2["Cp"] = Cp2
            s2["Fmax"] = Fmax2
            s2["p"] = p2
            s2["b0"] = a2.params[0]
            s2["b1"] = a2.params[1]
            s2["cib0"] = 0.5*(a2.conf_int(pSig)[0, 1] - a2.conf_int(pSig)[0, 0])
            s2["cib1"] = 0.5*(a2.conf_int(pSig)[1, 1] - a2.conf_int(pSig)[1, 0])
    if (iCp3 > nEndPts - 1) and (iCp3 < (n - nEndPts - 1)):
        if len(a3.params) == 3:
            s3["Cp"] = xCp3
            s3["Fmax"] = Fmax3
            s3["p"] = p3
            s3["b0"] = a3.params[0]
            s3["b1"] = a3.params[1]
            s3["b2"] = a3.params[2]
            s3["c2"] = a3.params[1] + a3.params[2]
            s3["cib0"] = 0.5*(a3.conf_int(pSig)[0, 1] - a3.conf_int(pSig)[0, 0])
            s3["cib1"] = 0.5*(a3.conf_int(pSig)[1, 1] - a3.conf_int(pSig)[1, 0])
            s3["cic2"] = 0.5*(a3.conf_int(pSig)[2, 1] - a3.conf_int(pSig)[2, 0])

    return Cp2, s2, Cp3, s3
