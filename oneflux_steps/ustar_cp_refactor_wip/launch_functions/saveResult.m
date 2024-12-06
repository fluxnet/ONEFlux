function [error_str, cSiteYr, errorCode] = saveResult(cFailure, cSiteYr, output_folder, site, year, Cp, clock, notes)
    error_str = "";
    errorCode = 0;
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
        errorCode = 1;
    end
end