#!/bin/bash
# Time-stamp: <2025-11-27>

# ------------------------ SGE options ------------------------------
#$ -q long.q
#$ -cwd
#$ -N selectMRI
#$ -m ea
#$ -M USER
#$ -o logs/selectMRI_output.txt
#$ -e logs/selectMRI_error.txt
#$ -S /bin/bash


#$ -l gpu=1
#$ -l h_vmem=16G
#$ -l h_rt=48:00:00


# ------------------------ JOB execution ----------------------------
# Set monitoring for errors
set -euo pipefail

echo "***** Job started *****"
date

# Load modules and list them for reproducibility
module load singularity/3.7.0
module list

# Identify the subject
subID="01"

# Run the fMRIprep preprocessing pipeline
echo "***** Starting MRI preprocessing for subject $subID *****"
bash data_MRI/code/preproc_singleSUB_singularity.sh "$subID" 
echo "**** Job ended ****"
date