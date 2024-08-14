function p = cpdFmax2pCp3(Fmax, n)
    % Main function to calculate the probability p for the 3-parameter model

    % Check for invalid inputs
    if isInvalidInput(Fmax, n)
        p = NaN;
        return;
    end

    % Define the table data
    [pTable, nTable, FmaxTable] = defineTables();

    % Interpolate the critical Fmax values based on n
    FmaxCritical = interpolateFmaxCritical(n, nTable, FmaxTable);

    % Handle cases where Fmax is outside the table's range
    if Fmax < FmaxCritical(1)
        p = extrapolateLowFmax(Fmax, n, FmaxCritical(1));
    elseif Fmax > FmaxCritical(end)
        p = extrapolateHighFmax(Fmax, n, FmaxCritical(end));
    else
        % Interpolate the probability for the given Fmax
        p = interpolateProbability(Fmax, FmaxCritical, pTable);
    end
end

function isInvalid = isInvalidInput(Fmax, n)
    % Check if the input values are invalid
    isInvalid = isnan(Fmax) || isnan(n) || n < 10;
end

function [pTable, nTable, FmaxTable] = defineTables()
    % Define the pTable, nTable, and FmaxTable used for interpolation
    pTable = [0.90, 0.95, 0.99]';
    nTable = [10:10:100, 150:50:600, 800, 1000, 2500]';
    FmaxTable = [
        11.646, 15.559, 28.412;
        9.651, 11.948, 18.043;
        9.379, 11.396, 16.249;
        9.261, 11.148, 15.750;
        9.269, 11.068, 15.237;
        9.296, 11.072, 15.252;
        9.296, 11.059, 14.985;
        9.341, 11.072, 15.013;
        9.397, 11.080, 14.891;
        9.398, 11.085, 14.874;
        9.506, 11.127, 14.828;
        9.694, 11.208, 14.898;
        9.691, 11.310, 14.975;
        9.790, 11.406, 14.998;
        9.794, 11.392, 15.044;
        9.840, 11.416, 14.980;
        9.872, 11.474, 15.072;
        9.929, 11.537, 15.115;
        9.955, 11.552, 15.086;
        9.995, 11.549, 15.164;
        10.102, 11.673, 15.292;
        10.169, 11.749, 15.154;
        10.478, 12.064, 15.519
    ];
end

function FmaxCritical = interpolateFmaxCritical(n, nTable, FmaxTable)
    % Interpolate the critical Fmax values based on n
    np = size(FmaxTable, 2);
    FmaxCritical = zeros(1, np);
    for ip = 1:np
        FmaxCritical(ip) = interp1(nTable, FmaxTable(:, ip), n, 'pchip');
    end
end

function p = extrapolateLowFmax(Fmax, n, FmaxCriticalLow)
    % Handle the case where Fmax is below the table's range
    fAdj = finv(0.95, 3, n) * Fmax / FmaxCriticalLow;
    p = 2 * (1 - fcdf(fAdj, 3, n));
    p = min(p, 1); % Ensure p does not exceed 1
end

function p = extrapolateHighFmax(Fmax, n, FmaxCriticalHigh)
    % Handle the case where Fmax is above the table's range
    fAdj = finv(0.995, 3, n) * Fmax / FmaxCriticalHigh;
    p = 2 * (1 - fcdf(fAdj, 3, n));
    p = max(p, 0); % Ensure p does not go below 0
end

function p = interpolateProbability(Fmax, FmaxCritical, pTable)
    % Interpolate the probability for the given Fmax
    p = interp1(FmaxCritical, 1 - pTable, Fmax, 'pchip');
end
