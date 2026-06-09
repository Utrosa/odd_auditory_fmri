#! /usr/bin/env python
# Time-stamp: <2025-05-09 m.utrosa@bcbl.eu>
"""
Select target artifacts for inclusion as regressors in the first level GLM analysis.

Artifacts are sourced from fMRIprep output (timeseries csv). 
fMRIprep estimates confounds from a motion-corrected BOLD images, brain mask, 
mcflirt movement parameters, and a segmentation. 

fMRIprep calculates the following confounds:
	- mean global signal,
	- mean tissue class signal,
	- tCompCor, 
	- aCompCor,
	- Frame-wise Displacement,
	- 6 motion parameters,
	- DVARS, and
	- spike regressors.

1. Confounds
Defaults:
	- rot & trans: rigid-body transform parameters in x, y and z directions indicate how much and how fast you move.
	- csf & wm: the average signal inside cerebrospinal fluid and white-matter masks across time.

Optionally, adding physiological regressors: respiration and heartbeat.
TO-DO: Adding 02 and CO2 regressors.

2. Motion Outliers
Adding only columns for volumes with motion outliers.
Outliers are identified with "1" in the "motion_outlier" columns.
Find the 1 in these columns and extract the volume number (the row number).
"""

# Import python packages
import argparse, bids
import pandas as pd
from pathlib import Path
from datetime import datetime

# Import custom-made functions (scripts)
from scripts import grabber

def filter_artifacts(homePath, subID, sesID, acqIDs, confound_keys, include_biopac=True):
	'''
	Filter artifacts.

	Parameters:
		homePath: Base directory of the project.
	    subID: Subject identifier.
	    sesID: Session identifier.
	    acqIDs: List of acquisition labels in order of data collection.
	    confound_keys: List of confound keys/labels.
	    include_biopac: If True, includes physiological regressors from BIOPAC data.

	Side effects:
	    Creates two files on disk, including:
	    - txt with confound values (no header)
	    - txt with motion outliers values (no header)
	    - md summary file including column names of selected artifacts

    '''

	# Define paths
	homePath = Path(homePath)
	confoundPath  = homePath / "data_MRI"
	regressorPath = homePath / "data_physio" / "raw"
	outputPath    = homePath / "data_physio" / "artifacts"
	outputPath.mkdir(exist_ok=True, parents=True)

	MRILayout    = bids.layout.BIDSLayout(confoundPath,  validate=False, derivatives=True)
	physioLayout = bids.layout.BIDSLayout(regressorPath, validate=False)

	# Specify confounds if none are specified
	if confound_keys[0] == 'None':
		print("No preference for confounds was specified.")

		trans_rot_keys = ['trans_x', 'trans_y', 'trans_z',
						 'rot_x', 'rot_y', 'rot_z']
		csf_wm_keys    = ["csf", "csf_derivative1", "csf_derivative1_power2", 
						  "csf_power2", "white_matter", "white_matter_derivative1",
						  "white_matter_derivative1_power2", "white_matter_power2",
						  "csf_wm"]
		confounds = trans_rot_keys + csf_wm_keys
	else:
		confounds = []
		for ck in confound_keys:
			confounds.append(ck)

	print(f"\nTaking the following confound parameters:\n{confounds}") 

	# Loop through fMRIprep confound files per acquisition
	outlier_columns = {} # for summary readme file
	for acqID in acqIDs:

		# Grab the correct files
		confound_conf  = grabber.define_grabconf(subID, sesID, "timeseries", "tsv", acquisition=acqID)
		regressor_conf = grabber.define_grabconf(subID, sesID, "regressors", "tsv", acquisition=acqID)
		timeseries = grabber.grab_BIDS_object(confoundPath,  MRILayout,    confound_conf)
		regressors = grabber.grab_BIDS_object(regressorPath, physioLayout, regressor_conf)
		print(f"\n\nTimeseries file: {timeseries[0].path}")
		print(f"Regressors file: {regressors[0].path}")

		if timeseries:

			# Load the data
			df_timeseries = pd.read_csv(timeseries[0].path, sep='\t')
			df_regressors = pd.read_csv(regressors[0].path, sep='\t', header=None).reset_index(drop=True)
			
			# ~~~~~~~~~ CONFOUNDS ~~~~~~~~~
			# Filter the data to select only columns with "confound_keys"
			df_selected = df_timeseries[confounds].reset_index(drop=True)
			
			# Optionally, add BIOPAC regressors as confounds
			if include_biopac:
				print("\nAdding physiological confounds from TAPAS.\n")
				df_final = df_selected.join(df_regressors)
				df_final = df_final.fillna(0)
			else:
				print("\nNot adding physiological confounds from TAPAS.\n")
				df_final = df_selected
				df_final = df_final.fillna(0)
			
			# Save confounds as a text file
			confound_filename = f"sub-{subID:02d}_ses-{sesID:02d}_acq-{acqID}_confounds.txt"
			confounds_out     = outputPath / confound_filename
			df_final.to_csv(confounds_out, sep=' ', header=False, index=False,)

			# ~~~~~~~~~ OUTLIERS ~~~~~~~~~
			# Identify the rows with motion outliers.
			# Note, indexing starts with 0 in pandas and 1 in LibreOffice ;)
			outlier_vols = []
			outlier_cols = []
			for key in df_timeseries.keys():
				if key.startswith('motion_outlier'):
					outlier_cols.append(key)
					for row, value in enumerate(df_timeseries[key]):
						if value == 1:
							outlier_vols.append(row)
			
			# Save column names per acquistion for tracking filtering process
			outlier_columns[acqID] = outlier_cols
			
			# Save outliers as a text file
			outlier_filename = f"sub-{subID:02d}_ses-{sesID:02d}_acq-{acqID}_outliers.txt"
			outlier_out      = outputPath / outlier_filename
			with open(outlier_out, 'w') as f:
				f.write('\n'.join(map(str, outlier_vols)))

			# Print progress report
			print(f"~~~~~~~~ Filtered confounds & artifacts for {acqID} acquistion ~~~~~~~~")

	# Save info on which counfounds and outliers were selected.
	readme_file = f"{outputPath}/sub-{subID:02d}_ses-{sesID:02d}_summary.md"
	with open(readme_file, 'w') as f:
		f.write("# Filer Artifacts - Summary\n")
		f.write(f"- Time and date: {datetime.now()}\n")
		f.write(f"- Acquisitions: {acqIDs}\n")
		f.write(f"- Confounds: {confounds}\n")
		f.write(f"- Motion Outliers: {outlier_columns}\n")

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	
	parser.add_argument("homePath")
	parser.add_argument("subID",  type=int)
	parser.add_argument("sesID",  type=int)
	parser.add_argument("--acqIDs", nargs="+", required=True)
	parser.add_argument("--confound_keys", nargs="+", required=True)
	parser.add_argument(
		"--include_biopac",
		action="store_true",
		help="Includes physiological regressors obtained with TAPAS from BIOPAC data."
		)

	args = parser.parse_args()

	filter_artifacts(
		args.homePath,
		args.subID,
		args.sesID,
		args.acqIDs,
		args.confound_keys,
		include_biopac=args.include_biopac
		)