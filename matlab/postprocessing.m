function postprocessing
% Interactive visualization of measured horn antenna power patterns.
% Select a polarization configuration and a measurement frequency.

% --- Locate the data folder ---
scriptDir = fileparts(mfilename('fullpath'));
repoRoot = fileparts(scriptDir);
dataDir = fullfile(repoRoot, 'data');

% --- Define the four measurement datasets ---
datasetFiles = {
    'radiationPattern_corrected_eplane_co_new.csv'
    'radiationPattern_eplane_cross_new.csv'
    'radiationPattern_hplane_co_new.csv'
    'radiationPattern_hplane_cross_new.csv'
};

datasetLabels = {
    'E-plane Co-polarized'
    'E-plane Cross-polarized'
    'H-plane Co-polarized'
    'H-plane Cross-polarized'
};

% --- Load and validate all datasets ---
patternData = cell(numel(datasetFiles), 1);

for i = 1:numel(datasetFiles)

    filePath = fullfile(dataDir, datasetFiles{i});

    if ~isfile(filePath)
        error('Required data file not found: %s', filePath);
    end

    [anglesThis, frequenciesThis, s21This] = ...
        readPatternFile(filePath);

    if i == 1
        angles = anglesThis;
        frequenciesGHz = frequenciesThis;
    else
        if ~isequal(anglesThis, angles)
            error('The angle grids differ between datasets.');
        end

        if numel(frequenciesThis) ~= numel(frequenciesGHz) || ...
                any(abs(frequenciesThis - frequenciesGHz) > 1e-9)
            error('The frequency grids differ between datasets.');
        end
    end

    patternData{i} = struct( ...
        'angles', anglesThis, ...
        's21Db', s21This);
end

% --- Create the interactive figure ---
fig = figure( ...
    'Name', 'Horn Antenna Power Pattern', ...
    'NumberTitle', 'off', ...
    'Color', 'w', ...
    'Position', [100 100 950 720]);

uicontrol(fig, ...
    'Style', 'text', ...
    'String', 'Configuration', ...
    'Units', 'normalized', ...
    'Position', [0.05 0.925 0.17 0.04], ...
    'HorizontalAlignment', 'left', ...
    'BackgroundColor', 'w');

configurationMenu = uicontrol(fig, ...
    'Style', 'popupmenu', ...
    'String', datasetLabels, ...
    'Value', 1, ...
    'Units', 'normalized', ...
    'Position', [0.22 0.925 0.34 0.045], ...
    'Callback', @updatePlot);

uicontrol(fig, ...
    'Style', 'text', ...
    'String', 'Frequency', ...
    'Units', 'normalized', ...
    'Position', [0.59 0.925 0.11 0.04], ...
    'HorizontalAlignment', 'left', ...
    'BackgroundColor', 'w');

frequencyLabels = arrayfun( ...
    @(f) sprintf('%.4f GHz', f), ...
    frequenciesGHz, ...
    'UniformOutput', false);

frequencyMenu = uicontrol(fig, ...
    'Style', 'popupmenu', ...
    'String', frequencyLabels, ...
    'Value', 1, ...
    'Units', 'normalized', ...
    'Position', [0.70 0.925 0.24 0.045], ...
    'Callback', @updatePlot);

pax = polaraxes( ...
    'Parent', fig, ...
    'Position', [0.10 0.08 0.80 0.80]);

% Display the initial configuration and frequency.
updatePlot();

    function updatePlot(~, ~)

        datasetIndex = configurationMenu.Value;
        frequencyIndex = frequencyMenu.Value;

        currentData = patternData{datasetIndex};

        s21 = currentData.s21Db(:, frequencyIndex);
        valid = isfinite(s21) & isfinite(currentData.angles);

        if ~any(valid)
            error('No valid measurements are available for this selection.');
        end

        % Normalize the measured S21 values to the maximum at this frequency.
        s21Normalized = s21 - max(s21(valid));

        % Redraw the polar pattern.
        cla(pax);

        polarplot( ...
            pax, ...
            deg2rad(currentData.angles), ...
            s21Normalized, ...
            'LineWidth', 2);

        pax.RLim = [-40 0];
        pax.ThetaZeroLocation = 'top';

        title(pax, sprintf('%s at %.4f GHz', ...
            datasetLabels{datasetIndex}, ...
            frequenciesGHz(frequencyIndex)));

    end

end


function [angles, frequenciesGHz, s21Db] = readPatternFile(filePath)
% Read a measurement CSV.
% Row 1 contains frequency values in Hz.
% Column 1 contains angle values in degrees.
% The remaining values contain measured S21 in dB.

raw = readmatrix(filePath);

if size(raw, 1) < 2 || size(raw, 2) < 2
    error('The file does not contain a valid measurement matrix: %s', ...
        filePath);
end

frequenciesHz = raw(1, 2:end);
angles = raw(2:end, 1);
s21Db = raw(2:end, 2:end);

frequenciesGHz = frequenciesHz ./ 1e9;

if any(~isfinite(frequenciesGHz)) || ...
        any(~isfinite(angles))
    error('Invalid frequency or angle values found in: %s', filePath);
end

if size(s21Db, 1) ~= numel(angles) || ...
        size(s21Db, 2) ~= numel(frequenciesGHz)
    error('The measurement dimensions are inconsistent in: %s', filePath);
end

end
