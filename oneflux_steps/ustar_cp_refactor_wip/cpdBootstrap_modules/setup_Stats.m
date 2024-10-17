function [Stats] = setup_Stats(nBoot, nSeasons, nStrataX)

    StatsMT = generate_statsMT();

    Stats=StatsMT;

	for iBoot=1:nBoot;
		for iSeason=1:nSeasons;
			for iStrata=1:nStrataX;
				Stats(iSeason,iStrata,iBoot)=StatsMT;
			end; 
		end; 
	end;
end
