function d = mydoy(t)
    % MYDOY Calculate the day of the year for given serial date numbers.
    % Input:
    %   t - Array of serial date numbers
    % Output:
    %   d - Day of the year corresponding to each date number
    
    % Convert serial date numbers to date vectors
    [y, m, d, h, mi, s] = mydatevec(t);
    
    % Calculate day-of-year
    d = floor(datenum(y, m, d) - datenum(y - 1, 12, 31));
end
