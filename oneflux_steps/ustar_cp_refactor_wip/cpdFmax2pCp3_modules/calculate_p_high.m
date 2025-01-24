function p = calculate_p_high(Fmax, FmaxCritical_high, n)
    % calculate_p_high calculates p when Fmax is above the highest critical value.
    fAdj = finv(0.995, 3, n) * Fmax / FmaxCritical_high;
    p = 2 * (1 - fcdf(fAdj, 3, n));
    p = max(p, 0);
end