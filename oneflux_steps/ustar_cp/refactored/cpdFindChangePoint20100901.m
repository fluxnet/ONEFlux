function [Cp2, s2, Cp3, s3] = cpdFindChangePoint20100901(xx, yy, fPlot, cPlot)
    % Main function to detect change points using 2-parameter and 3-parameter models

    % Initialize output structures
    [Cp2, Cp3, s2, s3] = initializeOutputs();

    % Clean and preprocess data
    [x, y, n] = cleanData(xx, yy);
    if n < 10
        return;
    end

    % Remove extreme linear regression outliers
    [x, y, n] = removeOutliers(x, y);
    if n < 10
        return;
    end

    % Compute reduced model statistics
    [SSERed2, SSERed3] = computeReducedModelStatistics(x, y);

    % Compute F scores and find maximum for both models
    [Fc2, Fc3] = computeFMaxScores(x, y, n, SSERed2, SSERed3);

    % Identify and evaluate change points
    [Cp2, s2] = evaluateChangePoint(Fc2, x, y, n, SSERed2, '2-parameter');
    [Cp3, s3] = evaluateChangePoint(Fc3, x, y, n, SSERed3, '3-parameter');

    % Plot results if required
    if fPlot
        plotResults(x, y, Cp2, Cp3, s2, s3, cPlot);
    end
end

function [Cp2, Cp3, s2, s3] = initializeOutputs()
    % Initialize outputs to NaN and empty structures
    Cp2 = NaN;
    Cp3 = NaN;
    s2 = initializeStruct();
    s3 = initializeStruct();
end

function s = initializeStruct()
    % Initialize a structure with NaN fields
    s = struct('n', NaN, 'Cp', NaN, 'Fmax', NaN, 'p', NaN, ...
               'b0', NaN, 'b1', NaN, 'b2', NaN, 'c2', NaN, ...
               'cib0', NaN, 'cib1', NaN, 'cic2', NaN);
end

function [x, y, n] = cleanData(xx, yy)
    % Clean and reshape data, removing NaNs
    x = reshape(xx, length(xx), 1);
    y = reshape(yy, length(yy), 1);
    iNaN = isnan(x + y);
    x(iNaN) = [];
    y(iNaN) = [];
    n = length(x);
end

function [x, y, n] = removeOutliers(x, y)
    % Remove extreme outliers based on linear regression
    a = [ones(length(x), 1), x] \ y;
    yHat = a(1) + a(2) * x;
    dy = y - yHat;
    mdy = mean(dy);
    sdy = std(dy);
    ns = 4;
    iOut = abs(dy - mdy) > ns * sdy;
    x(iOut) = [];
    y(iOut) = [];
    n = length(x);
end

function [SSERed2, SSERed3] = computeReducedModelStatistics(x, y)
    % Compute the reduced model statistics for later use
    yHat2 = mean(y);
    SSERed2 = sum((y - yHat2).^2);

    a = [ones(length(x), 1), x] \ y;
    yHat3 = a(1) + a(2) * x;
    SSERed3 = sum((y - yHat3).^2);
end

function [Fc2, Fc3] = computeFMaxScores(x, y, n, SSERed2, SSERed3)
    % Compute F scores for all possible change points
    Fc2 = NaN(n, 1);
    Fc3 = NaN(n, 1);

    nEndPtsN = 3;
    nEndPts = max(floor(0.05 * n), nEndPtsN);

    for i = 1:(n - 1)
        Fc2(i) = calculateFScore2(x, y, i, n, SSERed2);
        Fc3(i) = calculateFScore3(x, y, i, n, SSERed3);
    end
end

function Fc2 = calculateFScore2(x, y, i, n, SSERed2)
    % Calculate the F score for the 2-parameter model
    iAbv = (i + 1):n;
    x1 = x;
    x1(iAbv) = x(i);
    a2 = [ones(n, 1), x1] \ y;
    SSEFull2 = sum((y - (a2(1) + a2(2) * x1)).^2);
    Fc2 = (SSERed2 - SSEFull2) / (SSEFull2 / (n - 2));
