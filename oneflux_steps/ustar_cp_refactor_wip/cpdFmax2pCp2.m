	function p=cpdFmax2pCp2(Fmax,n) 
	
%p = cpdFmax2pCp2(Fmax,n) 
%
%	assigns the probability p that the 2-parameter, 
%	operational change-point model fit is significant. 
%
%	It interpolates within a Table pTable, generated 
%	for the 2-parameter model by Alan Barr following Wang (2003).  
%
%	If Fmax is outside the range in the table, 
%	then the normal F stat is used to help extrapolate. 

%	Functions called: stats toolbox - fcdf, finv

%	Written by Alan Barr April 2010

%	=======================================================================
%	=======================================================================

	p=NaN; if isnan(Fmax) | isnan(n) | n<10; return; end; 
	
	pTable=[0.80 0.90 0.95 0.99]'; np=length(pTable); 
	nTable=[10 15 20 30 50 70 100 150 200 300 500 700 1000]'; % tmp run to 200 1e5 reps
	FmaxTable = ...
		 [	3.9293 6.2992 9.1471 18.2659; ... 
			3.7734 5.6988 7.8770 13.8100; ...
			3.7516 5.5172 7.4426 12.6481; ...
			3.7538 5.3224 7.0306 11.4461; ...
			3.7941 5.3030 6.8758 10.6635; ...
			3.8548 5.3480 6.8883 10.5026; ...
			3.9798 5.4465 6.9184 10.4527; ...
			4.0732 5.5235 6.9811 10.3859; ...
			4.1467 5.6136 7.0624 10.5596; ...
			4.2770 5.7391 7.2005 10.6871; ...
			4.4169 5.8733 7.3421 10.6751; ...
			4.5556 6.0591 7.5627 11.0072; ...
			4.7356 6.2738 7.7834 11.2319]; 

	FmaxCritical=[]; for ip=1:np; FmaxCritical(ip)=interp1(nTable,FmaxTable(:,ip),n,'pchip'); end; 
	if Fmax<FmaxCritical(1); 
		fAdj=finv(0.90,3,n)*Fmax/FmaxCritical(1); 
		p=2*(1-fcdf(fAdj,3,n)); 
		if p>1; p=1; end; 
		return; end; 
	if Fmax>FmaxCritical(end); 
		fAdj=finv(0.995,3,n)*Fmax/FmaxCritical(3); 
		p=2*(1-fcdf(fAdj,3,n)); 
		if p<0; p=0; end; 
		return; end; 
	p=interp1(FmaxCritical,1-pTable,Fmax,'pchip'); 
	
