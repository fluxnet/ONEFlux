function isValid = validate_inputs(Fmax, n)
    % validate_inputs checks if Fmax and n are valid inputs.
    isValid = ~(isnan(Fmax) || isnan(n) || n < 10);
end