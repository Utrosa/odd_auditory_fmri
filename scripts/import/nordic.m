function nordic(fn_magn_in, fn_phase_in, denoisedPath)
    
    % Set parameters as suggested by official documentation
    ARG.noise_volume_last = 1;
    ARG.temporal_phase=1; % Correction for slice and time-specific phase
    ARG.phase_filter_width=10;
    ARG.write_gzipped_niftis = 1;

    % Create the output directory, if it doesn't exit already.
    ARG.DIROUT = denoisedPath;
    if not(isfolder(ARG.DIROUT))
        mkdir(ARG.DIROUT);
    end

    % Correct the issue with the file separators
    if ARG.DIROUT(end) ~= filesep
        ARG.DIROUT = [ARG.DIROUT filesep];
    end
    
    % Extract the BOLD filename from the full path
    [~, fname, ~] = fileparts(fn_magn_in);
    fn_out = fname(1:end-4);

    % Run the NORDIC for fMRI data
    NIFTI_NORDIC(fn_magn_in, fn_phase_in, fn_out, ARG)
end