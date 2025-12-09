#! /usr/bin/env python
# Time-stamp: <2025-11-03 m.utrosa@bcbl.eu>
#
# Prerequisties python: install dcm2bids & dcm2niix in your virtual environment (python 3.8+).
#
# Manually copy DICOM files from the data folder on BCBL servers.
# Open the Citrix Workspace app and log-in with your username and password.
# 	If the app doesn't function, connect via the browser to https://gateway.bcbl.eu/.
# Open your network folder (app).
# For pilot data navigate to the G:\Exchange folder.
# For non-pilot data navigate to your G:\<project_name> folder.
# Copy all data and navigate to your F:\<username> folder.
# Paste all data to your personal folder.
# 	This step is necessary for pilot data, as that data is NOT permanently stored.
# Move the files to /home/<username>/projects/<project_name>/data_MRI/sourcedata/dicoms/
# If necessary, unzip by running unzip <foldername> in your terminal.
#
# IMPORTANT: Check that the data is complete. The automatic uploading fails at times !
# If data is not complete, send subID + sesID + date of scanning to David to reupload
# missing files from PACS.

# Import python packages
import bids, bioread, os, sys, time

# Import custom-made functions
from scripts import grabber

def import_MRI(subID, sesID, project, homePath, acq_list):

	# 1. BIDS data import
	dicomFold = f'{homePath}/data_MRI/sourcedata/dicoms/sub-{subID:02d}_ses-{sesID:02d}_{project}/'
	dataPath  = f'{homePath}/data_MRI/sourcedata/raw' # Path to BIDS-converted raw data
	if not os.path.exists(dataPath):
	    os.makedirs(dataPath)

	confFile  = f'{homePath}/scripts/import/conf_{project}.json'
	options   = f'-d {dicomFold} -p {subID:02d} -s {sesID:02d}'
	bids_cmd  = f'dcm2bids {options} -c {confFile} -o {dataPath} '
	print("\nRunning:", bids_cmd)
	os.system(bids_cmd)

	# Remove unnecessary tmp folder
	os.system(f"rm -r {homePath}/data_MRI/sourcedata/raw/tmp_dcm2bids/")

	# 2. Remove background noise from MP2RAGE UNI image for the first session only.
	# Code: https://github.com/srikash/MPRAGEise?tab=readme-ov-file
	if sesID == 1:
		anatPath   = f"{dataPath}/sub-{subID:02d}/ses-{sesID:02d}/anat"
		anatLayout = bids.layout.BIDSLayout(anatPath, validate=False)

		INV2_image_conf = grabber.define_grabconf(subID, sesID, "MP2RAGE", "nii.gz", inv=2)
		UNI_image_conf  = grabber.define_grabconf(subID, sesID, "UNIT1", "nii.gz")

		INV2_image = grabber.grab_BIDS_object(anatPath, anatLayout, INV2_image_conf)[0]
		UNI_image  = grabber.grab_BIDS_object(anatPath, anatLayout, UNI_image_conf)[0]

		mp2rage_cmd = f'{homePath}/scripts/import/MPRAGEise.py -i {INV2_image.path} -u {UNI_image.path} -o {dataPath}/sub-{subID:02d}/ses-{sesID:02d}/anat'
		print("\nRunning:", mp2rage_cmd)
		os.system(mp2rage_cmd)
		
		# Create a json file for the unbiased clean T1 image.
		os.rename(f"{anatPath}/sub-{subID:02d}_ses-{sesID:02d}_UNIT1.json", f"{anatPath}/sub-{subID:02d}_ses-{sesID:02d}_T1w.json")

		# Remove redundant files
		os.remove(UNI_image.path)
		
		# Rename the denoised T1 image
		anatLayout = bids.layout.BIDSLayout(anatPath, validate=False, reset_database=True)
		T1_conf    = grabber.define_grabconf(subID, sesID, "T1w", "nii.gz")
		T1_image   = grabber.grab_BIDS_object(anatPath, anatLayout, T1_conf)[0]
		os.rename(T1_image.path, f"{anatPath}/sub-{subID:02d}_ses-{sesID:02d}_T1w.nii.gz")
	else:
		print(f"MP2RAGE was not background-corrected for session {sesID:02d}. Assuming MP2RAGE was collected in ses-01.")

	# 3. Denoise functional images with NORDIC
	# Code: https://github.com/SteenMoeller/NORDIC_Raw/tree/main)
	funcPath = f"{dataPath}/sub-{subID:02d}/ses-{sesID:02d}/func"
	nordPath = f'{homePath}/data_MRI/sourcedata/denoised/'
	funcLayout = bids.layout.BIDSLayout(funcPath, validate=False)

	for ac in acq_list:
		bold_image_conf = grabber.define_grabconf(subID, sesID, "bold", "nii.gz", acquisition=ac)
		bold_image = grabber.grab_BIDS_object(funcPath, funcLayout, bold_image_conf)
		
		for i in range(0, len(bold_image), 2):
			bold  = bold_image[i].path
			phase = bold_image[i + 1].path
			nordic_cmd = (
				 f"addpath('/home/mutrosa/Documents/projects/select_fMRI/scripts/import'); "
				 f"nordic('{bold}', '{phase}', '{nordPath}'); "
				  "exit;")
			print("\nRunning:", nordic_cmd)
			os.system(f'matlab -nodesktop -nosplash -r "{nordic_cmd}"')

if __name__ == "__main__":
    subID, sesID, project, homePath, acq_list = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5:]
    import_MRI(subID, sesID, project, homePath, acq_list)