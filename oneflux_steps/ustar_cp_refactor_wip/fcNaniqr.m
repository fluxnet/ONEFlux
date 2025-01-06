	function [IQR]=fcNaniqr(X)
	
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

	nd = get_dims(X);
	
	switch nd; 
		case 1; 
	    	IQR = iqr_1D_eval(X);
		case 2; 
			IQR = iqr_2d_eval(X);
		case 3; 
			IQR = iqr_3d_eval(X);
   
	end; 
	
	