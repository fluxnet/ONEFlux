function [cPlot, iPlot] = plotStratum(fPlot, nSeasons, nStrata, iPlot, iSeason, iStrata, cSiteYr)
    cPlot=''; 
	if fPlot==1; 
		iPlot=iPlot+1; 
		subplot(nSeasons,nStrata,iPlot); 
		if iSeason==1 & iStrata==1
			cPlot=cSiteYr; 
		end
	end; 
end