	function [CpA,nA,tW,CpW,cMode,cFailure,fSelect,sSine,FracSig,FracModeD,FracSelect] ... 
		= cpdAssignUStarTh20100901(Stats,fPlot,cSiteYr) 

%cpdAssignUStarTh20100901
%	aggregates and assigns uStarTh from the Stats* structured records 
%	as output by cpdBootstrapUStarTh20100901. 
%
%Syntax: 
%
%	[CpA,nA,tW,CpW,cMode,cFailure,fSelect,sSine,FracSig,FracModeD,FracSelect] ... 
%		= cpdExtractuStarTh20100901 (Stats,fPlot,cSiteYr) 
%
%	where: 
%
%	-	Stats is a structured record output by
%		cpdBootstrapuStarTh20100901, can be:
%		- Stats2 (2-parameter operational change-point model) or 
%		- Stats3 (3-parameter diagnostic change-point model)
%	-	fPlot is a flag that is set to 1 for plotting
%		the aggregation analysis
%	-	cSiteYr is text containing site and year for the fPlot plot
%
%	-	CpA is a scalar or vector of annual uStarTh (ChangePoint) means 
%	-	nA is the number of selected change-points in the annual mean
%	-	CpW and tW are vectors showing seasonal variation in uStarTh 
%	-	cMode is the dominant change-point mode: 
%		D Deficit (b1>0) or E Excess (b1<0)
%	-	cFailure is a string containing failure messages
%	-	fSelect is an array the same size as Stats* that flags the
%		selected Cp values for computing CpA and CpW
%	-	sSine contains the coefficients of an annual sine curve 
%		fit to tW and CpW
%	-	FracSig,FracModeD,FracSelect are the fraction of attempted
%		change-point detections that are significant, in mode D and
%		select.
%
%The Stats2 or Stats3 records may be 2D (nWindows x nStrata) 
%or 3D (nWindows x nStrata x nBoot). If 2D, then CpA 
%is a scalar and CpW is averaged across the nStrata temperature strata.  
%If 3D, then CpA is a vector of length nBoot and CpW is averaged 
%across nBoot bootstraps and nStrata temperature strata.  
%Stats input is accepted from both 4Season (nWindows=4) 
%and flexible window (nWindows>=7) processing. 
%
%The aggregation process is selective, selecting only: 
% - significant change points (p <= 0.05)
% - in the dominant mode (Deficit (b1>0) or Excess (b1<0))
% - after excluding outliers (based on regression stats).
%No assignment is made if the detection failure rate 
%is too high.   

%	========================================================================
%	========================================================================

%	Functions called: 
%
%		fcBin, fcDatetick, fcEqnAnnualSine, fcNaniqr, fcReadFields 
%		fcr2Calc, fcx2colvec, fcx2rowvec
%		stats toolbox:  nanmedian, nanmean, nlinfit, prctile

%	Written 16 April 2010 by Alan Barr

%	=======================================================================
%	=======================================================================

	CpA=[]; nA=[]; tW=[]; CpW=[]; fSelect=[]; cMode=''; cFailure=''; sSine=[]; 
	FracSig=[]; FracModeD=[]; FracSelect=[]; 

%	Compute window sizes etc.	

	nDim=ndims(Stats); 
	switch nDim; 
		case 2; [nWindows,nBoot]=size(Stats); nStrata=1; nStrataN=0.5; 
		case 3; [nWindows,nStrata,nBoot]=size(Stats); nStrataN=1;  
		otherwise; cFailure='Stats must be 2D or 3D.'; return; 
	end; 
	nWindowsN=4; nSelectN=nWindowsN*nStrataN*nBoot; 
	
	CpA=NaN*ones(nBoot,1); nA=NaN*ones(nBoot,1); tW=NaN*ones(nWindows,1); CpW=NaN*ones(nWindows,1);

