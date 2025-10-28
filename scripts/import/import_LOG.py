#! /usr/bin/env python
# Time-stamp: <2025-05-09 m.utrosa@bcbl.eu>
#
# Manually copy logfiles (for each subject and session) from the MRI computer.
# Open FileZilla on the MRI computer.
# 	This is the old yellow screen - Windows 10 (option 2).
# Upload all logfiles from /localizer/subXX/bids_output
# 					  to   /home/mutrosa/Documents/projects/localizer_fMRI/logfiles
#
# IMPORTANT: rename logfiles according to BIDS-standard. Check the order of functional
# scans (dicom numbers) and then replace the "run-{O2d}" with "acq-{sequenceName}".

# Import python packages
import bids, sys, shutil

# Import custom-made functions
from scripts import grabber

# Copy logfile data to preprocessing folder
def import_LOG(subID, sesID, project, homePath):

	# 1. LOGFILE data import
	rawFold   = f'{homePath}/data_logs/bids/' # BIDS-compliant logfiles folder
	outPath   = f'{homePath}/data_MRI/sourcedata/raw/sub-{subID:02d}/ses-{sesID:02d}/func/'
	logLayout = bids.layout.BIDSLayout(rawFold, validate=False)
	grabconf  = grabber.define_grabconf(subID, sesID, "events", "tsv", task = "localizer")
	logfiles  = grabber.grab_BIDS_object(rawFold, logLayout, grabconf)

	if not logfiles:
		print(f"No logfiles found for sub-{subID:02d} ses-{sesID:02d} in {rawFold} ! :()")
	else:
		for lf in logfiles: 
			print(f"\nCopying {lf.path} to {outPath}")
			shutil.copy(lf.path, outPath)

if __name__ == "__main__":
    subID, sesID, project, homePath = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
    import_LOG(subID, sesID, project, homePath)