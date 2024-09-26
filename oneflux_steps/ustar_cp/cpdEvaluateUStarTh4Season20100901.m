	function [Cp2,Stats2,Cp3,Stats3] = ... 
		cpdEvaluateUStarTh4Season20100901 ...
		(t,NEE,uStar,T,fNight,fPlot,cSiteYr) 

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

	nt=length(t); [y,m,d]=fcDatevec(t); 
	iYr=median(y); EndDOY=fcDoy(datenum(iYr,12,31.5)); 
	
	nPerDay=round(1/nanmedian(diff(t))); 

	nSeasons=4; nStrataN=4; nStrataX=8; nBins=50; nPerBin = 5;
	switch nPerDay;
		case 24; nPerBin=3; 
		case 48; nPerBin=5; 
	end;
	nPerSeasonN=nStrataN*nBins*nPerBin; 
	nN=nSeasons*nPerSeasonN;
	
	itOut=find(uStar<0 | uStar>3); uStar(itOut)=NaN; % reduced to 3 on 15 Jan 2010
	
	itAnnual=find(fNight==1 & ~isnan(NEE+uStar+T)); ntAnnual=length(itAnnual); 
	
%	Initialize outputs. 	

	Cp2=NaN*ones(nSeasons,nStrataX); 
	Cp3=NaN*ones(nSeasons,nStrataX); 
		
	StatsMT=[]; 
	StatsMT.n=NaN; StatsMT.Cp=NaN; StatsMT.Fmax=NaN; StatsMT.p=NaN; 
	StatsMT.b0=NaN; StatsMT.b1=NaN; StatsMT.b2=NaN; StatsMT.c2=NaN; 
	StatsMT.cib0=NaN; StatsMT.cib1=NaN; StatsMT.cic2=NaN; % preceding elements output by changepoint function
	StatsMT.mt=NaN; StatsMT.ti=NaN; StatsMT.tf=NaN; 
	StatsMT.ruStarVsT=NaN; StatsMT.puStarVsT=NaN; 
	StatsMT.mT=NaN; StatsMT.ciT=NaN; % these elements added by this program.  
						
	Stats2=StatsMT; Stats3=StatsMT; 
	for iSeason=1:nSeasons;
		for iStrata=1:nStrataX;
			Stats2(iSeason,iStrata)=StatsMT;
			Stats3(iSeason,iStrata)=StatsMT;
		end; 
	end;
	
	if ntAnnual<nN; return; end; 
	
	nPerSeason=round(ntAnnual/nSeasons); 
	
%	Move Dec to beginning of year and date as previous year.

	itD=find(m==12); 
	itReOrder=[min(itD):nt 1:(min(itD)-1)]; 
	t(itD)=t(itD)-EndDOY; t=t(itReOrder); 
	T=T(itReOrder); uStar=uStar(itReOrder); 
	NEE=NEE(itReOrder); fNight=fNight(itReOrder); 
	
	itAnnual=find(fNight==1 & ~isnan(NEE+uStar+T)); ntAnnual=length(itAnnual); 
	
%	Reset nPerSeason and nInc based on actual number of good data. 
%	nSeasons is a temporary variable. 
	
	nSeasons=round(ntAnnual/nPerSeason); nPerSeason=ntAnnual/nSeasons; 
	nPerSeason=round(nPerSeason); 
	
%	Stratify in two dimensions:
%	1. by time using moving windows
%	2. by temperature class
%	Then estimate change points Cp2 and Cp3 for each stratum. 

	if fPlot==1; fcFigLoc(1,0.9,0.9,'MC'); iPlot=0; end; 
	
	for iSeason=1:nSeasons; 
		
		switch iSeason; 
			case 1; jtSeason=1:nPerSeason; 
			case nSeasons; jtSeason=((nSeasons-1)*nPerSeason+1):ntAnnual; 
			otherwise; jtSeason=((iSeason-1)*nPerSeason+1):(iSeason*nPerSeason); 
		end; 
		itSeason=itAnnual(jtSeason); ntSeason=length(itSeason); 
		nStrata=floor(ntSeason/(nBins*nPerBin)); 
		if nStrata<nStrataN; nStrata=nStrataN; end; 
		if nStrata>nStrataX; nStrata=nStrataX; end; 
		
		TTh=prctile(T(itSeason),0:(100/nStrata):100);
		for iStrata=1:nStrata;
			
			cPlot=''; 
			if fPlot==1; 
				iPlot=iPlot+1; subplot(nSeasons,nStrata,iPlot); 
				if iSeason==1 & iStrata==1; cPlot=cSiteYr; end; 
			end; 
			
			itStrata=find(T>=TTh(iStrata) & T<=TTh(iStrata+1));
			itStrata=intersect(itStrata,itSeason); 
			
			[n,muStar,mNEE] = fcBin(uStar(itStrata),NEE(itStrata),[],nPerBin);

			[xCp2,xs2,xCp3,xs3] = cpdFindChangePoint20100901(muStar,mNEE,fPlot,cPlot); 
			
			%	add fields not assigned by cpdFindChangePoint function
			
			[n,muStar,mT] = fcBin(uStar(itStrata),T(itStrata),[],nPerBin);
			[r,p]=corrcoef(muStar,mT); 
			
			xs2.mt=mean(t(itStrata)); xs2.ti=t(itStrata(1)); xs2.tf=t(itStrata(end)); 
			xs2.ruStarVsT=r(2,1); xs2.puStarVsT=p(2,1); 
			xs2.mT=mean(T(itStrata)); xs2.ciT=0.5*diff(prctile(T(itStrata),[2.5 97.5])); 
			
			xs3.mt=xs2.mt; xs3.ti=xs2.ti; xs3.tf=xs2.tf; 
			xs3.ruStarVsT=xs2.ruStarVsT; xs3.puStarVsT=xs2.puStarVsT; 
			xs3.mT=xs2.mT; xs3.ciT=xs2.ciT; 
			
			Cp2(iSeason,iStrata)=xCp2; 
			Stats2(iSeason,iStrata)=xs2; 
			
			Cp3(iSeason,iStrata)=xCp3; 
			Stats3(iSeason,iStrata)=xs3; 
			
		end; % for iStrata
		
	end; % for iSeason

%	========================================================================
%	========================================================================
	
	