#! /usr/bin/env bash
# Time-stamp: <2025-08-07 m.utrosa@bcbl.eu>
set -eo pipefail

# Run the code in an environment specific to the project.
source activate localizer_fMRI

# Subject-specific parameters
subID=4
sesID=1
task="localizer"
homePath='/home/mutrosa/Documents/projects/localizer_fMRI'

# STEP 1: Filter Artifacts
## a.) Extracts motion confounds from fMRIprep derivatives.
## b.) Adds physiological regressors (TAPAS) to the confound dataframe.
## b.) Extracts motion outliers from fMRIprep derivatives.
echo "STEP 1: Filtering artifacts ..."
python -m scripts.analysis.artifacts "$subID" "$sesID" "$homePath"
echo "Completed STEP 1 ;)"

# # STEP 2: Design
# echo "STEP 2: Parsing logfiles to get NiPype Design Bunch ..."
# python scripts/analysis/designer.py "$subID" "$sesID" "$homePath"
# echo "Completed STEP 3 ;)"

conda deactivate