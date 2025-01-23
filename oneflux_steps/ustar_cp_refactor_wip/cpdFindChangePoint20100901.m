	function [Cp2,s2,Cp3,s3] = cpdFindChangePoint20100901(xx,yy,fPlot,cPlot) 
	
%cpdFindChangePoint20100901
%
%is an operational version of the Lund and Reeves (2002) 
%change-point detection algorithm as modified and 
%implemented by Alan Barr for uStarTh evaluation. 
%
%Syntax: 
%
%[Cp2,s2,Cp3,s3] = cpdFindChangePoint20100901(uStar,NEE,fPlot,Txt)
%
%- Cp2 changepoint (uStarTh) from operational 2-parameter model, 
%- Cp3 changepoint (uStarTh) from diagnostic 3-parameter model, 
%- s2 structured record containing statistics from Cp2 evaluation, 
%- s3 structured record containing statistics from Cp3 evaluation
%
%- xx,yy variables for change-point detection
%- fPlot flag set to 1 to plot 
%- cPlot text string for plot title
%
%Note: The individual variables Cp2 and Cp3 are set to NaN if not significant
%but the values s2.Cp and s3.Cp are retained even if not significant.

%	=======================================================================
%	=======================================================================

%	Functions called:
%	- cpdFmax2pCp2,cpdFmax2pCp3
%	from stats toolbox - regress

%	Written by Alan Barr, last updated 7 Oct 2010 

%	=======================================================================
%	=======================================================================

	metadata = struct();
	metadata.siteFile = 'CA-Cbo_qca_ustar_2007';
	metadata.oneFluxDir = '/home/ia/iccs_repos/ONEFlux/';
	metadata.relArtifactsDir = 'tests/test_artifacts';
	metadata.frequency = 50;  %frequncy_to_log_input/ouput, defualt is 10 if not specified


%	Initialize outputs. 
	metadata.inputNames = {};
	metadata.outputNames = {'Cp2','s2','Cp3','s3'};
	[Cp2, Cp3, s2, s3] = logFuncResult('log.json', @initValues, metadata);
	% [Cp2, Cp3, s2, s3] = initValues();
%	=======================================================================
%	=======================================================================

%	Exclude missing data. 
	metadata.inputNames = {'xx', 'yy'};
	metadata.outputNames = {'x', 'y'};
	[x, y] = logFuncResult('log.json', @removeNans, metadata, xx, yy);
	% [x, y] = removeNans(xx, yy);

	n=length(x+y); if n<10; return; end;
%	Exclude extreme lin reg outliers. 
	
	metadata.inputNames = {'x', 'y', 'n'};
	metadata.outputNames = {'x', 'y'};
	[x, y] = logFuncResult('log.json', @removeOutliers, metadata, x, y, n);
	% [x, y] = removeOutliers(x, y, n);

	n=length(x+y); if n<10; return; end;

	%	Compute statistics of reduced (null hypothesis) models
%	for later testing of Cp2 and Cp3 significance.  
	metadata.inputNames = {'x', 'y', 'n'};
	metadata.outputNames = {'SSERed2', 'SSERed3'};
	% [SSERed2, SSERed3] = logFuncResult('log.json', @computeReducedModels, metadata, x, y, n);
	[SSERed2, SSERed3] = computeReducedModels(x, y, n);

	nRed2=1; nRed3=2; %nRed2 and nRed3 not used,

	%	Compute F score (Fc2 and Fc3) for each data point 	
%	in order to identify Fmax.

	MT=NaN*ones(n,1); Fc2=MT; Fc3=MT; 

	[nEndPts] = computeNEndPts(n);

	for i=1:(n-1); % min of 1 points at either end (was nEndPts before 20100318)
		
		% fit operational 2 parameter model, with zero slope above Cp2: 
		% 2 connected line segments, segment 2 has zero slope
		% parameters b0, b1 and xCp
		metadata.inputNames = {'i', 'n', 'x', 'y', 'SSERed2', 'Fc2'};
		metadata.outputNames = {'iAbv', 'Fc2'};
		[iAbv, Fc2] = logFuncResult('log.json', @fitOperational2ParamModel, metadata, i, n, x, y, SSERed2, Fc2);
		% [iAbv, Fc2] = fitOperational2ParamModel(i, n, x, y, SSERed2, Fc2); %nfull2, define within function
		% fit diagnostic 3 parameter model, with non-zero slope above Cp2: 
		% 2 connected line segments with noslope constraints 
		% parameters b0, b1, b2 and xCp
		metadata.inputNames = {'i', 'iAbv', 'n', 'x', 'y', 'SSERed3', 'Fc3'};
		metadata.outputNames = {'Fc3'};
		[Fc3] = logFuncResult('log.json', @fitOperational3ParamModel, metadata, i, iAbv, n, x, y, SSERed3, Fc3);
		% [Fc3] = fitOperational3ParamModel(i, iAbv, n, x, y, SSERed3, Fc3); %nfull3, fc3 define within function

	end; 
	
