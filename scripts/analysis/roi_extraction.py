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
from nilearn.image import resample_to_img

# Import custom-made functions
import grabber

# -----------------------------------------------------------------------------
# DEFINE FUNCTIONS
# -----------------------------------------------------------------------------
def extract_roi_array(subID, sesID, acqID, atlas, template, spmT, rois, out_dir):
	'''
	Extracts spmT values from the specified regions of interest (ROIs).
	All extracted ROIs are saved in out_dir.

	Parameters:
	- subID: integer number, identifying the participant
	- sesID: integer number, identifying the session info
	- acqID: string, identifying the functional MRI sequence
	- atlas: string, path to an established atlas
	- template: string, path to space in which input data is (MNI or native)
	- spmT: string, path to outputs of 1st Level Analysis with SPM in Nipype
	- rois: dictionary, specifying names, volume and atlas label of target ROIs.
	- out_dir: string, specifying the folder name for saving the results as .nii.gz

	Returns:
	- spmT_rois: dictionary, extracted spmT values per each ROI

	'''
	# Load template image (MNI, T1w)
	template_img = nib.load(template)

	# Load atlas image (Sitek)
	atlas_img = nib.load(atlas)
	atlas_data = atlas_img.get_fdata()

	# Load SPM's t-values from 1st level analysis in Nipype
	spmT_img  = nib.load(spmT_path)
	spmT_data = spmT_img.get_fdata() 

	# Extract ROIs from the atlas
	spmT_rois = {}
	for name, roi in rois.items():
	    mask = (atlas_data == roi['label']).astype(np.uint8)

		# Select only the spmT values that are inside the ROI masks
		spmT_roi = mask[spmT_data]

		# Save in array for plotting
		spmT[name] = spmT_roi

		# Create directory
		os.makedirs(out_dir, exist_ok = True)

		# Save result as nifti
		result_filename = f"sub-{subID:02d}_ses-{sesID:02d}_acq-{acqID}_roi-{name}.nii.gz"
		result_path 	= os.path.join(out_dir, result_filename)
		result_img  	= nib.Nifti1Image(spmT_roi, template_img.affine, header = spmT_img.header)
		nib.save(result_img, result_path)
	
	return spmT_rois

# def plot_violins(mask_paths, subID, sesID, acqID_list, out_dir):
# 	rows = []
# 	for mask_path in mask_paths:

# 		# Extract ROI and acquisition names
# 		roi_name = mask_path.split("roi-")[1].split("_acq")[0]
# 		acq_name = mask_path.split("acq-")[1].split("_space")[0]
		
# 		mask_img = nib.load(mask_path)
# 		vals = mask_img.get_fdata().flatten()
# 		vals = vals[vals != 0]
# 		rows.extend([{"ROI": roi_name, "acqID": acq_name, "values": v} for v in vals])
	
# 	df = pd.DataFrame(rows)
# 	if df.empty:
# 		print("No values found in masks.")
# 		return []

# 	for roi, group in df.groupby("ROI"):
# 		n_acq = len(acqID_list)
# 		fig, axes = plt.subplots(1, n_acq, figsize = (1.5 * n_acq, 8), sharey = True)

# 		for ax, acq in zip(axes, acqID_list):
# 			sub_df = group[group["acqID"] == acq]
# 			color_map = dict(zip(acqID_list, sns.color_palette("pastel", n_colors=len(acqID_list))))
# 			if not sub_df.empty:
# 				sns.violinplot(y = "values", data = sub_df, ax = ax, hue="ROI", legend = False,
# 							   inner = "quartile", cut = 0, palette = [color_map[acq]])

# 				ax.set_title(f"{acq}", fontsize = 8)
# 				ax.set_xlabel("")
# 			ax.set_xticks([])

# 		fig.suptitle(f"sub-{subID:02d}_ses-{sesID:02d}_roi-{roi}", fontsize = 12)
# 		fig.tight_layout()
# 		fig_path = os.path.join(out_dir, 
# 		   f"sub-{subID:02d}_ses-{sesID:02d}_roi-{roi}_violins.png")
# 		plt.savefig(fig_path, dpi = 200, bbox_inches = "tight")
# 		plt.close(fig)

# -----------------------------------------------------------------------------
# RUN FUNCTIONS
# -----------------------------------------------------------------------------

subID = 4
sesID = 1

if subID == 1:
	acqID_list = ["DresdenNoFat", "DresdenWFat", "ME1TR880", "ME3TR1600", 
				  "ME3TR1100", "ME3TR850", "ME3TR700"]
elif subID == 2:
	acqID_list = ["DresdenNoFat", "DresdenWFat", "ME1TR880", "ME3TR1600"]
elif subID == 3:
	if sesID == 1:
		acqID_list = ["DresdenNoFat", "DresdenWFat", "ME1TR880", "ME3TR1600",
					  "ME3TR1100", "ME3TR850", "ME3TR700"]
	else:
		acqID_list = ["DresdenNoFat175", "DresdenWFat175", "ME1TR780", 
					  "ME3TR1180", "ME3TR770", "ME3TR680"]
else:
	if sesID == 1:
		acqID_list = ["DresdenNoFat", "DresdenWFat", "ME1TR880"]
	else:
		acqID_list = ["ME3TR1600", "ME3TR1100", "ME3TR850", "ME3TR700", 
					  "DresdenNoFat175", "DresdenWFat175",
  					  "ME1TR780", "ME3TR1180", "ME3TR770", "ME3TR680"]

# Define ROIs
# Size represents the volume (mm3) of auditory subcortical structures obtained
# in their in-vivo functional clusters. See Table 1 in Sitek et al. (2019).
# Label is identified from plotting unique atlas values in freeview.
rois = {'IC-L'  : {'size': 146, 'label': 5},
		'IC-R'  : {'size': 146, 'label': 6},
		'MGB-L' : {'size': 152, 'label': 7},
		'MGB-R' : {'size': 152, 'label': 8}}


homePath   = "/home/mutrosa/Documents/projects/localizer_fMRI"
atlas_path = homePath + f"/templates/atlas/invivo_resampled_to-MNI_res-01.nii.gz"
MNI_path   = homePath + "/templates/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz"
spmT_path  = homePath + f"/results/1stLevel/sub-{subID:02d}/ses-{sesID:02d}/acq-{acqID}/spmT_0001_trans_out.nii.gz"

mask_paths = []
for acqID in acqID_list:
	for key, roi in rois.items():
		mask_path = extract_roi__MNI(key, roi['path'], roi['size'], 
										acqID, subID, sesID, tmp_dir)
		mask_paths.append(mask_path)

# Plotting
plot_violins(mask_paths, subID, sesID, acqID_list, tmp_dir)# Prerequisites
import nibabel as nib
import numpy as np
import os

# Create folder to store masks
out_fold   = "rois"
out_dir    = os.makedirs(out_fold, exist_ok=True)

# Load atlas image
atlas_img  = nib.load(atlas_path)
atlas_data = atlas_img.get_fdata()
affine     = atlas_img.affine

# Link atlas labels to target ROIs
label_dict = {"IC-R":  5,
              "IC-L":  6,
              "MGB-R": 7,
              "MGB-L": 8}

# Extract masks for target ROIs
for name, label in label_dict.items():
    mask = (atlas_data == label).astype(np.uint8)
    out_file = f"{name}.nii.gz"
    nib.save(nib.Nifti1Image(mask, affine), f"{out_fold}/{out_file}")
    print(f"Saved {out_file}")