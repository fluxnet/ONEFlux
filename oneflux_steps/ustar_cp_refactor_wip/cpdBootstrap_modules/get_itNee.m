function [itNee] = get_itNee(NEE, uStar, T, iNight)

    itNee=find(~isnan(NEE+uStar+T));

	itNee=intersect(itNee,iNight);

end