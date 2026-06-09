#! /usr/bin/env bash
# Time-stamp: <2025-23-02 m.utrosa@bcbl.eu>

subID=2
sesID=1

root="/home/mutrosa/Documents/projects/select_fMRI/data_MRI/"
data="sourcedata/raw/raw_withoutNORDIC/sub-0$subID/ses-0$sesID/"

# Anatomical
# img="anat/sub-0"$subID"_ses-0"$sesID"_T1w.nii.gz"
img="anat/sub-0"$subID"_ses-0"$sesID"_UNIT1.nii.gz"

# Input
in="$root/$data/$img"

# Output
name="sub-0"$subID"_ses-0"$sesID"_UNIT1"
out=$"/home/mutrosa/Documents/projects/select_fMRI/presentations/$name"

# RUN
python deface_image.py "$in" "$out"