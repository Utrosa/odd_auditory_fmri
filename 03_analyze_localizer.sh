#! /usr/bin/env bash
# Time-stamp: <2025-02-17 m.utrosa@bcbl.eu>

set -eo pipefail
# -e => exits if any of the processes called generate a non-zero return code at the end.
# -o pipefail => deals with failures in the middle of a pipeline.

# Run the code in an environment specific to the project.
source activate nipype

# Subject-specific parameters
#TO-D0: parallelization over subjects & sessions! 
subID=4
sesID=1  # roi_extraction & filter_artifacts can't be done over subjects / sessions
# subIDs=2 # the analysis can be done over multiple subjects and sessions
# sesIDs=1

# Project-specific paths: project root, MNI template, and atlas for ROIs
homePath='/home/mutrosa/Documents/projects/select_fMRI'
MNIpath="$homePath/templates/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz"
atlasPath="$homePath/templates/atlas/invivo_resampled_to-MNI_res-01.nii.gz"

# Aquisition labels for pilot study O4
acqIDs=("NOACC15" "NOACC16")

# Aquisition labels for pilot study O3
# acqIDs=("PF78" "NOACC" "GRAPPA")

# Single-echo acquisition labels
# if [[ "$sesID" -eq 1 ]]; then
# 	acqIDs=("DresdenNoFat" "DresdenWFat" "ME1TR880")
# elif [[ "$sesID" -eq 2 ]]; then
# 	acqIDs=("DresdenWFat175" "ME1TR780") # sub-02; ses-02
# elif [[ "$sesID" -eq 3 ]]; then
# 	acqIDs=("DresdenNoFat175" "DresdenWFat175" "ME1TR780") # sub-01; ses-03
# fi

# Full dataset acquisition labels.
# if [[ "$sesID" -eq 1 ]]; then
# 	acqIDs=("DresdenNoFat" "DresdenWFat" "ME1TR880" "ME3TR1600" "ME3TR1100" "ME3TR850" "ME3TR700") # ses-01
# elif [[ "$sesID" -eq 3 ]]; then
# 	acqIDs=("DresdenNoFat175" "DresdenWFat175" "ME1TR780" "ME3TR1180" "ME3TR770" "ME3TR680") # sub-01; ses-03
# elif [[ "$sesID" -eq 2 ]]; then
# 	acqIDs=("DresdenWFat175" "ME1TR780" "ME3TR1180" "ME3TR770" "ME3TR680") # sub-02; ses-02
# fi

# Analysis-specific parameters
biopac=1    # 0: exclude BIOPAC physiological regressors; 1: include them
# smoothing=2 # If larger than zero, applies smoothing kernel of that size in mm.
# volterra=0  # 0: no volterra; 1: applies volterra

# Confound keys
# confound_keys=( \
# 			"csf" \
# 			"csf_derivative1" \
# 			"csf_derivative1_power2" \
# 			"csf_power2" \
# 			"white_matter" \
# 			"white_matter_derivative1" \
# 			"white_matter_derivative1_power2" \
# 			"white_matter_power2" \
# 			"csf_wm"
# 		)
confound_keys=( \
	'trans_x' \
	'trans_y' \
	'trans_z' \
	'rot_x' \
	'rot_y' \
	'rot_z'
	)
# confound_keys=None # Takes the default counfounds: trans, rot, csf, wm

#############################################################################################
#############################################################################################

# STEP 1: Filter Artifacts
## a.) Extracts specified confounds and motion artifacts from fMRIprep derivatives.
## b.) Optionally adds physiological regressors (TAPAS) to the confounds dataframe.

echo "**************** STEP 1: Filtering confounds & artifacts ***************"

if [[ "$biopac" -eq 1 ]]; then
	python -m scripts.analysis.filter_artifacts \
			"$homePath" "$subID" "$sesID" \
			--acqIDs "${acqIDs[@]}" \
			--confound_keys "${confound_keys[@]}" \
			--include_biopac

elif [[ "$biopac" -eq 0 ]]; then
	python -m scripts.analysis.filter_artifacts \
		"$homePath" "$subID" "$sesID" \
		--acqIDs "${acqIDs[@]}" \
		--confound_keys "${confound_keys[@]}"
fi
echo "*************************** Completed STEP 1 ***************************"

# STEP 2: Nipype 1st level GLM analysis
# a.) Specifies nodes, connects them, and visualizes the workflow.
# b.) Generates the SPM-specific model, the design matrix, and estimates contrasts.
# d.) Warps results from T1w space to MNI.

# echo "***************** STEP 2: SPM 1st level GLM analysis *******************"

# python -m scripts.analysis.first_level_analysis \
# 	"$homePath" \
# 	"$MNIpath" \
# 	--subIDs "$subIDs" \
# 	--sesIDs "$sesIDs" \
# 	--acqIDs "${acqIDs[@]}" \
# 	--smoothing "$smoothing"

# echo "*************************** Completed STEP 2 ***************************"

# # STEP 3: Extraction of target ROIs s& visualization

# echo "***************** STEP 3: Extracting ROIs and plotting *****************"

# ts=$(python -m scripts.analysis.roi_extraction \
# 	"$subID" \
# 	"$sesID" \
# 	"$ts" \
# 	"$homePath" \
# 	"$atlasPath" \
# 	"${acqIDs[@]}")

# echo "*************************** Completed STEP 3 ***************************"

conda deactivate
spd-say done