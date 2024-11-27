function varargout = logFuncResult(filename, f, metadata, varargin)
    % LOGFUNCRESULT Logs function inputs and outputs, saving each variable as a CSV or JSON file.
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


    metadata.description = func2str(f);
    metadata.inputNames;
    metadata.outputNames;
    oneFluxDir = metadata.oneFluxDir;
    relArtifactsDir = metadata.relArtifactsDir;
    functionDir = string(func2str(f)) + '_artifacts';
    


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
    
    siteDir = metadata.siteFile;

    dirPath = fullfile(oneFluxDir, relArtifactsDir, functionDir, siteDir);
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
