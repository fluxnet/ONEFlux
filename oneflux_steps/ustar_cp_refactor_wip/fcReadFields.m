	function x = fcReadFields(stats, FieldName, varargin);

		s = [];

		if nargin > 2 && any(strcmp(varargin, 'jsondecode'))
			s = jsondecode(stats);
		else
			s = stats; % Assume stats is already a struct
		end
	
		if isempty(s)
			error('Decoded structure is empty. Check the JSON format.');
		end

 
		
	nd=ndims(s); ns=size(s); x=NaN*ones(ns); 
	
  fid = fopen('fcReadFields.log', 'a');
  fprintf(fid, 'nd = %s\n', string(nd));
  fprintf(fid, 'ns = %s\n', string(ns));
  % log the s struct
  fprintf(fid, '%s\n', jsonencode(s));

	switch nd; 
		case 2; 
			for i=1:ns(1); 
				for j=1:ns(2); 
					tmp=getfield(s,{i,j},FieldName); 
          fprintf('tmp = %s\n', string(tmp));
					if ~isempty(tmp); x(i,j)=tmp; end;
				end; 
			end; 
		case 3; 
			for i=1:ns(1); 
				for j=1:ns(2); 
					for k=1:ns(3); 
						tmp=getfield(s,{i,j,k},FieldName); 
						if ~isempty(tmp); x(i,j,k)=tmp; end; 
					end;
				end;
			end;
		otherwise; 
	end; 
  fclose(fid);

