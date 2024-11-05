
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
