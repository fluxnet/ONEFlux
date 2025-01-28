function p = calculate_p_low(lowerP, Fmax, FmaxCritical_low, n)
    % calculate_p_low calculates p when Fmax is below the lowest critical value.
    fAdj = finv(lowerP, 3, n) * Fmax / FmaxCritical_low;
    p = 2 * (1 - fcdf(fAdj, 3, n));
    p = min(p, 1);
end