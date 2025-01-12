function itStrata = findStratumIndices(T, itSeason, TTh, iStrata)
    itStrata = find(T >= TTh(iStrata) & T <= TTh(iStrata + 1));
    itStrata = intersect(itStrata, itSeason); % Filter by current season
end