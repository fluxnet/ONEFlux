function PPFD = derivePpfdColFromRg(Rg)

    fprintf('(PPFD_IN from SW_IN)...');
    PPFD = Rg * 2.24;
    p = find(Rg < -9990);
    PPFD(p) = -9999;
    clear p;

end