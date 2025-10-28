#! /usr/bin/env python
# Time-stamp: <2025-05-09 m.utrosa@bcbl.eu>
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
import bioread, os, sys, bids

# Import custom-made functions
from scripts import grabber

def import_MRI(subID, sesID, project, homePath):

	# 1. BIDS data import
	dicomFold = f'{homePath}/data_MRI/sourcedata/dicoms/{sesID:02d}_{project}_{subID:02d}/'
	dataPath  = f'{homePath}/data_MRI/sourcedata/raw' # Path to BIDS-converted raw data
	if not os.path.exists(dataPath):
	    os.makedirs(dataPath)

	confFile  = f'{homePath}/scripts/import/conf_{project}.json'
	options   = f'-d {dicomFold} -p {subID:02d} -s {sesID:02d}'
	bids_cmd  = f'dcm2bids {options} -c {confFile} -o {dataPath} '
	print("\nRunning:", bids_cmd)
	os.system(bids_cmd)
	os.system(f"rm -r {homePath}/data_MRI/sourcedata/raw/tmp_dcm2bids/") # Remove unnecessary tmp folder

	# 2. Remove background noise from MP2RAGE UNI image for the first session only.
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
		os.system(f"cp {anatPath}/sub-{subID:02d}_ses-{sesID:02d}_UNIT1.json {anatPath}/sub-{subID:02d}_ses-{sesID:02d}_T1w.json")

	else:
		print(f"MP2RAGE was not background-corrected for session {sesID:02d}. Assuming MP2RAGE was collected in ses-01.")

	# 3. Remove background noise from functional images.

if __name__ == "__main__":
    subID, sesID, project, homePath = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
    import_MRI(subID, sesID, project, homePath)