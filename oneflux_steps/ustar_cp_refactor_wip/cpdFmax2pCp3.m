function p = cpdFmax2pCp3(Fmax, n)
    % cpdFmax2pCp3 calculates the probability p that the 3-parameter
    % diagnostic change-point model fit is significant.

    % Validate inputs
    if ~validate_inputs(Fmax, n)
        p = NaN;
        return;
    end

    % Get data tables
    pTable = get_pTable();
    nTable = get_nTable();
    FmaxTable = get_FmaxTable();

    % Interpolate critical Fmax values
    FmaxCritical = interpolate_FmaxCritical(n, nTable, FmaxTable);

    % Calculate p based on Fmax comparison
    if Fmax < FmaxCritical(1)
        p = calculate_p_low(Fmax, FmaxCritical(1), n);
    elseif Fmax > FmaxCritical(3)
        p = calculate_p_high(Fmax, FmaxCritical(3), n);
    else
        p = calculate_p_interpolate(Fmax, FmaxCritical, pTable);
    end
end
