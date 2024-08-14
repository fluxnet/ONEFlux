function [Cp2, Stats2, Cp3, Stats3] = cpdBootstrapUStarTh4Season20100901(t, NEE, uStar, T, fNight, fPlot, cSiteYr, nBoot)
    % Main function for bootstrapping uStarTh estimation across four seasons

    % Initialize output structures and variables
    [Cp2, Cp3, Stats2, Stats3, StatsMT, nt, nPerDay, ntNee, ntN] = initializeBootstrap(t, NEE, uStar, T, fNight, nBoot);

    if ntNee >= ntN
        % Perform bootstrapping
        for iBoot = 1:nBoot
            [Cp2(:,:,iBoot), Stats2(:,:,iBoot), Cp3(:,:,iBoot), Stats3(:,:,iBoot)] = performBootstrapIteration(...
                t, NEE, uStar, T, fNight, fPlot, cSiteYr, iBoot, nt, ntNee);
        end
    end
end

function [Cp2, Cp3, Stats2, Stats3, StatsMT, nt, nPerDay, ntNee, ntN] = initializeBootstrap(t, NEE, uStar, T, fNight, nBoot)
    % Initialize output matrices and other necessary variables
    
    nt = length(t);
    nPerDay = round(1/nanmedian(diff(t)));
    
    iNight = find(fNight);
    iOut = find(uStar < 0 | uStar > 4);
    uStar(iOut) = NaN;
    
    nSeasons = 4;
    nStrataN = 4;
    nStrataX = 8;
    nBins = 50;

    nPerBin = 5;
    if nPerDay == 24
        nPerBin = 3;
    elseif nPerDay == 48
        nPerBin = 5;
    end

    nPerSeason = nStrataN * nBins * nPerBin;
    ntN = nSeasons * nPerSeason;
    
    itNee = find(~isnan(NEE + uStar + T));
    itNee = intersect(itNee, iNight);
    ntNee = length(itNee);
    
    StatsMT = initializeStatsMT();
    
    Cp2 = NaN * ones(nSeasons, nStrataX, nBoot);
    Cp3 = NaN * ones(nSeasons, nStrataX, nBoot);
    Stats2 = repmat(StatsMT, nSeasons, nStrataX, nBoot);
    Stats3 = repmat(StatsMT, nSeasons, nStrataX, nBoot);
end

function StatsMT = initializeStatsMT()
    % Initialize the template for Stats structure
    
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

function [Cp2, Stats2, Cp3, Stats3] = performBootstrapIteration(t, NEE, uStar, T, fNight, fPlot, cSiteYr, iBoot, nt, ntNee)
    % Perform a single iteration of the bootstrapping process
    
    if iBoot > 1
        fPlot = 0;
    end
    
    it = sort(randi(nt, nt, 1));
    ntNee = sum(ismember(it, find(~isnan(NEE + uStar + T))));

    [Cp2, Stats2, Cp3, Stats3] = cpdEvaluateUStarTh4Season20100901(...
        t(it), NEE(it), uStar(it), T(it), fNight(it), fPlot, cSiteYr);
end
