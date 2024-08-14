function exitcode = launch(input_folder, output_folder)
    % Main function to launch the data processing workflow
    exitcode = 0;
    warning off;

    % Validate and prepare input and output folder paths
    input_folder = validateAndPreparePath(input_folder, pwd);
    output_folder = validateAndPreparePath(output_folder, pwd);
    mkdir(output_folder);

    % Define column names and indices
    input_columns_names = {'USTAR', 'NEE', 'TA', 'PPFD_IN', 'SW_IN'};
    USTAR_INDEX = 1;
    NEE_INDEX = 2;
    TA_INDEX = 3;
    PPFD_INDEX = 4;
    RG_INDEX = 5;

    % Log input and output folders
    fprintf('\n\nUstar Threshold Computation by Alan Barr\n\ninput in %s\noutput in %s\n\n', input_folder, output_folder);
    
    % Find and process all matching files in the input folder
    files = dir([input_folder, '*_qca_ustar_*.csv']);
    fprintf('%d files found.\n\n', numel(files));

    for n = 1:numel(files)
        fprintf('Processing n.%02d, %s...', n, files(n).name);

        % Load dataset from file
        [dataset, success] = loadDataset([input_folder, files(n).name]);
        if ~success
            exitcode = 1;
            continue;
        end

        % Parse metadata from the dataset
        [site, year, notes, success] = parseMetadata(dataset);
        if ~success
            exitcode = 1;
            continue;
        end

        % Import data and headers from the file
        [header, data, success] = importData([input_folder, files(n).name], length(notes));
        if ~success
            exitcode = 1;
            continue;
        end

        % Match the required columns in the header
        [columns_index, ppfd_from_rg, success] = matchColumns(header, input_columns_names, PPFD_INDEX);
        if ~success
            exitcode = 1;
            continue;
        end

        % Extract and prepare the data based on the matched columns
        [uStar, NEE, Ta, PPFD, Rg] = extractAndPrepareData(data, columns_index, USTAR_INDEX, NEE_INDEX, TA_INDEX, PPFD_INDEX, RG_INDEX, ppfd_from_rg);

        % Validate the extracted data
        if ~validateData(NEE, uStar, Ta, Rg)
            continue;
        end

        % Generate the time series based on the uStar data
        t = generateTimeSeries(uStar);
        fNight = Rg < 5;
        T = Ta;

        % Perform the seasonal analysis and save results
        [Cp, success] = processSeasonalAnalysis(t, NEE, uStar, T, fNight, site, year, output_folder, notes);
        if ~success
            exitcode = 1;
        end
    end
end

function path = validateAndPreparePath(path, default_path)
    % Validates and prepares the file path, ensuring it ends with a file separator
    if ~exist('path', 'var') || isempty(path)
        path = [default_path, filesep];
    elseif length(path) < 2 || (length(path) > 1 && path(2) ~= ':')
        path = [default_path, filesep, path];
    end
    if path(end) ~= '\' && path(end) ~= '/'
        path = [path, filesep];
    end
end

function [dataset, success] = loadDataset(file)
    % Loads the dataset from the specified file
    fid = fopen(file, 'r');
    if fid == -1
        fprintf('Unable to open file\n');
        dataset = {};
        success = false;
    else
        dataset = textscan(fid, '%[^\n]');
        dataset = dataset{1};
        fclose(fid);
        success = true;
    end
end

function [site, year, notes, success] = parseMetadata(dataset)
    % Parses metadata such as site, year, and notes from the dataset
    try
        site = strrep(dataset{1}, 'site,', '');
        year = strrep(dataset{2}, 'year,', '');
        notes = dataset(9:end);
        for i = 10:length(dataset)
            if strncmpi(dataset{i}, 'notes', 5)
                notes{end + 1} = strrep(dataset{i}, 'notes,', '');
            else
                break;
            end
        end
        success = true;
    catch
        fprintf('Error parsing metadata\n');
        site = '';
        year = '';
        notes = {};
        success = false;
    end
end

function [header, data, success] = importData(file, notes_length)
    % Imports data and headers from the specified file, accounting for the number of notes
    try
        imported_data = importdata(file, ',', (9 + notes_length));
        header = imported_data.textdata;
        data = imported_data.data;
        success = true;
    catch
        fprintf('Error importing data\n');
        header = {};
        data = [];
        success = false;
    end
end

