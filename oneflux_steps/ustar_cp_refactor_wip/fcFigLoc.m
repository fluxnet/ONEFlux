	function myFigLoc(iFig,dx,dy,cLoc); 

%fcFigLoc(iFig,dx,dy,cLoc) 	
%
%	creates a figure window of fractional size (dx by dy) at location cLoc.
%
%	cLoc is a string that identifies the figure location.
%	 -	Format A		'LowerLeft', 'MiddleCentre', 'UpperRight', etc.
%						or 'NW', 'NC', 'MW' ,'SE', etc. 
%	 -	Format B		'xShift=fraction yShift=fraction' 
%						where the fractions define the fractional shifts 
%						left-right and up-down.
%
%	Examples:
%
%	myFigLoc(1,1,1,'UpperLeft') fills the window.
%	myFigLoc(1,0.3,0.4,'NW') creates a small figure in the upper left.
%	myFigLoc(1,0.3,0.4,'xShift=1 yShift=0.4') creates a small figure 
%		to the extreme right and 40% up the screen. 

%	Written by Alan Barr 24 June 2005.

%	=======================================================================

	ss=get(0,'ScreenSize'); nxPixels=ss(3); nyPixels=ss(4); 
	if nxPixels==3200; nxPixels=1600; end; % new 1 Aug for double monitors.
	
	xFractionFull=1; 
	yFractionBottom=0.03; yFractionTop=0.06; yFractionFull=1-yFractionBottom-yFractionTop; 
%	[0 36 1600 1200-3*36] is a perfect full figure position for a 1600x1200 screen.
	
	nxPixelsFull=xFractionFull*nxPixels; 
	nyPixelsFull=yFractionFull*nyPixels; 
	nyPixelsBottom=yFractionBottom*nyPixels; 
	
	xLocLeft=[]; yLocBottom=[]; nxPixels=[]; nyPixels=[]; 
	nxPixels=dx*nxPixelsFull; nyPixels=dy*nyPixelsFull; 
	
	if ~isempty(strfind(cLoc,'Left')); xFractionShift=0.0; end; 
	if ~isempty(strfind(cLoc,'Centre')); xFractionShift=0.5; end; 
	if ~isempty(strfind(cLoc,'Right')); xFractionShift=1.0; end; 
	if ~isempty(strfind(cLoc,'Lower')); yFractionShift=0.0; end; 
	if ~isempty(strfind(cLoc,'Middle')); yFractionShift=0.5; end; 
	if ~isempty(strfind(cLoc,'Upper')); yFractionShift=1.0; end; 
	
	if ~isempty(strfind(cLoc,'W')); xFractionShift=0.0; end; 
	if ~isempty(strfind(cLoc,'C')); xFractionShift=0.5; end; 
	if ~isempty(strfind(cLoc,'E')); xFractionShift=1.0; end; 
	if ~isempty(strfind(cLoc,'S')); yFractionShift=0.0; end; 
	if ~isempty(strfind(cLoc,'M')); yFractionShift=0.5; end; 
	if ~isempty(strfind(cLoc,'N')); yFractionShift=1.0; end; 
	
	if ~isempty(strfind(cLoc,'xShift=')) & ~isempty(strfind(cLoc,'yShift=')); 
		ix=strfind(cLoc,'xShift='); iy=strfind(cLoc,'yShift='); 
		xFractionShift=str2num(cLoc((ix+7):(iy-1))); 
		yFractionShift=str2num(cLoc((iy+7):end)); 
	end; 	
	
	xLocLeft=xFractionShift*(1-dx)*nxPixelsFull; 
	yLocBottom=nyPixelsBottom+yFractionShift*(1-dy)*nyPixelsFull; 
	
	FigLoc=[xLocLeft yLocBottom nxPixels nyPixels]; 
	
	if length(FigLoc)<4; disp('myFigLoc aborted.'); return; end;  

	figure(iFig); clf; 
	set(iFig,'Position',FigLoc); 
	set (iFig,'PaperPositionMode','auto'); 
	
	
