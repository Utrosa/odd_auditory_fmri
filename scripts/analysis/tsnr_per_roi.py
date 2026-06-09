#! /usr/bin/env python
# Time-stamp: <2026-02-23 m.utrosa@bcbl.eu>
"""
Create temporal signal-to-noise ratio (tSNR) maps to identify where
in the brain we're capturing most signals versus noise.

Goal: high test-retest reliability (trusting MRI measurements)
Problem: differential power in MRI (signal fallouts)
Env: conda activate nipype
"""

# Import python packages
import argparse
import bids
import nibabel as nib
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Import custom-made functions
import grabber

def calculate_tsnr(homePath, subID, sesID, atlas, rois):
	"""
	Compute temporal Signal-to-Noise Ration (tSNR)
	for inferior colliculus and medial geniculate body
	for each BOLD acquisition in T1w space.

	tSNR is defined as:
		mean(signal over time) / std(signal over time)

	Parameters:
		homePath: Base directory of the project.
	    subID: Subject identifier.
	    sesID: Session identifier.
	    atlas: Path to an atlas image in the same space as BOLD.

	Side effects:
		- Creates one CSV file per session and subject with tSNR values

	Raises:
	    FileNotFoundError if required preprocessed derivative files are missing.
	    ValueError: If atlas and BOLD images do not match in shape.
	"""

	# Define output paths
	PREPROC_DIR = homePath / "data_MRI" / "derivatives"
	OUT_DIR = homePath / "results_tSNR" / f"sub-{subID:02d}" / f"ses-{sesID:02d}"
	OUT_DIR.mkdir(parents=True, exist_ok=True)

	print(f"\ntSNR output folder: {OUT_DIR}")

	# Load atlas image (Sitek)
	atlas_img    = nib.load(atlas)
	atlas_data   = atlas_img.get_fdata()
	atlas_affine = atlas_img.affine

	# Find BOLD data
	BOLD_CONF   = grabber.define_grabconf(subID, sesID, "bold", "nii.gz", space = "T1w")
	BOLD_LAYOUT = bids.layout.BIDSLayout(PREPROC_DIR, validate=False)
	BOLD_FILES  = grabber.grab_BIDS_object(PREPROC_DIR, BOLD_LAYOUT, BOLD_CONF)
	if not BOLD_FILES:
		raise FileNotFoundError(
			f"No derivatives found for sub-{subID:02d}, ses-{sesID:02d} in {PREPROC_DIR}."
			)
	else:
		print(f"\n Detected BOLD files: \n{BOLD_FILES}")

	# Calculate tSNR per bold scan and roi
	for boldID in BOLD_FILES:

		# Load BOLD image
		print(f"BOLD ID: {boldID}")
		bold_img  = nib.load(boldID)
		bold_data = bold_img.get_fdata()

		# Calculate tSNR
		# tSNR is the mean BOLD signal across the timeseries divided by
		# the standard deviation of the BOLD signal across the timeseries.
		mean_signal = np.mean(bold_data, axis=1)
		std_signal  = np.std(bold_data,  axis=1)

		# Safe division
		tsnr_voxels = np.divide(
			mean_signal,
			std_signal,
			out = np.zeros_like(mean_signal),
			where = std_signal > 0
		)

		all_roi_tsnr = []
		for roi_name, roi_specs in rois.items():

			# Extract data from the ROI
			roi_mask = (atlas_data == roi_specs['label']).astype(float)
			bold_masked = roi_mask * tsnr_voxels
			roi_data = tsnr_voxels[roi_maks > 0].flatten()

			# Store voxelwise for violin plot
			for val in roi_data:
				all_roi_tsnr.append({
					"subject": subID,
					"session": sesID,
					"bold": boldID,
					"roi": roi_name,
					"tsnr": val
				})

		# Save to CSV
		tsnr_file = OUT_DIR / f"sub-{subID:02d}_ses-{sesID:02d}_acq-{boldID}_roi-{roi_name}_tSNR.csv"
		tsnr_df = pd.DataFrame(all_roi_tsnr)
		tsnr_df.to_csv(tsnr_file, index=False)
		print(f"Saved {out_file}")

def plot_tsnr_violins(tsnr_dir, subID, sesID):
	"""
	Creates one multi-panel figure per session and subject.
	Each subplot visualizes tSNR distrubution per roi (one CSV file).
	"""

	# Collect data per subject and session
	T_PATH = Path(tsnr_dir)
	csv_files = sorted(T_PATH.glob("*.csv"))
	print((f"\n Plotting from: {csv_files}"))

	# Subplot grid
	n_files = len(csv_files)
	n_cols  = min(2, n_files)
	n_rows  = np.ceil(n_files / n_cols)

	# Figure
	fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 8))
	axes = axes.flatten()
	for idx, csv_files in enumerate(csv_files):

		df = pd.read_csv(csv_files)

		sns.violinplot(
			data=df,
			x="roi",
			y="tsnr",
			inner="box",
			cut=0,
			ax=axes[idx]
		)

		axes[idx].set_title(csv_file.stem)
		axes[idx].tick_params(axis="x", rotation=45)
		axes[idx].set_xlabel("ROI")
		axes[idx].set_ylabel("tSNR")

		fig.suptitle(
			f"Voxelwise tSNR Distribution\nsub-{subID:02d} ses-{sesID:02d}",
			fontsize=14
			)

		plt.tight_layout()

		# Save
		fig_file = T_PATH / f"sub-{subID:02d}_ses-{sesID:02d}_tSNR_violin.png"
		plt.savefig(fig_file, dpi=300)
		plt.close()
		
		print(f"Saved violin plot to: {fig_file}")

# ------- EXAMPLE USAGE
subID = 4
sesID = 1

homePath  = Path("/home/mutrosa/Documents/projects/select_fMRI")
atlas_path = homePath / "templates" / "atlas" / "invivo_resampled_to-T1w_res-01.nii.gz"
tsnr_path  = homePath / "results_tSNR" / f"sub-{subID}" / f"ses-{sesID}"
rois = {
	'IC-L'  : {'size': 146, 'label': 5},
	'IC-R'  : {'size': 146, 'label': 6},
	'MGB-L' : {'size': 152, 'label': 7},
	'MGB-R' : {'size': 152, 'label': 8}
	}

calculate_tsnr(homePath, subID, sesID, atlas_path, rois)
plot_tsnr_violins(tsnr_path, subID, sesID)