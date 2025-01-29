function nStrata = computeStrataCount(ntSeason, nBins, nPerBin, nStrataN, nStrataX)
    nStrata = floor(ntSeason / (nBins * nPerBin));
    nStrata = max(nStrata, nStrataN); % Ensure minimum strata count
    nStrata = min(nStrata, nStrataX); % Enforce maximum strata count
end