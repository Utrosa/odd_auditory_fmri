#! /usr/bin/env bash
# Time-stamp: <2025-04-07 m.utrosa@bcbl.eu>
set -eo pipefail
# -e Exits if any of the processes called generate a non-zero return code at the end.
# -o pipefail Deals with failures in the middle of a pipeline.

# Running the code in an environment specific to the project
source activate localizer_fMRI

# Activate the correct conda environment: conda activate dcm2bids
subID="03"

# STEP 0
## Curate the data automatically and manually (remove bad runs).
## Bad runs are runs that were interrupted due to participant's request (bathroom break, discomfort, ...),
## or a mistake while running the sequences (sound not coming through, response pad keys not working ...).

# STEP 1
## Run the standard fMRIprep preprocessing pipeline.
echo "Starting MRI preprocessing ..."
bash data_MRI/code/preproc_singleSUB.sh "$subID" 
echo "Completed STEP 1 ;)"

conda deactivate