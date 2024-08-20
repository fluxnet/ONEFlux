	function y=fcEqnAnnualSine(b,t); 
	
	nDaysPerYr=datenum(2000-1,12,31)/2000; 
	Omega=2*pi/nDaysPerYr; 
	y=b(1)+b(2)*sin(Omega*(t-b(3))); 
	
