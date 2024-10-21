# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m


@function
def cpdFmax2pCp2(Fmax=None, n=None):
    # p = cpdFmax2pCp2(Fmax,n)

    # assigns the probability p that the 2-parameter,
    # operational change-point model fit is significant.

    # It interpolates within a Table pTable, generated
    # for the 2-parameter model by Alan Barr following Wang (2003).

    # If Fmax is outside the range in the table,
    # then the normal F stat is used to help extrapolate.

    # Functions called: stats toolbox - fcdf, finv

    # Written by Alan Barr April 2010

    # =======================================================================
    # =======================================================================

    p = copy(NaN)
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:21
    if logical_or(logical_or(isnan(Fmax), isnan(n)), n) < 10:
        return p

    pTable = concat([0.8, 0.9, 0.95, 0.99]).T
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:23
    np = length(pTable)
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:23
    nTable = concat([10, 15, 20, 30, 50, 70, 100, 150, 200, 300, 500, 700, 1000]).T
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:24

    FmaxTable = matlabarray(
        concat(
            [
                [3.9293, 6.2992, 9.1471, 18.2659],
                [3.7734, 5.6988, 7.877, 13.81],
                [3.7516, 5.5172, 7.4426, 12.6481],
                [3.7538, 5.3224, 7.0306, 11.4461],
                [3.7941, 5.303, 6.8758, 10.6635],
                [3.8548, 5.348, 6.8883, 10.5026],
                [3.9798, 5.4465, 6.9184, 10.4527],
                [4.0732, 5.5235, 6.9811, 10.3859],
                [4.1467, 5.6136, 7.0624, 10.5596],
                [4.277, 5.7391, 7.2005, 10.6871],
                [4.4169, 5.8733, 7.3421, 10.6751],
                [4.5556, 6.0591, 7.5627, 11.0072],
                [4.7356, 6.2738, 7.7834, 11.2319],
            ]
        )
    )
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:25
    FmaxCritical = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:40
    for ip in arange(1, np).reshape(-1):
        FmaxCritical[ip] = interp1(nTable, FmaxTable[arange(), ip], n, "pchip")
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:40

    if Fmax < FmaxCritical[1]:
        fAdj = dot(finv(0.9, 3, n), Fmax) / FmaxCritical[1]
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:42
        p = dot(2, (1 - fcdf(fAdj, 3, n)))
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:43
        if p > 1:
            p = 1
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:44
        return p

    if Fmax > FmaxCritical[end()]:
        fAdj = dot(finv(0.995, 3, n), Fmax) / FmaxCritical[3]
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:47
        p = dot(2, (1 - fcdf(fAdj, 3, n)))
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:48
        if p < 0:
            p = 0
        # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:49
        return p

    p = interp1(FmaxCritical, 1 - pTable, Fmax, "pchip")


# oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp2.m:51
