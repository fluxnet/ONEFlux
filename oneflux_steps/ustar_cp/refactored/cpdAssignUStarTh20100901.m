function [CpA,nA,tW,CpW,cMode,cFailure,fSelect,sSine,FracSig,FracModeD,FracSelect] = cpdAssignUStarTh20100901(Stats, fPlot, cSiteYr)
    % Main function to aggregate and assign uStarTh from the Stats structure

    % Initialize outputs
    [CpA, nA, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect] = initializeOutputs();

    % Determine dimensions of the Stats structure
    [nWindows, nStrata, nBoot, nDim, nSelectN] = computeWindowSizes(Stats);

    if isempty(nDim)
        cFailure = 'Stats must be 2D or 3D.';
        return;
    end

    % Extract necessary fields from the Stats structure
    [xmt, xCp, b1, c2, cib1, cic2, p] = extractFields(Stats);

    % Determine the model type (2-parameter or 3-parameter)
    [nPar, c2, cic2] = determineModelType(c2, b1);

    % Classify and select significant change points
    [fP, iSelect, cMode, fSelect, FracSig, FracModeD, FracSelect, cFailure] = classifyAndSelectChangePoints(xmt, xCp, b1, c2, p, nPar);

    if ~isempty(cFailure)
        return;
    end

    % Aggregate the selected change points into seasonal and annual values
    [CpA, nA, tW, CpW] = aggregateChangePoints(xmt, xCp, iSelect, fSelect, nWindows, nStrata, nBoot, nDim);

    % Fit an annual sine curve to the selected data
    sSine = fitAnnualSineCurve(mt(iSelect), Cp(iSelect));

    % Plot results if required
    if fPlot
        plotResults(xmt, xCp, iSelect, tW, CpW, sSine, cMode, cSiteYr, nPar, nSelect, FracSig, FracModeD, FracSelect);
    end
end

function [CpA, nA, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect] = initializeOutputs()
    % Initialize output variables
    CpA = [];
    nA = [];
    tW = [];
    CpW = [];
    fSelect = [];
    cMode = '';
    cFailure = '';
    sSine = [];
    FracSig = [];
    FracModeD = [];
    FracSelect = [];
end

function [nWindows, nStrata, nBoot, nDim, nSelectN] = computeWindowSizes(Stats)
    % Determine dimensions and calculate selection parameters
    nDim = ndims(Stats);

    switch nDim
        case 2
            [nWindows, nBoot] = size(Stats);
            nStrata = 1;
            nStrataN = 0.5;
        case 3
            [nWindows, nStrata, nBoot] = size(Stats);
            nStrataN = 1;
        otherwise
            nDim = [];
            return;
    end

    nWindowsN = 4;
    nSelectN = nWindowsN * nStrataN * nBoot;
end

