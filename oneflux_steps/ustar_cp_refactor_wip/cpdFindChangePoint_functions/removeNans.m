function [x, y] = removeNans(xx, yy)
    % removeNaNs  Reshape input vectors into column vectors and remove NaNs pairwise.
    %
    %   [x, y] = removeNaNs(xx, yy)
    %   reshapes xx, yy into column vectors x, y respectively, then removes any
    %   elements where x or y are NaN.
    %
    %   INPUTS:
    %       xx - Input vector (row or column)
    %       yy - Input vector (row or column)
    %
    %   OUTPUTS:
    %       x  - Column vector with NaNs removed
    %       y  - Column vector with NaNs removed (corresponding rows to x)
    %
    % EXAMPLE:
    %   xx = [1; 2; NaN; 4];
    %   yy = [10; NaN; 30; 40];
    %   [x, y] = removeNaNs(xx, yy);
    %   % x = [1; 4], y = [10; 40]
    
        % Reshape xx and yy into column vectors
        x = reshape(xx, length(xx), 1);
        y = reshape(yy, length(yy), 1);
    
        % Find indices where either x or y are NaN
        iNaN = find(isnan(x + y));
    
        % Remove those entries
        x(iNaN) = [];
        y(iNaN) = [];
    
    end