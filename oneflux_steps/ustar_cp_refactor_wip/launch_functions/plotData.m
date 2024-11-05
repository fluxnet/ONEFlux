function fPlot = plotData(t, uStar, NEE, Ta, PPFD, Rg)
    fPlot=0;
	if fPlot;
		plot(t,uStar,'.'); mydatetick(t,'Mo',4,1); pause;
		plot(t,NEE,'.'); mydatetick(t,'Mo',4,1); pause;
		plot(t,Ta,'.'); mydatetick(t,'Mo',4,1); pause;
		plot(t,PPFD,'.'); mydatetick(t,'Mo',4,1); pause;
		plot(t,Rg,'.'); mydatetick(t,'Mo',4,1); pause;
	end
end