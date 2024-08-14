function [Cp2, Stats2, Cp3, Stats3] = cpdEvaluateUStarTh4Season20100901(t, NEE, uStar, T, fNight, fPlot, cSiteYr)
    % Main function for evaluating uStarTh for a site-year of data using change-point detection
    
    % Initial data preparation
    [nt, nPerDay, itAnnual, ntAnnual, EndDOY] = initializeData(t, NEE, uStar, T, fNight);
    
    % Initialize output matrices and Stats structures
    [Cp2, Cp3, Stats2, Stats3, StatsMT] = initializeOutputs(ntAnnual);
    
    % If there are not enough data points, return early
    if ntAnnual < numDataPointsRequired(nPerDay)
        return;
    end
    
    % Reorder data so that December is at the beginning of the year
    [t, T, uStar, NEE, fNight] = reorderData(t, T, uStar, NEE, fNight, EndDOY);
    
    % Perform stratification and change-point detection
    [Cp2, Stats2, Cp3, Stats3] = performStratificationAndDetection(t, NEE, uStar, T, fNight, StatsMT, ntAnnual, nPerDay, fPlot, cSiteYr);
end

function [nt, nPerDay, itAnnual, ntAnnual, EndDOY] = initializeData(t, NEE, uStar, T, fNight)
    % Initialize and preprocess data, calculate necessary parameters
    nt = length(t);
    nPerDay = round(1/nanmedian(diff(t)));
    [y, m, d] = fcDatevec(t);
    iYr = median(y);
    EndDOY = fcDoy(datenum(iYr, 12, 31.5));
    
    % Filter out invalid uStar values
    uStar(uStar < 0 | uStar > 3) = NaN;
    
    % Find indices of valid nighttime data points
    itAnnual = find(fNight == 1 & ~isnan(NEE + uStar + T));
    ntAnnual = length(itAnnual);
end

function [Cp2, Cp3, Stats2, Stats3, StatsMT] = initializeOutputs(ntAnnual)
    % Initialize output matrices and Stats structures
    nSeasons = 4;
    nStrataX = 8;
    
    Cp2 = NaN(nSeasons, nStrataX);
    Cp3 = NaN(nSeasons, nStrataX);
    
    StatsMT = initializeStatsMT();
    Stats2 = repmat(StatsMT, nSeasons, nStrataX);
    Stats3 = repmat(StatsMT, nSeasons, nStrataX);
end

function StatsMT = initializeStatsMT()
    % Initialize the template for Stats structure with NaN values
    StatsMT.n = NaN;
    StatsMT.Cp = NaN;
    StatsMT.Fmax = NaN;
    StatsMT.p = NaN;
    StatsMT.b0 = NaN;
    StatsMT.b1 = NaN;
    StatsMT.b2 = NaN;
    StatsMT.c2 = NaN;
    StatsMT.cib0 = NaN;
    StatsMT.cib1 = NaN;
    StatsMT.cic2 = NaN;
    StatsMT.mt = NaN;
    StatsMT.ti = NaN;
    StatsMT.tf = NaN;
    StatsMT.ruStarVsT = NaN;
    StatsMT.puStarVsT = NaN;
    StatsMT.mT = NaN;
    StatsMT.ciT = NaN;
end

function nN = numDataPointsRequired(nPerDay)
    % Calculate the number of data points required for the analysis
    nSeasons = 4;
    nStrataN = 4;
    nBins = 50;
    nPerBin = 5;
    if nPerDay == 24
        nPerBin = 3;
    elseif nPerDay == 48
        nPerBin = 5;
    end
    nPerSeasonN = nStrataN * nBins * nPerBin;
    nN = nSeasons * nPerSeasonN;
end

function [t, T, uStar, NEE, fNight] = reorderData(t, T, uStar, NEE, fNight, EndDOY)
    % Reorder data to move December to the beginning of the year
    [~, m, ~] = fcDatevec(t);
    itD = find(m == 12);
    itReOrder = [min(itD):length(t), 1:(min(itD) - 1)];
    t(itD) = t(itD) - EndDOY;
    t = t(itReOrder);
    T = T(itReOrder);
    uStar = uStar(itReOrder);
    NEE = NEE(itReOrder);
    fNight = fNight(itReOrder);
end

