# fMRI Sequence Selection
We developed 16 functional MRI sequences that we are comparing in their ability to record brain signals from subcortical auditory areas.

## Project Goals
1. Develop and test functional 2D EPI and multi-echo sequences with parameters optimzed for data collection from subcortical brain regions.
2. Evaluate signal quality for each sequence and select the best one.

## Summary of Data Analysis Steps 
Data are stored in 3 different folders, depending on their source (MRI scanner, software for the experimental task and physiological data - BIOPAC).

### 01 Curation
1. Get the data from the source and save :
	.dcm files from MRI scanner in data_MRI/sourcedata/dicoms
	.acq files from BIOPAC in data_physio/sourcedata
	.txt files from Expyriment in BIDS data_logs/sourcedata
	--> These folders are untouched by next steps to ensure replicable pipeline.
2. Check that data is complete and correctly named. Naming conventions are:
   .dcm data: sub-{subID:02d}_ses-{sesID:02d}_{project} folders
   .acq data:
   .txt data: include only files from the "bids_output" folder which have ".tsv" extension. All files should be in "sourcedata" folder without subfolders.
3. Exclude incomplete data (e.g.: functional scans that were interrupted) and remove any duplicate data. Refer to the laboratory log to guide decisions. The log contains info on execution of the MRI protocol during data acquisition such as errors or modifications.
4. Check onsets in log files and run `onset_correction.py` if necessary.
5. Run 00_pre_import.py to create sidecar files, needed for the config file.
6. Set up the config file for BIDSifying MRI data with `dcm2bids`. The configuration doesn't have to include the headscouts and the phoenix ZIP report. Validate the config.json file: https://jsonlint.com/.

### 02 Importing & Preprocessing
1. Run: `bash 01_import_localizer.sh`
   Outputs:
   - raw MRI data in BIDS
   - background-corrected T1 (mp2rage) images
   - denoised functional and sbref images ([NORDIC](https://github.com/SteenMoeller/NORDIC_Raw/tree/main))
   - removed noise scans from bold and FH sbref for Dresden acquisitions
   - correctly named & onset corrected logfiles in (sub-XX/ses-XX/func/)
   - preprocessed physio data and physiological noise regressors (TAPAS) per session, subject, and functional sequence
   - optionally: optimally combined multi-echo BOLD and single-band references images ([t2smap](https://doi.org/10.21105/joss.03669))
3. Correct PhaseEncodingDirection with `correct_PED.py`, if necessary.
4. Visually inspect T1 and denoised images with `visualize.sh`.
5. Add task stimuli, `dataset_description`, and `README` files to data_MRI/sourcedata/raw/.
7. Run [BIDS Validator](http://bids.neuroimaging.io/tools/validator.html) on the dataset to ensure compliance to [the latest BIDS specification](https://bids-specification.readthedocs.io/en/stable/).
8. Run: `bash 02_fMRIprep_localizer.sh`
   Outputs:
   - preprocessed fMRI data
9. Delete temporary cache and work directories once preprocessing is successful.

### 03 Analysis
1. Run `bash 03_analyze_localizer.sh`

   Outputs:
	- modified counfounds and outliers (physiological artifacts)