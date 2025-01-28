function [Fc3] = fitOperational3ParamModel( ...
    i, iAbv, n, x, y, SSERed3, Fc3)
% fitOperational3ParamModel
%   Fits a 3-parameter model representing two connected line segments:
%     Segment 1: slope = a3(2)
%     Segment 2: slope = a3(2) + a3(3), but zero shift until x > x(i)
%
%   The function directly uses the variable names from the original snippet.
%
%   PARAMETERS (do not rename, to preserve original variable naming):
%     i        - current index marking the "pivot" x(i)
%     iAbv     - vector of indices above i (e.g., i+1:n)
%     n        - total number of data points
%     x, y     - data vectors
%     SSERed3  - SSE for the reduced model (for comparison)
%     nFull3   - number of parameters in the 'full' 3-parameter model
%
%   OUTPUTS:
%     zAbv     - zero/one indicator vector of length n (1 where x > x(i))
%     x1       - the original x (used as a regressor)
%     x2       - (x - x(i)) * zAbv
%     a3       - regression coefficients [intercept; slope; slope increment]
%     yHat3    - fitted values using the 3-parameter model
%     SSEFull3 - SSE of the 3-parameter model
%     Fc3_i    - F-statistic for testing improvement vs. SSERed3

    nFull3 = 3;
    % Create a zero/one indicator for points above x(i)
    zAbv = zeros(n,1);
    zAbv(iAbv) = 1;

    % Define x1 and x2 for the segmented model
    x1 = x;
    x2 = (x - x(i)) .* zAbv;

    % Fit the 3-parameter model
    % A = [ones(n,1) x1 x2];
    a3 = [ones(n,1) x1 x2] \ y;

    % Predicted values
    yHat3 = a3(1) + a3(2)*x1 + a3(3)*x2;

    % Full model SSE
    SSEFull3 = sum((y - yHat3).^2);
    % Compute F-statistic
    % Fc3 = a3;
    Fc3(i) = (SSERed3 - SSEFull3) / (SSEFull3 / (n - nFull3));
    % Fc3 =a3;
end