%	Assign changepoints from Fc2 and Fc3 maxima. 
%	Calc stats and test for significance of Fmax scores.

	pSig=0.05; 
	metadata.inputNames = {'Fc2', 'x', 'y', 'n', 'pSig'};
	metadata.outputNames = {'Fmax2', 'iCp2', 'xCp2', 'a2', 'a2int', 'yHat2', 'p2', 'Cp2'};
	[Fmax2, iCp2, xCp2, a2, a2int, yHat2, p2, Cp2] = logFuncResult('log.json', @fitTwoParameterModel, metadata, Fc2, x, y, n, pSig);
	% [Fmax2, iCp2, xCp2, a2, a2int, yHat2, p2, Cp2] = fitTwoParameterModel(Fc2, x, y, n, pSig);

	metadata.inputNames = {'Fc3', 'x', 'y', 'n', 'pSig'};
	metadata.outputNames = {'Fmax3', 'iCp3', 'xCp3', 'a3', 'a3int', 'yHat3', 'p3', 'Cp3'};
	[Fmax3, iCp3, xCp3, a3, a3int, yHat3, p3, Cp3] = logFuncResult('log.json', @fitThreeParameterModel, metadata, Fc3, x, y, n, pSig);
	% [Fmax3, iCp3, xCp3, a3, a3int, yHat3, p3, Cp3] = fitThreeParameterModel(Fc3, x, y, n, pSig);

%	Assign values to s2, but only if not too close to end points.  	
	
	s2.n=n; s3.n=n; 
	
	if iCp2>(nEndPts) & iCp2<(n-nEndPts);
		metadata.inputNames = {'a2', 'a2int', 'Cp2', 'Fmax2', 'p2', 's2'};
		metadata.outputNames = {'s2'};
		s2 = logFuncResult('log.json', @updateS2, metadata, a2, a2int, Cp2, Fmax2, p2, s2);
		% [s2] = updateS2(a2, a2int, Cp2, Fmax2, p2, s2);
	end;
	
	if iCp3>(nEndPts) & iCp3<(n-nEndPts);
		metadata.inputNames = {'a3', 'a3int', 'xCp3', 'Fmax3', 'p3', 's3'};
		metadata.outputNames = {'s3'};
		s3 = logFuncResult('log.json', @updateS3, metadata, a3, a3int, xCp3, Fmax3, p3, s3);  % typo? xCp3 or Cp3?
		% [s3] = updateS3(a3, a3int, xCp3, Fmax3, p3, s3);
	end;
	
%	=======================================================================
%	=======================================================================
	
	if fPlot==1;
		
		cla; hold on; 
		plot(x,y,'ko','MarkerFaceColor','k'); 
		plot(x,yHat2,'r-','linewidth',2); 
		plot(x,yHat3,'g-','linewidth',2); 
		plot([xCp2 xCp2],[min(y) max(y)],'r-','linewidth',2); 
		plot([xCp3 xCp3],[min(y) max(y)],'g-','linewidth',2); 
		hold off; grid on; box on; 
		
		if a2(2)>0; cMode='D'; else cMode='E'; end; 
		title(sprintf('%s %5.3f %s',cPlot,Cp2,cMode)); 
		
		xX=max(x)*1.02; if xX>0; xlim([0 xX]); end;
		yN=min(y); yX=max(y); dy=yX-yN; 
		yN=yN-0.02*dy; yX=yX+0.02*dy;
		if yN<yX; ylim([yN yX]); end; 
		
		set(gca,'FontSize',10);

	end;
	
%	=======================================================================
%	=======================================================================

