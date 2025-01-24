	function rv=fcx2rowvec(x); % column vector.
	
	rv=reshape(x,1,prod(size(x))); 