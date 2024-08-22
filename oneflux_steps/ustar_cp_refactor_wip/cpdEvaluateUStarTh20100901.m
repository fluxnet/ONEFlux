	function [Cp2,Stats2,Cp3,Stats3] = ... 
		cpdEvaluateUStarTh20100901 ...
		(t,NEE,uStar,T,fNight,fPlot,cSiteYr) 

%cpdEvaluateUStarTh20100901
%
%estimates uStarTh for one site-year of data using change-point 
%detection (cpd) methods implemented within the general framework 
%of the Papale et al. (2006) uStarTh evaluation method. 
%
%Syntax: 
%
%	[Cp2,Stats2,Cp3,Stats3] = ... 
%		cpdEvaluateUStarTh20100901 ...
%			(t,NEE,uStar,T,fNight,fPlot,cSiteYr) 
%	where:
%	 - Cp2 and Cp3 are nW x nT matrices containing change-point 
%		uStarTh estimates from the 2-parameter operational 
%		and 3-parameter diagnostic models 
%	 - Stats2 and Stats3 are structured records containing the 
%		corresponding nW x nT matrices of cpd statistics.  
%	 - t is the time vector
%	 - NEE, uStar and T (temperature)
%	 - fNight is a vector specifying day (0) or night (1)
%	 - fPlot is a scalar flag that is set high (1) to plot
%	 - cSiteYr is a text string used in the plot title
%
%The analysis is based on one year of data.  
%The data are stratified by time of year 
%and temperature into nW by nT strata, 
%each with a fixed number of data.
%The uStarTh is estimated independently for each stratum, 
%using two separate change-point models: 
%the 2-parameter operational and 
%3-parameter diagnostic models.  
%
%The primary modification Papale et al. (2006) is the use of 
%change-point detection (cpd) rather than a moving point test 
%to evaluate the uStarTh.  The cpd method is adopted from 
%Lund and Reeves (2002) and Wang (2003).  
%
%Relationship to other programs:
%
%	1. cpdBootstrapUStarTh20100901
%		- function that implements bootstrapping 
%		  to estimate uncertainty in annual uStarTh 
%	calls
%	2. CPDEvaluateUStarTh20100901
%		- function that computes uStarTh for one site-year of data 
%		  with independent uStarTh analyses for each nW x nT strata
%		  (after stratifying by time of year and temerature)
%	calls 
%	3. cpdFindChangePoint20100901 
%		- function for change-point detection
%		  applied to each strata 

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

%	Seasonal variation is evaluated using moving windows of 1,000 good
%	points (for 30-min data) or 600 good points (for 60-min data).

%	Within each window, the data are stratified by temperature 
%	into 4 equal classes.  

	nt=length(t); [y,m,d]=fcDatevec(t); 
	iYr=median(y); EndDOY=fcDoy(datenum(iYr,12,31.5)); 
	
	nPerDay=round(1/nanmedian(diff(t))); 

	nWindowsN=4; nStrata=4; nBins=50; nPerBin = 5;
	switch nPerDay;
		case 24; nPerBin=3; 
		case 48; nPerBin=5; 
	end;
	nPerWindow=nStrata*nBins*nPerBin; nInc=0.5*nPerWindow; 
	nN=nWindowsN*nPerWindow;
	
	itOut=find(uStar<0 | uStar>3); uStar(itOut)=NaN; % reduced to 3 on 15 Jan 2010
	
	itAnnual=find(fNight==1 & ~isnan(NEE+uStar+T)); ntAnnual=length(itAnnual); 
	
