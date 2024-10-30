function [Cp2, Stats2, Cp3, Stats3] = cpdBootstrapUStarTh4Season20100901(t, NEE, uStar, T, fNight, fPlot, cSiteYr, nBoot, varargin)
    %	cpdBootstrapUStarTh4Season20100901

%	is a simplified operational version of 

%	20100901 changes 3A 4I to 2A 3I as sggested by Xiaolan Wang. 	
	
%	20100408 replaces 20100318, updating ChPt function from:
%	FindChangePointMod3LundReeves2002_20100318 to
%	FindChangePointMod2A4ILundReeves2002_20100408.
%	which: adds back A model, makes a correction to the significance test,
%	and adds a comparison of the 4- versus 3-parameter models. 
%	and adds a comparison of the 4- versus 3-parameter models. 

%	20100318 new version with small tweaks to FindChangePoint
%	also adds mT and ciT to Stats structures.
%
%	is a new working implementation of Alan's u*Th evaluation algorithm
%	based on Lund and Reeves' (2002) modified by Wang's (2003) change-point
%	detection algorithm. 
%
%	Relationship to other programs:
%
%	Called by batchNewNacpEstimateUStarTh_Moving_Mod3LundChPt_20100115 
%		- script which identifies which sites to process 
%	Calls newNacpEvaluateUStarTh_MovingStrat_20100114
%		- function that processes an individual year of data, using 
%		  FindChangePointMod3LundReeves2002_20091204
%	
%	This implementation may supplant all previous versions. 
%
%	It uses moving windows of fixed size to evaluate seasonal variation.  
%
%	Three combinations of stratification and pooling are implemented.  
%	 - All begin with 2D (time x temperature) stratification 
%	   (moving-window time x n temperature classes within each window). 
%	 - Two (W and A) add normalization and pooling.  
%
%	1. Method S (full stratification) 
%		estimates the change-points for each of the strata 
%		(nWindows x nTClasses) with no need for normalization.  
%	2. Method W (pooling within time windows) 
%		begins with a variant of S but pools the temperature classes 
%		within each time window before estimating one change-point per window. 
%		Before pooling, the binned mean NEE data within each temperature class 
%		are normalized against the 80th NEE percentile for that class. 
%	3. Method A (pooling to annual) 
%		further pools the pooled normalized data from W over all time windows 
%		before estimating a single change-point per year. 
% 
%	The detailed analysis parameters are output in a Stats structured
%	record. 

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

    % Define constants
    nSeasons = 4;
    nStrataX = 8;
    
    % Initialize parameters
    nt = length(t);
    
    iNight = get_iNight(fNight);

    updated_uStar = update_uStar(uStar);
    
    ntN = get_ntN(t, nSeasons);

    % Generate itNee and ntNee
    itNee = get_itNee(NEE, uStar, T, iNight);
    ntNee = length(itNee);

    Cp2 = setup_Cp(nSeasons, nStrataX, nBoot);
    Cp3 = setup_Cp(nSeasons, nStrataX, nBoot);

    Stats2 = setup_Stats(nBoot, nSeasons, nStrataX);
    Stats3 = setup_Stats(nBoot, nSeasons, nStrataX);
	
    % by alessio
	%disp(' ');
	%fprintf('cpdBootstrapUStarTh4Season20100901  %s   nObs: %g %g %g %g \n',cSiteYr,nt,sum(~isnan([NEE uStar T])));
	%disp(' ');

	
	if ntNee>=ntN;
		
		% Boot-strapping.
		
		for iBoot=1:nBoot;
			
			%t0=now;
			
			it = generate_rand_int_array(nt);
			% ntNee=sum(ismember(it,itNee));
			
			if iBoot>1; fPlot=0; end;
			
			[xCp2,xStats2, xCp3,xStats3] = ...
				cpdEvaluateUStarTh4Season20100901 ...
					(t(it),NEE(it),updated_uStar(it),T(it),fNight(it),fPlot,cSiteYr); 
			
			%dt=(now-t0)*24*60*60;
            %by alessio
			%fprintf('Bootstrap uStarTh %s:  %g/%g   nObs %g  Cp2 %4.3f  Cp3 %4.3f   %3.1fs \n', ...
			%	cSiteYr,iBoot,nBoot,ntNee,nanmedian(fcx2rowvec(xCp2)),nanmedian(fcx2rowvec(xCp3)),dt);
			
			Cp2(:,:,iBoot)=xCp2; Stats2(:,:,iBoot)=xStats2;
			Cp3(:,:,iBoot)=xCp3; Stats3(:,:,iBoot)=xStats3;
			
		end; % for iBoot
		
	end; % if ntNee>=ntN;

	if size(varargin)>0
		Stats2 = jsonencode(Stats2);
		Stats3 = jsonencode(Stats3);
	end
end