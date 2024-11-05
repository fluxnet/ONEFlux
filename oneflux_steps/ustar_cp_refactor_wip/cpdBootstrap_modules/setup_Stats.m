function [Stats] = setup_Stats(nBoot, nSeasons, nStrataX, varargin)

    StatsMT = generate_statsMT();

    Stats=StatsMT;

	% This function will return different outputs for the case where any of
	% nBoot, nSeasons or nStrataX are zero, depending on whether 'Stats' is 
	% preallocated with 'StatsMT' or not.
	% This does not affect the normal running of the code. Just this edge case.

	% We should follow up with Gilberto to understand his preferred implementation.
	% James Emberton 21/10/2024

	% Discussed with Gilberton on 25/10/2024. Agreed to preserve current implementation. 
	% Will review when we are converting to python

	for iBoot=1:nBoot;
		for iSeason=1:nSeasons;
			for iStrata=1:nStrataX;
				Stats(iSeason,iStrata,iBoot)=StatsMT;
			end; 
		end; 
	end;
	if size(varargin)>0;
		Stats = jsonencode(Stats);
end
