function output = logFuncResult(filename, f, varargin)
    % Apply the function f to the input arguments in varargin
    output = f(varargin{:});
    dirPath = './tests/';
    filePath = fullfile(dirPath, filename);
    % Convert input and output to a comma seperated string
    outputStr = strjoin(string(output(:)), ',');
    inputArrayStr = strjoin(string([varargin{:}]), ',');
    

    resultStr = sprintf('%s | %s | %s', inputArrayStr, func2str(f), outputStr);
    
    % Open the file in append mode
    fileID = fopen(filePath, 'a');
    
    % Write the result to the file
    fprintf(fileID, '%s\n', resultStr);
    
    % Close the file
    fclose(fileID);

    
    % Print message to indicate the result has been saved
    fprintf('Result has been saved to %s\n', filePath); 
end