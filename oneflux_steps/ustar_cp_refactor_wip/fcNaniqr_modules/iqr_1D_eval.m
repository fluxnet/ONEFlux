function [IQR] = iqr_1D_eval(X)

    iYaN=find(~isnan(X)); 
		nYaN=length(iYaN); 
		IQR=NaN; 
			if nYaN<=3
				y=X(iYaN); 
				yN=prctile(y,25); 
				yX=prctile(y,75); 
				IQR=yX-yN; 
			end
    end