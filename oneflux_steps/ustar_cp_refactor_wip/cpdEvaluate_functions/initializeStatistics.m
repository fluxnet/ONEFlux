function [Stats2, Stats3] = initializeStatistics(nSeasons, nStrataX, varargin)

	StatsMT = generate_statsMT();
						
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