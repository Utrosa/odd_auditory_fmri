#! /usr/bin/env python
# Time-stamp: <2026-03-03 m.utrosa@bcbl.eu>
"""
Create temporal signal-to-noise ratio (tSNR) maps to identify where
in the brain we're capturing most signals versus noise.

Goal: high test-retest reliability (trusting MRI measurements)
Problem: differential power in MRI (signal fallouts)
Environment: conda activate nipype
"""

# Import python packages
import argparse
import bids
import subprocess
import nibabel as nib
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Import custom-made functions
import grabber

def cut_bold(homePath, preprocPath, subID, sesID, acqIDs, task_time, dummy_vols, space):
	"""
	Cut each BOLD acquisition into two files: task and rest.
	We collected 12 min of data in Pilot 03 and 04. The last 2 min
	are without a task, serving as a signal baseline (resting state).

	Parameters:
		homePath: Base directory of the project.
		preprocPath: Directory with preprocessed BOLD images.
	    subID: Subject identifier.
	    sesID: Session identifier.
	    acqIDs: A list of acquisition labels.
	    task_time: Task duration in seconds.
	    dummy_vols: Number of dummy volumes at the start (no-task).
	    space: T1w or MNI152NLin2009cAsym

	Side effects:
		- Creates two BOLD files per session and subject.

	Raises:
	    FileNotFoundError if required preprocessed derivative files are missing.
	"""

	# Define output paths
	OUT_DIR =  homePath / "data_MRI" / "preproc_cut"
	OUT_DIR.mkdir(parents=True, exist_ok=True)
	print(f"\nCutting output folder: {OUT_DIR}")

	for acqID in acqIDs:

		# Find BOLD nii.gz
		BOLD_CONF   = grabber.define_grabconf(subID, sesID, "bold", "nii.gz", space = space, acquisition=acqID)
		BOLD_LAYOUT = bids.layout.BIDSLayout(preprocPath, validate=False)
		BOLD_FILE   = grabber.grab_BIDS_object(preprocPath, BOLD_LAYOUT, BOLD_CONF)
		if not BOLD_FILE:
			raise FileNotFoundError(
				f"No derivative BOLD found for sub-{subID:02d}, ses-{sesID:02d}, acq-{acqID} in {preprocPath}."
				)

		# Get the voulmen number at which the task stops (rest starts)
		TR = BOLD_FILE[0].get_metadata()['RepetitionTime']
		n_vols = subprocess.run(
			["fslnvols", BOLD_FILE[0].path],
			check=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True,
		)
		n_vols = int(n_vols.stdout.strip())
		task_vols  = task_time // TR # correct for zero-indexing in fsl!
		task_vols  = task_vols + dummy_vols # account for time spent collecting the first 4 dummy vols
		rest_vols  = n_vols - task_vols

		# Use FSL to extract timeseries before and after 10 min point

		# ------ TASK: assuming start at 0 and end at the cut point ------
		print(f"\n~~~~~~ Working on TASK timeseries {acqID} ~~~~~~")
		TAKS_NAME = f"sub-{subID:02d}_ses-{sesID:02d}_task-localizer_acq-{acqID}_space-{space}_desc-preproc_bold.nii.gz"
		TASK_OUT  = OUT_DIR / "task" / f"sub-{subID:02d}" / f"ses-{sesID:02d}" 
		TASK_OUT.mkdir(parents=True, exist_ok=True)
		TASK_PATH = TASK_OUT / TAKS_NAME

		task = subprocess.run(
			["fslroi", str(BOLD_FILE[0].path), str(TASK_PATH), "0", str(task_vols)],
			check=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True,
			)
		print(task)

		# ------ REST: assuming start at cut point and end at the last volume ------
		print(f"\n~~~~~~ Working on REST timeseries for {acqID} ~~~~~~")
		REST_NAME = f"sub-{subID:02d}_ses-{sesID:02d}_task-rest_acq-{acqID}_space-{space}_desc-preproc_bold.nii.gz"
		REST_OUT  = OUT_DIR / "rest" / f"sub-{subID:02d}" / f"ses-{sesID:02d}"
		REST_OUT.mkdir(parents=True, exist_ok=True)
		
		REST_PATH = REST_OUT / REST_NAME
		rest = subprocess.run(
			["fslroi", str(BOLD_FILE[0].path), str(REST_PATH), str(task_vols), str(rest_vols)],
			check=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True,
			)
		print(rest)

