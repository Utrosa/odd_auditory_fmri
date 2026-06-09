#! /usr/bin/env bash
# Time-stamp: <2025-04-07 m.utrosa@bcbl.eu>
set -eo pipefail
# -e Exits if any of the processes called generate a non-zero return code at the end.
# -o pipefail Deals with failures in the middle of a pipeline.

# Running the code in an environment specific to the project
source activate localizer_fMRI

# STEP 0
## Curate the data automatically and manually (remove bad runs).
## Bad runs are runs that were interrupted due to participant's request (bathroom break, discomfort, ...),
## or a mistake while running the sequences (sound not coming through, response pad keys not working ...).

# STEP 1
## Identify the subject
subID="01"

## Run the standard fMRIprep preprocessing pipeline.
echo "***** Starting MRI preprocessing for $subID *****"
date
bash data_MRI/code/preproc_singleSUB_docker.sh "$subID" 
echo "***** Completed preprocessing for $subID ;) *****"
date

conda deactivate
spd-say done