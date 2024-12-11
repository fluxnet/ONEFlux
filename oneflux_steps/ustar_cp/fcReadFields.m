function x = fcReadFields(stats, FieldName, varargin)

    % Initialize output
    nd = ndims(s); 
    ns = size(s); 
    x = NaN * ones(ns); 
    
    % Handle 2D and 3D arrays
    switch nd
        case 2
            for i = 1:ns(1)
                for j = 1:ns(2)
                    try
                        tmp = getfield(s, {i, j}, FieldName); 
                        if ~isempty(tmp)
                            x(i, j) = tmp;
                        end
                    catch
                        % Field not found
                    end
                end
            end
        case 3
            for i = 1:ns(1)
                for j = 1:ns(2)
                    for k = 1:ns(3)
                        try
                            tmp = getfield(s, {i, j, k}, FieldName); 
                            if ~isempty(tmp)
                                x(i, j, k) = tmp;
                            end
                        catch
                            % Field not found
                        end
                    end
                end
            end
    end
end
