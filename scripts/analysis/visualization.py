#! /usr/bin/env python
# Time-stamp: <2025-12-13 m.utrosa@bcbl.eu>
# Generic script to check data's orientation and shape.
# Visualizes results before and after warping stage in the analysis in progress.
# Before running, run the roi_extraction.py which generates rois and resamples
# Sitek's atlas.

# Prerequisites ---------------------------------------------------------------
import nibabel as nib
from nibabel.orientations import aff2axcodes, io_orientation
from nilearn.plotting import plot_stat_map
from nilearn.image import resample_to_img
from nilearn.plotting import plot_stat_map, plot_roi

# Parameters
# ["DresdenNoFat", "DresdenWFat", "ME1TR880", "ME3TR1600", "ME3TR1100", "ME3TR850", "ME3TR700"] # ses-01
# ["DresdenNoFat175", "DresdenWFat175", "ME1TR780", "ME3TR1180", "ME3TR770", "ME3TR680"] # ses-02
acqID = "DresdenNoFat175"
subID = 1
sesID = 3
roi = "IC-R" # CN-L', 'CN-R', 'SOC-L', 'SOC-R', 'IC-L', 'IC-R', 'MGB-L', 'MGB-R'

# Directories
homePath         = "/home/mutrosa/Documents/projects/select_fMRI"
resPath          = homePath + f"/results/1stLevel/sub-{subID:02d}/ses-{sesID:02d}/acq-{acqID}"
derPath          = homePath + "/data_MRI/derivatives"
temPath          = homePath + "/templates"

MNI_path         = temPath + "/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz"
sitek_atlas      = temPath + "/atlas/sub-invivo_MNI_rois.nii.gz"
resampled_atlas  = temPath + "/atlas/invivo_resampled_to-MNI_res-01.nii.gz"
ROI_path         = temPath + f"/rois/{roi}.nii.gz"
spmT_path_before = resPath + "/spmT_space-T1w_0001.nii"
spmT_path_after  = resPath + "/spmT_space-MNI_0001_trans_out.nii.gz"
con_path         = resPath + "/con_0001.nii"
T1w_path         = derPath + f"/sub-{subID:02d}/ses-01/anat/sub-{subID:02d}_ses-01_space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz"
# If T1 is not collected in session no. 1, this will crash ... the same assumption in import/import_MRI.py script!

# Load data with nibabel ------------------------------------------------------
spmT_image_before = nib.load(spmT_path_before)
spmT_image_after  = nib.load(spmT_path_after)
MNI_image         = nib.load(MNI_path)
T1w_image         = nib.load(T1w_path)
con_image         = nib.load(con_path)
sitek_image       = nib.load(sitek_atlas)
resampled_image   = nib.load(resampled_atlas)
ROI_image         = nib.load(ROI_path)

# -----------------------------------------------------------------------------
# CHECK DATA
# -----------------------------------------------------------------------------
# Image orientation (RAS)
print("\nio_orientation spmT Before:",    io_orientation(spmT_image_before.affine))
print("io_orientation spmT After:",       io_orientation(spmT_image_after.affine))
print("io_orientation MNI:",              io_orientation(MNI_image.affine))
print("io_orientation T1w:",              io_orientation(T1w_image.affine))
print("io_orientation con:",              io_orientation(con_image.affine))
print("io_orientation Sitek atlas:",      io_orientation(sitek_image.affine))
print("io_orientation Resampled atlas:",  io_orientation(resampled_image.affine))
print("io_orientation ROI:",              io_orientation(ROI_image.affine))

# Affine codes
print("\naxcodes spmT Before:",   aff2axcodes(spmT_image_before.affine))
print("axcodes spmT After:",      aff2axcodes(spmT_image_after.affine))
print("axcodes MNI:",             aff2axcodes(MNI_image.affine))
print("axcodes T1w:",             aff2axcodes(T1w_image.affine))
print("axcodes con:",             aff2axcodes(con_image.affine))
print("axcodes Sitek:",           aff2axcodes(sitek_image.affine))
print("axcodes Resampled:",       aff2axcodes(resampled_image.affine))
print("axcodes ROI:",             aff2axcodes(ROI_image.affine))

# Affine shape
print("\naffine shape spmT Before:",   spmT_image_before.affine.shape)
print("affine shape spmT After:",      spmT_image_after.affine.shape)
print("affine shape MNI:",             MNI_image.affine.shape)
print("affine shape T1w:",             T1w_image.affine.shape)
print("affine shape con:",             con_image.affine.shape)
print("affine shape Sitek:",           sitek_image.affine.shape)
print("affine shape Resampled:",       resampled_image.affine.shape)
print("affine shape ROI:",             ROI_image.affine.shape)

# qform differences in header
print("\nqform spmT Before:", spmT_image_before.header.get_qform()[0])
print("qform spmT After:",    spmT_image_after.header.get_qform()[0])
print("qform MNI:",           MNI_image.header.get_qform()[0])
print("qform T1w:",           T1w_image.header.get_qform()[0])
print("qform con:",           con_image.header.get_qform()[0])
print("qform Sitek:",         sitek_image.header.get_qform()[0])
print("qform Resampled:",     resampled_image.header.get_qform()[0])
print("qform ROI:",           ROI_image.header.get_qform()[0])

# sform differences in header
print("\nsform spmT Before:", spmT_image_before.header.get_sform()[0])
print("sform spmT After:",    spmT_image_after.header.get_sform()[0])
print("sform MNI:",           MNI_image.header.get_sform()[0])
print("sform T1w:",           T1w_image.header.get_sform()[0])
print("sform con:",           con_image.header.get_sform()[0])
print("sform Sitek:",         sitek_image.header.get_sform()[0])
print("sform Resampled:",     resampled_image.header.get_sform()[0])
print("sform ROI:",           ROI_image.header.get_sform()[0])

# Shape differences in header
print("\nshape spmT Before:", spmT_image_before.shape)
print("shape spmT After:",    spmT_image_after.shape)
print("shape MNI:",           MNI_image.shape)
print("shape T1w:",           T1w_image.shape)
print("shape con:",           con_image.shape)
print("shape Sitek:",         sitek_image.shape)
print("shape Resampled:",     resampled_image.shape)
print("shape ROI:",           ROI_image.shape)