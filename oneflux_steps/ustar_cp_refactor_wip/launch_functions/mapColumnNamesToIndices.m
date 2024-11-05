function [exitcode, columns_index] = ...
    mapColumnNamesToIndices(header, input_columns_names, notes, columns_index, varargin)

    if length(varargin) > 0

        % imported_data = importdata(varargin{1}, ',', (9+length(notes)));  
        % header = imported_data.('textdata');
        header = readtable(varargin{1}, 'Delimiter', ',', 'NumHeaderLines', 0, 'ReadVariableNames', false);
        header = table2cell(header);

    end
    on_error = 0;
    exitcode = 0;

    for y = 1:length(header(9+length(notes),:))
        for i = 1:numel(input_columns_names)
            if (strcmpi(header((9+length(notes)), y), input_columns_names(i))) | (strcmpi(header((9+length(notes)), y), strcat('itp',input_columns_names(i))))
                if columns_index(i) ~= -1
                    fprintf('column %s already founded at index %d\n', char(input_columns_names(i)), i);
                    on_error = 1;
                    break;
                else
                    columns_index(i) = y;
                end                       
            end
        end
        if ( 1 == on_error )
            break;
        end
    end
    
    if 1 == on_error 
        exitcode = 1;
        return;
    end
end