function [y, m, d, h, mn, s] = mydatevec(t)
    % Main function to convert datenum to date vectors.
    
    iYaN = find(~isnan(t)); 
    
    % Initialize output arrays
    [y, m, d, h, mn, s] = initializeVectors(size(t));
    
    % Convert datenum to datevec for non-NaN values
    [yy, mm, dd, hh, mmn, ss] = convertToDateVec(t(iYaN));
    
    % Populate non-NaN date components
    [y, m, d, h, mn, s] = populateDateComponents(iYaN, yy, mm, dd, hh, mmn, ss, y, m, d, h, mn, s);
    
    % Handle midnight case (0000 UTC) by converting to 2400 UTC
    [y, m, d, h] = handleMidnightCase(h, mn, s, t, y, m, d, h);
end

function [y, m, d, h, mn, s] = initializeVectors(sizeVec)
    % Initialize vectors with NaN values
    y = NaN * ones(sizeVec);
    m = y; d = y; h = y; mn = y; s = y;
end

function [yy, mm, dd, hh, mmn, ss] = convertToDateVec(t)
    % Convert datenum to datevec
    [yy, mm, dd, hh, mmn, ss] = datevec(t);
end

function [y, m, d, h, mn, s] = populateDateComponents(iYaN, yy, mm, dd, hh, mmn, ss, y, m, d, h, mn, s)
    % Populate date components for non-NaN values
    y(iYaN) = yy;
    m(iYaN) = mm;
    d(iYaN) = dd;
    h(iYaN) = hh;
    mn(iYaN) = mmn;
    s(iYaN) = ss;
end

function [y, m, d, h] = handleMidnightCase(h, mn, s, t, y, m, d, h)
    % Handle the case where the time is exactly midnight
    i2400 = find(h == 0 & mn == 0 & s == 0);
    [y2400, m2400, d2400, ~, ~, ~] = datevec(t(i2400) - 1);
    y(i2400) = y2400;
    m(i2400) = m2400;
    d(i2400) = d2400;
    h(i2400) = 24;
end
