function [PPFD, ppfd_from_rg] = areAllPpfdValuesInvalid(ppfd_from_rg, columns_index, PPFD_INDEX, data, varargin)
    PPFD = '';
    if length(varargin) > 0
        data = importdata(varargin{1}, ',');
    end

    if 0 == ppfd_from_rg
        PPFD = data(:, columns_index(PPFD_INDEX));
        % check if ppfd is invalid
        q = find(PPFD < -9990); 
        if numel(q) == numel(PPFD);
            ppfd_from_rg = 1;
        end        
    end

end