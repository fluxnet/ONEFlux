%	launch

%	Example of data input for Alan Barr's uStarTh programs. 
%	The data are input from a MatLab L3 file that Dario sent me 
%	a couple of years ago. 

%	load and assign data

function exitcode = launch(input_folder, output_folder)
exitcode = 0;
warning off;

% check input path
if 0 == exist('input_folder')
    input_folder = [pwd '/'];
elseif length(input_folder) < 2
    if input_folder(2) ~= ':'
        input_folder = [pwd '/' input_folder];
    end
end
if input_folder(length(input_folder)) ~= '\' && input_folder(length(input_folder)) ~= '/'
    input_folder = [input_folder '/'];
end

% check output path
if 0 == exist('output_folder')
    output_folder = [pwd '/'];
elseif length(output_folder) < 2 
    if output_folder(2) ~= ':'
        output_folder = [pwd '/' output_folder];  
    end
end
if output_folder(length(output_folder)) ~= '\' && output_folder(length(output_folder)) ~= '/'
    output_folder = [output_folder '/'];
end
mkdir(output_folder);

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
    
    % get site
    r = strncmpi(dataset(1), 'site', 4);
    if 0 == r
        fprintf('site keyword not found.\n');
        exitcode = 1;
        continue;
    end       
    site = dataset(1);
    site = strrep(site, 'site,', '');
    
    % get year
    r = strncmpi(dataset(2), 'year', 4);
    if 0 == r
        fprintf('year keyword not found.\n');
        exitcode = 1;
        continue;
    end       
    year = dataset(2);
    year = strrep(year, 'year,', '');
    
    % get lat
    r = strncmpi(dataset(3), 'lat', 3);
    if 0 == r
        fprintf('lat keyword not found.\n');
        exitcode = 1;
        continue;
    end       
    lat = dataset(3);
    lat = strrep(lat, 'lat,', '');
    
    % get lon
    r = strncmpi(dataset(4), 'lon', 3);
    if 0 == r
        fprintf('lon keyword not found.\n');
        exitcode = 1;
        continue;
    end       
    lon = dataset(4);
    lon = strrep(lon, 'lon,', '');
    
    % get timezone
    r = strncmpi(dataset(5), 'timezone', 8);
    if 0 == r
        fprintf('timezone keyword not found.\n');
        exitcode = 1;
        continue;
    end       
    timezone = dataset(5);
    timezone = strrep(timezone, 'timezone,', '');
    
    % get htower
    r = strncmpi(dataset(6), 'htower', 6);
    if 0 == r
        fprintf('htower keyword not found.\n');
        exitcode = 1;
        continue;
    end       
    htower = dataset(6);
    htower = strrep(htower, 'htower,', '');
    
    % get timeres
    r = strncmpi(dataset(7), 'timeres', 7);
    if 0 == r
        fprintf('timeres keyword not found.\n');
        exitcode = 1;
        continue;
    end       
    timeres = dataset(7);
    timeres = strrep(timeres, 'timeres,', '');
    
    % get sc_negl
    r = strncmpi(dataset(8), 'Sc_negl', 7);
    if 0 == r
        fprintf('sc_negl keyword not found.\n');
        exitcode = 1;
        continue;
    end       
    sc_negl = dataset(8);
    sc_negl = strrep(sc_negl, 'Sc_negl,', '');
    
    % get notes
    r = strncmpi(dataset(9), 'notes', 5);
    if 0 == r
        fprintf('notes keyword not found.\n');
        exitcode = 1;
        continue;
    end       
    notes = dataset(9);
    notes = strrep(notes, 'notes,', '');
    
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
    
    
    imported_data = importdata([input_folder,d(n).name], ',', (9+length(notes)));  
    header = imported_data.('textdata');
    data = imported_data.('data');
    columns_index = ones(numel(input_columns_names), 1) * -1;
    
    % parse header, by alessio
    on_error = 0;
    for y = 1:length(header(9+length(notes),:))
        for i = 1:numel(input_columns_names)
            if (strcmpi(header((9+length(notes)), y), input_columns_names(i))) | (strcmpi(header((9+length(notes)), y), strcat('itp',input_columns_names(i))))
                if columns_index(i) ~= -1
                    fprintf('column %s already founded at index %d\n', char(input_columns_names(i)), i);
                    on_error = 1;
                    break;
                else
                    columns_index(i) = y;
                end                       
            end
        end
        if ( 1 == on_error )
            break;
        end
    end
    
    if 1 == on_error 
        exitcode = 1;
        continue;
    end
          
    on_error = 0;
    ppfd_from_rg = 0;
    for i = 1:numel(columns_index)
        if -1 == columns_index(i)
            if i == PPFD_INDEX
                ppfd_from_rg = 1;
            else
                fprintf('column %s not found!\n', char(input_columns_names(i)));
                on_error = 1;
            end
        end        
    end
    
    if 1 == on_error
        exitcode = 1;
        continue;
    end
    
    uStar = data(:, columns_index(USTAR_INDEX));
    NEE = data(:, columns_index(NEE_INDEX));
    Ta = data(:, columns_index(TA_INDEX));
    Rg = data(:, columns_index(RG_INDEX));
    if 0 == ppfd_from_rg
        PPFD = data(:, columns_index(PPFD_INDEX));
        % check if ppfd is invalid
        q = find(PPFD < -9990); 
        if numel(q) == numel(PPFD);
            ppfd_from_rg = 1;
        end        
    end
    
    if 1 == ppfd_from_rg
        fprintf('(PPFD_IN from SW_IN)...');
        PPFD = Rg * 2.24;
        p = find(Rg < -9990);
        PPFD(p) = -9999;
        clear p;
    end

    clear data;
    
    %[t,uStar,NEE,Ta,PPFD,Rg] = textread([cIn,d(n).name],'%f %f %f %f %f %f %f','headerlines',0,'delimiter',',');   
    