function [columns_index, ppfd_from_rg, success] = matchColumns(header, input_columns_names, PPFD_INDEX)
    % Matches the required columns in the header and checks for their presence
    columns_index = ones(numel(input_columns_names), 1) * -1;
    on_error = false;
    ppfd_from_rg = 0;

    for y = 1:length(header)
        for i = 1:numel(input_columns_names)
            if strcmpi(header{y}, input_columns_names{i}) || strcmpi(header{y}, strcat('itp', input_columns_names{i}))
                if columns_index(i) ~= -1
                    fprintf('Column %s already found at index %d\n', char(input_columns_names{i}), i);
                    on_error = true;
                    break;
                else
                    columns_index(i) = y;
                end
            end
        end
        if on_error
            break;
        end
    end

    if any(columns_index == -1) && columns_index(PPFD_INDEX) == -1
        fprintf('Required column not found\n');
        success = false;
    else
        success = true;
    end
end

function [uStar, NEE, Ta, PPFD, Rg] = extractAndPrepareData(data, columns_index, USTAR_INDEX, NEE_INDEX, TA_INDEX, PPFD_INDEX, RG_INDEX, ppfd_from_rg)
    % Extracts and prepares the necessary data from the columns
    uStar = data(:, columns_index(USTAR_INDEX));
    NEE = data(:, columns_index(NEE_INDEX));
    Ta = data(:, columns_index(TA_INDEX));
    Rg = data(:, columns_index(RG_INDEX));

    if ~ppfd_from_rg
        PPFD = data(:, columns_index(PPFD_INDEX));
        if all(PPFD < -9990)
            ppfd_from_rg = 1;
        end
    end

    if ppfd_from_rg
        fprintf('(PPFD_IN from SW_IN)...');
        PPFD = Rg * 2.24;
        PPFD(Rg < -9990) = -9999;
    end

    % Replace missing values with NaN
    uStar(uStar == -9999) = NaN;
    NEE(NEE == -9999) = NaN;
    Ta(Ta == -9999) = NaN;
    PPFD(PPFD == -9999) = NaN;
    Rg(Rg == -9999) = NaN;
end

function valid = validateData(NEE, uStar, Ta, Rg)
    % Validates the extracted data to ensure it is usable
    valid = true;

    if all(isnan(NEE))
        fprintf('NEE is empty!\n');
        valid = false;
    end
    if all(isnan(uStar))
        fprintf('uStar is empty!\n');
        valid = false;
    end
    if isempty(Ta)
        fprintf('Ta is empty!\n');
        valid = false;
    end
    if isempty(Rg)
        fprintf('Rg is empty!\n');
        valid = false;
    end
end

function t = generateTimeSeries(uStar)
    % Generates a time series based on the number of uStar data points
    nrPerDay = mod(numel(uStar), 365);
    if nrPerDay == 0
        nrPerDay = mod(numel(uStar), 364);
    end
    t = 1 + (1 / nrPerDay);
    for n2 = 2:numel(uStar)
        t(n2, 1) = t(n2-1, 1) + (1 / nrPerDay);
    end
end

function [Cp, success] = processSeasonalAnalysis(t, NEE, uStar, T, fNight, site, year, output_folder, notes)
    % Processes the seasonal analysis and saves the results
    try
        fPlot = 0;
        cSiteYr = strrep([site, '_', year], '.csv', '');
        nBoot = 100;

        % Run seasonal analysis functions
        [Cp2, Stats2, Cp3, Stats3] = cpdBootstrapUStarTh4Season20100901(t, NEE, uStar, T, fNight, fPlot, cSiteYr, nBoot);
        [Cp, n, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect] = cpdAssignUStarTh20100901(Stats2, fPlot, cSiteYr);

        if isempty(cFailure)
            % Save the results to file
            dlmwrite([output_folder, char(site), '_uscp_', char(year), '.txt'], Cp, 'precision', 8);
            fid = fopen([output_folder, char(site), '_uscp_', char(year), '.txt'], 'a');
            fprintf(fid, '\n;processed with ustar_mp 1.0 on %s\n', datestr(clock));
            for i = length(notes):-1:1
                fprintf(fid, ';%s\n', notes{i});
            end
            fclose(fid);
            fprintf('ok\n');
            success = true;
        else
            fprintf('%s\n', cFailure);
            success = false;
        end
    catch
        fprintf('Error processing seasonal analysis\n');
        success = false;
    end
end
