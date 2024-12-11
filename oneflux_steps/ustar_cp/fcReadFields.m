function x = fcReadFields(stats, FieldName, varargin)

	s = [];

	if nargin > 2 && any(strcmp(varargin, 'jsondecode'))
		s = jsondecode(stats);
	else
		s = stats; % Assume stats is already a struct
	end

	if isempty(s)
		error('Decoded structure is empty. Check the JSON format.');
	end

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


function stats = jsonToStats(jsonStr)
    % Decode the JSON string into a MATLAB structure array
    decodedStats = jsondecode(jsonStr);

    % Define the template structure
    statsTemplate = struct(...
        'n', NaN, 'Cp', NaN, 'Fmax', NaN, 'p', NaN, ...
        'b0', NaN, 'b1', NaN, 'b2', NaN, 'c2', NaN, ...
        'cib0', NaN, 'cib1', NaN, 'cic2', NaN, ...
        'mt', NaN, 'ti', NaN, 'tf', NaN, ...
        'ruStarVsT', NaN, 'puStarVsT', NaN, ...
        'mT', NaN, 'ciT', NaN ...
    );

    % Ensure decodedStats is a struct
    if ~isstruct(decodedStats)
        error('Invalid JSON format: expected a structure.');
    end

    % Determine structure size
    dataSize = size(decodedStats);

    % Preallocate the stats structure
    stats = repmat(statsTemplate, dataSize);

    % Populate stats structure with error handling
    for i = 1:dataSize(1)
        for j = 1:dataSize(2)
            for k = 1:max(1, dataSize(3))
                if isfield(decodedStats, 'n') && ~isempty(decodedStats(i, j, k))
                    stats(i, j, k) = mergeStructures(statsTemplate, decodedStats(i, j, k));
                else
                    stats(i, j, k) = statsTemplate; % Use default if not filled
                end
            end
        end
    end
end

function outStruct = mergeStructures(template, inputStruct)
    fields = fieldnames(template);

    for f = 1:numel(fields)
        fieldName = fields{f};
        if isfield(inputStruct, fieldName) && ~isempty(inputStruct.(fieldName))
            outStruct.(fieldName) = inputStruct.(fieldName);
        else
            outStruct.(fieldName) = template.(fieldName); % Default if missing
        end
    end
end
