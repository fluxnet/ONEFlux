function [Cp2, Cp3, Stats2, Stats3] = initializeOutputs(nSeasons, nStrataX, nBoot, StatsMT)
    % Initialize output matrices
    Cp2 = NaN * ones(nSeasons, nStrataX, nBoot);
    Cp3 = NaN * ones(nSeasons, nStrataX, nBoot);
    
    Stats2 = repmat(StatsMT, [nSeasons, nStrataX, nBoot]);
    Stats3 = repmat(StatsMT, [nSeasons, nStrataX, nBoot]);
end