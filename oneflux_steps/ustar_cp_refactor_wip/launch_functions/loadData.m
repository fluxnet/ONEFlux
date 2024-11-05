function [header, data, columns_index] ...
    = loadData(input_folder, filename, notes, input_columns_names, varargin)
    % disp("start"); disp(filename); disp(input_folder);

    imported_data = importdata([input_folder,filename], ',', (9+length(notes)));  
    header = imported_data.('textdata');
    data = imported_data.('data');
    % disp(data);
    columns_index = ones(numel(input_columns_names), 1) * -1;

    if length(varargin) > 0
        outputDir = varargin{1};
        % disp(outputDir);
        variablesStruct = struct();

        variablesStruct.header = header;
        variablesStruct.data = data;
        variablesStruct.columns_index = columns_index;

        varNames = fieldnames(variablesStruct);

        for idx = 1:numel(varNames)
            varName = varNames{idx};
            var = variablesStruct.(varName);

            % Construct the file path using the variable name
            fileName = [varName, '.csv'];
            filePath = fullfile(outputDir, fileName);
            % disp(filePath);
            saveVariableAsCSV(var, filePath);
        end
    end

end
