import os
import numpy as np
import nibabel as nib
from nilearn.image import resample_to_img

subID      = 1
homePath   = "/home/mutrosa/Documents/projects/select_fMRI"
temPath    = homePath + "/templates"
out_fold   = temPath + "/rois"
os.makedirs(out_fold, exist_ok=True)

# Load atlases. Note: anatomical data should be collected in the first session!
MNI_atlas   = temPath + "/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz"
sitek_atlas = temPath + "/atlas/sub-invivo_MNI_rois.nii.gz"
T1w_scan    = homePath + f"/data_MRI/derivatives/sub-{subID:02d}/ses-01/anat/sub-{subID:02d}_ses-01_desc-preproc_T1w.nii.gz"
sitek_img = nib.load(sitek_atlas)
MNI_img   = nib.load(MNI_atlas)
T1w_img   = nib.load(T1w_scan)

# Resample
resampled_MNI = resample_to_img(sitek_img, MNI_img, interpolation='nearest', 
                                  copy_header=False, force_resample=True)

resampled_T1w = resample_to_img(sitek_img, T1w_img, interpolation='nearest', 
                                  copy_header=False, force_resample=True)

# Save the resampled atlases
out_path_MNI = f"{temPath}/atlas/invivo_resampled_to-MNI_res-01.nii.gz"
out_path_T1w = f"{temPath}/atlas/invivo_resampled_to-T1w_res-01.nii.gz"

resampled_MNI.to_filename(out_path_MNI)
resampled_T1w.to_filename(out_path_T1w)

# Load atlases
resampled_MNI_data  = resampled_MNI.get_fdata()
resampled_T1w_data  = resampled_T1w.get_fdata()

affine_MNI = resampled_MNI.affine
affine_T1w = resampled_T1w.affine

# Link atlas labels to target ROIs
label_dict = {
              "CN-L":  1,
              "CN-R":  2,
              "SOC-L": 3,
              "SOC-R": 4,
              "IC-L":  5,
              "IC-R":  6,
              "MGB-L": 7,
              "MGB-R": 8}

# Extract template masks for target ROIs
for name, label in label_dict.items():
    
    # MNI space
    mask_MNI = (resampled_MNI_data == label).astype(np.uint8)
    out_file_MNI = f"{name}_space-MNI.nii.gz"
    nib.save(nib.Nifti1Image(mask_MNI, affine_MNI), f"{out_fold}/{out_file_MNI}")
    print(f"Saved {out_file_MNI}")

    # T1w space
    mask_T1w = (resampled_T1w_data == label).astype(np.uint8)
    out_file_T1w = f"{name}_space-T1w.nii.gz"
    nib.save(nib.Nifti1Image(mask_T1w, affine_T1w), f"{out_fold}/{out_file_T1w}")
    print(f"Saved {out_file_T1w}")