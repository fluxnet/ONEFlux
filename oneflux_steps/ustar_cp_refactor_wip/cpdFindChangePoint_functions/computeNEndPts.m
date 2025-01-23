function [nEndPts] = computeNEndPts(n)
    % computeNEndPts
    % Sets minimum number of endpoints, then uses a fraction (5%)
    % of n to determine nEndPts, ensuring it does not fall below
    % a specified floor.
    %
    % INPUT:
    %   n          - Number of elements in the dataset
    %
    % OUTPUTS:
    %   nEndPts    - Computed number of endpoints, floored at 5% of n,
    %                not falling below nEndPtsN
    
    % Hard-coded minimum number of endpoints
    nEndPtsN = 3;
    
    % Compute 5% of n, then floor
    nEndPts = floor(0.05 * n);
    
    % Enforce a minimum value of nEndPtsN
    if nEndPts < nEndPtsN
        nEndPts = nEndPtsN;
    end
end