end

function Fc3 = calculateFScore3(x, y, i, n, SSERed3)
    % Calculate the F score for the 3-parameter model
    iAbv = (i + 1):n;
    zAbv = zeros(n, 1);
    zAbv(iAbv) = 1;
    x1 = x;
    x2 = (x - x(i)) .* zAbv;
    a3 = [ones(n, 1), x1, x2] \ y;
    SSEFull3 = sum((y - (a3(1) + a3(2) * x1 + a3(3) * x2)).^2);
    Fc3 = (SSERed3 - SSEFull3) / (SSEFull3 / (n - 3));
end

function [Cp, s] = evaluateChangePoint(Fc, x, y, n, SSERed, modelType)
    % Identify and evaluate change points from Fmax scores
    [Fmax, iCp] = max(Fc);
    xCp = x(iCp);
    pSig = 0.05;
    Cp = xCp;

    if strcmp(modelType, '2-parameter')
        [a, aInt, p] = evaluateModel2(x, y, iCp, n, Fmax, SSERed);
    else
        [a, aInt, p] = evaluateModel3(x, y, iCp, n, Fmax, SSERed);
    end

    if p > pSig
        Cp = NaN;
    end

    s = assignStructValues(a, aInt, Cp, Fmax, p, modelType, n);
end

function [a, aInt, p] = evaluateModel2(x, y, iCp, n, Fmax, SSERed)
    % Evaluate the 2-parameter model and compute significance
    iAbv = (iCp + 1):n;
    x1 = x;
    x1(iAbv) = x(iCp);
    [a, aInt] = regress(y, [ones(n, 1), x1]);
    p = cpdFmax2pCp2(Fmax, n);
end

function [a, aInt, p] = evaluateModel3(x, y, iCp, n, Fmax, SSERed)
    % Evaluate the 3-parameter model and compute significance
    iAbv = (iCp + 1):n;
    zAbv = zeros(n, 1);
    zAbv(iAbv) = 1;
    x1 = x;
    x2 = (x - x(iCp)) .* zAbv;
    [a, aInt] = regress(y, [ones(n, 1), x1, x2]);
    p = cpdFmax2pCp3(Fmax, n);
end

function s = assignStructValues(a, aInt, Cp, Fmax, p, modelType, n)
    % Assign values to the output structure
    s = initializeStruct();
    s.n = n;
    s.Cp = Cp;
    s.Fmax = Fmax;
    s.p = p;
    s.b0 = a(1);
    s.cib0 = 0.5 * diff(aInt(1, :));

    if strcmp(modelType, '2-parameter')
        s.b1 = a(2);
        s.cib1 = 0.5 * diff(aInt(2, :));
    else
        s.b1 = a(2);
        s.cib1 = 0.5 * diff(aInt(2, :));
        s.b2 = a(3);
        s.cic2 = 0.5 * diff(aInt(3, :));
        s.c2 = a(2) + a(3);
    end
end

function plotResults(x, y, Cp2, Cp3, s2, s3, cPlot)
    % Plot the results of the change-point detection
    cla;
    hold on;
    plot(x, y, 'ko', 'MarkerFaceColor', 'k');

    if ~isnan(Cp2)
        yHat2 = s2.b0 + s2.b1 * x;
        plot(x, yHat2, 'r-', 'linewidth', 2);
        plot([Cp2, Cp2], [min(y), max(y)], 'r-', 'linewidth', 2);
    end

    if ~isnan(Cp3)
        yHat3 = s3.b0 + s3.b1 * x + s3.b2 * (x - Cp3);
        plot(x, yHat3, 'g-', 'linewidth', 2);
        plot([Cp3, Cp3], [min(y), max(y)], 'g-', 'linewidth', 2);
    end

    hold off;
    grid on;
    box on;
    title(sprintf('%s %5.3f %s', cPlot, Cp2, 'D'));
    set(gca, 'FontSize', 10);
end
