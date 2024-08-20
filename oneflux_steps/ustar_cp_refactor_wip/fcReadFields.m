	function x = fcReadFields(s,FieldName); 
		
	nd=ndims(s); ns=size(s); x=NaN*ones(ns); 
	
	switch nd; 
		case 2; 
			for i=1:ns(1); 
				for j=1:ns(2); 
					tmp=getfield(s,{i,j},FieldName); 
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
