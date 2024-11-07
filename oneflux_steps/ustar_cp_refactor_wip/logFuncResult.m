function varargout = logFuncResult(filename, f, metadata, varargin)
    % LOGFUNCRESULT Logs function inputs and outputs, saving each variable as a CSV file.
    %
    %   [outputs...] = LOGFUNCRESULT(filename, f, varargin)
    %
    %   Inputs:
    %       - filename: Name of the log file (e.g., 'log.json').
    %       - f: Function handle to the function you want to log.
    %       - varargin: Cell array of input arguments for the function f.
    %
    %   Outputs:
    %       - varargout: The outputs returned by the function f.

    % Set default metadata if not provided
 


    metadata.description = func2str(f);
    metadata.inputNames;
    metadata.outputNames;
    


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
    
    oneFluxDir = '/home/ia/iccs_repos/ONEFlux/';
    artifactsDir = 'tests/test_artifacts/launch_artifacts/';
    dirPath = fullfile(oneFluxDir, artifactsDir);
    if ~exist(dirPath, 'dir')
        mkdir(dirPath);
    end
    filePath = fullfile(dirPath, filename);

    % Generate a unique identifier
    id = char(java.util.UUID.randomUUID);

    % Get function name
    function_name = func2str(f);

    % Create input paths structure
    inputPaths = struct();
    numArgs = length(varargin);
    for i = 1:numArgs
        % disp(metadata.inputNames);
        if length(metadata.inputNames) >= i
            fieldName = metadata.inputNames{i};
            
        else
            fieldName = sprintf('arg%d', i);
        end
        % Save input variable to CSV
        inputFilename = sprintf('%s_input_%s_%s.csv', function_name, fieldName, metadata.siteFile);
        inputFilePath = fullfile(dirPath, inputFilename);
        relativeInputFilePath = fullfile(artifactsDir, inputFilename);
        saveVariableAsCSV(varargin{i}, inputFilePath);
        % Store the path in the log
        inputPaths.(fieldName) = relativeInputFilePath;
    end

    % Save output variables to CSV
    outputPaths = struct();
    numOutputs = length(outputs);
    for i = 1:numOutputs
        if length(metadata.outputNames) >= i
            fieldName = metadata.outputNames{i};
        else
            fieldName = sprintf('out%d', i);
        end
        outputFilename = sprintf('%s_output_%s_%s.csv', function_name, fieldName, metadata.siteFile);
        outputFilePath = fullfile(dirPath, outputFilename);
        relativeOutputFilePath = fullfile(artifactsDir, outputFilename);
        saveVariableAsCSV(outputs{i}, outputFilePath);
        % Store the path in the log
        outputPaths.(fieldName) = relativeOutputFilePath;
    end

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
    fileID = fopen(filePath, 'a');
    fprintf(fileID, '%s\n', jsonStr);
    fclose(fileID);

    % Inform the user
    % fprintf('Result has been saved to %s\n', filePath); 
end

function saveVariableAsCSV(var, filePath)
    % SAVEVARIABLEASCSV Saves a variable to a CSV file.
    % Supports numeric arrays, tables, cell arrays, structs, strings.

    if isnumeric(var) || islogical(var)
        writematrix(var, filePath);
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
        catch
            error('Error writing struct to CSV.');
        end
    elseif ischar(var) || isstring(var)
        % Convert to cell and write
        writecell({var}, filePath);
    else
        error('Unsupported variable type for CSV export.');
    end
end