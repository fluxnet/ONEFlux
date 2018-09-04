function [y,m,d,h,mn,s]=mydatevec(t); 
%	
%	function [y,m,d,h,mn,s]=mydatevec(t) 
%	was written by Alan Barr to return 2400 UTC rather than 0000 UTC.

	iYaN=find(~isnan(t)); 
	
	y=NaN*ones(size(t)); m=y; d=y; h=y; mn=y; s=y; 

	[yy,mm,dd,hh,mmn,ss]=datevec(t(iYaN)); 
	y(iYaN)=yy; m(iYaN)=mm; d(iYaN)=dd; 
	h(iYaN)=hh; mn(iYaN)=mmn; s(iYaN)=ss; 
	
%	set 0000 UTC to 2400 UTC, previous day.	
	
	i2400=find(h==0 & mn==0 & s==0); 
	[y2400,m2400,d2400,q,q,q]=datevec(t(i2400)-1); 
	y(i2400)=y2400; m(i2400)=m2400; d(i2400)=d2400; h(i2400)=24; 
