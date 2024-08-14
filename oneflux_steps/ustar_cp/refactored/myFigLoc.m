function myFigLoc(iFig, dx, dy, cLoc)
    % Main function to position and size the figure based on input parameters.
    
    [xFractionShift, yFractionShift] = parseLocation(cLoc);
    FigLoc = calculateFigurePosition(dx, dy, xFractionShift, yFractionShift);
    
    if length(FigLoc) < 4
        disp('myFigLoc aborted.');
        return;
    end
    
    figure(iFig);
    clf;
    set(iFig, 'Position', FigLoc);
    set(iFig, 'PaperPositionMode', 'auto');
end

function [xFractionShift, yFractionShift] = parseLocation(cLoc)
    % Parses the location string to determine fractional shifts.
    
    if contains(cLoc, 'Left')
        xFractionShift = 0.0;
    elseif contains(cLoc, 'Centre')
        xFractionShift = 0.5;
    elseif contains(cLoc, 'Right')
        xFractionShift = 1.0;
    else
        xFractionShift = 0.5; % Default to center
    end

    if contains(cLoc, 'Lower')
        yFractionShift = 0.0;
    elseif contains(cLoc, 'Middle')
        yFractionShift = 0.5;
    elseif contains(cLoc, 'Upper')
        yFractionShift = 1.0;
    else
        yFractionShift = 0.5; % Default to center
    end

    if contains(cLoc, 'xShift=')
        xShiftIdx = strfind(cLoc, 'xShift=') + 7;
        yShiftIdx = strfind(cLoc, 'yShift=') - 1;
        xFractionShift = str2double(cLoc(xShiftIdx:yShiftIdx));
        yFractionShift = str2double(cLoc(yShiftIdx + 8:end));
    end
end

function FigLoc = calculateFigurePosition(dx, dy, xFractionShift, yFractionShift)
    % Calculates the figure position based on fractional sizes and shifts.
    
    [nxPixelsFull, nyPixelsFull] = getScreenSize();
    
    xFractionFull = 1;
    yFractionBottom = 0.03;
    yFractionTop = 0.06;
    yFractionFull = 1 - yFractionBottom - yFractionTop;
    
    nxPixelsFull = xFractionFull * nxPixelsFull;
    nyPixelsFull = yFractionFull * nyPixelsFull;
    nyPixelsBottom = yFractionBottom * nyPixelsFull;
    
    nxPixels = dx * nxPixelsFull;
    nyPixels = dy * nyPixelsFull;
    
    xLocLeft = xFractionShift * (1 - dx) * nxPixelsFull;
    yLocBottom = nyPixelsBottom + yFractionShift * (1 - dy) * nyPixelsFull;
    
    FigLoc = [xLocLeft, yLocBottom, nxPixels, nyPixels];
end

function [nxPixels, nyPixels] = getScreenSize()
    % Gets the screen size, adjusting for double monitors if necessary.
    
    ss = get(0, 'ScreenSize');
    nxPixels = ss(3);
    nyPixels = ss(4);
    
    if nxPixels == 3200
        nxPixels = 1600; % Adjust for double monitors
    end
end
