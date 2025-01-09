function [nt, m, EndDOY, nPerBin, nN] = initializeParameters(t, nSeasons, nStrataN, nBins)
	% Derive basic time information
	nt = length(t); 
	[y, m, d] = fcDatevec(t);
	iYr = median(y); 
	EndDOY = fcDoy(datenum(iYr, 12, 31.5));

	nPerDay = round(1 / nanmedian(diff(t)));
	
	% Define constants
	nPerBin = 5;

	% Adjust binning based on sampling frequency
	switch nPerDay
		case 24
			nPerBin = 3;
		case 48
			nPerBin = 5;
	end


	nPerSeasonN=nStrataN*nBins*nPerBin; 
	nN=nSeasons*nPerSeasonN;


end