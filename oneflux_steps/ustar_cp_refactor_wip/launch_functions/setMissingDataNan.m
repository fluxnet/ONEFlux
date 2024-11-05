function [uStar, NEE, Ta, PPFD, Rg] = setMissingDataNan(uStar, NEE, Ta, PPFD, Rg)

    uStar(uStar==-9999) = NaN;
    NEE(NEE==-9999) = NaN;
    Ta(Ta==-9999) = NaN;
    PPFD(PPFD==-9999) = NaN;
    Rg(Rg==-9999) = NaN;
    
end

