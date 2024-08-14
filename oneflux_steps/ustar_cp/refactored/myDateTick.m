function myDateTick(t, sFrequency, iDateStr, fLimits)
    % Convert datetime
    [y, m, d] = mydatevec(t); 
    iSerMos = (y - 1) * 12 + m; 
    iSerMo1 = min(iSerMos); 
    iSerMo2 = max(iSerMos); 
    nSerMos = iSerMo2 - iSerMo1 + 1; 
    
    % Initialize xDates
    xDates = calculateDates(iSerMo1, nSerMos, sFrequency); 

    % Set unique xDates
    xDates = unique(xDates); 
    set(gca, 'xTick', xDates); 
    set(gca, 'xTickLabel', []); 

    % Set date labels if requested
    if iDateStr > 0
        cDates = datestr(xDates, iDateStr); 
        set(gca, 'xTickLabel', cDates); 
    end; 

    % Set limits and grid if requested
    if fLimits == 1
        xlim([floor(min(xDates)), ceil(max(xDates))]); 
        grid on; 
        box on; 
    end; 
end

function xDates = calculateDates(iSerMo1, nSerMos, sFrequency)
    % Define the start of the series
    iYr1 = floor(iSerMo1 / 12) + 1; 
    iMo1 = mod(iSerMo1, 12); 
    if iMo1 == 0
        iMo1 = 12; 
        iYr1 = iYr1 - 1; 
    end

    % Initialize xDates array
    xDates = [];

    % Determine the frequency and generate dates accordingly
    switch sFrequency
        case 'Dy', xDates = t(1:48:end); 
        case 'Mo', xDates = datenum(iYr1, iMo1:(iMo1 + nSerMos), 1);
        case '2Mo', xDates = datenum(iYr1, iMo1:2:(iMo1 + nSerMos), 1);
        case '3Mo', xDates = datenum(iYr1, iMo1:3:(iMo1 + nSerMos), 1);
        case '4Mo', xDates = datenum(iYr1, iMo1:4:(iMo1 + nSerMos), 1);
        case '6Mo', xDates = datenum(iYr1, iMo1:6:(iMo1 + nSerMos), 1);
        case 'Yr', xDates = datenum(min(y):max(y)+1, 1, 1);

        % For periodic dates
        otherwise
            stepSize = str2double(sFrequency(1:end-2)); % Extract step size (e.g., 2 from '2Dy')
            numDays = 29; % Maximum number of days in a month
            switch sFrequency
                case '2Dy', numDays = 29;
                case '3Dy', numDays = 28;
                case '5Dy', numDays = 26;
                case '7Dy', numDays = 22;
                case '10Dy', numDays = 21;
                case '14Dy', numDays = 15;
                case '15Dy', numDays = 16;
            end

            for iDy = 1:stepSize:numDays
                xDates = [xDates; datenum(iYr1, iMo1:(iMo1 + nSerMos), iDy)];
            end
    end
end
