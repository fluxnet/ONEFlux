function [uStar, itAnnual, ntAnnual] = filterInvalidPoints(uStar, fNight, NEE, T)	
	% Filter edge cases for uStar
	
	itOut = find(uStar < 0 | uStar > 3);
	uStar(itOut) = NaN;

	itAnnual=find(fNight==1 & ~isnan(NEE+uStar+T)); ntAnnual=length(itAnnual); 

end