def calculate_tsnr(homePath, boldPath, maskPath, subID, sesID, acqIDs, task):
	"""
	Compute temporal Signal-to-Noise Ration (tSNR)
	for each BOLD acquisition in T1w space.

	tSNR is defined as:
		mean(signal over time) / std(signal over time)

	Parameters:
		homePath: Base directory of the project.
		boldPath: Directory with BOLD images.
		maskPath: Directory with preprocessed derivatives.
	    subID: Subject identifier.
	    sesID: Session identifier.
	    acqIDs: A list of acquisition labels.
	    task: Localizer vs rest.

	Side effects:
		- Creates one CSV file per session and subject with tSNR values

	Raises:
	    FileNotFoundError if required preprocessed derivative files are missing.
	"""

	# Define output paths
	OUT_DIR = homePath / "results_tSNR" / f"sub-{subID:02d}" / f"ses-{sesID:02d}"
	OUT_DIR.mkdir(parents=True, exist_ok=True)
	print(f"\ntSNR output folder: {OUT_DIR}")

	all_acq_tsnr = []    # initialize a list of dictionaries to store data
	for acqID in acqIDs: # loop through all acquisition labels

		# Find BOLD data
		BOLD_CONF   = grabber.define_grabconf(subID, sesID, "bold", "nii.gz", space = "T1w", acquisition=acqID)
		BOLD_LAYOUT = bids.layout.BIDSLayout(boldPath, validate=False)
		BOLD_FILE   = grabber.grab_BIDS_object(boldPath, BOLD_LAYOUT, BOLD_CONF)
		if not BOLD_FILE:
			raise FileNotFoundError(
				f"No derivative BOLD found for sub-{subID:02d}, ses-{sesID:02d}, acq-{acqID} in {boldPath}."
				)
		else:
			print(f"\n Calculating TSNR for BOLD file: \n{BOLD_FILE[0].path}")

		# Load BOLD image
		bold_img  = nib.load(BOLD_FILE[0])
		bold_data = bold_img.get_fdata()

		# Calculate tSNR
		# tSNR is the mean BOLD signal across the timeseries divided by
		# the standard deviation of the BOLD signal across the timeseries.
		mean_signal = np.mean(bold_data, axis=-1)
		std_signal  = np.std(bold_data,  axis=-1, ddof=1)

		# Safe division
		tsnr_voxels = np.divide(
			mean_signal,
			std_signal,
			out = np.zeros_like(mean_signal),
			where = std_signal > 0
		)

		# Find the mask
		MASK_CONF   = grabber.define_grabconf(subID, sesID, "mask", "nii.gz", space = "T1w", acquisition=acqID)
		MASK_LAYOUT = bids.layout.BIDSLayout(maskPath, validate=False)
		MASK_FILE   = grabber.grab_BIDS_object(maskPath, MASK_LAYOUT, MASK_CONF)

		# Load mask image
		mask_img = nib.load(MASK_FILE[0])
		mask     = mask_img.get_fdata().astype(bool)
		flattened_tsnr = tsnr_voxels[mask]

		# Store voxelwise for violin plot
		tsnr_df = pd.DataFrame({
								"subject": subID,
								"session": sesID,
								"task": task,
								"acqID": acqID,
								"tsnr": flattened_tsnr
								})

		# Save to CSV
		orig_path = Path(BOLD_FILE[0].path)
		base_name = orig_path.name.replace(".nii.gz", "")
		tsnr_file = OUT_DIR / f"{base_name}_tSNR.csv"
		tsnr_df.to_csv(tsnr_file, index=False)
		print(f"Saved {tsnr_file}")

def plot_tsnr_violins(tsnr_dir, subID, sesID):
	"""
	Creates a single figure per session and subject.
	Visualizes tSNR distrubution per acqID (one CSV file).
	"""

	# Collect data per subject and session
	T_PATH = Path(tsnr_dir)
	csv_files = sorted(T_PATH.glob("*.csv"))
	print((f"\nPlotting from: {csv_files}"))

	# Loop through each csv file and append the data
	all_data = []
	for csv_file in csv_files:
		df = pd.read_csv(csv_file)
		all_data.append(df)

	# Concatenate datafames
	combined_df = pd.concat(all_data, ignore_index=True)
	
	# Remove zero tSNR values
	combined_df = combined_df[
		(combined_df["tsnr"] > 0) &
		(combined_df["tsnr"] < 500)
	]
	print(combined_df.head())

	# Create a violin figure
	fig, ax = plt.subplots(figsize=(12, 10))
	sns.violinplot(
		data=combined_df,
		x="acqID",
		y="tsnr",
		hue="task",
		palette="pastel",
		inner="box",   # represent every observation inside the distribution
		cut=0,         # limit the violin within the data range
		ax=ax
	)

	# Set labels and title
	ax.set_title(f"tSNR for sub-{subID:02d}, ses-{sesID:02d}", fontsize=14)
	ax.set_xlabel("Acquisition ID")
	ax.set_ylabel("tSNR")
	ax.tick_params(axis="x")

	# Adjust layout to avoid overlapping
	plt.tight_layout()

	# Save the plot
	fig_file = T_PATH / f"sub-{subID:02d}_ses-{sesID:02d}_tSNR_violin.png"
	plt.savefig(fig_file, dpi=300)
	plt.close()

	print(f"Saved violin plot to: {fig_file}")

# ------- EXAMPLE USAGE ------- 
subID = 1
sesID = 2

homePath    = Path("/home/mutrosa/Documents/projects/select_fMRI")
preprocPath = homePath / "data_MRI" / "derivatives"
task_bold   = homePath / "data_MRI" / "preproc_cut" / "task" / f"sub-{subID:02d}" / f"ses-{sesID:02d}"
rest_bold   = homePath / "data_MRI" / "preproc_cut" / "rest" / f"sub-{subID:02d}" / f"ses-{sesID:02d}"
tsnr_path   = homePath / "results_tSNR" / f"sub-{subID:02d}" / f"ses-{sesID:02d}"
acqIDs      = ["PF78", "NOACC", "GRAPPA"]
# acqIDs      = ["NOACC15", "NOACC16"]
task_time   = 600 # Stable in expyriment software to 5 x 2 (sound-silence) = 10 60-sec trials
dummy_vols  = 4   # The number of volumes to wait before starting the task

cut_bold(homePath, preprocPath, subID, sesID, acqIDs, task_time, dummy_vols, "T1w")
calculate_tsnr(homePath, task_bold, preprocPath, subID, sesID, acqIDs, "localizer")
calculate_tsnr(homePath, rest_bold, preprocPath, subID, sesID, acqIDs, "rest")
plot_tsnr_violins(tsnr_path, subID, sesID)