function p = calculate_p_interpolate(Fmax, FmaxCritical, pTable)
    p = interp1(FmaxCritical, 1 - pTable, Fmax, 'pchip');
end
