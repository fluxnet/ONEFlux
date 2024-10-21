# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/launch.m

# launch

# Example of data input for Alan Barr's uStarTh programs.
# The data are input from a MatLab L3 file that Dario sent me
# a couple of years ago.

# load and assign data


@function
def launch(input_folder=None, output_folder=None, *args, **kwargs):
    varargin = launch.varargin
    nargin = launch.nargin

    exitcode = 0
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:10
    warning("off")
    # check input path
    if 0 == exist("input_folder"):
        input_folder = matlabarray(concat([pwd, "/"]))
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:15
    else:
        if length(input_folder) < 2:
            if input_folder[2] != ":":
                input_folder = matlabarray(concat([pwd, "/", input_folder]))
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:18

    if (
        input_folder[length(input_folder)] != "\\"
        and input_folder[length(input_folder)] != "/"
    ):
        input_folder = matlabarray(concat([input_folder, "/"]))
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:22

    # check output path
    if 0 == exist("output_folder"):
        output_folder = matlabarray(concat([pwd, "/"]))
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:27
    else:
        if length(output_folder) < 2:
            if output_folder[2] != ":":
                output_folder = matlabarray(concat([pwd, "/", output_folder]))
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:30

    if (
        output_folder[length(output_folder)] != "\\"
        and output_folder[length(output_folder)] != "/"
    ):
        output_folder = matlabarray(concat([output_folder, "/"]))
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
    d = dir(concat([input_folder, "*_qca_ustar_*.csv"]))
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:48
    error_str = cellarray([])
    # oneflux_steps/ustar_cp_refactor_wip/launch.m:49
    # by alessio
    fprintf("%d files founded.\n\n", numel(d))
    for n in arange(1, numel(d)).reshape(-1):
        # by alessio
        fprintf("processing n.%02d, %s...", n, d[n].name)
        fid = fopen(concat([input_folder, d[n].name]), "r")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:59
        if -1 == fid:
            fprintf("unable to open file\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:62
            continue
        dataset = textscan(fid, "%[^\n]")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:66
        dataset = dataset[1]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:66
        r = strncmpi(dataset[1], "site", 4)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:69
        if 0 == r:
            fprintf("site keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:72
            continue
        site = dataset[1]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:75
        site = strrep(site, "site,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:76
        r = strncmpi(dataset[2], "year", 4)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:79
        if 0 == r:
            fprintf("year keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:82
            continue
        year = dataset[2]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:85
        year = strrep(year, "year,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:86
        r = strncmpi(dataset[3], "lat", 3)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:89
        if 0 == r:
            fprintf("lat keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:92
            continue
        lat = dataset[3]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:95
        lat = strrep(lat, "lat,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:96
        r = strncmpi(dataset[4], "lon", 3)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:99
        if 0 == r:
            fprintf("lon keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:102
            continue
        lon = dataset[4]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:105
        lon = strrep(lon, "lon,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:106
        r = strncmpi(dataset[5], "timezone", 8)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:109
        if 0 == r:
            fprintf("timezone keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:112
            continue
        timezone = dataset[5]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:115
        timezone = strrep(timezone, "timezone,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:116
        r = strncmpi(dataset[6], "htower", 6)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:119
        if 0 == r:
            fprintf("htower keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:122
            continue
        htower = dataset[6]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:125
        htower = strrep(htower, "htower,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:126
        r = strncmpi(dataset[7], "timeres", 7)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:129
        if 0 == r:
            fprintf("timeres keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:132
            continue
        timeres = dataset[7]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:135
        timeres = strrep(timeres, "timeres,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:136
        r = strncmpi(dataset[8], "Sc_negl", 7)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:139
        if 0 == r:
            fprintf("sc_negl keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:142
            continue
        sc_negl = dataset[8]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:145
        sc_negl = strrep(sc_negl, "Sc_negl,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:146
        r = strncmpi(dataset[9], "notes", 5)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:149
        if 0 == r:
            fprintf("notes keyword not found.\n")
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:152
            continue
        notes = dataset[9]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:155
        notes = strrep(notes, "notes,", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:156
        i = 10
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:159
        while 1:
            r = strncmpi(dataset[i], "notes", 5)
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:161
            if 0 == r:
                break
            temp = dataset[i]
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:165
            temp = strrep(temp, "notes,", "")
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:166
            notes = matlabarray(concat([temp, notes]))
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:167
            i = i + 1
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:168

        fclose(fid)
        clear("i", "temp", "r", "fid")
        imported_data = importdata(
            concat([input_folder, d[n].name]), ",", (9 + length(notes))
        )
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:176
        header = getattr(imported_data, ("textdata"))
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:177
        data = getattr(imported_data, ("data"))
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:178
        columns_index = dot(ones(numel(input_columns_names), 1), -1)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:179
        on_error = 0
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:182
        for y in arange(1, length(header[9 + length(notes), arange()])).reshape(-1):
            for i in arange(1, numel(input_columns_names)).reshape(-1):
                if logical_or(
                    (strcmpi(header[(9 + length(notes)), y], input_columns_names[i])),
                    (
                        strcmpi(
                            header[(9 + length(notes)), y],
                            strcat("itp", input_columns_names[i]),
                        )
                    ),
                ):
                    if columns_index[i] != -1:
                        fprintf(
                            "column %s already founded at index %d\n",
                            char(input_columns_names[i]),
                            i,
                        )
                        on_error = 1
                        # oneflux_steps/ustar_cp_refactor_wip/launch.m:188
                        break
                    else:
                        columns_index[i] = y
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:191
            if 1 == on_error:
                break
        if 1 == on_error:
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:201
            continue
        on_error = 0
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:205
        ppfd_from_rg = 0
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:206
        for i in arange(1, numel(columns_index)).reshape(-1):
            if -1 == columns_index[i]:
                if i == PPFD_INDEX:
                    ppfd_from_rg = 1
                # oneflux_steps/ustar_cp_refactor_wip/launch.m:210
                else:
                    fprintf("column %s not found!\n", char(input_columns_names[i]))
                    on_error = 1
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:213
        if 1 == on_error:
            exitcode = 1
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:219
            continue
        uStar = data[arange(), columns_index[USTAR_INDEX]]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:223
        NEE = data[arange(), columns_index[NEE_INDEX]]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:224
        Ta = data[arange(), columns_index[TA_INDEX]]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:225
        Rg = data[arange(), columns_index[RG_INDEX]]
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:226
        if 0 == ppfd_from_rg:
            PPFD = data[arange(), columns_index[PPFD_INDEX]]
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:228
            q = find(PPFD < -9990)
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:230
            if numel(q) == numel(PPFD):
                ppfd_from_rg = 1
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:232
        if 1 == ppfd_from_rg:
            fprintf("(PPFD_IN from SW_IN)...")
            PPFD = dot(Rg, 2.24)
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:238
            p = find(Rg < -9990)
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:239
            PPFD[p] = -9999
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:240
            clear("p")
        clear("data")
        #     load([cIn,d(n).name]);
        uStar[uStar == -9999] = NaN
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:249
        NEE[NEE == -9999] = NaN
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:250
        Ta[Ta == -9999] = NaN
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:251
        PPFD[PPFD == -9999] = NaN
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:252
        Rg[Rg == -9999] = NaN
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:253
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
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:284
        if nrPerDay == 0:
            nrPerDay = mod(numel(uStar), 364)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:285
        t = 1 + (1 / nrPerDay)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:286
        for n2 in arange(2, numel(uStar)).reshape(-1):
            t[n2, 1] = t[n2 - 1, 1] + (1 / nrPerDay)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:287
        clear("n2")
        fNight = Rg < 5
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:290
        T = copy(Ta)
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:291
        # Look at inputs.
        fPlot = 0
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:295
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
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:307
        cSiteYr = strrep(d[n].name, ".txt", "")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:307
        cSiteYr = strrep(cSiteYr, "_ut", "_barr")
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:308
        nBoot = 100
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:309
        # by alessio
        # if exist([cOut,'4-season_analysis_',strrep(cSiteYr,'.txt',''),'.mat']) == 0
        Cp2, Stats2, Cp3, Stats3 = cpdBootstrapUStarTh4Season20100901(
            t, NEE, uStar, T, fNight, fPlot, cSiteYr, nBoot, nargout=4
        )
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:316
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
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:323
        if isempty(cFailure):
            # save([cOut,'4-season_analysis_',strrep(cSiteYr,'.txt',''),'.mat'],'Cp2','Stats2','Cp3','Stats3',...
            #    'Cp','n','tW','CpW','cMode','cFailure','fSelect','sSine','FracSig','FracModeD','FracSelect');
            cSiteYr = strrep(cSiteYr, ".csv", "")
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:327
            dlmwrite(
                concat([output_folder, char(site), "_uscp_", char(year), ".txt"]),
                Cp,
                "precision",
                8,
            )
            fid = fopen(
                concat([output_folder, char(site), "_uscp_", char(year), ".txt"]), "a"
            )
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:330
            fprintf(fid, "\n;processed with ustar_mp 1.0 on %s\n", datestr(clock))
            for i in arange(length(notes), 1, -1).reshape(-1):
                fprintf(fid, ";%s\n", notes[i])
            clear("i")
            fclose(fid)
            clear("fid")
            fprintf("ok\n")
        else:
            error_str = matlabarray(
                concat([[error_str], [char(site), "_uscp_", char(year), " ", cFailure]])
            )
            # oneflux_steps/ustar_cp_refactor_wip/launch.m:340
            fprintf("%s\n", cFailure)
            exitcode = 1
        # oneflux_steps/ustar_cp_refactor_wip/launch.m:342
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
