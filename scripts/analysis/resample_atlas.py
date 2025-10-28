#! /usr/bin/env python
# Time-stamp: <2025-18-09 m.utrosa@bcbl.eu>
# -----------------------------------------------------------------------------
# Resample Sitek's in-vivo atlas to resolution of the MNI reference used in
# preprocessing and data analyses.
#
# DOI: 10.7554/eLife.48932
# -----------------------------------------------------------------------------
import nibabel as nib
from nilearn.image import resample_to_img
from nibabel.orientations import aff2axcodes, io_orientation

# Download Sitek et al. (2019) atlas of subcortical brain regions from:
# https://osf.io/c4m82/files/osfstorage -> derivatives/MNI_space/atlases
homePath   = "/home/mutrosa/Documents/projects/localizer_fMRI"
atlas_path = homePath + f"/templates/atlas/sub-invivo_MNI_rois.nii.gz"
MNI_path   = homePath + "/templates/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz"

# Specify where to save the resampled atlas
out_dir = homePath + "/templates/atlas/"
out_path = f"{out_dir}invivo_resampled_to-MNI_res-01.nii.gz"

# Load images
atlas_img = nib.load(atlas_path)
MNI_img   = nib.load(MNI_path)

# Resample
resampled_atlas = resample_to_img(atlas_img, MNI_img, interpolation='continuous', 
								  copy_header=True, force_resample=True)
resampled_atlas.to_filename(out_path)

# Check that the transformation has been correctly executed
resampled_atlas_img = nib.load(out_path)

original_shape      = atlas_img.shape
original_affine     = atlas_img.affine

resampled_shape  = resampled_atlas_img.shape
resampled_affine = resampled_atlas_img.affine

MNI_shape  = MNI_img.shape
MNI_affine = MNI_img.affine

print(
    f"""Shape comparison:
- Original atlas image shape  : {original_shape}
- Resampled atlas image shape : {resampled_shape}
- MNI template image shape    : {MNI_shape}
"""
)

print(
    f"""Affine comparison:
- Original atlas image affine  : \n{original_affine}
- Resampled atlas image affine : \n{resampled_affine}
- MNI template image affine    : \n{MNI_affine}
"""
)

print(
    f"""Axis direction codes comparison:
- Original atlas image axcodes  : {aff2axcodes(original_affine)}
- Resampled atlas image axcodes : {aff2axcodes(resampled_affine)}
- MNI template image axcodes    : {aff2axcodes(MNI_affine)}
"""
)

print(
    f"""Input orientation comparison:
- Original atlas image orientation  : \n{io_orientation(original_affine)}
- Resampled atlas image orientation : \n{io_orientation(resampled_affine)}
- MNI template image orientation    : \n{io_orientation(MNI_affine)}
"""
)

print(
    f"""qform comparison:
- Original atlas image qform  : {atlas_img.header.get_qform()[0]}
- Resampled atlas image qform : {resampled_atlas_img.header.get_qform()[0]}
- MNI template image qform    : {MNI_img.header.get_qform()[0]}
"""
)

print(
    f"""sform comparison:
- Original atlas image sform  : {atlas_img.header.get_sform()[0]}
- Resampled atlas image sform : {resampled_atlas_img.header.get_sform()[0]}
- MNI template image sform    : {MNI_img.header.get_sform()[0]}
"""
)