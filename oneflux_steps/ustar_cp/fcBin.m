function [nBins,mx,my] = cpdBin(x,y,dx,nPerBin); 

%cpdBin 
%
%calculates binned mean values of vectors x and y 
%for use in change-point (uStarTh) detection 
%
%Syntax: [nBins,mx,my] = cpdBin(x,y,dx,nPerBin); 
%
%dx and nPerBin control how the data are binned. 
%	if dx is a positive scalar, it specifies the binning increment. 
%	if dx is a vector, it specifies the bin borders. 
%	if dx is empty, then nPerBin is used to bin the data, 
%		into bins with nPerBin points in each bin.   

%	-----------------------------------------------------------------------

	nBins=0; mx=[]; my=[]; 
	if dx<=0; disp('Function cpdBin aborted. dx cannot be <=0. ');  return; end; 
	
	switch length(dx);
		case 0; % if dx is empty, use nPerBin to bin the data 
				% into bins with nPerBin points in each bin.
			iYaN=find(~isnan(x+y)); nYaN=length(iYaN);
			nBins=floor(nYaN/nPerBin); 
			mx=NaN*ones(nBins,1); my=NaN*ones(nBins,1); 
			iprctile=0:(100/nBins):100;
			dx=prctile(x(iYaN),iprctile);
			xL=dx(1:(end-1)); xU=dx(2:end);
			jx=0; for i=1:length(xL);
				ix=find(~isnan(x+y) & x>=xL(i) & x<=xU(i));
				if length(ix)>=nPerBin;
					jx=jx+1;
					mx(jx)=mean(x(ix));
					my(jx)=mean(y(ix));
				end;
			end;
		case 1; % dx is a scalar specifying the binning interval.
			nx=min(x); xx=max(x);
			nx=floor(nx/dx)*dx;
			xx=ceil(xx/dx)*dx;
			for jx=nx:dx:xx;
				ix=find(~isnan(x+y) & abs(x-jx)<0.5*dx);
				if length(ix)>=nPerBin;
					nBins=nBins+1;
					mx(nBins,1)=mean(x(ix));
					my(nBins,1)=mean(y(ix));
				end;
			end;
		otherwise; % dx is a vector specifying the binning borders.
			xL=dx(1:(end-1)); xU=dx(2:end);
			for i=1:length(xL);
				ix=find(~isnan(x+y) & x>=xL(i) & x<=xU(i));
				if length(ix)>=nPerBin;
					nBins=nBins+1;
					mx(nBins,1)=mean(x(ix));
					my(nBins,1)=mean(y(ix));
				end;
			end;
	end;
	
	
			