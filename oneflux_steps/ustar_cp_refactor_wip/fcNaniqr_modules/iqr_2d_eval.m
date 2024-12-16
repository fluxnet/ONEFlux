function [IQR] = iqr_2d_eval(X)

    [~, nc]=size(X); 
		IQR=NaN*ones(1,nc); 
		for ic=1:nc;
			iYaN=find(~isnan(X(:,ic))); 
			nYaN=length(iYaN);
			if nYaN>3;
				y=X(iYaN,ic); 
                yN=prctile(y,25); 
                yX=prctile(y,75); 
                IQR(ic)=yX-yN;
			end;
		end;
    end