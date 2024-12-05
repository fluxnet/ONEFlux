function [Cp2, Stats2, Cp3, Stats3, iPlot] = ...
    processStrata(nSeasons, iSeason, nStrata, nPerBin, itSeason, T, uStar, NEE, t, ...
   TTh, fPlot, cSiteYr, iPlot, Cp2, Stats2, Cp3, Stats3)


   for iStrata=1:nStrata;
           
       [cPlot, iPlot ]= plotStratum(fPlot, nSeasons, nStrata, iPlot, iSeason, iStrata, cSiteYr);
       
       itStrata = findStratumIndices(T, itSeason, TTh, iStrata);
       
       [n,muStar,mNEE] = fcBin(uStar(itStrata),NEE(itStrata),[],nPerBin);

       [xCp2,xs2,xCp3,xs3] = cpdFindChangePoint20100901(muStar,mNEE,fPlot,cPlot); 
       
       %	add fields not assigned by cpdFindChangePoint function
       
       [n,muStar,mT] = fcBin(uStar(itStrata),T(itStrata),[],nPerBin);
       [r,p]=corrcoef(muStar,mT); 
       
       xs2 = addStatisticsFields(xs2, t, r, p, T, itStrata);
       
       xs3.mt=xs2.mt; xs3.ti=xs2.ti; xs3.tf=xs2.tf; 
       xs3.ruStarVsT=xs2.ruStarVsT; xs3.puStarVsT=xs2.puStarVsT; 
       xs3.mT=xs2.mT; xs3.ciT=xs2.ciT; 
       
       Cp2(iSeason,iStrata)=xCp2; 
       Stats2(iSeason,iStrata)=xs2; 
       
       Cp3(iSeason,iStrata)=xCp3; 
       Stats3(iSeason,iStrata)=xs3; 
       
   end;

end