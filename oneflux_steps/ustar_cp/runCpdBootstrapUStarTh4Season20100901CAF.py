# Generated with SMOP  0.41-beta
from .libsmop import *

# ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m

# 	runCpdBootstrapUStarTh4Season20100901CAF

warning("off")
Sites8, Sites5ca = GetNACPCCPSites
# ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:5
DirsSub, Sites8, Sites5us = GetNACPAmerifluxSites
# ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:6
Sites = sort(concat([myrv(Sites5ca), myrv(Sites5us)]))
# ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:8
nSites = length(Sites)
# ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:9
nBoot = 1000
# ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:11
cnBoot = num2str(nBoot)
# ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:11
DirCp = concat(
    ["i:\\Ameriflux\\uStarThAnalysis20100901\\Annual\\Merged\\Boot", cnBoot, "\\"]
)
# ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:13
mkdir(DirCp)
DirJpg = concat([DirCp, "figures\\"])
# ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:14
mkdir(DirJpg)
DirMerged = "i:\\Ameriflux\\nacpL234.Merged\\"
# ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:15
disp(" ")
disp(" ")
# 	========================================================================
# 	========================================================================

for iSite in arange(1, nSites).reshape(-1):
    try:
        cSite = char(Sites(iSite))
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:26
        t = []
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:28
        Ta = []
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:28
        Ts = []
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:28
        Rsd = []
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:28
        PPFD = []
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:28
        Fc = []
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:28
        NEE = []
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:28
        uStar = []
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:28
        TaGF = []
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:29
        TsGF = []
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:29
        RsdGF = []
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:29
        eval(concat(["load ", DirMerged, cSite, "_Met&Flx;"]))
        eval(concat(["load ", DirMerged, cSite, "_NeeQC;"]))
        iFilt = 3
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:33
        NEE = NeeQC(arange(), iFilt + 1)
        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:33
        if logical_not(isempty(NEE)):
            T = (TaGF + TsGF) / 2
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:37
            nt = length(t)
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:39
            y, m, d = datevec(t, nargout=3)
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:39
            fNight = RsdGF < 5
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:40
            iNight = find(fNight)
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:40
            iDay = find(logical_not(fNight))
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:40
            iOut = find(uStar < logical_or(0, uStar) > 4)
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:41
            uStar[iOut] = NaN
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:41
            nPerDay = round(1 / nanmedian(diff(t)))
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:43
            nSeasonsN = 4
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:45
            nStrataN = 4
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:45
            nStrataX = 8
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:45
            nBins = 50
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:45
            nPerBin = 5
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:45
            if 24 == nPerDay:
                nPerBin = 3
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:47
            else:
                if 48 == nPerDay:
                    nPerBin = 5
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:48
            nPerSeasonN = dot(dot(nStrataN, nBins), nPerBin)
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:50
            ntN = dot(nSeasonsN, nPerSeasonN)
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:51
            itNee = find(logical_not(isnan(NEE + uStar + T + PPFD)))
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:53
            itNee = intersect(itNee, iNight)
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:54
            iYrs = myrv(unique(y))
            # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:56
            for iYr in iYrs.reshape(-1):
                it = find(y == iYr)
                # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:60
                jtNee = intersect(it, itNee)
                # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:60
                njtNee = length(jtNee)
                # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:60
                if njtNee >= ntN:
                    cYr = num2str(iYr)
                    # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:64
                    FileCp = concat(
                        [
                            DirCp,
                            "cpdBootstrap4Season20100901_Boot",
                            cnBoot,
                            "_",
                            cSite,
                            "-",
                            cYr,
                            "C.mat",
                        ]
                    )
                    # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:65
                    if exist(FileCp) == 2:
                        disp(" ")
                        disp(concat([cSite, "-", cYr, " was already processed."]))
                        disp(" ")
                    else:
                        Cp2, Stats2, Cp3, Stats3 = cpdBootstrapuStarTh4Season20100901(
                            t(it),
                            NEE(it),
                            uStar(it),
                            T(it),
                            fNight(it),
                            1,
                            concat([cSite, "-", cYr]),
                            nBoot,
                            nargout=4,
                        )
                        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:73
                        (
                            aCp2,
                            nCp2,
                            tW2,
                            CpW2,
                            cMode2,
                            cFailure2,
                            fSelect2,
                            sSine2,
                            FracSig2,
                            FracModeD2,
                            FracSelect2,
                        ) = cpdAssignUStarTh20100901(
                            Stats2, 1, concat([cSite, "-", cYr]), nargout=11
                        )
                        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:78
                        FileJpg2 = concat(
                            [
                                DirJpg,
                                "cpdBootstrap4Season20100901_Boot",
                                cnBoot,
                                "_",
                                cSite,
                                "-",
                                cYr,
                                "_Model2C",
                            ]
                        )
                        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:79
                        eval(concat(["print -djpeg100 ", FileJpg2, ";"]))
                        (
                            aCp3,
                            nCp3,
                            tW3,
                            CpW3,
                            cMode3,
                            cFailure3,
                            fSelect3,
                            sSine3,
                            FracSig3,
                            FracModeD3,
                            FracSelect3,
                        ) = cpdAssignUStarTh20100901(
                            Stats3, 1, concat([cSite, "-", cYr]), nargout=11
                        )
                        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:83
                        FileJpg3 = concat(
                            [
                                DirJpg,
                                "cpdBootstrap4Season20100901_Boot",
                                cnBoot,
                                "_",
                                cSite,
                                "-",
                                cYr,
                                "_Model3C",
                            ]
                        )
                        # ../ONEFlux/oneflux_steps/ustar_cp/runCpdBootstrapUStarTh4Season20100901CAF.m:84
                        eval(concat(["print -djpeg100 ", FileJpg3, ";"]))
                        eval(
                            concat(
                                [
                                    "save ",
                                    FileCp,
                                    " Cp2 Cp3 Stats2 Stats3 ",
                                    "aCp2 nCp2 tW2 CpW2 cMode2 cFailure2 fSelect2 sSine2 FracSig2 FracModeD2 FracSelect2 ",
                                    "aCp3 nCp3 tW3 CpW3 cMode3 cFailure3 fSelect3 sSine3 FracSig3 FracModeD3 FracSelect3;",
                                ]
                            )
                        )
        disp(" ")
        disp(" ")
    finally:
        pass
