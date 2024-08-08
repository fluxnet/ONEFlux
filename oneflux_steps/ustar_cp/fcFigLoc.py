# Generated with SMOP  0.41-beta
from .libsmop import *

# ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m


@function
def myFigLoc(iFig=None, dx=None, dy=None, cLoc=None, *args, **kwargs):
    varargin = myFigLoc.varargin
    nargin = myFigLoc.nargin

    # fcFigLoc(iFig,dx,dy,cLoc)

    # 	creates a figure window of fractional size (dx by dy) at location cLoc.

    # 	cLoc is a string that identifies the figure location.
    # 	 -	Format A		'LowerLeft', 'MiddleCentre', 'UpperRight', etc.
    # 						or 'NW', 'NC', 'MW' ,'SE', etc.
    # 	 -	Format B		'xShift=fraction yShift=fraction'
    # 						where the fractions define the fractional shifts
    # 						left-right and up-down.

    # 	Examples:

    # 	myFigLoc(1,1,1,'UpperLeft') fills the window.
    # 	myFigLoc(1,0.3,0.4,'NW') creates a small figure in the upper left.
    # 	myFigLoc(1,0.3,0.4,'xShift=1 yShift=0.4') creates a small figure
    # 		to the extreme right and 40# up the screen.

    # 	Written by Alan Barr 24 June 2005.

    # 	=======================================================================

    ss = get(0, "ScreenSize")
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:25
    nxPixels = ss(3)
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:25
    nyPixels = ss(4)
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:25
    if nxPixels == 3200:
        nxPixels = 1600
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:26

    xFractionFull = 1
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:28
    yFractionBottom = 0.03
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:29
    yFractionTop = 0.06
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:29
    yFractionFull = 1 - yFractionBottom - yFractionTop
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:29
    # 	[0 36 1600 1200-3*36] is a perfect full figure position for a 1600x1200 screen.

    nxPixelsFull = dot(xFractionFull, nxPixels)
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:32
    nyPixelsFull = dot(yFractionFull, nyPixels)
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:33
    nyPixelsBottom = dot(yFractionBottom, nyPixels)
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:34
    xLocLeft = []
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:36
    yLocBottom = []
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:36
    nxPixels = []
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:36
    nyPixels = []
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:36
    nxPixels = dot(dx, nxPixelsFull)
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:37
    nyPixels = dot(dy, nyPixelsFull)
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:37
    if logical_not(isempty(strfind(cLoc, "Left"))):
        xFractionShift = 0.0
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:39

    if logical_not(isempty(strfind(cLoc, "Centre"))):
        xFractionShift = 0.5
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:40

    if logical_not(isempty(strfind(cLoc, "Right"))):
        xFractionShift = 1.0
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:41

    if logical_not(isempty(strfind(cLoc, "Lower"))):
        yFractionShift = 0.0
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:42

    if logical_not(isempty(strfind(cLoc, "Middle"))):
        yFractionShift = 0.5
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:43

    if logical_not(isempty(strfind(cLoc, "Upper"))):
        yFractionShift = 1.0
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:44

    if logical_not(isempty(strfind(cLoc, "W"))):
        xFractionShift = 0.0
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:46

    if logical_not(isempty(strfind(cLoc, "C"))):
        xFractionShift = 0.5
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:47

    if logical_not(isempty(strfind(cLoc, "E"))):
        xFractionShift = 1.0
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:48

    if logical_not(isempty(strfind(cLoc, "S"))):
        yFractionShift = 0.0
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:49

    if logical_not(isempty(strfind(cLoc, "M"))):
        yFractionShift = 0.5
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:50

    if logical_not(isempty(strfind(cLoc, "N"))):
        yFractionShift = 1.0
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:51

    if logical_and(
        logical_not(isempty(strfind(cLoc, "xShift="))),
        logical_not(isempty(strfind(cLoc, "yShift="))),
    ):
        ix = strfind(cLoc, "xShift=")
        # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:54
        iy = strfind(cLoc, "yShift=")
        # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:54
        xFractionShift = str2num(cLoc(arange((ix + 7), (iy - 1))))
        # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:55
        yFractionShift = str2num(cLoc(arange((iy + 7), end())))
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:56

    xLocLeft = dot(dot(xFractionShift, (1 - dx)), nxPixelsFull)
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:59
    yLocBottom = nyPixelsBottom + dot(dot(yFractionShift, (1 - dy)), nyPixelsFull)
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:60
    FigLoc = concat([xLocLeft, yLocBottom, nxPixels, nyPixels])
    # ../ONEFlux/oneflux_steps/ustar_cp/fcFigLoc.m:62
    if length(FigLoc) < 4:
        disp("myFigLoc aborted.")
        return

    figure(iFig)
    clf
    set(iFig, "Position", FigLoc)
    set(iFig, "PaperPositionMode", "auto")
