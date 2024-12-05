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

%	Initializations
	metadata = struct();
	metadata.siteFile = cSiteYr;
	metadata.oneFluxDir = '/home/ia/iccs_repos/ONEFlux/';
	metadata.relArtifactsDir = 'tests/test_artifacts';
	metadata.frequency = 20;  %frequncy_to_log_input/ouput, defualt is 10 if not specified


	nSeasons = 4; nStrataN = 4; 
	nStrataX = 8; nBins = 50;

	metadata.inputNames = {'t', 'nSeasons', 'nStrataN', 'nBins'};
	metadata.outputNames = {'nt', 'm', 'EndDOY', 'nPerBin', 'nN'};	

	[nt, m, EndDOY, nPerBin, nN] = logFuncResult('log.json', @initializeParameters, metadata, t, nSeasons, nStrataN, nBins);

	% [nt, m, EndDOY, nPerBin, nN] = initializeParameters(t, nSeasons, nStrataN, nBins);


	[uStar, itAnnual, ntAnnual] = filterInvalidPoints(uStar, fNight, NEE, T);

	Cp2=NaN*ones(nSeasons,nStrataX); 
	Cp3=NaN*ones(nSeasons,nStrataX); 
		
	[Stats2, Stats3, StatsMT] = initializeStatistics(nSeasons, nStrataX);
	
	

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



% function [Stats2, Stats3, StatsMT] = initializeStatistics(nSeasons, nStrataX)

% 	StatsMT=[]; 
% 	StatsMT.n=NaN; StatsMT.Cp=NaN; StatsMT.Fmax=NaN; StatsMT.p=NaN; 
% 	StatsMT.b0=NaN; StatsMT.b1=NaN; StatsMT.b2=NaN; StatsMT.c2=NaN; 
% 	StatsMT.cib0=NaN; StatsMT.cib1=NaN; StatsMT.cic2=NaN; % preceding elements output by changepoint function
% 	StatsMT.mt=NaN; StatsMT.ti=NaN; StatsMT.tf=NaN; 
% 	StatsMT.ruStarVsT=NaN; StatsMT.puStarVsT=NaN; 
% 	StatsMT.mT=NaN; StatsMT.ciT=NaN; % these elements added by this program.  
						
% 	Stats2=StatsMT; Stats3=StatsMT; 
% 	for iSeason=1:nSeasons;
% 		for iStrata=1:nStrataX;
% 			Stats2(iSeason,iStrata)=StatsMT;
% 			Stats3(iSeason,iStrata)=StatsMT;
% 		end; 
% 	end;

% end


% function [t, T, uStar, NEE, fNight, itAnnual, ntAnnual] = ...
% 	reorderAndPreprocessData(t, T, uStar, NEE, fNight, EndDOY, m, nt)

% 	itD=find(m==12); 
% 	itReOrder=[min(itD):nt 1:(min(itD)-1)]; 
% 	t(itD)=t(itD)-EndDOY; t=t(itReOrder); 
% 	T=T(itReOrder); uStar=uStar(itReOrder); 
% 	NEE=NEE(itReOrder); fNight=fNight(itReOrder); 
	
% 	itAnnual=find(fNight==1 & ~isnan(NEE+uStar+T)); ntAnnual=length(itAnnual); 
	
% end

% function jtSeason = computeSeasonIndices(iSeason, nSeasons, nPerSeason, ntAnnual)
% 	switch iSeason
%         case 1
%             jtSeason = 1:nPerSeason;
%         case nSeasons
%             jtSeason = ((nSeasons - 1) * nPerSeason + 1):ntAnnual;
%         otherwise
%             jtSeason = ((iSeason - 1) * nPerSeason + 1):(iSeason * nPerSeason);
%     end
% end


% function nStrata = computeStrataCount(ntSeason, nBins, nPerBin, nStrataN, nStrataX)
%     nStrata = floor(ntSeason / (nBins * nPerBin));
%     nStrata = max(nStrata, nStrataN); % Ensure minimum strata count
%     nStrata = min(nStrata, nStrataX); % Enforce maximum strata count
% end


% function TTh = computeTemperatureThresholds(T, itSeason, nStrata)
%     TTh = prctile(T(itSeason), 0:(100 / nStrata):100);
% end

% function itStrata = findStratumIndices(T, itSeason, TTh, iStrata)
%     itStrata = find(T >= TTh(iStrata) & T <= TTh(iStrata + 1));
%     itStrata = intersect(itStrata, itSeason); % Filter by current season
% end


% function xs = addStatisticsFields(xs, t, r, p, T, itStrata)
%     xs.mt = mean(t(itStrata));
%     xs.ti = t(itStrata(1));
%     xs.tf = t(itStrata(end));
%     xs.ruStarVsT = r(2, 1);
%     xs.puStarVsT = p(2, 1);
%     xs.mT = mean(T(itStrata));
%     xs.ciT = 0.5 * diff(prctile(T(itStrata), [2.5, 97.5]));
% end


% function [cPlot, iPlot] = plotStratum(fPlot, nSeasons, nStrata, iPlot, iSeason, iStrata, cSiteYr)
%     cPlot=''; 
% 	if fPlot==1; 
% 		iPlot=iPlot+1; 
% 		subplot(nSeasons,nStrata,iPlot); 
% 		if iSeason==1 & iStrata==1
% 			cPlot=cSiteYr; 
% 		end
% 	end; 
% end


% function [Cp2, Stats2, Cp3, Stats3, iPlot] = ...
% 	 processStrata(nSeasons, iSeason, nStrata, nPerBin, itSeason, T, uStar, NEE, t, ...
% 	TTh, fPlot, cSiteYr, iPlot, Cp2, Stats2, Cp3, Stats3)


% 	for iStrata=1:nStrata;
			
% 		[cPlot, iPlot ]= plotStratum(fPlot, nSeasons, nStrata, iPlot, iSeason, iStrata, cSiteYr);
		
% 		itStrata = findStratumIndices(T, itSeason, TTh, iStrata);
		
% 		[n,muStar,mNEE] = fcBin(uStar(itStrata),NEE(itStrata),[],nPerBin);

% 		[xCp2,xs2,xCp3,xs3] = cpdFindChangePoint20100901(muStar,mNEE,fPlot,cPlot); 
		
% 		%	add fields not assigned by cpdFindChangePoint function
		
% 		[n,muStar,mT] = fcBin(uStar(itStrata),T(itStrata),[],nPerBin);
% 		[r,p]=corrcoef(muStar,mT); 
		
% 		xs2 = addStatisticsFields(xs2, t, r, p, T, itStrata);
		
% 		xs3.mt=xs2.mt; xs3.ti=xs2.ti; xs3.tf=xs2.tf; 
% 		xs3.ruStarVsT=xs2.ruStarVsT; xs3.puStarVsT=xs2.puStarVsT; 
% 		xs3.mT=xs2.mT; xs3.ciT=xs2.ciT; 
		
% 		Cp2(iSeason,iStrata)=xCp2; 
% 		Stats2(iSeason,iStrata)=xs2; 
		
% 		Cp3(iSeason,iStrata)=xCp3; 
% 		Stats3(iSeason,iStrata)=xs3; 
		
% 	end;

% end
