#! /usr/bin/env bash
# Time-stamp: <2025-08-07 m.utrosa@bcbl.eu>

set -eo pipefail
# -e => exits if any of the processes called generate a non-zero return code at the end.
# -o pipefail => deals with failures in the middle of a pipeline.

# Run the code in an environment specific to the project.
source activate localizer_fMRI

# Subject-specific parameters
subID=3
sesID=2
project="SUBCORT_HIGHRES"
task="localizer"
homePath='/home/mutrosa/Documents/projects/localizer_fMRI'

# STEP 0
## Generate sidecar files to set up the configuration files.
## Run script pre_import.py in the terminal.

# STEP 1: MRI
## a.) BIDSifies sourcedata (dicoms).
## b.) Removes background noise from MP2RAGE UNI images (T1w).
echo "STEP 1: Starting curation of MRI data ..."
python -m scripts.import.import_MRI "$subID" "$sesID" "$project" "$homePath"
echo "Completed STEP 1 ;)"

# STEP 2: EVENTS
## a.) Copies behavioral logfiles to corresponding sub & ses folder in BIDS format.
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