function [Cp2, Stats2, Cp3, Stats3] = performBootstrapping(nBoot, t, NEE, uStar, T, fNight, fPlot, cSiteYr, Cp2, Stats2, Cp3, Stats3, itNee, nt)
    % Perform the bootstrapping process
    
    for iBoot = 1:nBoot
        t0 = now;
        
        % Generate random indices and calculate ntNee
        it = sort(randi(nt, nt, 1));
        ntNee = sum(ismember(it, itNee));
        
        if iBoot > 1
            fPlot = 0; % Turn off plotting after the first bootstrapping run
        end
        
        % Call evaluation function
        [xCp2, xStats2, xCp3, xStats3] = cpdEvaluateUStarTh4Season20100901(t(it), NEE(it), uStar(it), T(it), fNight(it), fPlot, cSiteYr);
        
        % Store results in the matrices
        Cp2(:, :, iBoot) = xCp2;
        Stats2(:, :, iBoot) = xStats2;
        Cp3(:, :, iBoot) = xCp3;
        Stats3(:, :, iBoot) = xStats3;
    end
end