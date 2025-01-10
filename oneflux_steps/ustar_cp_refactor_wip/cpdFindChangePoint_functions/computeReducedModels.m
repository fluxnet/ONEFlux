function [SSERed2, SSERed3] = computeReducedModels(x, y, n)
% computeReducedModels
% Compute statistics of reduced (null hypothesis) models
% for later testing of Cp2 and Cp3 significance.
%
% INPUTS:
%   x - independent variable (vector)
%   y - dependent variable (vector)
%   n - number of data points
%
% OUTPUTS:
%   yHat2   - mean(y), predicted value for the reduced model with only an intercept
%   SSERed2 - sum of squared errors for reduced model (only intercept)
%   a       - linear regression coefficients [intercept; slope]
%   yHat3   - predicted values from the linear model a(1) + a(2)*x
%   SSERed3 - sum of squared errors for the reduced model with intercept & slope
%   nRed2   - number of parameters in the reduced model 2 (1)
%   nFull2  - number of parameters in the full model 2 (2)
%   nRed3   - number of parameters in the reduced model 3 (2)
%   nFull3  - number of parameters in the full model 3 (3)
%

% 1) Reduced model with only mean (intercept)
yHat2   = mean(y);
SSERed2 = sum((y - yHat2).^2);

% 2) Reduced model with intercept + slope
a       = [ones(n,1), x] \ y;   % a(1) is intercept, a(2) is slope
yHat3   = a(1) + a(2) * x;
SSERed3 = sum((y - yHat3).^2);

end