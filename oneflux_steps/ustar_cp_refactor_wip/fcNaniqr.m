	function [IQR]=fcnaniqr(X)
	
%fcnaniqr computes the interquartile range, ignoring NaNs. 
%
%	IQR = fcnaniqr(X) 
%	returns the interquartile range of the values in X,
%	treating NaNs as missing.  
%
%	fcnaniqr is a limited adaptation of IQR: 
%	X cannot exceed 3 dimensions, 
%	and IQR is always computed across the 
%	first non-singleton dimension of X.
%
%	For vector input, IQR is a scalar.   
%	For 2D matrix input, IQR is a row vector containing 
%		the interquartile range of each column of X.  
%	For a 3D arrays, IQR is a 2d array, computed 
%		along the first non-singleton dimension of X.
%  
%	The IQR is a robust estimate of the spread of the data, 
%	since changes in the upper and lower 25% of the data 
%	do not affect it.
%

%	Written by Alan Barr 

%	=======================================================================
%	=======================================================================

	% find non-singleton dimensions of length d

	d=size(X); d=setdiff(d,1); nd=length(d); 
	
	switch nd; 
		case 1; 
	      iYaN=find(~isnan(X)); nYaN=length(iYaN); IQR=NaN; 
		   if nYaN<=3;
				y=X(iYaN); yN=prctile(y,25); yX=prctile(y,75); IQR=yX-yN; 
			end; 
		case 2; 
			[nr,nc]=size(X); IQR=NaN*ones(1,nc); 
			for ic=1:nc;
				iYaN=find(~isnan(X(:,ic))); nYaN=length(iYaN);
				if nYaN>3;
					y=X(iYaN,ic); yN=prctile(y,25); yX=prctile(y,75); IQR(ic)=yX-yN;
				end;
			end;
		case 3; 
			[nr,nc,nq]=size(X); IQR=NaN*ones(nc,nq); 
			for iq=1:nq;
				for ic=1:nc;
					iYaN=find(~isnan(X(:,ic,iq))); nYaN=length(iYaN);
					if nYaN>3;
						y=X(iYaN,ic,iq); yN=prctile(y,25); yX=prctile(y,75); IQR(ic,iq)=yX-yN;
					end; 
				end;
			end;
   
	end; 
	
	