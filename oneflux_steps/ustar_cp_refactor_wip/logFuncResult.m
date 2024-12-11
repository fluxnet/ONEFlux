function varargout = logFuncResult(filename, f, metadata, varargin)
    % LOGFUNCRESULT Logs function inputs and outputs, saving each variable as a CSV or JSON file.
    %
    %   [outputs...] = LOGFUNCRESULT(filename, f, metadata, varargin)
    %
    %   Inputs:
    %       - filename: Name of the log file (e.g., 'log.json').
    %       - f       : Function handle to the function you want to log.
    %       - metadata: Structure containing information about how to log the function.
    %       - varargin: Cell array of input arguments for the function f.
    %
    %   Outputs:
    %       - varargout: The outputs returned by the function f.

    % Example metadata structure:
    % metadata = struct();
    % metadata.siteFile = 'US-Seg'; % Site file name
    % metadata.oneFluxDir = '/path/to/ONEFlux/directory';
    % metadata.relArtifactsDir = '/relative/path/to/tests/test_artifacts';
    % metadata.frequency = 10; % Log every 10th call
    % metadata.offset = 0; % Start logging from the first call

    % The site file name can be extracted as so if `cSiteYr` is present

    % cSiteYrSplit = strsplit(cSiteYr, '.');
    % metadata.siteFile = cSiteYrSplit{1};

    % cpdFindChangePoint does not take cSitreYr in as an argument, so could be passed in using varargin.

    % Uusage. Replace

    %   [xCp2,xStats2, xCp3,xStats3] = ...
  	% cpdEvaluateUStarTh4Season20100901 ...
	  % 	(t(it),NEE(it),updated_uStar(it),T(it),fNight(it),fPlot,cSiteYr);

    % with this:

    %   metadata.inputNames = {'t_it_', 'NEE_it_', 'updated_uStar_it_', 'T_it_', 'fNight_it_', 'fplot', 'cSiteYr'};
    %   metadata.outputNames = {'xCp2', 'xStats2', 'xCp3', 'xStats3'};

    %   [xCp2,xStats2, xCp3,xStats3] = ...
    %     logFuncResult('log.json', @cpdEvaluateUStarTh4Season20100901, metadata,
    %                   t(it),NEE(it),updated_uStar(it),T(it),fNight(it),fPlot,cSiteYr);

    % In the main launch.m function at the very end you must clear the global frequency cache:

    % clear global globalFrequencyMetadata

    metadata.description = func2str(f);
    metadata.inputNames;
    metadata.outputNames;
    oneFluxDir = metadata.oneFluxDir;
    relArtifactsDir = metadata.relArtifactsDir;
    functionDir = string(func2str(f)) + '_artifacts';

    % Initialize frequency
    if ~isfield(metadata, 'frequency')
        metadata.frequency = 10; % Initialize frequency
    end
    if ~isfield(metadata, 'offset')
        metadata.offset = 0; % Initialize offset
    end
    offset = metadata.offset;
    frequency = metadata.frequency;

    % Declare a global variable to persist call counts across invocations
    global globalFrequencyMetadata;
    if isempty(globalFrequencyMetadata)
        globalFrequencyMetadata = struct(); % Initialize if not already set
    end

    % Use the string representation of the function handle as a unique identifier
    funcId = func2str(f);

    % Initialize call count for this function in the global metadata if not already present
    if ~isfield(globalFrequencyMetadata, funcId)
        globalFrequencyMetadata.(funcId) = offset; % Initialize call count
    end


    % Apply the function f to the input arguments and capture outputs
    % Determine the number of outputs the function f produces
    nOut = nargout(f);
    if nOut > 0
        % Function has variable number of outputs
        nOut = nargout;
    end

    % Prepare cell array to capture outputs
    outputs = cell(1, nOut);

    % Call the function with the inputs and capture outputs
    [outputs{:}] = f(varargin{:});

    % Return outputs to caller
    varargout = outputs;


    % Check if we should log based on the frequency
    if mod(globalFrequencyMetadata.(funcId), frequency) == offset

        siteDir = metadata.siteFile;
        % Add the value as a suffix to siteDir
        siteDirWithSuffix = sprintf('%s_%d', siteDir, globalFrequencyMetadata.(funcId));

        dirPath = fullfile(oneFluxDir, relArtifactsDir, functionDir, siteDirWithSuffix);
        if ~exist(dirPath, 'dir')
            mkdir(dirPath);
        end
        filePath = fullfile(dirPath, filename);


        % Get function name
        function_name = func2str(f);

        inputPaths = saveVariables(varargin, metadata.inputNames, 'input', dirPath, relArtifactsDir);
        outputPaths = saveVariables(outputs, metadata.outputNames, 'output', dirPath, relArtifactsDir);

        % Create the log entry structure
        logEntry = struct();
        logEntry.(function_name) = struct();
        logEntry.(function_name).siteFile = metadata.siteFile;
        logEntry.(function_name).description = metadata.description;
        logEntry.(function_name).input = inputPaths;
        logEntry.(function_name).output = outputPaths;

        % Convert the log entry to JSON
        jsonStr = jsonencode(logEntry);

        % Write the JSON string to the file
        fileID = fopen(filePath, 'w');
        fprintf(fileID, '%s\n', jsonStr);
        fclose(fileID);

        % Inform the user
        % fprintf('Result has been saved to %s\n', filePath);
    end

    % Increment the call count in the global metadata
    globalFrequencyMetadata.(funcId) = globalFrequencyMetadata.(funcId) + 1;
