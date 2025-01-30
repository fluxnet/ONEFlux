function [nd] = get_dims(X)
    % Size returns the shape of the input array.
    %   - If there are singleton dimensions, these are not counted as independant dimensions
    %   - E.g. if shape is (4, 4, 1), size returns (4, 4)
    % setdiff(n, 1) returns the unique values in n, excluding 1
    %   - E.g. if n = (4, 4), setdiff(n, 1) returns 4


    d=size(X); 
	d=setdiff(d,1); 
	nd=length(d);