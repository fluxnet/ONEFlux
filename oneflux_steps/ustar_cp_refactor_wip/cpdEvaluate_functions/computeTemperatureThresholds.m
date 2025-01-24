function TTh = computeTemperatureThresholds(T, itSeason, nStrata)
    TTh = prctile(T(itSeason), 0:(100 / nStrata):100);
end