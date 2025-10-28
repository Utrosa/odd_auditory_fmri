function makeBIOPAC_compatible(homePath, subID, sesID,task)    

    % Read in BIOPAC export files and set up variables.
    path       = sprintf('%s/data_physio/raw/', homePath);
    dataBIOPAC = matfile(sprintf('%stmp/sub-%02d_ses-%02d_task-%s_physio.mat', path, subID, sesID, task));
    channels   = dataBIOPAC.channels;
    nChannels  = numel(channels);
    
    % Determine sampling rate which should be the same for physio channels.
    targetRates = zeros(1, nChannels - 1);
    for i = 2:nChannels
        targetRates(i - 1) = channels{1, i}.samples_per_second;
    end
    
    % Check whether all physio channels' sampling rates are the same.
    if all(targetRates == targetRates(1))
        targetRate = targetRates(1);
        fprintf('All channels (excluding the "%s") have the same sampling rate: %.2f\n', channels{1,1}.name, targetRate);
    else
        fprintf('Warning: Not all physio channels have the same sampling rate.\n');
    end
    
    % Display the sampling rate of the trigger channel.
    fprintf('Sampling rate of the excluded channel "%s" is %.2f\n', channels{1,1}.name, channels{1,1}.samples_per_second);
    clear i; clear targetRates; clear dataBIOPAC;
    
    % Resample all channels to targetRate.
    labels        = cell(1, nChannels);
    units         = cell(1, nChannels);
    resampledData = cell(1, nChannels);
    for i = 1:nChannels
        labels{i} = channels{i}.name;
        units{i}  = channels{i}.units;
    
        % Resample, using antialiasing lowpass filter, if needed.
        raw = resample(channels{i}.data(:), targetRate, channels{i}.samples_per_second);
        resampledData{i} = raw;
    end
    
    % Truncate the re-sampled trigger column and consolidate data.
    data = zeros(numel(raw), nChannels);
    for i = 1:nChannels
        data(:, i) = resampledData{i}(1:numel(raw));
    end
    clear raw; clear resampledData;
    
    % Add metadata for TAPAS's PhysIO (input structure).
    isi          = 1 / targetRate;
    isi_units    = 's';
    start_sample = 0;
    for i = 1:numel(labels)
        originalName = lower(labels{i});
    
        % Rename labels as the TAPAS' readin functions expect.
        if contains(originalName, 'pneumatic')
            labels{i} = 'RSP';
        elseif contains(originalName, 'ppg')
            labels{i} = 'PPG100C';
        elseif contains(originalName, 'trigger')
            labels{i} = 'MRTtrigger';
        else
            labels{i} = channels{i}.name;  % fallback to original
        end
    end
    clear originalName; clear nChannels; clear i; clear homePath; 
    
    % Save Biopac-compatible file
    filename = sprintf('%ssub-%02d_ses-%02d_task-%s_compatible.mat', ...
               path, subID, sesID, task);
    save(filename, ...
        'data', 'isi', 'isi_units', 'labels', 'start_sample', 'units');
    
    % Check if file exists and print success or failure
    if exist(filename, 'file') == 2
        fprintf('Compatible data saved successfully to "%s"\n', filename);
    else
        fprintf('Error: Failed to save data to "%s"\n', filename);
    end