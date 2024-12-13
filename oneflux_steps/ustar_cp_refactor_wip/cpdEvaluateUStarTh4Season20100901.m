	function [Cp2,Stats2,Cp3,Stats3] = ... 
		cpdEvaluateUStarTh4Season20100901 ...
		(t,NEE,uStar,T,fNight,fPlot,cSiteYr,varargin) 

%	nacpEvaluateUStarTh4Season20100901

%	estimates uStarTh for a site-year of data using change-point 
%	detection (cpd) methods implemented within the general framework 
%	of the Papale et al. (2006) uStarTh evaluation method. 
%
%	Syntax: 
%		[Cp2,Stats2,Cp3,Stats3] = ... 
%			cpdEvaluateUStarTh20100901 ...
%				(t,NEE,uStar,T,fNight,fPlot,cSiteYr) 
%		where:
%		 - Cp2 and Cp3 are nW x nT matrices containing change-point 
%			uStarTh estimates from the 2-parameter operational 
%			and 3-parameter diagnostic models 
%		 - Stats2 and Stats3 are structured records containing the corresponding 
%			nW x nT matrices of cpd statistics.  
%		 - t is the time vector
%		 - NEE, uStar and T (temperature)
%		 - fNight is a vector specifying day (0) or night (1)
%		 - fPlot is a scalar flag that is set high (1) to plot
%		 - cSiteYr is a text string used in the plot title
%
%	The analysis is based on one year of data.  The year is stratified 
%	by time of year and temperature into nW by nT strata, each with a 
%	fixed number of data.
%	The uStarTh is estimated independently for each stratum, using two 
%	change-point models: the 2-parameter operational and 3-parameter 
%	diagnostic models.  
%
%	The primary modification Papale et al. (2006) is the use of 
%	change-point detection (cpd) rather than a moving point test 
%	to evaluate the uStarTh.  The cpd method is adopted from 
%	Lund and Reeves (2002) and Wang (2003).  
%	

%	Relationship to other programs:
%	1. cpdBootstrapUStarTh20100901
%		- function which processes specified sites including bootstrapping
%		  and data output.
%	calls
%	2. CPDEvaluateUStarTh20100901
%		- function that processes an individual year of data
%	calls 
%	3. cpdFindChangePoint20100901 (change-point detection function).

%	========================================================================
%	========================================================================

%	Functions called: 
%
%		cpdFindChangePoint20100901 
%		fcBin, fcDatevec, fcDoy
%		stats toolbox:  nanmedian, prctile, regress

%	Written by Alan Barr 15 Jan 2010. 

%	========================================================================
%	========================================================================

	nSeasons = 4; nStrataN = 4; 
	nStrataX = 8; nBins = 50;


	[nt, m, EndDOY, nPerBin, nN] = initializeParameters(t, nSeasons, nStrataN, nBins);

	[uStar, itAnnual, ntAnnual] = filterInvalidPoints(uStar, fNight, NEE, T);

	Cp2=NaN*ones(nSeasons,nStrataX); 
	Cp3=NaN*ones(nSeasons,nStrataX); 
		
	[Stats2, Stats3] = initializeStatistics(nSeasons, nStrataX);
	
	

	if ntAnnual<nN; 
		% disp('case1');
		if length(varargin) > 0
			Stats2 = jsonencode(Stats2);
			Stats3 = jsonencode(Stats3);
		end
		return; 
	end; 
	
	
%	Move Dec to beginning of year and date as previous year.

	[t, T, uStar, NEE, fNight, itAnnual, ntAnnual] = ...
		reorderAndPreprocessData(t, T, uStar, NEE, fNight, EndDOY, m, nt);
	
%	Reset nPerSeason and nInc based on actual number of good data. 
%	nSeasons is a temporary variable. 

	nPerSeason=round(ntAnnual/nSeasons); 
	nSeasons=round(ntAnnual/nPerSeason); nPerSeason=ntAnnual/nSeasons; 
	nPerSeason=round(nPerSeason); 
	
%	Stratify in two dimensions:
%	1. by time using moving windows
%	2. by temperature class
%	Then estimate change points Cp2 and Cp3 for each stratum. 
	iPlot = 0;
	if fPlot==1; fcFigLoc(1,0.9,0.9,'MC'); iPlot=0; end; 
	
	for iSeason=1:nSeasons; 
		
		jtSeason = computeSeasonIndices(iSeason, nSeasons, nPerSeason, ntAnnual);

		itSeason=itAnnual(jtSeason); ntSeason=length(itSeason); 
		
		nStrata = computeStrataCount(ntSeason, nBins, nPerBin, nStrataN, nStrataX);
		
		TTh = computeTemperatureThresholds(T, itSeason, nStrata);
		
		[Cp2, Stats2, Cp3, Stats3, iPlot] = ...
		        processStrata(nSeasons, iSeason, nStrata, nPerBin, itSeason, T, uStar, NEE, t, ...
		                TTh, fPlot, cSiteYr, iPlot, Cp2, Stats2, Cp3, Stats3);
	% for iStrata
		
	end; % for iSeason

	if length(varargin) > 0
		Stats2 = jsonencode(Stats2);
		Stats3 = jsonencode(Stats3);
	end

end