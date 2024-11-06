function [Stats] = setup_Stats(nBoot, nSeasons, nStrataX, varargin)

    StatsMT = generate_statsMT();

    %Stats=StatsMT;

	% This function will return different outputs for the case where any of
	% nBoot, nSeasons or nStrataX are zero, depending on whether 'Stats' is 
	% preallocated with 'StatsMT' or not.
	% This does not affect the normal running of the code. Just this edge case.

	% We should follow up with Gilberto to understand his preferred implementation.
	% James Emberton 21/10/2024

	% Preallocate the Stats array by repeating the template
	Stats(1:nSeasons, 1:nStrataX, 1:nBoot) = StatsMT;

	
	for i = 1:length(varargin)
		a = varargin{i};
		if iscell(a) && strcmp(a{1}, 'jsonencode')
			for j = 2:length(a)
				switch a{j}
					case 1
						Stats = jsonencode(Stats);
				end
			end
		end
	end
end
