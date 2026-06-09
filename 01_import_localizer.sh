#!/usr/bin/env bash
# Time-stamp: <10-02-2026 m.utrosa@bcbl.eu>

set -eo pipefail
# -e => exits if any of the processes called generate a non-zero return code at the end.
# -o pipefail => deals with failures in the middle of a pipeline.

# Run the code in an environment specific to the project
source activate localizer_fMRI

# Subject-specific parameters
subID=4
sesID=1
anatID=1

# Optional steps: 0 skips, 1 executes the step
nordic=0    # Applies NORDIC denoising of functional BOLD images
qform=0     # Copies sform into qform to correct for differences in oblique dataset
optcomb=0   # Optimally combines multi-ehco dataset
onsetcorr=0 # Corrects onset in logs (necessary for pilot01 & pilot02)

# Session-specific parameters
# CRITICAL: labels must in order of data collection (necessary for logfiles!)

### PILOT 04
acqIDs=("NOACC15" "NOACC16")

### PILOT O3
# acqIDs=("PF78" "NOACC" "GRAPPA")

### PILOT 02
# if [[ "$sesID" -eq 1 ]]; then
# 	acqIDs=("DresdenNoFat" "DresdenWFat" "ME1TR880" "ME3TR1600" "ME3TR1100" "ME3TR850" "ME3TR700")
# 	me_acqID=("ME3TR1600" "ME3TR1100" "ME3TR850" "ME3TR700")
# elif [[ "$sesID" -eq 3 ]]; then
# 	acqIDs=("DresdenNoFat175" "DresdenWFat175" "ME1TR780" "ME3TR1180" "ME3TR770" "ME3TR680") # sub-01; ses-03
# 	me_acqID=("ME3TR1180" "ME3TR770" "ME3TR680") 
# elif [[ "$sesID" -eq 2 ]]; then
# 	acqIDs=("DresdenWFat175" "ME1TR780" "ME3TR1180" "ME3TR770" "ME3TR680") # sub-02; ses-02
# 	me_acqID=("ME3TR1180" "ME3TR770" "ME3TR680") 
# fi

# Project-specific parameters
n_noise_scans=1
task="localizer"
project="SubCort_HighRes"
homePath="/home/mutrosa/Documents/projects/select_fMRI"
bidsPath="$homePath/data_MRI/sourcedata/raw/sub-0$subID/ses-0$sesID"

###############################################################################
###############################################################################

# STEP 0
# Generate sidecar files to set up the configuration file.
# Run script pre_import.py in the terminal.

# STEP 1
# a.) BIDSifies sourcedata (dicoms).
# b.) Removes background noise from MP2RAGE UNI images (T1w).
# c.) Applies denoising to the functional scans using NORDIC method.
# d.) Optionally: optimally combines echos from multi-echo acquistions.
# e.) Optionally: corrects qform, if data is oblique.
# f.) Removes the noise scan from functional scans.

echo "**************** STEP 1: Starting curation of MRI data *****************"

if [[ "$nordic" -eq 1 ]]; then
	python -m scripts.import.import_MRI \
			"$subID" "$sesID" "$anatID" "$project" \
			"$homePath" "${acqIDs[@]}" \
			--nordic --tidy
elif [[ "$nordic" -eq 0 ]]; then
	python -m scripts.import.import_MRI \
			"$subID" "$sesID" "$anatID" "$project" \
			"$homePath" "${acqIDs[@]}"
fi

if [[ "$qform" -eq 1 ]]; then
	echo "Fixing qform by copying sform from: $bidsPath"
	find "$bidsPath" -name "*bold.nii.gz" -exec fslorient -copysform2qform {} \;
	find "$bidsPath" -name "*bold.nii.gz" -exec sh -c 'fslhd "$1" | grep form_code' _ {} \;
fi

if [[ "$optcomb" -eq 1 ]]; then
	python -m scripts.import.optimal_combo \
			"$subID" "$sesID" "$task" "$homePath" "${me_acqID[@]}"
	python -m scripts.import.rename_t2smap \
			"$homePath"
fi

python -m scripts.import.remove_noise_scan "$homePath" "$subID" "$sesID" "$n_noise_scans" --overwrite

echo "*************************** Completed STEP 1 ***************************"

# STEP 2: EVENTS
# a.) Renames logfiles according to BIDS with info about the acquisition ID.
#	  CRITICAL: acquisition labels MUST BE in the order of data collection !
# b.) Copies behavioral logfiles to the "raw" BIDS-compliant folder in BIDS format.

echo "*********************** STEP 2: Moving LOGFILES ************************"

python -m scripts.import.import_LOG \
		"$homePath" "$subID" "$sesID" "${acqIDs[@]}"

if [[ "$onsetcorr" -eq 1 ]]; then
	python -m scripts.import.onset_correction \
			"$homePath" "$subID" "$sesID" "${acqIDs[@]}"
fi
echo "*************************** Completed STEP 2 ***************************"

# STEP 3: BIOPAC
# a.) Converts sourcedata (.acq) into TAPAS-compatible data (.mat or .txt).
# b.) Preprocesses the compatible data.
# c.) Calculates regressors.

echo "******************** STEP 3: Starting PHYSIO import ********************"

python -m scripts.import.import_PHYSIO "$subID" "$sesID" "$project" "$task" "$homePath"

echo "*************************** Completed STEP 3 ***************************"

conda deactivate
spd-say done