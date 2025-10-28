function tapas(homePath, subID, sesID, project, task)

    % Set up paths to raw DICOM files and compatible physio data.
    dcmPath    = sprintf('%s/data_MRI/sourcedata/dicoms/%02d_%s_%02d/', homePath, sesID, project, subID);
    biopacPath = sprintf('%s/data_physio/raw/', homePath);

    % Load data
    compData = load(sprintf('%ssub-%02d_ses-%02d_task-%s_compatible.mat', biopacPath, subID, sesID, task));

    % Identify target DICOM images in the DICOM directory.
    localizerDir = dir([dcmPath '*mm*']); % "mm" is unique to func scans
    disp(localizerDir);
    excludeDir   = {'AP', 'PA', 'Pha', 'SBRef'}; % ignore non-func scans
    localizerDir = localizerDir(~cellfun(@(x) any(contains(x, excludeDir)), {localizerDir.name}));

    % Set up the same func scan labels as in the configuration for raw MRI data.
    names = {localizerDir.name};
    for i = 1:length(names)
        name = names{i};
        % Remove the last 3 characters
        SeriesDescription = regexprep(name, '_\d+$', '');
    
        % Update labels according as in conf_SUBCORT_HIGHRES.json
    
        %%% --------- 1.5 mm sequences --------- %%%
        if strcmp(SeriesDescription, "Dresden_1.5mm_SMS1_TR2100_noFatSat")
            localizerDir(i).bids_name = 'DresdenNoFat';
 
        elseif strcmp(SeriesDescription, "Dresden_1.5mm_SMS1_TR2400_wFatSat")
            localizerDir(i).bids_name = 'DresdenWFat';
    
        elseif strcmp(SeriesDescription, "ME1_1.5mm_SMS2_TR880")
            localizerDir(i).bids_name = 'ME1TR880';
    
        elseif strcmp(SeriesDescription, "ME3_SMS2_1.5mm_TR1600")
            localizerDir(i).bids_name = 'ME3TR1600';
        
        elseif strcmp(SeriesDescription, "ME3_SMS3_1.5mm_TR1100")
            localizerDir(i).bids_name = 'ME3TR1100';
    
        elseif strcmp(SeriesDescription, "ME3_SMS4_1.5mm_TR850")
            localizerDir(i).bids_name = 'ME3TR850';
    
        elseif strcmp(SeriesDescription, "ME3_SMS5_1.5mm_TR700")
            localizerDir(i).bids_name = 'ME3TR700';      
         
        %%% --------- 1.75 mm sequences --------- %%%
        elseif strcmp(SeriesDescription, "Dresden_1.75mm_SMS1_TR1640_noFatSat")
            localizerDir(i).bids_name = 'DresdenNoFat175';    
    
        elseif strcmp(SeriesDescription, "Dresden_1.75mm_SMS1_TR1820_wFatSat")
            localizerDir(i).bids_name = 'DresdenWFat175';
    
        elseif strcmp(SeriesDescription, "ME1_1.75mm_SMS2_TR780")
            localizerDir(i).bids_name = 'ME1TR780';
    
        elseif strcmp(SeriesDescription, "ME3_1.75mm_SMS2_TR1180")
            localizerDir(i).bids_name = 'ME3TR1180';
       
        elseif strcmp(SeriesDescription, "ME3_1.75mm_SMS3_TR770")
            localizerDir(i).bids_name = 'ME3TR770';
    
        elseif strcmp(SeriesDescription, "ME3_1.75mm_SMS4_TR680")
            localizerDir(i).bids_name = 'ME3TR680';
    
        end
    
    end

    % Display all the functional scans found for this participant.
    bids_names = {localizerDir.bids_name};
    fprintf('%d FUNCTIONAL SEQUENCES FOUND:\n%s\n', numel(bids_names), strjoin(bids_names, ',\n'));

    % Find the last DICOM file per functional scan.
    funcInfo = struct();
    for i = 1:length(localizerDir)
        thisVolNum = 0;
        tmpDir = dir([localizerDir(i).folder '/' localizerDir(i).name '/']);
    
        % Loop through all DICOMS per functional scan.
        for dicom = 1:length(tmpDir)
    
            % Skip weird dicoms with dots in their name.
            if tmpDir(dicom).name == "." || tmpDir(dicom).name ==".."
                continue;
            end
    
            % Split the DICOM names by the dot.
            ix     = strsplit(tmpDir(dicom).name, ".");
            numVal = str2double(ix{end-1});
    
            % Find the largest DICOM ID.
            if numVal > thisVolNum
                thisVolNum = numVal;
                thisDicom = [tmpDir(dicom).folder '/' tmpDir(dicom).name];
            end
        end
    
        % Add the identified last DICOM & other necessary info.
        funcInfo.lastDICOMimage(i) = {thisDicom} ;
    
        % Get info from the last DICOM image
        metaData  = dicominfo(thisDicom);
    
        % The InstanceNumber refers to the number of the file (in this case the
        % last DICOM). In the old DICOM format, there is one file per slice.
        % No. of files: InstanceNumber
        % No. of vols : AcquisitionNumber
        funcInfo.NofVols(i)   = metaData.AcquisitionNumber;
        funcInfo.NofSlices(i) = metaData.NumberOfFrames;
    
        % No TR reported in DICOM metadata, read from filename.
        strTR  = regexp(localizerDir(i).name, 'TR(\d+)', 'tokens');
        funcInfo.TR(i) = str2double(strTR{1}{1});
    end


    clear dicom; clear thisVolNum; clear thisDicom; clear numVal; clear ix;
    clear metadata; clear excludeDir; clear strTR; clear tmpDir;
    
    %% LOOP THROUGH ALL FUNCTIONAL SEQUENCES ----------------------------------
    for i = 1:length(funcInfo.TR)

        
        %% Create the main input structure - PhysIO.
        physio = tapas_physio_new();
        
        %% save_dir module
        % Directory where output model, regressors and figure-files are saved to.
        physio.save_dir = biopacPath;
        
        %% write_BIDS module
        physio.write_bids.bids_step = 4;
        physio.write_bids.bids_dir    = biopacPath;
        physio.write_bids.bids_prefix = sprintf('sub-%02d_ses-%02d_task-%s', subID, sesID, task);
        
        %% log_files module
        % General physiological log-file information: file names, sampling rates.
        physio.log_files.vendor      = 'biopac_Mat';
        physio.log_files.cardiac     = sprintf('%ssub-%02d_ses-%02d_task-%s_compatible.mat', biopacPath, subID, sesID, task);
        physio.log_files.respiration = sprintf('%ssub-%02d_ses-%02d_task-%s_compatible.mat', biopacPath, subID, sesID, task);
        
        % Additional file for relative timing information between logfiles and MRI scans.
        % The time stamp in the DICOM header is on the same time axis as the time stamp in the physiological log file.
        physio.log_files.scan_timing = funcInfo.lastDICOMimage{1, i};
        
        % Sampling rate is 125 Hz for all channels except the Trigger channel.
        physio.log_files.sampling_interval = compData.isi;
        
        % Which scan shall be aligned to which part of the logfile.
        physio.log_files.align_scan  = 'last';
        
        %% scan_timing module
        % Parameters for sequence timing & synchronization
        physio.scan_timing.sqpar.Nslices = funcInfo.NofSlices(1, i);
        
        % Equals Nslices because we didn't trigger with the heart beat.
        physio.scan_timing.sqpar.NslicesPerBeat = [];
        
        % Volume repetition time in seconds
        physio.scan_timing.sqpar.TR = funcInfo.TR(1, i)/1000;
        physio.scan_timing.sqpar.Ndummies = 0;
        
        % Number of full volumes saved. Usually, rows in the nifti design matrix.
        physio.scan_timing.sqpar.Nscans = double(funcInfo.NofVols(1, i));
        
        % Time between the acquisition of 2 subsequent slices; typically TR/Nslices.
        % NOTE: only necessary, if preproc.grad_direction is empty and nominal scan
        % timing is used.
        physio.scan_timing.sqpar.time_slice_to_slice = [];
        physio.scan_timing.sqpar.Nprep = [];
        physio.scan_timing.sqpar.onset_slice = 1; % 1 in Alejandro's code
        
        % Method to determine slice acquisition onset times.
        % 'nominal'           derive slice acquisition timing from sqpar directly
        % 'gradient_log'      derive from logged gradient time courses (Philips)
        % 'scan_timing_log'   uses individual scan timing logfile with time stamps
        %                     specified in log_files.scan_timing
        %                     e.g.,
        %                     *_INFO.log for 'Siemens_Tics' (time stamps for every slice and volume)
        %                     *.dcm (DICOM) for Siemens, is first volume (non-dummy) used in GLM analysis
        %                     *.tsv (3rd column) for BIDS, using the scanner volume trigger onset events
        %                     NOTE: This setting needs a valid filename entered in log_files.scan_timing.
        physio.scan_timing.sync.method = 'nominal';
        
        %% preproc module
        % Preprocessing strategy and parameters for physiological data.
        
        % Measurement modality of input cardiac signal: 'ECG','ECG_raw', 'PPU'
        physio.preproc.cardiac.modality = 'PPU';
        
        % Filter properties for bandpass-filtering of cardiac signal before peak
        % detection, phase extraction, and other physiological traces.
        physio.preproc.cardiac.filter.include = 0; % 1 = YES; 0 = NO
        % Zero in Alejandro's code.
        
        % The initial cardiac pulse selection structure determines how most of the
        % cardiac pulses are detected.
        % 'auto_matched' [default]: auto generation of representative QRS-wave;
        %                           detection via max. auto-correlation with it.
        % 'load_from_logfile': from phys logfile, detected R-peaks of scanner.
        % 'manual': via manually selected QRS-wave for autocorrelations.
        % 'load': from previous manual/auto run.
        physio.preproc.cardiac.initial_cpulse_select.method = 'auto_matched';
        % AT: load_from_logfile ... but IDK if we have because BIOPAC for me
        
        % Maximum allowed physiological heart rate in beats per minute.
        physio.preproc.cardiac.initial_cpulse_select.auto_matched.max_heart_rate_bpm = 90;
        
        % Peak height threshold in z-scored cardiac waveform to find pulse events.
        physio.preproc.cardiac.posthoc_cpulse_select.min = 0.4;
        
        % The post-hoc cardiac pulse selection structure: If only few (<20) cardiac
        % pulses are missing in a session due to bad signal quality, a manual
        % selection after visual inspection is possible. The results are saved for
        % reproducibility.
        %
        % 'off'     - no manual selection of peaks
        % 'manual'  - pick and save additional peaks manually
        % 'load'    - load previously selected cardiac pulses
        physio.preproc.cardiac.posthoc_cpulse_select.method = 'off';
        
        % [f_min, f_max] frequency interval in Hz of all frequency that should
        % pass the passband filter. Remove high frequency noise and low frequency
        % drifts, but don't distort.
        physio.preproc.respiratory.filter.passband = [0.01, 2.0];
        
        % Whether to remove spikes from the raw respiratory trace using a sliding
        % window median filter.
        physio.preproc.respiratory.despike = false;
        
        %% model module
        % Derive physiological noise model from preprocessed data. Several models
        % can be combined.
        
        % Unless, we want a session mean (then set to 'all), no orthogonalisation
        % is needed because our acquisition was NOT triggered to heartbeat.
        physio.model.orthogonalise = 'none';
        
        % True only for RETROICOR model.
        physio.model.censor_unreliable_recording_intervals = true; % DEFAULT
        
        % Saving the entire physio-structure
        physio.model.output_multiple_regressors = sprintf('sub-%02d_ses-%02d_task-%s_acq-%s_regressors.tsv', subID, sesID, task, string(bids_names{1, i}));
        physio.model.output_physio              = sprintf('sub-%02d_ses-%02d_task-%s_acq-%s_physio.mat', subID, sesID, task, string(bids_names{1, i}));
        
        %%%% RETROICOR Model: Glover et al. 2000. Based on cardiac & resp. phase.
        physio.model.retroicor.include  = 1;  % 1 = included; 0 = not used
        
        % Natural number, order of cardiac phase Fourier expansion.
        model.retroicor.order.c  = 3;
        
        % Natural number, order of respiratory phase Fourier expansion.
        model.retroicor.order.r  = 4;
        
        % Natural number, order of cardiac-respiratory-phase-interaction Fourier expansion
        model.retroicor.order.cr = 1;
        
        % %%%% RVT Model: Respiratory Volume per time model , Birn et al., 2006/8
        % physio.model.rvt.include = 1;
        % physio.model.rvt.method  = 'hilbert';
        % physio.model.rvt.delays  = 0; % Delays: 0, 5, 10, 15, and 20s (Jo et al., 2010 NeuroImage 52)
        %
        % %%%% HRV Model: Heart Rate variability, Chang et al., 2009
        % physio.model.hrv.include = 1;
        % physio.model.hrv.delays  = 0; % Delays e.g. 0:6:24s (Shmueli et al, 2007, NeuroImage 38)
        %
        % %%%% Noise ROIs Model: Anatomical Component Correction, Behzadi et al, 2007
        % physio.model.noise_rois.include = 0;
        %
        % % Cell of preprocessed fMRI nifti/analyze files, from which time series
        % % shall be extracted.
        % physio.model.noise_rois.fmri_files = {};
        %
        % % Cell of Masks/tissue probability maps characterizing where noise resides.
        % physio.model.noise_rois.roi_files = {};
        %
        % % Single threshold or vector [1, nRois] of thresholds to be applied to mask files to decide
        % % which voxels to include (e.g. a probability like 0.99, if roi_files are tissue probability maps)
        % physio.model.noise_rois.thresholds = 0.9;
        % physio.model.noise_rois.n_voxel_crop = 0;
        %
        % % integer >=1: number of principal components to be extracted from all
        % % voxel time series within each ROI
        % physio.model.noise_rois.n_components = 1;
        %
        %  % Coregister : Estimate & Reslice will be performed on the noise NOIs, so
        %  % their geometry (space + voxel size) will match the fMRI volume.
        % physio.model.noise_rois.force_coregister = 1;
        %
        % %%%% Movement Model: Regressor model 6/12/24, Friston et al. 1996
        % physio.model.movement.include = 1;
        % physio.model.movement.file_realignment_parameters = '';
        %
        % % The actual setting depends on the chosen thresholding method:
        % % 'MAXVAL'   -  [1,1...6] max translation (in mm) and rotation (in deg) threshold
        % %                recommended: 1/3 of voxel size (e.g., 1 mm)
        % %                default: 1 (mm)
        % %                1 value   -> used for translation and rotation
        % %                2 values  -> 1st = translation (mm), 2nd = rotation (deg)
        % %                6 values  -> individual threshold for each axis (x,y,z,pitch,roll,yaw)
        % % 'FD'       -   [1,1] framewise displacement (in mm)
        % %                default: 0.5 (mm)
        % %                recommended for subject rejection: 0.5 (Power et al., 2012)
        % %                recommended for censoring: 0.2 (Power et al., 2015)
        % % 'DVARS'    -   [1,1] in percent BOLD signal change
        % %                recommended for censoring: 1.4 % (Satterthwaite et al., 2013)
        % model.movement.censoring_threshold = 0.5;
        %
        % %   'None'      - no motion censoring performed
        % %   'MAXVAL'    - thresholding (max. translation/rotation)
        % %   'FD''       - frame-wise displacement (as defined by Power et al., 2012)
        % %                 i.e., |rp_x(n+1) - rp_x(n)| + |rp_y(n+1) - rp_y(n)| + |rp_z(n+1) - rp_z(n)|
        % %                       + 50 mm *(|rp_pitch(n+1) - rp_pitch(n)| + |rp_roll(n+1) - rp_roll(n)| + |rp_yaw(n+1) - rp_yaw(n)|
        % %                 where 50 mm is an average head radius mapping a rotation into a translation of head surface
        % %   'DVARS'     - root mean square over brain voxels of
        % %                 difference in voxel intensity between consecutive volumes
        % %                 (Power et al., 2012))
        % physio.model.movement.censoring_method = 'FD';
        
        %% verbose module
        physio.verbose.level = 0; % 1--4
        physio.verbose.fig_output_file = sprintf('sub-%02d_ses-%02d_task-%s_acq-%s_output.jpg', subID, sesID, task, string(bids_names{1, i}));
        physio.verbose.show_figs = true;
        physio.verbose.save_figs = true;
        
        %% ons_sec module
        physio.ons_secs.c_scaling = 1;
        physio.ons_secs.r_scaling = 1;
        
        %% Create main regressors by inputing the PhysIO.
        [physio_out, R, ons_secs] = tapas_physio_main_create_regressors(physio);
    end
end 