function [Cp2, Stats2, Cp3, Stats3] = performStratificationAndDetection(t, NEE, uStar, T, fNight, StatsMT, ntAnnual, nPerDay, fPlot, cSiteYr)
    % Perform stratification and change-point detection
    nSeasons = round(ntAnnual / round(ntAnnual / 4));
    nPerSeason = round(ntAnnual / nSeasons);
    
    for iSeason = 1:nSeasons
        jtSeason = getSeasonIndices(iSeason, nPerSeason, ntAnnual);
        itSeason = findSeasonIndices(jtSeason, fNight, NEE, uStar, T);
        [nStrata, TTh] = calculateStrata(T, itSeason);
        
        for iStrata = 1:nStrata
            itStrata = findStrataIndices(T, TTh, iStrata, itSeason);
            [Cp2, Stats2, Cp3, Stats3] = evaluateChangePoints(iSeason, iStrata, Cp2, Stats2, Cp3, Stats3, ...
                uStar, NEE, T, t, itStrata, StatsMT, fPlot, cSiteYr);
        end
    end
end

function jtSeason = getSeasonIndices(iSeason, nPerSeason, ntAnnual)
    % Get indices for the current season
    if iSeason == 1
        jtSeason = 1:nPerSeason;
    elseif iSeason == ntAnnual
        jtSeason = ((ntAnnual - 1) * nPerSeason + 1):ntAnnual;
    else
        jtSeason = ((iSeason - 1) * nPerSeason + 1):(iSeason * nPerSeason);
    end
end

function itSeason = findSeasonIndices(jtSeason, fNight, NEE, uStar, T)
    % Find indices for the current season based on valid data points
    itSeason = find(fNight == 1 & ~isnan(NEE(jtSeason) + uStar(jtSeason) + T(jtSeason)));
end

function [nStrata, TTh] = calculateStrata(T, itSeason)
    % Calculate the number of temperature strata and their thresholds
    nStrataN = 4;
    nStrataX = 8;
    nBins = 50;
    nPerBin = 5;
    
    nStrata = floor(length(itSeason) / (nBins * nPerBin));
    if nStrata < nStrataN
        nStrata = nStrataN;
    end
    if nStrata > nStrataX
        nStrata = nStrataX;
    end
    
    TTh = prctile(T(itSeason), 0:(100 / nStrata):100);
end

function itStrata = findStrataIndices(T, TTh, iStrata, itSeason)
    % Find indices for the current strata based on temperature thresholds
    itStrata = find(T >= TTh(iStrata) & T <= TTh(iStrata + 1));
    itStrata = intersect(itStrata, itSeason);
end

function [Cp2, Stats2, Cp3, Stats3] = evaluateChangePoints(iSeason, iStrata, Cp2, Stats2, Cp3, Stats3, uStar, NEE, T, t, itStrata, StatsMT, fPlot, cSiteYr)
    % Evaluate change points and update the output matrices and Stats structures
    cPlot = '';
    if fPlot == 1
        fcFigLoc(1, 0.9, 0.9, 'MC');
        if iSeason == 1 && iStrata == 1
            cPlot = cSiteYr;
        end
    end
    
    [n, muStar, mNEE] = fcBin(uStar(itStrata), NEE(itStrata), [], 5);
    [xCp2, xs2, xCp3, xs3] = cpdFindChangePoint20100901(muStar, mNEE, fPlot, cPlot);
    
    % Add fields not assigned by cpdFindChangePoint function
    [n, muStar, mT] = fcBin(uStar(itStrata), T(itStrata), [], 5);
    [r, p] = corrcoef(muStar, mT);
    
    xs2 = addAdditionalFields(xs2, t, itStrata, T, r, p);
    xs3 = xs2;
    
    Cp2(iSeason, iStrata) = xCp2;
    Stats2(iSeason, iStrata) = xs2;
    Cp3(iSeason, iStrata) = xCp3;
    Stats3(iSeason, iStrata) = xs3;
end

function xs = addAdditionalFields(xs, t, itStrata, T, r, p)
    % Add additional fields to the Stats structure
    xs.mt = mean(t(itStrata));
    xs.ti = t(itStrata(1));
    xs.tf = t(itStrata(end));
    xs.ruStarVsT = r(2, 1);
    xs.puStarVsT = p(2, 1);
    xs.mT = mean(T(itStrata));
    xs.ciT = 0.5 * diff(prctile(T(itStrata), [2.5 97.5]));
end
