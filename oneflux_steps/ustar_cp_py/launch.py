# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/launch.m

# launch

# Example of data input for Alan Barr's uStarTh programs.
# The data are input from a MatLab L3 file that Dario sent me
# a couple of years ago.

# load and assign data


@function
def launch(input_folder=None, output_folder=None):
    globals().update(load_all_vars())

    exitcode = 0
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:10
    warning("off")
    # check input path
    if 0 == exist(input_folder):
        input_folder = pwd + "/"
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:15
    else:
        if length(input_folder) < 2:
            if take(input_folder, 2) != ":":
                input_folder = pwd + "/" + input_folder
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:18

    if (
        take(input_folder, length(input_folder)) != "\\"
        and take(input_folder, length(input_folder)) != "/"
    ):
        input_folder = input_folder + "/"
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:22

    # check output path
    if 0 == exist(output_folder):
        output_folder = pwd + "/"
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:27
    else:
        if length(output_folder) < 2:
            if take(output_folder, 2) != ":":
                output_folder = pwd + "/" + output_folder
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:30

    if (
        take(output_folder, length(output_folder)) != "\\"
        and take(output_folder, length(output_folder)) != "/"
    ):
        output_folder = output_folder + "/"
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:34

    mkdir(output_folder)
    # by alessio
    USTAR_INDEX = 1
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:39
    NEE_INDEX = 2
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:40
    TA_INDEX = 3
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:41
    PPFD_INDEX = 4
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:42
    RG_INDEX = 5
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:43
    input_columns_names = cellarray(["USTAR", "NEE", "TA", "PPFD_IN", "SW_IN"])
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:44
    # by alessio
    fprintf(
        "\n\nUstar Threshold Computation by Alan Barr\n\ninput in %s\noutput in %s\n\n",
        input_folder,
        output_folder,
    )
    d = dir(input_folder + "*_qca_ustar_*.csv")
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:48
    error_str = cellarray([])
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:49
    # by alessio
    fprintf("%d files founded.\n\n", numel(d))
    for n in arange(1, numel(d)).reshape(-1):
        # by alessio
        fprintf("processing n.%02d, %s...", n, take(d, n).name)
        fid = fopen(matlabarray([input_folder, take(d, n).name]), "r")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:59
        if -1 == fid:
            fprintf("unable to open file\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:62
            continue
        dataset = textscan(fid, "%[^\n]")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:66
        dataset = take(dataset, 1)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:67
        r = strncmpi(take(dataset, 1), "site", 4)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:70
        if 0 == r:
            fprintf("site keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:73
            continue
        site = take(dataset, 1)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:76
        site = strrep(site, "site,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:77
        r = strncmpi(take(dataset, 2), "year", 4)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:80
        if 0 == r:
            fprintf("year keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:83
            continue
        year = take(dataset, 2)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:86
        year = strrep(year, "year,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:87
        r = strncmpi(take(dataset, 3), "lat", 3)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:90
        if 0 == r:
            fprintf("lat keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:93
            continue
        lat = take(dataset, 3)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:96
        lat = strrep(lat, "lat,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:97
        r = strncmpi(take(dataset, 4), "lon", 3)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:100
        if 0 == r:
            fprintf("lon keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:103
            continue
        lon = take(dataset, 4)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:106
        lon = strrep(lon, "lon,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:107
        r = strncmpi(take(dataset, 5), "timezone", 8)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:110
        if 0 == r:
            fprintf("timezone keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:113
            continue
        timezone = take(dataset, 5)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:116
        timezone = strrep(timezone, "timezone,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:117
        r = strncmpi(take(dataset, 6), "htower", 6)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:120
        if 0 == r:
            fprintf("htower keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:123
            continue
        htower = take(dataset, 6)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:126
        htower = strrep(htower, "htower,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:127
        r = strncmpi(take(dataset, 7), "timeres", 7)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:130
        if 0 == r:
            fprintf("timeres keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:133
            continue
        timeres = take(dataset, 7)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:136
        timeres = strrep(timeres, "timeres,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:137
        r = strncmpi(take(dataset, 8), "Sc_negl", 7)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:140
        if 0 == r:
            fprintf("sc_negl keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:143
            continue
        sc_negl = take(dataset, 8)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:146
        sc_negl = strrep(sc_negl, "Sc_negl,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:147
        notes = cellarray([])
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:150
        m = 9
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:151
        while 1:
            temp = take(dataset, m)
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:153
            if 0 == strncmpi(temp, "notes", 5):
                break
            temp = strrep(temp, "notes,", "")
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:157
            notes[end() + 1] = temp
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:158
            m = m + 1
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:159

        fclose(fid)
        clear("temp", "fid")
        imported_data = importdata(matlabarray([input_folder, take(d, n).name]), ",", m)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:166
        header = matlabarray(getattr(imported_data, "textdata"))
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:167
        data = matlabarray(getattr(imported_data, "data"))
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:168
        columns_index = matlabarray(dot(ones(numel(input_columns_names), 1), -1))
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:169
        on_error = 0
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:172
        columns = header[end(), :]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:173
        for y in arange(1, length(columns)).reshape(-1):
            for i in arange(1, numel(input_columns_names)).reshape(-1):
                if logical_or(
                    (strcmpi(take(columns, y), input_columns_names[i])),
                    (strcmpi(take(columns, y), strcat("itp", input_columns_names[i]))),
                ):
                    if columns_index[i] != -1:
                        fprintf(
                            "column %s already founded at index %d\n",
                            char(input_columns_names[i]),
                            i,
                        )
                        on_error = 1
                        # oneflux_steps/ustar_cp_refactor_wip/launch.m:179
                        break
                    else:
                        columns_index[i] = y
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:182
            if 1 == on_error:
                break
        if 1 == on_error:
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:192
            continue
        on_error = 0
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:196
        ppfd_from_rg = 0
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:197
        for i in arange(1, numel(columns_index)).reshape(-1):
            if -1 == columns_index[i]:
                if i == PPFD_INDEX:
                    ppfd_from_rg = 1
                # oneflux_steps/ustar_cp_refactor_wip/launch.m:201
                else:
                    fprintf("column %s not found!\n", char(input_columns_names[i]))
                    on_error = 1
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:204
        if 1 == on_error:
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:210
            continue
        uStar = matlabarray(data[:, columns_index[USTAR_INDEX]])
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:214
        NEE = matlabarray(data[:, columns_index[NEE_INDEX]])
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:215
        Ta = matlabarray(data[:, columns_index[TA_INDEX]])
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:216
        Rg = matlabarray(data[:, columns_index[RG_INDEX]])
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:217
        if 0 == ppfd_from_rg:
            PPFD = matlabarray(data[:, columns_index[PPFD_INDEX]])
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:219
            q = find(PPFD < -9990)
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:221
            if numel(q) == numel(PPFD):
                ppfd_from_rg = 1
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:223
        if 1 == ppfd_from_rg:
            fprintf("(PPFD_IN from SW_IN)...")
            PPFD = matlabarray(dot(Rg, 2.24))
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:229
            p = find(Rg < -9990)
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:230
            PPFD[p] = -9999
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:231
            clear("p")
        clear("data")
        #     load([cIn,d(n).name]);
        uStar[uStar == -9999] = NaN
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:240
        NEE[NEE == -9999] = NaN
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:241
        Ta[Ta == -9999] = NaN
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:242
        PPFD[PPFD == -9999] = NaN
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:243
        Rg[Rg == -9999] = NaN
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:244
        #         data_L3(data_L3==-9999)=NaN; data_L3(data_L3==-6999)=NaN;
        # by carlo, added by alessio on February 21, 2014
        if sum(isnan(NEE)) == numel(NEE):
            fprintf("NEE is empty!\n")
            continue
        if sum(isnan(uStar)) == numel(uStar):
            fprintf("uStar is empty!\n")
            continue
        if isempty(Ta):
            fprintf("Ta is empty!\n")
            continue
        if isempty(Rg):
            fprintf("Rg is empty!\n")
            continue
        # il DoY sarebbe il Dtime
        # 	i=strmatch('DoY',int_L3,'exact'); t=data_L3(:,i);
        # 	i=strmatch('ustar',int_L3,'exact'); uStar=data_L3(:,i);
        # 	i=strmatch('NEE_or',int_L3,'exact'); NEE=data_L3(:,i);
        # 	i=strmatch('Ta',int_L3,'exact'); Ta=data_L3(:,i);
        # 	i=strmatch('PPFD',int_L3,'exact'); PPFD=data_L3(:,i);
        # 	i=strmatch('Rg',int_L3,'exact'); Rg=data_L3(:,i);
        # by alessio ( by carlo)
        # insert Dtime
        nrPerDay = mod(numel(uStar), 365)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:275
        if nrPerDay == 0:
            nrPerDay = mod(numel(uStar), 364)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:276
        t = matlabarray(1 + (1 / nrPerDay))
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:277
        for n2 in arange(2, numel(uStar)).reshape(-1):
            t[n2, 1] = t[n2 - 1, 1] + (1 / nrPerDay)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:278
        clear("n2")
        fNight = Rg < 5
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:281
        T = copy(Ta)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:282
        # Look at inputs.
        fPlot = 0
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:286
        if fPlot:
            plot(t, uStar, ".")
            mydatetick(t, "Mo", 4, 1)
            pause
            plot(t, NEE, ".")
            mydatetick(t, "Mo", 4, 1)
            pause
            plot(t, Ta, ".")
            mydatetick(t, "Mo", 4, 1)
            pause
            plot(t, PPFD, ".")
            mydatetick(t, "Mo", 4, 1)
            pause
            plot(t, Rg, ".")
            mydatetick(t, "Mo", 4, 1)
            pause
        # Call uStarTh bootstrappng program (2 versions)
        # and assign annual Cp arrays.
        fPlot = 0
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:298
        cSiteYr = strrep(take(d, n).name, ".txt", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:298
        cSiteYr = strrep(cSiteYr, "_ut", "_barr")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:299
        nBoot = 100
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:300
        # by alessio
        # if exist([cOut,'4-season_analysis_',strrep(cSiteYr,'.txt',''),'.mat']) == 0
        Cp2, Stats2, Cp3, Stats3 = cpdBootstrapUStarTh4Season20100901(
            t, NEE, uStar, T, fNight, fPlot, cSiteYr, nBoot, nargout=4
        )
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:307
        (
            Cp,
            n,
            tW,
            CpW,
            cMode,
            cFailure,
            fSelect,
            sSine,
            FracSig,
            FracModeD,
            FracSelect,
        ) = cpdAssignUStarTh20100901(Stats2, fPlot, cSiteYr, nargout=11)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:314
        if isempty(cFailure):
            # save([cOut,'4-season_analysis_',strrep(cSiteYr,'.txt',''),'.mat'],'Cp2','Stats2','Cp3','Stats3',...
            #    'Cp','n','tW','CpW','cMode','cFailure','fSelect','sSine','FracSig','FracModeD','FracSelect');
            cSiteYr = strrep(cSiteYr, ".csv", "")
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:318
            dlmwrite(
                output_folder + char(site) + "_uscp_" + char(year) + ".txt",
                Cp,
                "precision",
                8,
            )
            fid = fopen(
                output_folder + char(site) + "_uscp_" + char(year) + ".txt", "a"
            )
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:321
            fprintf(fid, "\n;processed with ustar_mp 1.0 on %s\n", datestr(clock))
            for i in arange(length(notes), 1, -1).reshape(-1):
                fprintf(fid, ";%s\n", notes[i])
            clear("i")
            fclose(fid)
            clear("fid")
            fprintf("ok\n")
        else:
            error_str = matlabarray(
                [[error_str], [char(site), "_uscp_", char(year), " ", cFailure]]
            )
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:331
            fprintf("%s\n", cFailure)
            exitcode = 1
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:333
        # by alessio
        # end
        #     print -djpeg100 Plot2_4Season_CACa1-2001;
        # commented by alessio
        # 	# multi-season analysis
        #     if exist([cOut,'multi-season_analysis_',strrep(cSiteYr,'.txt',''),'.mat']) == 0
        #         [Cp2,Stats2,Cp3,Stats3] = ...
        #             cpdBootstrapUStarTh20100901 ...
        #                 (t,NEE,uStar,T,fNight,fPlot,cSiteYr,nBoot);
        #
        #         [Cp,n,tW,CpW,cMode,cFailure,fSelect,sSine,FracSig,FracModeD,FracSelect] ...
        #             = cpdAssignUStarTh20100901(Stats2,fPlot,cSiteYr);
        #     # 	print -djpeg100 Plot2_CACa1-2001;
        #
        #         if isempty(cFailure)
        #             save([cOut,'multi-season_analysis_',strrep(cSiteYr,'.txt',''),'.mat'],'Cp2','Stats2','Cp3','Stats3',...
        #                 'Cp','n','tW','CpW','cMode','cFailure','fSelect','sSine','FracSig','FracModeD','FracSelect');
        #         else
        #             error_str = [error_str;{cSiteYr},'multi-season_analysis',cFailure];
        #         end
        #     end
        clear(
            "uStar",
            "cFailure",
            "cMode",
            "cSiteYr",
            "fNight",
            "fPlot",
            "fSelect",
            "n",
            "nBoot",
            "sSine",
            "t",
        )
        clear(
            "tW",
            "Cp3",
            "CpW",
            "FracModeD",
            "FracSelect",
            "FracSig",
            "NEE",
            "PPFD",
            "Rg",
            "Stats2",
            "Stats3",
            "T",
            "Ta",
            "Cp",
            "Cp2",
        )

    clear("n")
    # quit

    # by alessio
    # save('resumeBarr','cIn','cOut','d','error_str');
    return exitcode
