#! /usr/bin/env python
# Time-stamp: <2025-05-09 m.utrosa@bcbl.eu>

# Import python packages
import pandas as pd
import bids, os, sys

# Import custom-made functions (scripts)
from scripts import grabber

def filter_artifacts(subID, sesID, homePath, confound_keys=None):
	'''
	01. Confounds
	fMRIprep output in csv indicating motion parameters (rot & trans in x, y and z directions)
	They indicate how much you move and derivatives for how fast you move.
	Resave, in a temporary file, only the columns of interest.
	Add TAPAS regressors to this temporary file.
	Adding 02 and CO2: ask Cesar.

	02. Outliers
	fMRIprep computes this automatically.
	These are added as columns in the same fMRIprep file.
	Outliers are identified as 1 in the motion_outlier columns.
	Find the 1 in these columns and extract the volume number (the row number).
    '''

	# Define paths
	confoundPath  = f"{homePath}/data_MRI/"
	regressorPath = f"{homePath}/data_physio/raw/"
	outputPath    = f"{homePath}/data_physio/artifacts/"
	os.makedirs(outputPath, exist_ok=True)

	# Specify MRI acquisition labels and get BIDS layout
	acqIDs = [
			"DresdenNoFat", "DresdenWFat", "ME1TR880", "ME3TR1600", "ME3TR1100",
			"ME3TR850", "ME3TR700", "DresdenNoFat175", "DresdenWFat175", 
			"ME1TR780", "ME3TR1180", "ME3TR770", "ME3TR680"
			]

	MRILayout    = bids.layout.BIDSLayout(confoundPath,  validate=False, derivatives=True)
	physioLayout = bids.layout.BIDSLayout(regressorPath, validate=False)

	# Specify confounds
	if not confound_keys:
		confound_keys = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']

	# Loop through fMRIprep confound files
	for i in acqIDs:

		# Grab the correct files
		confound_conf  = grabber.define_grabconf(subID, sesID, "timeseries", "tsv", acquisition=i)
		regressor_conf = grabber.define_grabconf(subID, sesID, "regressors", "tsv", acquisition=i)

		timeseries = grabber.grab_BIDS_object(confoundPath,  MRILayout,    confound_conf)
		regressors = grabber.grab_BIDS_object(regressorPath, physioLayout, regressor_conf)

		if timeseries:

			# Load the data, select target confounds from fMRIprep timeseries, and join with tapas regressors.
			df_timeseries = pd.read_csv(timeseries[0].path, sep='\t')
			df_regressors = pd.read_csv(regressors[0].path, sep='\t', header=None).reset_index(drop=True)
			df_selected   = df_timeseries[confound_keys].reset_index(drop=True)
			df_final      = df_selected.join(df_regressors)
			df_final.to_csv(f'{outputPath}/sub-{subID:02d}_ses-{sesID:02d}_acq-{i}_confounds.txt', header=False, index=False,
							sep=' ')

			# Identify the motion outliers and associated rows. Indexing starts with 0 in pandas and 1 in LibreOffice ;)
			outlier_vols = []
			for key in df_timeseries.keys():
				if key.startswith('motion_outlier'):
					for row, value in enumerate(df_timeseries[key]):
						if value == 1:
							outlier_vols.append(row)

			# Save
			with open(f'{outputPath}/sub-{subID:02d}_ses-{sesID:02d}_acq-{i}_outliers.txt', 'w') as f:
				f.write('\n'.join(map(str, outlier_vols)))

			# Return progress report
			print(f"Filtered artifacts for functional scanning sequence with acquisition ID: {i}")

if __name__ == "__main__":
	subID, sesID, homePath = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
	filter_artifacts(subID, sesID, homePath)