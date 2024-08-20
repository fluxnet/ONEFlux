	function [Cp2,Stats2,Cp3,Stats3] = ... 
		cpdBootstrapUStarTh20100901 ...
			(t,NEE,uStar,T,fNight,fPlot,cSiteYr,nBoot) 
	
%cpdBootstrapUStarTh20100901
%
%estimates uStarTh uncertainty for one site-year of data 
%using change-point detection (cpd) methods 
%implemented within the general framework 
%of the Papale et al. (2006) uStarTh algorithm
%
%Syntax: 
%
%	[Cp2,Stats2,Cp3,Stats3] = ... 
%		cpdBootstrapUStarTh20100901 ...
%			(t,NEE,uStar,T,fNight,fPlot,cSiteYr,nBoot) 
%	where:
%	 - Cp2 and Cp3 are nW x nT x nBoot matrices containing change-point 
%		uStarTh estimates from the 2-parameter operational 
%		and 3-parameter diagnostic models 
%	 - Stats2 and Stats3 are structured records containing the corresponding 
%		nW x nT x nBoot matrices of cpd statistics.  
%	 - t is the time vector
%	 - NEE, uStar and T (temperature) are inputs
%	 - fNight is a vector specifying day (0) or night (1)
%	 - fPlot is a scalar flag that is set high (1) to plot
%	 - cSiteYr is a text string used in the plot title
%	 - nBoot is the number of bootstraps
%
%Relationship to other programs:
%
%	1. cpdBootstrapUStarTh20100901
%		- function that implements bootstrapping 
%		  to estimate uncertainty in annual uStarTh 
%	calls
%	2. CPDEvaluateUStarTh20100901
%		- function that computes uStarTh for one site-year of data 
%		  with independent uStarTh analyses for each of nW x nT strata
%		  (stratified by time of year and temerature)
%	calls 
%	3. cpdFindChangePoint20100901 
%		- function for change-point detection
%		  applied to individual strata 

%	========================================================================
%	========================================================================

%	Functions called: 
%
%		cpdEvaluateUStarTh20100901 
%		fcx2roevec
%		stats toolbox:  nanmedian 

%	Written by Alan Barr 15 Jan 2010. 

%	========================================================================
%	========================================================================

%	Initializations
			
	nt=length(t); 
	nPerDay=round(1/nanmedian(diff(t)));

	nWindowsN=4; nStrata=4; nBins=50; nPerBin = 5;
	switch nPerDay;
		case 24; nPerBin=3;
		case 48; nPerBin=5;
	end;
	nPerWindow=nStrata*nBins*nPerBin; 
	nInc=0.5*nPerWindow;
	ntN=nWindowsN*nPerWindow;
	
	iNight=find(fNight); 
	uStar(uStar<0 | uStar>4)=NaN; % exclude unreasonable uStar
	
	itNee=find(~isnan(NEE+uStar+T)); itNee=intersect(itNee,iNight); 
	ntNee=length(itNee);
	nWindows=ceil(ntNee/nInc)+1; % add 1 to accommodate bootstrapping variability in ntNee

	StatsMT=[];
	StatsMT.n=NaN; StatsMT.Cp=NaN; StatsMT.Fmax=NaN; StatsMT.p=NaN;
	StatsMT.b0=NaN; StatsMT.b1=NaN; StatsMT.b2=NaN; StatsMT.c2=NaN;
	StatsMT.cib0=NaN; StatsMT.cib1=NaN; StatsMT.cic2=NaN;
	StatsMT.mt=NaN; StatsMT.ti=NaN; StatsMT.tf=NaN;
	StatsMT.ruStarVsT=NaN; StatsMT.puStarVsT=NaN;
	StatsMT.mT=NaN; StatsMT.ciT=NaN;
	
	Cp2=NaN*ones(nWindows,nStrata,nBoot);
	Cp3=NaN*ones(nWindows,nStrata,nBoot);
	
	Stats2=StatsMT; Stats3=StatsMT;
	for iBoot=1:nBoot;
		for iWindow=1:nWindows;
			for iStrata=1:nStrata;
				Stats2(iWindow,iStrata,iBoot)=StatsMT;
				Stats3(iWindow,iStrata,iBoot)=StatsMT;
			end; 
		end; 
	end;
	
	disp(' ');
	fprintf('cpdBootstrapUStarTh20100901  %s   nObs: %g %g %g %g \n',cSiteYr,nt,sum(~isnan([NEE uStar T])));
	disp(' ');
	
%	Bootstrapping.
		
	if ntNee>=ntN;
		
		for iBoot=1:nBoot;
			
			t0=now;
			
			it=sort(randi(nt,nt,1)); 
			ntNee=sum(ismember(it,itNee)); 
			
			if iBoot>1; fPlot=0; end;
			
			[xCp2,xStats2, xCp3,xStats3] = ...
				cpdEvaluateUStarTh20100901 ...
					(t(it),NEE(it),uStar(it),T(it),fNight(it),fPlot,cSiteYr); 
				
			[nW,nS]=size(xCp2); % nW (and ntNee) vary because of bootstrapping 
			dt=(now-t0)*24*60*60;
			fprintf('Bootstrap uStarTh %s:  %g/%g   nObs %g  nWindows %g   Cp2 %4.3f  Cp3 %4.3f   %3.1fs \n', ...
				cSiteYr,iBoot,nBoot,ntNee,nW,nanmedian(fcx2rowvec(xCp2)),nanmedian(fcx2rowvec(xCp3)),dt);
			
			Cp2(1:nW,:,iBoot)=xCp2; Stats2(1:nW,:,iBoot)=xStats2;
			Cp3(1:nW,:,iBoot)=xCp3; Stats3(1:nW,:,iBoot)=xStats3;
			
		end; % for iBoot
		
	end; % if ntNee>=ntN;
	
%	========================================================================
%	========================================================================

