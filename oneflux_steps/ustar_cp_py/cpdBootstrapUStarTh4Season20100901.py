# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m


@function
def cpdBootstrapUStarTh4Season20100901(
    t=None,
    NEE=None,
    uStar=None,
    T=None,
    fNight=None,
    fPlot=None,
    cSiteYr=None,
    nBoot=None,
    varargin=None,
    *args,
    **kwargs,
):
    varargin = cpdBootstrapUStarTh4Season20100901.varargin
    nargin = cpdBootstrapUStarTh4Season20100901.nargin

    # cpdBootstrapUStarTh4Season20100901

    # is a simplified operational version of

    # 20100901 changes 3A 4I to 2A 3I as sggested by Xiaolan Wang.

    # 20100408 replaces 20100318, updating ChPt function from:
    # FindChangePointMod3LundReeves2002_20100318 to
    # FindChangePointMod2A4ILundReeves2002_20100408.
    # which: adds back A model, makes a correction to the significance test,
    # and adds a comparison of the 4- versus 3-parameter models.
    # and adds a comparison of the 4- versus 3-parameter models.

    # 20100318 new version with small tweaks to FindChangePoint
    # also adds mT and ciT to Stats structures.

    # is a new working implementation of Alan's u*Th evaluation algorithm
    # based on Lund and Reeves' (2002) modified by Wang's (2003) change-point
    # detection algorithm.

    # Relationship to other programs:

    # Called by batchNewNacpEstimateUStarTh_Moving_Mod3LundChPt_20100115
    # - script which identifies which sites to process
    # Calls newNacpEvaluateUStarTh_MovingStrat_20100114
    # - function that processes an individual year of data, using
    # FindChangePointMod3LundReeves2002_20091204
    #
    # This implementation may supplant all previous versions.

    # It uses moving windows of fixed size to evaluate seasonal variation.

    # Three combinations of stratification and pooling are implemented.
    # - All begin with 2D (time x temperature) stratification
    # (moving-window time x n temperature classes within each window).
    # - Two (W and A) add normalization and pooling.

    # 1. Method S (full stratification)
    # estimates the change-points for each of the strata
    # (nWindows x nTClasses) with no need for normalization.
    # 2. Method W (pooling within time windows)
    # begins with a variant of S but pools the temperature classes
    # within each time window before estimating one change-point per window.
    # Before pooling, the binned mean NEE data within each temperature class
    # are normalized against the 80th NEE percentile for that class.
    # 3. Method A (pooling to annual)
    # further pools the pooled normalized data from W over all time windows
    # before estimating a single change-point per year.
    #
    # The detailed analysis parameters are output in a Stats structured
    # record.

    # ========================================================================
    # ========================================================================

    # Functions called:

    # cpdEvaluateUStarTh20100901
    # fcx2roevec
    # stats toolbox:  nanmedian

    # Written by Alan Barr 15 Jan 2010.

    # ========================================================================
    # ========================================================================

    # Define constants
    nSeasons = 4
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:69
    nStrataX = 8
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:70

    nt = length(t)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:73
    iNight = get_iNight(fNight)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:75
    updated_uStar = update_uStar(uStar)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:77
    ntN = get_ntN(t, nSeasons)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:79

    itNee = get_itNee(NEE, uStar, T, iNight)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:82
    ntNee = length(itNee)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:83
    Cp2 = setup_Cp(nSeasons, nStrataX, nBoot)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:85
    Cp3 = setup_Cp(nSeasons, nStrataX, nBoot)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:86
    Stats2 = setup_Stats(nBoot, nSeasons, nStrataX)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:88
    Stats3 = setup_Stats(nBoot, nSeasons, nStrataX)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:89

    # disp(' ');
    # fprintf('cpdBootstrapUStarTh4Season20100901  #s   nObs: #g #g #g #g \n',cSiteYr,nt,sum(~isnan([NEE uStar T])));
    # disp(' ');

    if ntNee >= ntN:
        for iBoot in arange(1, nBoot).reshape(-1):
            it = generate_rand_int_array(nt)
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:105
            if iBoot > 1:
                fPlot = 0
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:108
            xCp2, xStats2, xCp3, xStats3 = cpdEvaluateUStarTh4Season20100901(
                t[it],
                NEE[it],
                updated_uStar[it],
                T[it],
                fNight[it],
                fPlot,
                cSiteYr,
                nargout=4,
            )
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:110
            # by alessio
            # fprintf('Bootstrap uStarTh #s:  #g/#g   nObs #g  Cp2 #4.3f  Cp3 #4.3f   #3.1fs \n', ...
            # cSiteYr,iBoot,nBoot,ntNee,nanmedian(fcx2rowvec(xCp2)),nanmedian(fcx2rowvec(xCp3)),dt);
            Cp2[arange(), arange(), iBoot] = xCp2
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:119
            Stats2[arange(), arange(), iBoot] = xStats2
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:119
            Cp3[arange(), arange(), iBoot] = xCp3
            # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:120
            Stats3[arange(), arange(), iBoot] = xStats3
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:120

    if size(varargin) > 0:
        Stats2 = jsonencode(Stats2)
        # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:127
        Stats3 = jsonencode(Stats3)
    # oneflux_steps/ustar_cp_refactor_wip/cpdBootstrapUStarTh4Season20100901.m:128

    return Cp2, Stats2, Cp3, Stats3


if __name__ == "__main__":
    pass
