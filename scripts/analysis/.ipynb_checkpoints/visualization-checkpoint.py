#! /usr/bin/env python
# Time-stamp: <2025-12-09 m.utrosa@bcbl.eu>

# Visualization
import nibabel as nib
from nibabel.orientations import aff2axcodes, io_orientation
from nilearn.plotting import plot_stat_map

# Parameters
acqID = "DresdenNoFat"
subID = 3
sesID = 1

# Location of files
homePath  = "/home/mutrosa/Documents/projects/localizer_fMRI"

spmT_path_before = homePath + f"/results/1stLevel/sub-{subID:02d}/ses-{sesID:02d}/acq-{acqID}/spmT_0001.nii"
spmT_path_after  = homePath + f"/results/1stLevel/sub-{subID:02d}/ses-{sesID:02d}/acq-{acqID}/spmT_0001_trans_out.nii.gz"
MNI_path         = homePath + "/templates/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz"
T1w_path         = homePath + f"/data_MRI/derivatives/sub-{subID:02d}/ses-01/anat/sub-{subID:02d}_ses-01_space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz"
con_path         = homePath + f"/results/1stLevel/sub-{subID:02d}/ses-{sesID:02d}/acq-{acqID}/con_0001.nii"
atlas_path       = homePath + f"/templates/atlas/sub-invivo_MNI_rois.nii.gz"

# Load data with nibabel
spmT_image_before = nib.load(spmT_path_before)
spmT_image_after  = nib.load(spmT_path_after)
MNI_image         = nib.load(MNI_path)
T1w_image         = nib.load(T1w_path)
con_image         = nib.load(con_path)
atlas_image       = nib.load(atlas_path)

# Image orientation (RAS)
print("io_orientation spmT Before:", io_orientation(spmT_image_before.affine))
print("io_orientation spmT After:",  io_orientation(spmT_image_after.affine))
print("io_orientation MNI:",         io_orientation(MNI_image.affine))
print("io_orientation T1w:",         io_orientation(T1w_image.affine))
print("io_orientation con:",         io_orientation(con_image.affine))
print("io_orientation atlas:",       io_orientation(atlas_image.affine))

# Check affine shape and codes
print("axcodes spmT Before:", aff2axcodes(spmT_image_before.affine))
print("axcodes spmT After:",  aff2axcodes(spmT_image_after.affine))
print("axcodes MNI:",         aff2axcodes(MNI_image.affine))
print("axcodes T1w:",         aff2axcodes(T1w_image.affine))
print("axcodes con:",         aff2axcodes(con_image.affine))
print("axcodes atlas:",       aff2axcodes(atlas_image.affine))

print("affine shape spmT Before:", spmT_image_before.affine.shape)
print("affine shape spmT After:",  spmT_image_after.affine.shape)
print("affine shape MNI:",         MNI_image.affine.shape)
print("affine shape T1w:",         T1w_image.affine.shape)
print("affine shape con:",         con_image.affine.shape)
print("affine shape atlas:",       atlas_image.affine.shape)

# qform differences in header
print("qform spmT Before:", spmT_image_before.header.get_qform()[0])
print("qform spmT After:",  spmT_image_after.header.get_qform()[0])
print("qform MNI:",         MNI_image.header.get_qform()[0])
print("qform T1w:",         T1w_image.header.get_qform()[0])
print("qform con:",         con_image.header.get_qform()[0])
print("qform atlas:",       atlas_image.header.get_qform()[0])

# sform differences in header
print("sform spmT Before:", spmT_image_before.header.get_sform()[0])
print("sform spmT After:",  spmT_image_after.header.get_sform()[0])
print("sform MNI:",         MNI_image.header.get_sform()[0])
print("sform T1w:",         T1w_image.header.get_sform()[0])
print("sform con:",         con_image.header.get_sform()[0])
print("sform atlas:",       atlas_image.header.get_sform()[0])

# Plot statistical maps (T-map) before warping
plot_before = plot_stat_map(
    spmT_path_before, bg_img = MNI_path,
    title = f'spmT sub-{subID:02d} ses-{sesID:02d} acq-{acqID} before warping',
    threshold=2, display_mode='ortho')
plot_before.savefig(f"stat_map_sub-{subID:02d}_{acqID}_before_warper.png")


# Plot statistical maps (T-map) after warping
plot_after = plot_stat_map(
    spmT_path_after, bg_img = MNI_path,
    title = f'spmT sub-{subID:02d} ses-{sesID:02d} acq-{acqID} after warping',
    threshold=2, display_mode='ortho')
plot_after.savefig(f"stat_map_sub-{subID:02d}_ses-{sesID:02d}_acq-{acqID}_after_warper.png")


# Resample to match Sitek's atlas
from nilearn.image import resample_to_img
resampled_spmT = resample_to_img(spmT_image_after, atlas_image, interpolation='nearest',  copy_header=True, force_resample=True)
resampled_spmT.to_filename("resampled_spmT.nii.gz")

resampled_MNI = resample_to_img(MNI_image, atlas_image, interpolation='nearest', copy_header=True, force_resample=True)
resampled_MNI.to_filename("resampled_MNI.nii.gz")

# check affines / sform / qform
img_spmT = nib.load("resampled_spmT.nii.gz")
img_MNI  = nib.load("resampled_MNI.nii.gz")
print('spmT qform:\n', img_spmT.header.get_qform()[0])
print('MNI  qform:\n', img_MNI.header.get_qform()[0])

from nilearn.plotting import plot_stat_map, plot_roi
plot = plot_stat_map("resampled_spmT.nii.gz", bg_img = "resampled_MNI.nii.gz", title='spmT')
plot.savefig(f"stat_map_sub-{subID:02d}_ses-{sesID:02d}_acq-{acqID}_after_resampling.png")


# Extract ROIs
# Violin Plots