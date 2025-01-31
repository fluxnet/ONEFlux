function [s2] = updateS2(a2, a2int, Cp2, Fmax2, p2, s2)
    % updateS2
    %   Uses regression coefficients (a2, a2int) and other parameters (Cp2, Fmax2, p2)
    %   to compute b0, cib0, b1, cib1 and update the fields of s2.
    %
    %   PARAMETERS (no renaming):
    %       a2     - Regression coefficients vector
    %       a2int  - Confidence intervals for those coefficients
    %       Cp2    - Change point for two-parameter model
    %       Fmax2  - Maximum F-value for two-parameter model
    %       p2     - p-value corresponding to Fmax2
    %
    %   OUTPUTS (no renaming):
    %       b0, cib0 - Intercept and its half-width confidence interval
    %       b1, cib1 - Slope and its half-width confidence interval
    %       s2       - Struct with updated fields
    
        % Extract intercept and half-width of its confidence interval
        b0    = a2(1);
        cib0  = 0.5 * diff(a2int(1, :));
    
        % Extract slope and half-width of its confidence interval
        b1    = a2(2);
        cib1  = 0.5 * diff(a2int(2, :));
    
        % Update s2 fields
        s2.Cp   = Cp2;
        s2.Fmax = Fmax2;
        s2.p    = p2;
        s2.b0   = b0;
        s2.b1   = b1;
        s2.b2   = NaN;
        s2.c2   = NaN;
        s2.cib0 = cib0;
        s2.cib1 = cib1;
        s2.cic2 = NaN;
    end
    