%	Extract variable arrays from Stats structure.	
%	Reassign mt and Cp as x* to retain array shape, 
%	then convert the extracted arrays to column vectors. 

	cVars={'mt','Cp','b1','c2','cib1','cic2','p'}; nVars=length(cVars); 
	for i=1:nVars; 
		cv=char(cVars(i)); eval([cv '=fcReadFields(Stats,''' cv ''');']); 
		switch cv; 
			case 'mt'; xmt=mt; 
			case 'Cp'; xCp=Cp; 
			otherwise; 
		end; 
		eval([cv '=fcx2colvec(' cv ');']); 
	end; 
	pSig=0.05; fP = p<=pSig; 
	
%	Determine if Stats input is from the operational 2-parameter 
%	or diagnostic 3-parameter change-point model
%	and set c2 and cic2 to zero if 2-parameter 

	nPar=3; if sum(~isnan(c2))==0; nPar=2; c2=0*b1; cic2=c2; end; 

%	Classify Cp regressions by slopes of b1 and c2 regression coeff: 
%	- NS: not sig, mfP=NaN, p>0.05
%	- ModeE: atypical significant Cp (b1<c2)
%	- ModeD: typical significant Cp (b1>=c2) 

	iTry=find(~isnan(mt)); nTry=length(iTry); 
	iCp=find(~isnan(b1+c2+Cp)); nCp=length(iCp); 
	iNS=find(fP==0 & ~isnan(b1+c2+Cp)); nNS=length(iNS); 
	iSig=find(fP==1 & ~isnan(b1+c2+Cp)); nSig=length(iSig); 
	iModeE=find(fP==1 & b1<c2); nModeE=length(iModeE); 
	iModeD=find(fP==1 & b1>=c2); nModeD=length(iModeD); 
	
%	Evaluate and accept primary mode of significant Cps
				
	if nModeD>=nModeE; iSelect=iModeD; cMode='D'; else iSelect=iModeE; cMode='E'; end; nSelect=length(iSelect); 
	fSelect=zeros(size(fP)); fSelect(iSelect)=1; fSelect=logical(fSelect); 
	fModeD=NaN*ones(size(fP)); fModeD(iModeD)=1; 
	fModeE=NaN*ones(size(fP)); fModeE(iModeE)=1; 
	
	FracSig=nSig/nTry; FracModeD=nModeD/nSig; FracSelect=nSelect/nTry; 
	
%	Abort analysis if too few of the regressions produce significant Cps. 

	if FracSelect<0.10; cFailure='Less than 10% successful detections. '; return;  end; 
				
%	Exclude outliers from Select mode based on Cp and regression stats

	switch nPar; 
		case 2; x=[Cp b1 cib1]; nx=3; 
		case 3; x=[Cp b1 c2 cib1 cic2]; nx=5; 
	end; 
	
	mx=nanmedian(x); sx=fcNaniqr(x); 
	xNorm=NaN*x; for i=1:nx; xNorm(:,i)=(x(:,1)-mx(i))/sx(i); end; 
	xNormX=max(abs(xNorm),[],2); 
	ns=5; fOut=(xNormX>ns); iOut=find(fOut); 
	iSelect=setdiff(iSelect,iOut); nSelect=length(iSelect); 
	fSelect = ~fOut & fSelect; 
	fModeD(iOut)=NaN; iModeD=find(fModeD==1); nModeD=length(iModeD); 
	fModeE(iOut)=NaN; iModeE=find(fModeE==1); nModeE=length(iModeE); 
	iSig=union(iModeD,iModeE); nSig=length(iSig); 
	
	FracSig=nSig/nTry; FracModeD=nModeD/nSig; FracSelect=nSelect/nTry;
	
	if nSelect<nSelectN; cFailure=sprintf('Too few selected change points: %g/%g',nSelect,nSelectN); return;  end; 
	
%	Aggregate the values to season and year.

	xCpSelect=NaN*xCp; xCpSelect(iSelect)=xCp(iSelect); xCpGF=xCpSelect; 
	switch nDim;
		case 2; CpA=fcx2colvec(nanmean(xCpGF)); 
			nA=fcx2colvec(sum(~isnan(xCpSelect))); 
		case 3; CpA=fcx2colvec(nanmean(reshape(xCpGF,nWindows*nStrata,nBoot))); 
			nA=fcx2colvec(sum(~isnan(reshape(xCpSelect,nWindows*nStrata,nBoot)))); 
	end;
	
%	Calculate mean tW and CpW for each window based on Select data only.  
%	Because the bootstrap varies the number of windows among bootstraps, 
%	base on the median number of windows and reshape sorted data.  

	nW=nanmedian(sum(~isnan(reshape(xmt,nWindows,nStrata*nBoot)))); 
	[mtSelect,i]=sort(mt(iSelect)); CpSelect=Cp(iSelect(i)); 
	xBins=prctile(mtSelect,0:(100/nW):100); 
	[n,tW,CpW]=fcBin(mtSelect,CpSelect,xBins,0); 
	
%	Fit annual sine curve 
	
	bSine=[1,1,1]; 
	[bSine]=nlinfit(mt(iSelect),Cp(iSelect),'fcEqnAnnualSine',bSine); 
	yHat=fcEqnAnnualSine(bSine,mt(iSelect)); r2=fcr2Calc(Cp(iSelect),yHat); 
	mtHat=sort(mt(iSelect)); CpHat=fcEqnAnnualSine(bSine,mtHat); 
	
	if bSine(2)<0; bSine(2)=-bSine(2); bSine(3)=bSine(3)+365.25/2; end; 
	bSine(3)=mod(bSine(3),365.25); 
	sSine=[fcx2rowvec(bSine) r2]; 
	
%	=======================================================================
%	=======================================================================
	
	if fPlot; 
		
		FracSelectByWindow=sum(reshape(~isnan(xCpGF),nWindows,nStrata*nBoot),2)./sum(reshape(~isnan(xmt),nWindows,nStrata*nBoot),2); 
		mtByWindow=nanmean(reshape(xmt,nWindows,nStrata*nBoot),2); 
		
		fcFigLoc(1,0.5,0.45,'NE'); 
		
		subplot('position',[0.08 0.56 0.60 0.38]); hold on; box on; 
		plot(mt,Cp,'r.',mt(iModeE),Cp(iModeE),'b.',mt(iModeD),Cp(iModeD),'g.');
		nBins=nWindows; 
		if nModeD>=nBins*30;
			[n,mx,my]=fcBin(mt(iModeD),Cp(iModeD),[],round(nModeD/nBins));
			hold on; plot(mx,my,'ko-','MarkerFaceColor','y','MarkerSize',8,'LineWidth',2);
		end; 
		if nModeE>=nBins*30;
			[n,mx,my]=fcBin(mt(iModeE),Cp(iModeE),[],round(nModeE/nBins));
			hold on; plot(mx,my,'bo-','MarkerFaceColor','c','MarkerSize',8,'LineWidth',2);
		end; 
		fcDatetick(mt,'Mo',4,1); ylabel('Cp');
		ylabel('Raw Cp Modes D (green) E (red)'); ylim([0 prctile(Cp,99.9)]);
		hold off; 
		title(sprintf('%s  Stats%g  Mode%s  nSelect/nTry: %g/%g  uStarTh: %5.3f (%5.3f) ', ...
			cSiteYr,nPar,cMode,nSelect,nTry, ... 
			nanmedian(Cp(iSelect)),0.5*diff(prctile(Cp(iSelect),[2.5 97.5])) ));
		
		subplot('position',[0.08 0.06 0.60 0.38]); hold on; box on; 
		switch cMode; case 'G'; c='g'; case 'L'; c='b'; otherwise; c='k'; end; 
		plot(mt(iSelect),Cp(iSelect),[c '.'],mtHat,CpHat,'r-','LineWidth',3); 
		plot(tW,CpW,'ro','MarkerFaceColor','y','MarkerSize',9','LineWidth',2); 
		fcDatetick(mt(iSelect),'Mo',4,1); 
		ylabel('Select Cp'); ylim([0 prctile(Cp(iSelect),99)]);
		title(sprintf('Cp = %5.3f + %5.3f sin(wt - %3.0f) (r^2 = %5.3f) ',bSine,r2 )); 
		
		subplot('position',[0.76 0.56 0.22 0.38]); 
		hist(CpA,30); grid on; box on; 
		xlim([min(CpA) max(CpA)]); 
		xlabel('Annual \itu_*^{Th}'); ylabel('Frequency'); 
		title(sprintf('Median (CI): %5.3f (%5.3f) ', ... 
			nanmedian(CpA),0.5*diff(prctile(CpA,[2.5 97.5])) )); 
		
		subplot('position',[0.76 0.06 0.22 0.38]); 
		plot(mtByWindow,FracSelectByWindow,'o-'); 
		fcDatetick(mtByWindow,'Mo',4,1); 
		ylabel('FracSelectByWindow'); ylim([0 1]); 
		
	end;
	
%	=======================================================================
%	=======================================================================
	
