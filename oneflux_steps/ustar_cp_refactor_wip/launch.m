%	launch

%	Example of data input for Alan Barr's uStarTh programs. 
%	The data are input from a MatLab L3 file that Dario sent me 
%	a couple of years ago. 

%	load and assign data

function exitcode = launch(input_folder, output_folder)
    exitcode = 0;
    warning off;

    [input_folder, output_folder] = checkPath(input_folder, output_folder);

    %by alessio
    USTAR_INDEX = 1;
    NEE_INDEX = 2;
    TA_INDEX = 3;
    PPFD_INDEX = 4;
    RG_INDEX = 5;
    input_columns_names = {'USTAR' 'NEE' 'TA' 'PPFD_IN' 'SW_IN' };

    %by alessio
    fprintf('\n\nUstar Threshold Computation by Alan Barr\n\ninput in %s\noutput in %s\n\n', input_folder, output_folder);
    d = dir([input_folder,'*_qca_ustar_*.csv']);
    error_str = {};

    % by alessio
    fprintf('%d files founded.\n\n', numel(d));

    for n = 1:numel(d)
        % by alessio
        fprintf('processing n.%02d, %s...', n, d(n).name);

        % open file
        fid = fopen([input_folder,d(n).name] ,'r');
        if -1 == fid
            fprintf('unable to open file\n');
            exitcode = 1;
            continue;
        end
        
        dataset = textscan(fid,'%[^\n]');dataset = dataset{1};
        
        [exitcode, site, year, lat, lon, timezone, htower, timeres, sc_negl, notes] ...
            = notValidHeader(dataset);

        if exitcode == 1
            continue;
        end
        
        % get more notes
        i = 10;
        while 1
            r = strncmpi(dataset(i), 'notes', 5);
            if 0 == r
                break;
            end       
            temp = dataset(i);
            temp = strrep(temp, 'notes,', '');
            notes = [temp notes];
            i = i + 1;
        end
        
        
        fclose(fid);
        clear i temp r fid;
        filename = d(n).name;
        
        [header, data, columns_index] = loadData(input_folder, filename, notes, input_columns_names);
        
        % parse header, by alessio
        [exitcode, columns_index] = mapColumnNamesToIndices(header, input_columns_names, notes, columns_index);
        
        if exitcode == 1
            continue;
        end
        
        [ppfd_from_rg, exitcode] = ppfdColExists(PPFD_INDEX, columns_index, input_columns_names);
        
        if exitcode == 1
            continue;
        end
        
        uStar = data(:, columns_index(USTAR_INDEX));
        NEE = data(:, columns_index(NEE_INDEX));
        Ta = data(:, columns_index(TA_INDEX));
        Rg = data(:, columns_index(RG_INDEX));

        [PPFD, ppfd_from_rg] = areAllPpfdValuesInvalid(ppfd_from_rg, columns_index, PPFD_INDEX, data);
        
        if 1 == ppfd_from_rg

            PPFD = derivePpfdColFromRg(Rg);
        end

        clear data;


        [uStar, NEE, Ta, PPFD, Rg] = setMissingDataNan(uStar, NEE, Ta, PPFD, Rg);

        [exitcode] = anyColumnsEmpty(uStar, NEE, Ta, Rg);
        if exitcode == 1
            continue;
        end

    %il DoY sarebbe il Dtime
    % 	i=strmatch('DoY',int_L3,'exact'); t=data_L3(:,i); 
    % 	i=strmatch('ustar',int_L3,'exact'); uStar=data_L3(:,i); 
    % 	i=strmatch('NEE_or',int_L3,'exact'); NEE=data_L3(:,i); 
    % 	i=strmatch('Ta',int_L3,'exact'); Ta=data_L3(:,i); 
    % 	i=strmatch('PPFD',int_L3,'exact'); PPFD=data_L3(:,i); 
    % 	i=strmatch('Rg',int_L3,'exact'); Rg=data_L3(:,i); 

        %by alessio ( by carlo)
        % insert Dtime
        t = createTimeArray(uStar);

        
        fNight=Rg<5; % flag nighttime periods
        T=Ta;
        
    %	Look at inputs.	
        fPlot = plotData(t, uStar, NEE, Ta, PPFD, Rg);
        
    %	Call uStarTh bootstrappng program (2 versions) 
    %	and assign annual Cp arrays.	
        
        fPlot=0; cSiteYr=strrep(d(n).name,'.txt','');%'CACa1-2001'; 
        cSiteYr = strrep(cSiteYr, '_ut', '_barr');
        nBoot=100;
        
        
        % 4-season analysis
        %by alessio
        %if exist([cOut,'4-season_analysis_',strrep(cSiteYr,'.txt',''),'.mat']) == 0

            [Cp2,Stats2,Cp3,Stats3] = ... 
                cpdBootstrapUStarTh4Season20100901 ...
                    (t,NEE,uStar,T,fNight,fPlot,cSiteYr,nBoot); 

        % 	print -djpeg100 Plot1_4Season_CACa1-2001; 

        % commented by alessio
        % 	% multi-season analysis
        %     if exist([cOut,'multi-season_analysis_',strrep(cSiteYr,'.txt',''),'.mat']) == 0 
        %         [Cp2,Stats2,Cp3,Stats3] = ... 
        %             cpdBootstrapUStarTh20100901 ...
        %                 (t,NEE,uStar,T,fNight,fPlot,cSiteYr,nBoot); 
        % 
        %         [Cp,n,tW,CpW,cMode,cFailure,fSelect,sSine,FracSig,FracModeD,FracSelect] ... 
        %             = cpdAssignUStarTh20100901(Stats2,fPlot,cSiteYr); 
        %     % 	print -djpeg100 Plot2_CACa1-2001; 
        % 
        %         if isempty(cFailure)
        %             save([cOut,'multi-season_analysis_',strrep(cSiteYr,'.txt',''),'.mat'],'Cp2','Stats2','Cp3','Stats3',...
        %                 'Cp','n','tW','CpW','cMode','cFailure','fSelect','sSine','FracSig','FracModeD','FracSelect');
        %         else
        %             error_str = [error_str;{cSiteYr},'multi-season_analysis',cFailure];
        %         end        
        %     end
            [Cp,n,tW,CpW,cMode,cFailure,fSelect,sSine,FracSig,FracModeD,FracSelect] ... 
            = cpdAssignUStarTh20100901(Stats2,fPlot,cSiteYr); 
        

        [error_str, cSiteYr, exitcode] = saveResult(cFailure, cSiteYr, output_folder, site, year, Cp, clock, notes);

        % by alessio
        %end    
    %     print -djpeg100 Plot2_4Season_CACa1-2001; 

        

        clear uStar cFailure cMode cSiteYr fNight fPlot fSelect n nBoot sSine t 
        clear tW Cp3 CpW FracModeD FracSelect FracSig NEE PPFD Rg Stats2 Stats3 T Ta Cp Cp2
    end
    clear n

    %quit

    % by alessio
    %save('resumeBarr','cIn','cOut','d','error_str');
end