end



function paths = saveVariables(vars, varNames, ioPrefix, dirPath, artifactsDir)
    % Helper function to process and save variables and generate paths
    paths = struct();
    numVars = length(vars);
    for i = 1:numVars
        if length(varNames) >= i
            fieldName = varNames{i};
        else
            fieldName = sprintf('var%d', i);
        end
        % Save variable as CSV
        filename = sprintf('%s_%s.csv', ioPrefix, fieldName);
        filename = saveVariableAsCSVorJSON(vars{i}, dirPath, filename);
        relativeFilePath = fullfile(artifactsDir, filename);
        paths.(fieldName) = relativeFilePath;
    end
end


function filename = saveVariableAsCSVorJSON(var, dirPath, filename)
    % SAVEVARIABLEASCSV Saves a variable to a CSV file.
    % Supports numeric arrays, tables, cell arrays, structs, strings.
    filePath = fullfile(dirPath, filename);
    if isnumeric(var) || islogical(var)
        writematrix(var, filePath)
        % writematrix(var, filePath, 'WriteMode','append');
    elseif istable(var)
        writetable(var, filePath);
    elseif iscell(var)
        % Try to write cell array
        try
            writecell(var, filePath);
        catch
            error('Error writing cell array to CSV.');
        end
    elseif isstruct(var)
        % Convert struct to table
        try
            T = struct2table(var);
            writetable(T, filePath);
        catch csvError
            warning('Failed to write to CSV. Trying JSON format instead.');

            try
                jsonFilename = strrep(filename, '.csv', '.json');
                jsonFilePath = fullfile(dirPath, jsonFilename);
                jsonData = jsonencode(var);

                fid = fopen(jsonFilePath, 'w');
                % fid = fopen(jsonFilePath, 'a');

                if fid == -1
                    error('Could not open file for writing JSON.');
                end

                fwrite(fid, jsonData, 'char');
                fclose(fid);
                filename = jsonFilename;
                % disp('Successfully written struct to JSON.');

            catch jsonError
                % If both CSV and JSON writing fail, throw an error
                error('Error writing struct to CSV and JSON.\nCSV Error: %s\nJSON Error: %s', ...
                      csvError.message, jsonError.message);
            end

        end
    elseif ischar(var) || isstring(var)
        % Convert to cell and write
        writecell({var}, filePath);
    else
        error('Unsupported variable type for CSV export.');
    end
end