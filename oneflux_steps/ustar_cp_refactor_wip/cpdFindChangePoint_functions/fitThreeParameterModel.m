function [Fmax3, iCp3, xCp3, a3, a3int, yHat3, p3, Cp3] ...
    = fitThreeParameterModel(Fc3, x, y, n, pSig)
% fitThreeParameterModel
% Finds the maximum F-value in Fc3 (three-parameter model), identifies the
% change point xCp3, creates model variables, performs regression, and
% determines whether Cp3 is significant.
%
% PARAMETERS (matching original snippet's variables):
%   Fc3   - Vector of F-values for each potential breakpoint
%   x, y  - Data vectors
%   n     - Total number of observations
%   pSig  - Significance threshold for p3
%
% OUTPUTS (matching original snippet's variables):
%   Fmax3  - Maximum value in Fc3
%   iCp3   - Index of the maximum F-value
%   xCp3   - x-value at iCp3 (the change point)
%   iAbv   - Indices above iCp3
%   zAbv   - 0/1 indicator vector for points above xCp3
%   x1     - Copy of x used as a regressor
%   x2     - (x - xCp3) .* zAbv
%   a3     - Regression coefficients [intercept; slope; slope increment]
%   a3int  - Confidence intervals of regression coefficients (from regress)
%   yHat3  - Fitted values from the 3-parameter model
%   p3     - p-value from cpdFmax2pCp3 for Fmax3
%   Cp3    - Final breakpoint (NaN if p3 > pSig)

    % Find maximum of Fc3 and index
    [Fmax3, iCp3] = max(Fc3);
    
    % Define change point
    xCp3 = x(iCp3);
    
    % Indices above iCp3
    iAbv = (iCp3 + 1) : n;
    
    % Create a zero/one indicator vector for points above xCp3
    zAbv = zeros(n, 1);
    zAbv(iAbv) = 1;
    
    % Define regression variables
    x1 = x;
    x2 = (x - xCp3) .* zAbv;
    
    % Perform linear regression on [1, x1, x2]
    [a3, a3int] = regress(y, [ones(n, 1) x1 x2]);
    
    % Predicted values from the fitted model
    yHat3 = a3(1) + a3(2) * x1 + a3(3) * x2;
    
    % Compute p-value for the maximum F (user-defined function)
    p3 = cpdFmax2pCp3(Fmax3, n);
    
    % Set Cp3 (NaN if not significant)
    Cp3 = xCp3;
    if p3 > pSig
        Cp3 = NaN;
    end
end
