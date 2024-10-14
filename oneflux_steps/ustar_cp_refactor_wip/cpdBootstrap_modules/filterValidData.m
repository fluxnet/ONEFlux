function [itNee, ntNee] = filterValidData(NEE, uStar, T, iNight)
    % Filter valid data based on non-NaN values and nighttime condition
    itNee = find(~isnan(NEE + uStar + T));
    itNee = intersect(itNee, iNight);
    ntNee = length(itNee);
end