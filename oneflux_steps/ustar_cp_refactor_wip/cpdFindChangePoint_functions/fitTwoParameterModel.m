function [Fmax2, iCp2, xCp2, a2, a2int, yHat2, p2, Cp2] = fitTwoParameterModel(Fc2, x, y, n, pSig)
    % fitTwoParameterModel
    % Finds the maximum F-value, corresponding index, computes the piecewise
    % model, and determines statistical significance of the change point Cp2.
    %
    % PARAMETERS (no variable name changes from original snippet):
    %   Fc2   - Vector of F-values for each potential breakpoint
    %   x, y  - Data vectors
    %   n     - Total number of observations
    %   pSig  - Significance threshold for p2
    %
    % OUTPUTS (matching original variable names):
    %   Fmax2    - Maximum F-value found in Fc2
    %   iCp2     - Index at which Fmax2 occurs
    %   xCp2     - Value of x at iCp2
    %   iAbv     - Indices above iCp2
    %   x1       - Modified x with values at iAbv set to xCp2
    %   a2       - Regression coefficients from [ones(n,1) x1]\y
    %   a2int    - 95% confidence intervals of regression coefficients (from regress)
    %   yHat2    - Fitted values for the two-parameter (piecewise) model
    %   p2       - p-value computed via cpdFmax2pCp2
    %   Cp2      - Final breakpoint; set to xCp2 if p2 <= pSig, else NaN
    
        % Find maximum value of Fc2 and corresponding index
        [Fmax2, iCp2] = max(Fc2);
        
        % Define breakpoint as x(iCp2)
        xCp2 = x(iCp2);
        
        % Indices above iCp2
        iAbv = (iCp2+1):n;
        
        % Create x1: force values beyond iCp2 to xCp2
        x1 = x;
        x1(iAbv) = xCp2;
        
        % Perform linear regression on modified x1
        [a2, a2int] = regress(y, [ones(n,1) x1]);
        
        % Compute fitted values
        yHat2 = a2(1) + a2(2)*x1;
        
        % Compute p-value for Fmax2 (user-defined function cpdFmax2pCp2)
        p2 = cpdFmax2pCp2(Fmax2, n);
        
        % Decide if Cp2 is significant
        Cp2 = xCp2;
        if p2 > pSig
            Cp2 = NaN;
        end
    end
    