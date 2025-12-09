#! /usr/bin/env bash
# Time-stamp: <2025-12-09 m.utrosa@bcbl.eu>

set -eo pipefail
# -e => exits if any of the processes called generate a non-zero return code at the end.
# -o pipefail => deals with failures in the middle of a pipeline.

# Run the code in an environment specific to the project.
source activate localizer_fMRI

# Subject-specific parameters
subID=1
sesID=1

# Project-specific parameters
project="SubCort_HighRes"
task="localizer"
homePath="/home/mutrosa/Documents/projects/select_fMRI"

# Session-specific parameters
if (( sesID == 1 )); then
	acq_list=("DresdenNoFat" "DresdenWFat" "ME1TR880" "ME3TR1600" "ME3TR1100" "ME3TR850" "ME3TR700")
else
	acq_list=("DresdenNoFat175" "DresdenWFat175" "ME1TR780" "ME3TR1180" "ME3TR770" "ME3TR680")
fi

# STEP 0
## Generate sidecar files to set up the configuration files.
## Run script pre_import.py in the terminal.

# a.) BIDSifies sourcedata (dicoms).
# b.) Removes background noise from MP2RAGE UNI images (T1w).
# c.) Removes noise from functional scans using NORDIC.
echo "STEP 1: Starting curation of MRI data ..."
python -m scripts.import.import_MRI "$subID" "$sesID" "$project" "$homePath" "${acq_list[@]}"
python -m scripts.import.optimal_combo "$subID" "$sesID" "$task" "$homePath"
echo "Completed STEP 1 ;)"

# STEP 2: EVENTS
# a.) Copies behavioral logfiles to corresponding sub & ses folder in BIDS format.
echo "STEP 2: Moving LOGFILES..."
python -m scripts.import.import_LOG "$subID" "$sesID" "$project" "$homePath"
echo "Completed STEP 2 ;)"

# STEP 3: BIOPAC
## a.) Converts sourcedata (.acq) into TAPAS-compatible data (.mat or .txt).
## b.) Preprocesses the compatible data.
## c.) Calculates regressors.
echo "STEP 3: Starting PHYSIO import..."
python -m scripts.import.import_PHYSIO "$subID" "$sesID" "$project" "$task" "$homePath"
echo "Completed STEP 3 ;)"

conda deactivate
spd-say done