function jtSeason = computeSeasonIndices(iSeason, nSeasons, nPerSeason, ntAnnual)
	switch iSeason
        case 1
            jtSeason = 1:nPerSeason;
        case nSeasons
            jtSeason = ((nSeasons - 1) * nPerSeason + 1):ntAnnual;
        otherwise
            jtSeason = ((iSeason - 1) * nPerSeason + 1):(iSeason * nPerSeason);
    end
end