%     load([cIn,d(n).name]);
    uStar(uStar==-9999) = NaN;
    NEE(NEE==-9999) = NaN;
    Ta(Ta==-9999) = NaN;
    PPFD(PPFD==-9999) = NaN;
    Rg(Rg==-9999) = NaN;
%         data_L3(data_L3==-9999)=NaN; data_L3(data_L3==-6999)=NaN;

    % by carlo, added by alessio on February 21, 2014
    if sum(isnan(NEE)) == numel(NEE); 
        fprintf('NEE is empty!\n');
        continue;
    end
    if sum(isnan(uStar)) == numel(uStar); 
        fprintf('uStar is empty!\n');
        continue;
    end
    if isempty(Ta); 
        fprintf('Ta is empty!\n');
        continue;
    end
    if isempty(Rg); 
        fprintf('Rg is empty!\n');
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
    nrPerDay = mod(numel(uStar),365);
    if nrPerDay == 0; nrPerDay = mod(numel(uStar),364);end
    t = 1 + (1 / nrPerDay);
    for n2 = 2:numel(uStar); t(n2,1) = t(n2-1,1)+ (1 / nrPerDay);end
    clear n2
	
	fNight=Rg<5; % flag nighttime periods
	T=Ta;
	
%	Look at inputs.	
	
	fPlot=0; 
	if fPlot;
		plot(t,uStar,'.'); mydatetick(t,'Mo',4,1); pause;
		plot(t,NEE,'.'); mydatetick(t,'Mo',4,1); pause;
		plot(t,Ta,'.'); mydatetick(t,'Mo',4,1); pause;
		plot(t,PPFD,'.'); mydatetick(t,'Mo',4,1); pause;
		plot(t,Rg,'.'); mydatetick(t,'Mo',4,1); pause;
	end;
	
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

    [Cp,n,tW,CpW,cMode,cFailure,fSelect,sSine,FracSig,FracModeD,FracSelect] ... 
        = cpdAssignUStarTh20100901(Stats2,fPlot,cSiteYr); 
    if isempty(cFailure)
        %save([cOut,'4-season_analysis_',strrep(cSiteYr,'.txt',''),'.mat'],'Cp2','Stats2','Cp3','Stats3',...
        %    'Cp','n','tW','CpW','cMode','cFailure','fSelect','sSine','FracSig','FracModeD','FracSelect');
        cSiteYr = strrep(cSiteYr, '.csv', '');
        dlmwrite([output_folder,char(site),'_uscp_',char(year),'.txt'], Cp, 'precision', 8);
        
        fid = fopen([output_folder,char(site),'_uscp_',char(year),'.txt'], 'a');
        fprintf(fid, '\n;processed with ustar_mp 1.0 on %s\n', datestr(clock));
        for i = length(notes):-1:1
            fprintf(fid, ';%s\n', notes{i});
        end
        clear i
        fclose(fid);
        clear fid;
        fprintf('ok\n');
    else
        error_str = [error_str; char(site),'_uscp_',char(year),' ',cFailure];
        fprintf('%s\n', cFailure);
        exitcode = 1;
    end
    % by alessio
    %end    
%     print -djpeg100 Plot2_4Season_CACa1-2001; 
	
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

    clear uStar cFailure cMode cSiteYr fNight fPlot fSelect n nBoot sSine t 
    clear tW Cp3 CpW FracModeD FracSelect FracSig NEE PPFD Rg Stats2 Stats3 T Ta Cp Cp2
end
clear n

%quit

% by alessio
%save('resumeBarr','cIn','cOut','d','error_str');
