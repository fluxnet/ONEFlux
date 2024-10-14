function [updated_ustar] = update_uStar(uStar)

    updated_ustar = uStar;  % Initialize to same size as input
    iOut = find(uStar < 0 | uStar > 4);
    updated_ustar(iOut) = NaN;  % Modify uStar here, must return updated uStar

end