# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m


@function
def myDateTick(t=None, sFrequency=None, iDateStr=None, fLimits=None):
    y, m, d, h, mn, s = mydatevec(t, nargout=6)
    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:3
    iYrs = unique(y)
    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:4
    iSerMos = dot((y - 1), 12) + m
    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:5
    iSerMo1 = min(iSerMos)
    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:6
    iSerMo2 = max(iSerMos)
    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:6
    nSerMos = iSerMo2 - iSerMo1 + 1
    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:7
    xDates = matlabarray([])
    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:9
    if "Dy" == sFrequency:
        xDates = t[arange(1, end(), 48)]
    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:12
    else:
        if "2Dy" == sFrequency:
            iYr1 = floor(iSerMo1 / 12) + 1
            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:14
            iMo1 = mod(iSerMo1, 12)
            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:14
            if iMo1 == 0:
                iMo1 = 12
                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:14
                iYr1 = iYr1 - 1
            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:14
            for iDy in arange(1, 29, 2).reshape(-1):
                xDates = matlabarray(
                    concat([xDates, datenum(iYr1, arange(iMo1, (iMo1 + nSerMos)), iDy)])
                )
        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:15
        else:
            if "3Dy" == sFrequency:
                iYr1 = floor(iSerMo1 / 12) + 1
                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:17
                iMo1 = mod(iSerMo1, 12)
                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:17
                if iMo1 == 0:
                    iMo1 = 12
                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:17
                    iYr1 = iYr1 - 1
                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:17
                for iDy in arange(1, 28, 3).reshape(-1):
                    xDates = matlabarray(
                        concat(
                            [xDates, datenum(iYr1, arange(iMo1, (iMo1 + nSerMos)), iDy)]
                        )
                    )
            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:18
            else:
                if "5Dy" == sFrequency:
                    iYr1 = floor(iSerMo1 / 12) + 1
                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:20
                    iMo1 = mod(iSerMo1, 12)
                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:20
                    if iMo1 == 0:
                        iMo1 = 12
                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:20
                        iYr1 = iYr1 - 1
                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:20
                    for iDy in arange(1, 26, 5).reshape(-1):
                        xDates = matlabarray(
                            concat(
                                [
                                    xDates,
                                    datenum(iYr1, arange(iMo1, (iMo1 + nSerMos)), iDy),
                                ]
                            )
                        )
                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:21
                else:
                    if "7Dy" == sFrequency:
                        iYr1 = floor(iSerMo1 / 12) + 1
                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:23
                        iMo1 = mod(iSerMo1, 12)
                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:23
                        if iMo1 == 0:
                            iMo1 = 12
                            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:23
                            iYr1 = iYr1 - 1
                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:23
                        for iDy in arange(1, 22, 7).reshape(-1):
                            xDates = matlabarray(
                                concat(
                                    [
                                        xDates,
                                        datenum(
                                            iYr1, arange(iMo1, (iMo1 + nSerMos)), iDy
                                        ),
                                    ]
                                )
                            )
                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:24
                    else:
                        if "10Dy" == sFrequency:
                            iYr1 = floor(iSerMo1 / 12) + 1
                            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:26
                            iMo1 = mod(iSerMo1, 12)
                            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:26
                            if iMo1 == 0:
                                iMo1 = 12
                                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:26
                                iYr1 = iYr1 - 1
                            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:26
                            for iDy in arange(1, 21, 10).reshape(-1):
                                xDates = matlabarray(
                                    concat(
                                        [
                                            xDates,
                                            datenum(
                                                iYr1,
                                                arange(iMo1, (iMo1 + nSerMos)),
                                                iDy,
                                            ),
                                        ]
                                    )
                                )
                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:27
                        else:
                            if "14Dy" == sFrequency:
                                iYr1 = floor(iSerMo1 / 12) + 1
                                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:29
                                iMo1 = mod(iSerMo1, 12)
                                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:29
                                if iMo1 == 0:
                                    iMo1 = 12
                                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:29
                                    iYr1 = iYr1 - 1
                                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:29
                                for iDy in arange(1, 15, 14).reshape(-1):
                                    xDates = matlabarray(
                                        concat(
                                            [
                                                xDates,
                                                datenum(
                                                    iYr1,
                                                    arange(iMo1, (iMo1 + nSerMos)),
                                                    iDy,
                                                ),
                                            ]
                                        )
                                    )
                            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:30
                            else:
                                if "15Dy" == sFrequency:
                                    iYr1 = floor(iSerMo1 / 12) + 1
                                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:32
                                    iMo1 = mod(iSerMo1, 12)
                                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:32
                                    if iMo1 == 0:
                                        iMo1 = 12
                                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:32
                                        iYr1 = iYr1 - 1
                                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:32
                                    for iDy in arange(1, 16, 15).reshape(-1):
                                        xDates = matlabarray(
                                            concat(
                                                [
                                                    xDates,
                                                    datenum(
                                                        iYr1,
                                                        arange(iMo1, (iMo1 + nSerMos)),
                                                        iDy,
                                                    ),
                                                ]
                                            )
                                        )
                                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:33
                                else:
                                    if "Mo" == sFrequency:
                                        iYr1 = floor(iSerMo1 / 12) + 1
                                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:35
                                        iMo1 = mod(iSerMo1, 12)
                                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:35
                                        if iMo1 == 0:
                                            iMo1 = 12
                                            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:35
                                            iYr1 = iYr1 - 1
                                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:35
                                        xDates = datenum(
                                            iYr1, arange(iMo1, (iMo1 + nSerMos)), 1
                                        )
                                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:36
                                    # # # 			datestr(xDates)
                                    # # # 			datestr([min(t) max(t)])
                                    # # # 			pause;
                                    else:
                                        if "2Mo" == sFrequency:
                                            iYr1 = floor(iSerMo1 / 12) + 1
                                            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:41
                                            iMo1 = mod(iSerMo1, 12)
                                            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:41
                                            if iMo1 == 0:
                                                iMo1 = 12
                                                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:41
                                                iYr1 = iYr1 - 1
                                            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:41
                                            xDates = datenum(
                                                iYr1,
                                                arange(iMo1, (iMo1 + nSerMos), 2),
                                                1,
                                            )
                                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:42
                                        else:
                                            if "3Mo" == sFrequency:
                                                iYr1 = floor(iSerMo1 / 12) + 1
                                                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:44
                                                iMo1 = mod(iSerMo1, 12)
                                                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:44
                                                if iMo1 == 0:
                                                    iMo1 = 12
                                                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:44
                                                    iYr1 = iYr1 - 1
                                                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:44
                                                xDates = datenum(
                                                    iYr1,
                                                    arange(iMo1, (iMo1 + nSerMos), 3),
                                                    1,
                                                )
                                            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:45
                                            else:
                                                if "4Mo" == sFrequency:
                                                    iYr1 = floor(iSerMo1 / 12) + 1
                                                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:47
                                                    iMo1 = mod(iSerMo1, 12)
                                                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:47
                                                    if iMo1 == 0:
                                                        iMo1 = 12
                                                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:47
                                                        iYr1 = iYr1 - 1
                                                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:47
                                                    xDates = datenum(
                                                        iYr1,
                                                        arange(
                                                            iMo1, (iMo1 + nSerMos), 4
                                                        ),
                                                        1,
                                                    )
                                                # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:48
                                                else:
                                                    if "6Mo" == sFrequency:
                                                        iYr1 = floor(iSerMo1 / 12) + 1
                                                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:50
                                                        iMo1 = mod(iSerMo1, 12)
                                                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:50
                                                        if iMo1 == 0:
                                                            iMo1 = 12
                                                            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:50
                                                            iYr1 = iYr1 - 1
                                                        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:50
                                                        xDates = datenum(
                                                            iYr1,
                                                            arange(
                                                                iMo1,
                                                                (iMo1 + nSerMos),
                                                                6,
                                                            ),
                                                            1,
                                                        )
                                                    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:51
                                                    else:
                                                        if "Yr" == sFrequency:
                                                            iYr1 = min(iYrs)
                                                            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:53
                                                            iYr2 = max(iYrs)
                                                            # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:53
                                                            xDates = datenum(
                                                                arange(iYr1, iYr2 + 1),
                                                                1,
                                                                1,
                                                            )
    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:54

    xDates = unique(xDates)
    # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:56
    set(gca, "xTick", xDates)
    set(gca, "xTickLabel", [])
    if iDateStr > 0:
        cDates = datestr(xDates, iDateStr)
        # oneflux_steps/ustar_cp_refactor_wip/fcDatetick.m:59
        set(gca, "xTickLabel", cDates)

    if fLimits == 1:
        xlim(concat([floor(min(xDates)), ceil(max(xDates))]))
        grid("on")
        box("on")
