function [ppfd_from_rg, errorCode] = ppfdColExists(PPFD_INDEX, columns_index, input_columns_names)

    errorCode = 0;
    on_error = 0;
    ppfd_from_rg = 0;
    for i = 1:numel(columns_index)
        if -1 == columns_index(i)
            if i == PPFD_INDEX
                ppfd_from_rg = 1;
            else
                fprintf('column %s not found!\n', char(input_columns_names(i)));
                on_error = 1;
            end
        end        
    end
    
    if 1 == on_error
        errorCode = 1;
        return;
    end

end