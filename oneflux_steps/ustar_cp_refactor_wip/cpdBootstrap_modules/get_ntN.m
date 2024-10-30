function [ntN] = get_ntN(t, nSeasons)

    nStrataN = 4; % Local variable, used to calculate ntN
    nBins = 50;  % Local variable, used to calculate ntN

    nPerBin = get_nPerBin(t);

    % Calculate ntN based on nStrataN, nBins, and nPerBin
    nPerSeason = nStrataN * nBins * nPerBin;
    ntN = nSeasons * nPerSeason;

end