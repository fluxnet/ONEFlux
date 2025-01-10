function [s3] = updateS3(a3, a3int, xCp3, Fmax3, p3, s3)
    % updateS3
    %   Extracts parameters from a3, a3int and updates the struct s3.
    %
    %   PARAMETERS (matching original snippet's variable names):
    %       a3     - Regression coefficients [b0; b1; b2]
    %       a3int  - Confidence intervals for those coefficients
    %       xCp3   - Change point for the 3-parameter model
    %       Fmax3  - Maximum F-value for the 3-parameter model
    %       p3     - p-value corresponding to Fmax3
    %
    %   OUTPUTS (matching original snippet's variable names):
    %       b0, cib0 - Intercept and half-width of its confidence interval
    %       b1, cib1 - First slope parameter and half-width of its CI
    %       b2, cic2 - Second slope increment and half-width of its CI
    %       c2       - Combined slope = b1 + b2
    %       s3       - Struct with all relevant fields
    
        % Intercept and half-width confidence interval
        b0   = a3(1);
        cib0 = 0.5 * diff(a3int(1, :));
    
        % First slope and half-width confidence interval
        b1   = a3(2);
        cib1 = 0.5 * diff(a3int(2, :));
    
        % Second slope increment and half-width confidence interval
        b2   = a3(3);
        cic2 = 0.5 * diff(a3int(3, :));
    
        % Combined slope
        c2 = a3(2) + a3(3);
    
        % Populate s3 struct
        s3.Cp   = xCp3;
        s3.Fmax = Fmax3;
        s3.p    = p3;
        s3.b0   = b0;
        s3.b1   = b1;
        s3.b2   = b2;
        s3.c2   = c2;
        s3.cib0 = cib0;
        s3.cib1 = cib1;
        s3.cic2 = cic2;
    end
    