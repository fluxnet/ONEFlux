function [nPerBin] = get_nPerBin(t)

    nPerDay = get_nPerDay(t);

    switch nPerDay
        case 24
            nPerBin = 3;
        case 48
            nPerBin = 5;
        otherwise
            nPerBin = 5; % Default case
    end

end