# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m


@function
def cpdFmax2pCp3(Fmax=None, n=None):
    # p = cpdFmax2pCp3(Fmax,n)

    # assigns the probability p that the 3-parameter,
    # diagnostic change-point model fit is significant.

    # It interpolates within a Table pTable, generated
    # for the 3-parameter model by Wang (2003).

    # If Fmax is outside the range in the table,
    # then the normal F stat is used to help extrapolate.

    # Functions called: stats toolbox - fcdf, finv

    # Written by Alan Barr April 2010

    # =======================================================================
    # =======================================================================

    p = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:21
    if logical_or(logical_or(isnan(Fmax), isnan(n)), n) < 10:
        return p

    pTable = concat([0.9, 0.95, 0.99]).T
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:23
    nTable = concat([arange(10, 100, 10), arange(150, 600, 50), 800, 1000, 2500]).T
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:24
    FmaxTable = matlabarray(
        concat(
            [
                [11.646, 15.559, 28.412],
                [9.651, 11.948, 18.043],
                [9.379, 11.396, 16.249],
                [9.261, 11.148, 15.75],
                [9.269, 11.068, 15.237],
                [9.296, 11.072, 15.252],
                [9.296, 11.059, 14.985],
                [9.341, 11.072, 15.013],
                [9.397, 11.08, 14.891],
                [9.398, 11.085, 14.874],
                [9.506, 11.127, 14.828],
                [9.694, 11.208, 14.898],
                [9.691, 11.31, 14.975],
                [9.79, 11.406, 14.998],
                [9.794, 11.392, 15.044],
                [9.84, 11.416, 14.98],
                [9.872, 11.474, 15.072],
                [9.929, 11.537, 15.115],
                [9.955, 11.552, 15.086],
                [9.995, 11.549, 15.164],
                [10.102, 11.673, 15.292],
                [10.169, 11.749, 15.154],
                [10.478, 12.064, 15.519],
            ]
        )
    )
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:25
    FmaxCritical = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:49
    for ip in arange(1, 3).reshape(-1):
        FmaxCritical[ip] = interp1(nTable, FmaxTable[arange(), ip], n, "pchip")
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:49

    if Fmax < FmaxCritical[1]:
        fAdj = dot(finv(0.95, 3, n), Fmax) / FmaxCritical[1]
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:51
        p = dot(2, (1 - fcdf(fAdj, 3, n)))
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:52
        if p > 1:
            p = 1
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:53
        return p

    if Fmax > FmaxCritical[3]:
        fAdj = dot(finv(0.995, 3, n), Fmax) / FmaxCritical[3]
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:56
        p = dot(2, (1 - fcdf(fAdj, 3, n)))
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:57
        if p < 0:
            p = 0
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:58
        return p

    p = interp1(FmaxCritical, 1 - pTable, Fmax, "pchip")


# oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3.m:60
