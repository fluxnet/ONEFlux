function p = cpdFmax2pCp3(Fmax, n)
    assigns the probability p that the 3-parameter, 
    %	diagnostic change-point model fit is significant. 
    %
    %	It interpolates within a Table pTable, generated 
    %	for the 3-parameter model by Wang (2003).  
    %
    %	If Fmax is outside the range in the table, 
    %	then the normal F stat is used to help extrapolate. 

    %	Functions called: stats toolbox - fcdf, finv

    %	Originally written by Alan Barr April 2010

    %	=======================================================================
    %	=======================================================================

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
