function [exitcode, site, year, lat, lon, timezone, htower, timeres, sc_negl, notes] ... 
    = notValidHeader(dataset)
    exitcode = 0; 
    [site, year, lat, lon, timezone, htower, timeres, sc_negl, notes] = deal(NaN);
    % get site
    r = strncmpi(dataset(1), 'site', 4);
    if 0 == r
        fprintf('site keyword not found.\n');
        exitcode = 1;
        return;
    end       
    site = dataset(1);
    site = strrep(site, 'site,', '');
    
    % get year
    r = strncmpi(dataset(2), 'year', 4);
    if 0 == r
        fprintf('year keyword not found.\n');
        exitcode = 1;
        return;
    end       
    year = dataset(2);
    year = strrep(year, 'year,', '');
    
    % get lat
    r = strncmpi(dataset(3), 'lat', 3);
    if 0 == r
        fprintf('lat keyword not found.\n');
        exitcode = 1;
        return;
    end       
    lat = dataset(3);
    lat = strrep(lat, 'lat,', '');
    
    % get lon
    r = strncmpi(dataset(4), 'lon', 3);
    if 0 == r
        fprintf('lon keyword not found.\n');
        exitcode = 1;
        return;
    end       
    lon = dataset(4);
    lon = strrep(lon, 'lon,', '');
    
    % get timezone
    r = strncmpi(dataset(5), 'timezone', 8);
    if 0 == r
        fprintf('timezone keyword not found.\n');
        exitcode = 1;
        return;
    end       
    timezone = dataset(5);
    timezone = strrep(timezone, 'timezone,', '');
    
    % get htower
    r = strncmpi(dataset(6), 'htower', 6);
    if 0 == r
        fprintf('htower keyword not found.\n');
        exitcode = 1;
        return;
    end       
    htower = dataset(6);
    htower = strrep(htower, 'htower,', '');
    
    % get timeres
    r = strncmpi(dataset(7), 'timeres', 7);
    if 0 == r
        fprintf('timeres keyword not found.\n');
        exitcode = 1;
        return;
    end       
    timeres = dataset(7);
    timeres = strrep(timeres, 'timeres,', '');
    
    % get sc_negl
    r = strncmpi(dataset(8), 'Sc_negl', 7);
    if 0 == r
        fprintf('sc_negl keyword not found.\n');
        exitcode = 1;
        return;
    end       
    sc_negl = dataset(8);
    sc_negl = strrep(sc_negl, 'Sc_negl,', '');
    
    % get notes
    r = strncmpi(dataset(9), 'notes', 5);
    if 0 == r
        fprintf('notes keyword not found.\n');
        exitcode = 1;
        return;
    end       
    notes = dataset(9);
    notes = strrep(notes, 'notes,', '');

end