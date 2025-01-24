	function cv=fcx2colvec(x) 
	
%	fcx2colvec(x) converts an array x to an n x 1 column vector cv
	
	cv=reshape(x,numel(x),1); 
	