function [xmt, xCp, b1, c2, cib1, cic2, p] = extractFields(Stats)
    % Extract and reshape necessary fields from the Stats structure
    cVars = {'mt', 'Cp', 'b1', 'c2', 'cib1', 'cic2', 'p'};
    nVars = length(cVars);

    for i = 1:nVars
        cv = char(cVars(i));
        eval([cv '=fcReadFields(Stats,''' cv ''');']);
        eval([cv '=fcx2colvec(' cv ');']);
    end
end

function [nPar, c2, cic2] = determineModelType(c2, b1)
    % Determine if the model is 2-parameter or 3-parameter
    nPar = 3;
    if sum(~isnan(c2)) == 0
        nPar = 2;
        c2 = 0 * b1;
        cic2 = c2;
    end
end

function [fP, iSelect, cMode, fSelect, FracSig, FracModeD, FracSelect, cFailure] = classifyAndSelectChangePoints(xmt, xCp, b1, c2, p, nPar)
    % Classify change points and select the primary mode
    pSig = 0.05;
    fP = p <= pSig;

    iTry = find(~isnan(xmt));
    nTry = length(iTry);

    iModeE = find(fP == 1 & b1 < c2);
    iModeD = find(fP == 1 & b1 >= c2);
    nModeE = length(iModeE);
    nModeD = length(iModeD);

    if nModeD >= nModeE
        iSelect = iModeD;
        cMode = 'D';
    else
        iSelect = iModeE;
        cMode = 'E';
    end

    nSelect = length(iSelect);

    fSelect = false(size(fP));
    fSelect(iSelect) = true;

    FracSig = sum(fP) / nTry;
    FracModeD = nModeD / sum(fP);
    FracSelect = nSelect / nTry;

    if FracSelect < 0.10
        cFailure = 'Less than 10% successful detections.';
    else
        cFailure = '';
    end

    % Exclude outliers based on regression stats
    [iSelect, fSelect, nModeD, nModeE] = excludeOutliers(xCp, b1, c2, cib1, cic2, iSelect, fSelect, nModeD, nModeE, nPar);
end

function [iSelect, fSelect, nModeD, nModeE] = excludeOutliers(xCp, b1, c2, cib1, cic2, iSelect, fSelect, nModeD, nModeE, nPar)
    % Exclude outliers from selected change points
    switch nPar
        case 2
            x = [xCp, b1, cib1];
        case 3
            x = [xCp, b1, c2, cib1, cic2];
    end

    mx = nanmedian(x);
    sx = fcNaniqr(x);
    xNorm = (x - mx) ./ sx;
    xNormX = max(abs(xNorm), [], 2);
    ns = 5;

    fOut = xNormX > ns;
    iOut = find(fOut);

    iSelect = setdiff(iSelect, iOut);
    fSelect = ~fOut & fSelect;
    nModeD = sum(fSelect & b1 >= c2);
    nModeE = sum(fSelect & b1 < c2);
end

function [CpA, nA, tW, CpW] = aggregateChangePoints(xmt, xCp, iSelect, fSelect, nWindows, nStrata, nBoot, nDim)
    % Aggregate selected change points into seasonal and annual values
    xCpSelect = NaN(size(xCp));
    xCpSelect(iSelect) = xCp(iSelect);
    xCpGF = xCpSelect;

    switch nDim
        case 2
            CpA = fcx2colvec(nanmean(xCpGF));
            nA = fcx2colvec(sum(~isnan(xCpSelect)));
        case 3
            CpA = fcx2colvec(nanmean(reshape(xCpGF, nWindows * nStrata, nBoot)));
            nA = fcx2colvec(sum(~isnan(reshape(xCpSelect, nWindows * nStrata, nBoot))));
    end

    nW = nanmedian(sum(~isnan(reshape(xmt, nWindows, nStrata * nBoot))));
    [mtSelect, i] = sort(xmt(iSelect));
    CpSelect = xCp(iSelect(i));
    xBins = prctile(mtSelect, 0:(100 / nW):100);
    [~, tW, CpW] = fcBin(mtSelect, CpSelect, xBins, 0);
end

function sSine = fitAnnualSineCurve(mt, Cp)
    % Fit an annual sine curve to the selected data
    bSine = [1, 1, 1];
    bSine = nlinfit(mt, Cp, 'fcEqnAnnualSine', bSine);
    yHat = fcEqnAnnualSine(bSine, mt);
    r2 = fcr2Calc(Cp, yHat);

    if bSine(2) < 0
        bSine(2) = -bSine(2);
        bSine(3) = bSine(3) + 365.25 / 2;
    end

    bSine(3) = mod(bSine(3), 365.25);
    sSine = [fcx2rowvec(bSine), r2];
end

function plotResults(xmt, xCp, iSelect, tW, CpW, sSine, cMode, cSiteYr, nPar, nSelect, FracSig, FracModeD, FracSelect)
    % Plot the results of the analysis
    FracSelectByWindow = sum(reshape(~isnan(xCpGF), nWindows, nStrata * nBoot), 2) ./ sum(reshape(~isnan(xmt), nWindows, nStrata * nBoot), 2);
    mtByWindow = nanmean(reshape(xmt, nWindows, nStrata * nBoot), 2);

    fcFigLoc(1, 0.5, 0.45, 'NE');

    subplot('position', [0.08, 0.56, 0.60, 0.38]);
    hold on;
    box on;
    plot(mt, Cp, 'r.', mt(iModeE), Cp(iModeE), 'b.', mt(iModeD), Cp(iModeD), 'g.');

    nBins = nWindows;

    if nModeD >= nBins * 30
        [~, mx, my] = fcBin(mt(iModeD), Cp(iModeD), [], round(nModeD / nBins));
        hold on;
        plot(mx, my, 'ko-', 'MarkerFaceColor', 'y', 'MarkerSize', 8, 'LineWidth', 2);
    end

    if nModeE >= nBins * 30
        [~, mx, my] = fcBin(mt(iModeE), Cp(iModeE), [], round(nModeE / nBins));
        hold on;
        plot(mx, my, 'bo-', 'MarkerFaceColor', 'c', 'MarkerSize', 8, 'LineWidth', 2);
    end

    fcDatetick(mt, 'Mo', 4, 1);
    ylabel('Cp');
    ylabel('Raw Cp Modes D (green) E (red)');
    ylim([0, prctile(Cp, 99.9)]);
    hold off;

    title(sprintf('%s  Stats%g  Mode%s  nSelect/nTry: %g/%g  uStarTh: %5.3f (%5.3f) ', ...
        cSiteYr, nPar, cMode, nSelect, nTry, ...
        nanmedian(Cp(iSelect)), 0.5 * diff(prctile(Cp(iSelect), [2.5, 97.5]))));

    subplot('position', [0.08, 0.06, 0.60, 0.38]);
    hold on;
    box on;
    plot(mt(iSelect), Cp(iSelect), 'k.', mtHat, CpHat, 'r-', 'LineWidth', 3);
    plot(tW, CpW, 'ro', 'MarkerFaceColor', 'y', 'MarkerSize', 9, 'LineWidth', 2);
    fcDatetick(mt(iSelect), 'Mo', 4, 1);
    ylabel('Select Cp');
    ylim([0, prctile(Cp(iSelect), 99)]);

    title(sprintf('Cp = %5.3f + %5.3f sin(wt - %3.0f) (r^2 = %5.3f) ', bSine, r2));

    subplot('position', [0.76, 0.56, 0.22, 0.38]);
    hist(CpA, 30);
    grid on;
    box on;
    xlim([min(CpA), max(CpA)]);
    xlabel('Annual \itu_*^{Th}');
    ylabel('Frequency');
    title(sprintf('Median (CI): %5.3f (%5.3f) ', nanmedian(CpA), 0.5 * diff(prctile(CpA, [2.5, 97.5]))));

    subplot('position', [0.76, 0.06, 0.22, 0.38]);
    plot(mtByWindow, FracSelectByWindow, 'o-');
    fcDatetick(mtByWindow, 'Mo', 4, 1);
    ylabel('FracSelectByWindow');
    ylim([0, 1]);
end
