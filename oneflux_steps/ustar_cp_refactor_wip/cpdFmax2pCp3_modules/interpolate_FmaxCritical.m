function FmaxCritical = interpolate_FmaxCritical(n, nTable, FmaxTable)
    % interpolate_FmaxCritical interpolates critical Fmax values for the given n.
    FmaxCritical = zeros(1, 3);
    for ip = 1:3
        FmaxCritical(ip) = interp1(nTable, FmaxTable(:, ip), n, 'pchip');
    end
end