function [t, T, uStar, NEE, fNight, itAnnual, ntAnnual] = ...
	reorderAndPreprocessData(t, T, uStar, NEE, fNight, EndDOY, m, nt)

	itD=find(m==12); 
	itReOrder=[min(itD):nt 1:(min(itD)-1)]; 
	t(itD)=t(itD)-EndDOY; t=t(itReOrder); 
	T=T(itReOrder); uStar=uStar(itReOrder); 
	NEE=NEE(itReOrder); fNight=fNight(itReOrder); 
	
	itAnnual=find(fNight==1 & ~isnan(NEE+uStar+T)); ntAnnual=length(itAnnual); 
	
end