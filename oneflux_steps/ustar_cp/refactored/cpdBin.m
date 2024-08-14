function [nBins, mx, my] = cpdBin(x, y, dx, nPerBin)
    % Main function to calculate binned mean values of x and y

    % Handle invalid or edge cases early
    if isempty(x) || isempty(y) || isempty(dx) || dx <= 0
        disp('Function cpdBin aborted. Invalid input parameters.');
        nBins = 0;
        mx = [];
        my = [];
        return;
    end

    % Initialize output variables
    nBins = 0;
    mx = [];
    my = [];

    % Remove NaN values from x and y
    validIndices = ~isnan(x + y);
    x = x(validIndices);
    y = y(validIndices);

    % Choose binning strategy based on the type of dx
    if isscalar(dx)
        [nBins, mx, my] = binUsingScalarDx(x, y, dx, nPerBin);
    elseif isempty(dx)
        [nBins, mx, my] = binUsingNPerBin(x, y, nPerBin);
    else
        [nBins, mx, my] = binUsingVectorDx(x, y, dx, nPerBin);
    end
end

function [nBins, mx, my] = binUsingScalarDx(x, y, dx, nPerBin)
    % Binning strategy when dx is a scalar
    nx = min(x);
    xx = max(x);
    binEdges = nx:dx:xx;
    nBins = 0;

    for jx = binEdges
        ix = find(abs(x - jx) < 0.5 * dx);
        if length(ix) >= nPerBin
            nBins = nBins + 1;
            mx(nBins, 1) = mean(x(ix));
            my(nBins, 1) = mean(y(ix));
        end
    end
end

function [nBins, mx, my] = binUsingNPerBin(x, y, nPerBin)
    % Binning strategy when dx is empty, using nPerBin
    nValid = length(x);
    nBins = floor(nValid / nPerBin);
    if nBins == 0
        return;
    end

    mx = NaN(nBins, 1);
    my = NaN(nBins, 1);
    binEdges = prctile(x, linspace(0, 100, nBins + 1));
    
    for i = 1:nBins
        ix = find(x >= binEdges(i) & x <= binEdges(i+1));
        if length(ix) >= nPerBin
            mx(i) = mean(x(ix));
            my(i) = mean(y(ix));
        end
    end
end

function [nBins, mx, my] = binUsingVectorDx(x, y, dx, nPerBin)
    % Binning strategy when dx is a vector specifying the bin borders
    nBins = 0;
    mx = [];
    my = [];
    
    for i = 1:(length(dx) - 1)
        ix = find(x >= dx(i) & x <= dx(i+1));
        if length(ix) >= nPerBin
            nBins = nBins + 1;
            mx(nBins, 1) = mean(x(ix));
            my(nBins, 1) = mean(y(ix));
        end
    end
end
