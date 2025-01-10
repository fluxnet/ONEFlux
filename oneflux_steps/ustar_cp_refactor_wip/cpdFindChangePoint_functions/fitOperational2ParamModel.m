function [iAbv, Fc2] = fitOperational2ParamModel(i, n, x, y, SSERed2, Fc2)
    % fitOperational2ParamModel
    % Fit a 2-parameter model with zero slope above Cp2 (i.e., 2 connected line segments).
    %   Segment 1: slope = a2(2)
    %   Segment 2: slope = 0 for x > x(i)
    %
    % PARAMETERS (do not rename, to preserve original variable naming):
    %   i        - Index at which the second segment (flat) starts
    %   n        - Total number of points
    %   x, y     - Data vectors
    %   SSERed2  - SSE for reduced model (for comparison)
    %   nFull2   - Number of parameters in the 'full' model
    %
    % OUTPUTS:
    %   iAbv     - Indices above i
    %   x1       - Modified x with elements after i forced to x(i)
    %   a2       - Coefficients from linear regression: [intercept; slope]
    %   yHat2    - Fitted values using the 2-parameter operational model
    %   SSEFull2 - SSE for this 'full' 2-parameter model
    %   Fc2_i    - F-statistic for testing improvement of this model vs. reduced model

    % Indices above i
    nFull2 = 2;
    iAbv = (i+1):n;

    % Create modified x (x1) by setting x(iAbv) to x(i)
    x1 = x;
    x1(iAbv) = x(i);

    % Fit the model: a2(1) is intercept, a2(2) is slope for segment 1
    a2 = [ones(n,1), x1] \ y;

    % Predicted values
    yHat2 = a2(1) + a2(2)*x1;

    % SSE for the 'full' 2-parameter model
    SSEFull2 = sum((y - yHat2).^2);

    % Compute the F-statistic:
    % ( SSERed2 - SSEFull2 ) / ( SSEFull2 / (n - nFull2) )
    Fc2(i) = (SSERed2 - SSEFull2) / (SSEFull2 / (n - nFull2));
end