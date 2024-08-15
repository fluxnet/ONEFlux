function p = cpdFmax2pCp2(Fmax, n)
    % Main function to calculate the probability p for the 2-parameter model

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
    pTable = [0.80, 0.90, 0.95, 0.99]';
    nTable = [10, 15, 20, 30, 50, 70, 100, 150, 200, 300, 500, 700, 1000]';
    FmaxTable = [
        3.9293, 6.2992, 9.1471, 18.2659;
        3.7734, 5.6988, 7.8770, 13.8100;
        3.7516, 5.5172, 7.4426, 12.6481;
        3.7538, 5.3224, 7.0306, 11.4461;
        3.7941, 5.3030, 6.8758, 10.6635;
        3.8548, 5.3480, 6.8883, 10.5026;
        3.9798, 5.4465, 6.9184, 10.4527;
        4.0732, 5.5235, 6.9811, 10.3859;
        4.1467, 5.6136, 7.0624, 10.5596;
        4.2770, 5.7391, 7.2005, 10.6871;
        4.4169, 5.8733, 7.3421, 10.6751;
        4.5556, 6.0591, 7.5627, 11.0072;
        4.7356, 6.2738, 7.7834, 11.2319
    ];
end

function FmaxCritical = interpolateFmaxCritical(n, nTable, FmaxTable)
    % Interpolate the critical Fmax values based on n
    np = length(FmaxTable(1, :));
    FmaxCritical = zeros(1, np);
    for ip = 1:np
        FmaxCritical(ip) = interp1(nTable, FmaxTable(:, ip), n, 'pchip');
    end
end

function p = extrapolateLowFmax(Fmax, n, FmaxCriticalLow)
    % Handle the case where Fmax is below the table's range
    fAdj = finv(0.90, 3, n) * Fmax / FmaxCriticalLow;
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
