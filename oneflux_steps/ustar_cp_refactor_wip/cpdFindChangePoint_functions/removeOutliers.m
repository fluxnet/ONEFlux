function [x, y] = removeOutliers(x, y, n)
    % Seems to be a bug here since outliers are detected in data which is the same to several decimal places
    % removeOutliers
    % Fits a simple linear model to (x, y), computes residuals, and removes
    % outliers beyond ns standard deviations from the mean residual.

    % Perform linear regression
    a = [ones(n,1) x] \ y;    % a(1) is intercept, a(2) is slope

    % Predicted values
    yHat = a(1) + a(2)*x;

    % Residuals
    dy = y - yHat;

    % Mean and std of residuals
    mdy = mean(dy);
    sdy = std(dy);

    % Number of std-dev multiples to define an outlier
    ns = 4;

    % Indices of outliers
    iOut = find(abs(dy - mdy) > ns * sdy);

    % Remove outliers from x and y
    x(iOut) = [];
    y(iOut) = [];
end