%	Initialize outputs. 	

	Cp2=NaN*ones(nWindowsN,nStrata); 
	Cp3=NaN*ones(nWindowsN,nStrata); 
		
	StatsMT=[]; 
	StatsMT.n=NaN; StatsMT.Cp=NaN; StatsMT.Fmax=NaN; StatsMT.p=NaN; 
	StatsMT.b0=NaN; StatsMT.b1=NaN; StatsMT.b2=NaN; StatsMT.c2=NaN; 
	StatsMT.cib0=NaN; StatsMT.cib1=NaN; StatsMT.cic2=NaN; % preceding elements output by changepoint function
	StatsMT.mt=NaN; StatsMT.ti=NaN; StatsMT.tf=NaN; 
	StatsMT.ruStarVsT=NaN; StatsMT.puStarVsT=NaN; 
	StatsMT.mT=NaN; StatsMT.ciT=NaN; % these elements added by this program.  
						
	Stats2=StatsMT; Stats3=StatsMT; 
	for iWindow=1:nWindowsN;
		for iStrata=1:nStrata;
			Stats2(iWindow,iStrata)=StatsMT;
			Stats3(iWindow,iStrata)=StatsMT;
		end; 
	end;
	
	if ntAnnual<nN; return; end; 
	
%	append wrap-around data to start and end of record; 
%	18 Jan 2010 just need to wrap one end. 

	itAdd1=itAnnual(end-nInc-1):nt; % itAdd2=1:itAnnual(nInc); 
	
	t=[t(itAdd1)-EndDOY; t]; 
	T=[T(itAdd1); T]; 
	uStar=[uStar(itAdd1); uStar]; 
	NEE=[NEE(itAdd1); NEE]; 
	fNight=[fNight(itAdd1); fNight]; 
    
	itAnnual=find(fNight==1 & ~isnan(NEE+uStar+T)); ntAnnual=length(itAnnual); 
	
%	Reset nPerWindow and nInc based on actual number of good data. 
%	nWindows is a temporary variable. 
	
	nWindows=round(ntAnnual/nPerWindow); nPerWindow=ntAnnual/nWindows; 
	nInc=round(nPerWindow/2); nPerWindow=round(nPerWindow); 
	
%	Stratify in two dimensions:
%	1. by time using moving windows
%	2. by temperature class
%	Then estimate change points Cp2 and Cp3 for each stratum. 
	
	iWindow=0; 
	
	for jt1=1:nInc:(ntAnnual-nInc);
		
		iWindow=iWindow+1; 
		
		jt2=jt1+nPerWindow-1; 
		if jt2>ntAnnual; jt2=ntAnnual; jt1=ntAnnual-nPerWindow+1; end; 
		itWindow=itAnnual(jt1:jt2); 
		
		TTh=prctile(T(itWindow),0:(100/nStrata):100);
		for iStrata=1:nStrata;
			
			itStrata=find(T>=TTh(iStrata) & T<=TTh(iStrata+1));
			itStrata=intersect(itStrata,itWindow); 
			
			[n,muStar,mNEE] = fcBin(uStar(itStrata),NEE(itStrata),[],nPerBin);

			[xCp2,xs2,xCp3,xs3] = cpdFindChangePoint20100901(muStar,mNEE,fPlot,cSiteYr); 
			
			%	add fields not assigned by cpdFindChangePoint function
			
			[n,muStar,mT] = fcBin(uStar(itStrata),T(itStrata),[],nPerBin);
			[r,p]=corrcoef(muStar,mT); 
			
			xs2.mt=mean(t(itStrata)); xs2.ti=t(itStrata(1)); xs2.tf=t(itStrata(end)); 
			xs2.ruStarVsT=r(2,1); xs2.puStarVsT=p(2,1); 
			xs2.mT=mean(T(itStrata)); xs2.ciT=0.5*diff(prctile(T(itStrata),[2.5 97.5])); 
			
			xs3.mt=xs2.mt; xs3.ti=xs2.ti; xs3.tf=xs2.tf; 
			xs3.ruStarVsT=xs2.ruStarVsT; xs3.puStarVsT=xs2.puStarVsT; 
			xs3.mT=xs2.mT; xs3.ciT=xs2.ciT; 
			
			Cp2(iWindow,iStrata)=xCp2; 
			Stats2(iWindow,iStrata)=xs2; 
			
			Cp3(iWindow,iStrata)=xCp3; 
			Stats3(iWindow,iStrata)=xs3; 
			
		end; % for iStrata
		
	end; % for jt1
		
%	========================================================================
%	========================================================================
	
	