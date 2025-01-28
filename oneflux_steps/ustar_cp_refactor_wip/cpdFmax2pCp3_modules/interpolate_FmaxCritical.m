function FmaxCritical = interpolate_FmaxCritical(n, pTableSize, nTable, FmaxTable)
    % interpolate_FmaxCritical interpolates critical Fmax values for the given n.
    FmaxCritical = zeros(1, pTableSize);
    for ip = 1:pTableSize
        FmaxCritical(ip) = interp1(nTable, FmaxTable(:, ip), n, 'pchip');
    end
end