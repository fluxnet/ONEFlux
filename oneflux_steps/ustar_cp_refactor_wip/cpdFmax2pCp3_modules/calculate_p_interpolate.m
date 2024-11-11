function p = calculate_p_interpolate(Fmax, FmaxCritical, pTable)
    % calculate_p_interpolate calculates p using interpolation.
    p = interp1(FmaxCritical, 1 - pTable, Fmax, 'pchip');
end