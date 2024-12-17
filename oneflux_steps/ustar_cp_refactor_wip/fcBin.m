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

      % Positions of `x` and `y` where neither is NaN
      % and the number of such positions
			iYaN=find(~isnan(x+y)); nYaN=length(iYaN);

      % Number of bins we need is then the non-values / number of points per bin
			nBins=floor(nYaN/nPerBin);

      % Initialize the output vectors with NaNs
			mx=NaN*ones(nBins,1); my=NaN*ones(nBins,1);

      % Calculate the percentile boundaries for the bins
			iprctile=0:(100/nBins):100;

      % Calculate the `x` value at the top of percentile per bin
			dx=prctile(x(iYaN),iprctile);

      % xL has all but last point
      % xU has all but first point
			xL=dx(1:(end-1)); xU=dx(2:end);
			jx=0; for i=1:length(xL);
        % indices of all points that should go in bin `jx`
				ix=find(~isnan(x+y) & x>=xL(i) & x<=xU(i));
        % if there are not too many points to go in the bin
        % store the mean of x and y vectors in the bin
				if length(ix)>=nPerBin;
					jx=jx+1;
					mx(jx)=mean(x(ix));
					my(jx)=mean(y(ix));
				end;
			end;
		case 1; % dx is a scalar specifying the binning interval.

      % Find the lower and upper bounds with x
			nx=min(x); xx=max(x);

      % Turn these into the integer values of the bounds
			nx=floor(nx/dx)*dx;
			xx=ceil(xx/dx)*dx;

      % Iterate through the space with `jx` giving
      % the bottom of the bin value between the lower and
      % upper bounds here, covering `dx` at a time
      for jx=nx:dx:xx;
        % indices of all points that should go in this bin:
        % those which arent nan and which lie within the lower half of the bin
        % (which will *throw some data away*)
        ix=find(~isnan(x+y) & abs(x-jx)<0.5*dx);
        % if we have more points to include in this bin than the
        % current bin size, then include the means in this
        % bin (counted by `nBins` so far)

				if length(ix)>=nPerBin;
					nBins=nBins+1;
          % update the bins
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


