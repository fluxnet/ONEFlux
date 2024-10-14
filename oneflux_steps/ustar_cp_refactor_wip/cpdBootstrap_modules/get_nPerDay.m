function [nPerDay] = get_nPerDay(t)
    nPerDay = round(1/nanmedian(diff(t)));
end