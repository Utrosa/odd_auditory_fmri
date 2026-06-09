#! /usr/bin/env python
# Time-stamp: <2025-18-09 m.utrosa@bcbl.eu>
# -----------------------------------------------------------------------------
# Extracting values from collected data within ROI masks from Sitek's atlas
# DOI: 10.7554/eLife.48932
# -----------------------------------------------------------------------------

# Import python packages
import os, bids
import pandas as pd
import numpy as np
import nibabel as nib
import seaborn as sns
import matplotlib.pyplot as plt

# Import custom-made functions
import grabber

# -----------------------------------------------------------------------------
# DEFINE FUNCTIONS
# -----------------------------------------------------------------------------
def extract_roi_array(subID, sesID, acqID, atlas, spmT_path, rois, out_dir):
	'''
	Extracts spmT values from the specified regions of interest (ROIs).
	All extracted ROIs are saved in out_dir.

	Parameters:
	- subID: integer number, identifying the participant
	- sesID: integer number, identifying the session info
	- acqID: string, identifying the functional MRI sequence
	- atlas: string, path to an established atlas
	- spmT_path: string, path to outputs of 1st Level Analysis with SPM in Nipype
	- rois: dictionary, specifying names, volume and atlas label of target ROIs.
	- out_dir: string, specifying the folder name for saving the results as .nii.gz

	Returns:
	- spmT_rois: dictionary, extracted spmT values per each ROI
	- spmT_roi_paths: dictionary, paths to the extracted spmT values per each ROI

	'''
	# Load atlas image (Sitek)
	atlas_img    = nib.load(atlas)
	atlas_data   = atlas_img.get_fdata()
	atlas_affine = atlas_img.affine

	# Load SPM's t-map
	spmT_img    = nib.load(spmT_path)
	spmT_data   = spmT_img.get_fdata() 
	spmT_affine = spmT_img.affine

	# Compare affines and ignore tiny differences due to floating points
	print(atlas_affine)
	print("qform spmT:",    spmT_img.header.get_qform()[0])
	print("qform Sitek:",   atlas_img.header.get_qform()[0])
	print("sform spmT:",    spmT_img.header.get_sform()[0])
	print("sform Sitek:",   atlas_img.header.get_sform()[0])
	print(spmT_affine)

	# Extract spmT values per ROI
	spmT_rois = {}
	spmT_roi_paths = {}
	for name, roi in rois.items():
		mask_array  = (atlas_data == roi['label']).astype(float)
		spmT_masked = mask_array * spmT_data
		contrast_array = spmT_data[mask_array > 0].flatten() # Alejandro says: "Plot this!"

		# Save result
		result_filename = f"sub-{subID:02d}_ses-{sesID:02d}_acq-{acqID}_roi-{name}.nii.gz"
		result_path = os.path.join(out_dir, result_filename)
		nib.save(nib.Nifti1Image(spmT_masked, spmT_affine), result_path)

		# Save voxels values for plotting
		spmT_rois[name]      = contrast_array
		spmT_roi_paths[name] = result_path

	return spmT_rois, spmT_roi_paths

def plot_violins(mask_paths, subID, sesID, acqIDs, out_dir, scale):

	rows = []
	for acq_name, roi_masks in mask_paths.items():
		
		for roi_name, roi_path in roi_masks.items():
			mask_img = nib.load(roi_path)
			vals = mask_img.get_fdata().flatten()
			vals = vals[vals != 0]
			if len(vals) < 5:
				print(f"Warning: very few voxels for {roi_name}, {acq_name}")
			rows.extend([{"ROI": roi_name, "acqID": acq_name, "values": v} for v in vals])
		
	df = pd.DataFrame(rows)
	print(df.head())

	for roi, group in df.groupby("ROI"):
		n_acq = len(acqIDs)
		fig, axes = plt.subplots(1, n_acq, figsize = (1.5 * n_acq, 8), sharey = True)
		
		if n_acq == 1:
			axes = [axes]
		
		for ax, acq in zip(axes, acqIDs):
			sub_df = group[group["acqID"] == acq]
			color_map = dict(zip(acqIDs, sns.color_palette("pastel", n_colors=len(acqIDs))))
			if not sub_df.empty:
				sns.violinplot(y = "values", data = sub_df, ax = ax, hue="ROI",
							   legend = False, inner = "box", cut = 0, 
							   palette = [color_map[acq]], bw_adjust = 0.5)

				ax.set_title(f"{acq}", fontsize = 8)
				ax.set_xlabel("")
			ax.set_xticks([])
			if scale == True:
				ax.set_ylim(-5, 5)

		fig.suptitle(f"sub-{subID:02d}_ses-{sesID:02d}_roi-{roi}", fontsize = 12)
		fig.tight_layout()
		fig_path = os.path.join(out_dir,f"sub-{subID:02d}_ses-{sesID:02d}_roi-{roi}_violins.png")
		plt.savefig(fig_path, dpi = 200, bbox_inches = "tight")
		plt.close(fig)

# -----------------------------------------------------------------------------
# EXAMPLE USAGE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
	
	# Define subject and session info -----------------------------------------
	subID = 4
	sesID = 1

	if sesID == 1:
		acqIDs = ["NOACC15", "NOACC16"]

	# # Pilot 03 acquisition labels
	# if sesID == 1:
	# 	acqIDs = ["PF78", "NOACC", "GRAPPA"]
		
	# Define ROIs -------------------------------------------------------------
	# Size represents the volume (mm3) of auditory subcortical structures in
	# their in-vivo functional clusters. See Table 1 in Sitek et al. (2019).
	# Label is identified from plotting unique atlas values in freeview.
	rois = {'CN-L'  : {'size': 11, 'label': 1},
			'CN-R'  : {'size': 11, 'label': 2},
			'SOC-L' : {'size': 29, 'label': 3},
			'SOC-R' : {'size': 29, 'label': 4},
			'IC-L'  : {'size': 146, 'label': 5},
			'IC-R'  : {'size': 146, 'label': 6},
			'MGB-L' : {'size': 152, 'label': 7},
			'MGB-R' : {'size': 152, 'label': 8}}

	homePath   = "/home/mutrosa/Documents/projects/select_fMRI"
	atlas_path = homePath + "/templates/atlas/invivo_resampled_to-MNI_res-01.nii.gz"
	MNI_path   = homePath + "/templates/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz"
	out_dir    = homePath + "/results/visualization"
	os.makedirs(out_dir, exist_ok=True)
	
	# Extract data from ROIs --------------------------------------------------
	mask_paths = {}
	for acqID in acqIDs:
		print(acqID)
		spmT_path  = homePath + f"/results/1stLevel/sub-{subID:02d}/ses-{sesID:02d}/acq-{acqID}/spmT_space-MNI_0001_trans_out.nii.gz"
		masks, mask_path = extract_roi_array(subID, sesID, acqID, atlas_path, spmT_path, rois, out_dir)
		mask_paths[acqID] = mask_path

	# Plotting ----------------------------------------------------------------
	plot_violins(mask_paths, subID, sesID, acqIDs, out_dir, scale=True)