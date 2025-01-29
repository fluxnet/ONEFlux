function [IQR] = iqr_3d_eval(X)
    [~,nc,nq]=size(X); 
	IQR=NaN*ones(nc,nq); 
		for iq=1:nq;
			for ic=1:nc;
				iYaN=find(~isnan(X(:,ic,iq))); 
				nYaN=length(iYaN);
				if nYaN>3;
					y=X(iYaN,ic,iq); 
					yN=prctile(y,25); 
					yX=prctile(y,75); 
					IQR(ic,iq)=yX-yN;
				end; 
			end;
		end;
    end