function t = createTimeArray(uStar)
    nrPerDay = mod(numel(uStar),365);
    if nrPerDay == 0; nrPerDay = mod(numel(uStar),364);end
    t = 1 + (1 / nrPerDay);
    for n2 = 2:numel(uStar); t(n2,1) = t(n2-1,1)+ (1 / nrPerDay);end
    clear n2
end
