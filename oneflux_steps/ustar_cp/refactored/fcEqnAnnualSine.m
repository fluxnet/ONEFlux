function y = fcEqnAnnualSine(b, t)
    % fcEqnAnnualSine Computes the value of an annual sine function.
    % Input:
    %   b - Coefficients [b0, b1, b2]
    %   t - Time vector
    % Output:
    %   y - Resulting values of the sine function

    % Calculate number of days per year
    nDaysPerYr = datenum(2000, 12, 31) / 2000;
    
    % Frequency of the annual sine function
    Omega = 2 * pi / nDaysPerYr;
    
    % Compute the sine function values
    y = b(1) + b(2) * sin(Omega * (t - b(3)));
end
