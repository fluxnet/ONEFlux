function [Stats2, Stats3] = initializeStatistics(nSeasons, nStrataX, varargin)

	StatsMT=[]; 
	StatsMT.n=NaN; StatsMT.Cp=NaN; StatsMT.Fmax=NaN; StatsMT.p=NaN; 
	StatsMT.b0=NaN; StatsMT.b1=NaN; StatsMT.b2=NaN; StatsMT.c2=NaN; 
	StatsMT.cib0=NaN; StatsMT.cib1=NaN; StatsMT.cic2=NaN; % preceding elements output by changepoint function
	StatsMT.mt=NaN; StatsMT.ti=NaN; StatsMT.tf=NaN; 
	StatsMT.ruStarVsT=NaN; StatsMT.puStarVsT=NaN; 
	StatsMT.mT=NaN; StatsMT.ciT=NaN; % these elements added by this program.  
						
	Stats2=StatsMT; Stats3=StatsMT; 
	for iSeason=1:nSeasons;
		for iStrata=1:nStrataX;
			Stats2(iSeason,iStrata)=StatsMT;
			Stats3(iSeason,iStrata)=StatsMT;
		end; 
	end;

	if length(varargin) > 0
		Stats2 = jsonencode(Stats2);
		Stats3 = jsonencode(Stats3);
	end

end