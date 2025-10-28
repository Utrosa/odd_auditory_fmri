#! /usr/bin/env python
# Time-stamp: <2025-08-07 m.utrosa@bcbl.eu>
#
# Prerequisites for python packages:  phys2bids;
# 									  bioread
# Prerequisites for matlab toolboxes: Signal Processing;
#									  Statistics and Machine Learning
#
# Manually copy physio data (BIOPAC) from the Physio computer in the MRI room.
# 	The Physio computer is located on the left, up in the corner.
# Open FileZilla on the Physio computer.
# For each subject and session, upload all .acq files
#	from /.../<project_name>/
#	to   /home/<username>/projects/<project_name>/data_phyiso/sourcedata/.

# Import python packages
import bids, os, sys

# Import custom-made functions
from scripts import grabber

def import_PHYSIO(subID, sesID, project, task, homePath):

	# 1. Physio data import
	physioPath   = f"{homePath}/data_physio/sourcedata/"
	physioLayout = bids.layout.BIDSLayout(physioPath, validate=False)
	physio_conf  = grabber.define_grabconf(subID, sesID, "physio", "acq")
	acq_object   = grabber.grab_BIDS_object(physioPath, physioLayout, physio_conf)
	acq_path 	 = acq_object[0].path # Works if only one BIOPAC datafile is collected per session.

	# 2. Create a temporary folder to store TAPAS-compatible data
	tmpPath = f"{homePath}/data_physio/raw/tmp/"
	if not os.path.exists(tmpPath):
	    os.makedirs(tmpPath)

	# 3. Transform .acq files to .mat and/or .txt
	acqFile = acq_path.split("sourcedata/")[1]
	matFile = acqFile.split(".")[0] + ".mat"
	txtFile = acqFile.split(".")[0] + ".txt"

	print(f"\nRunning:, acq2mat {acq_path} {tmpPath}{matFile}")
	os.system(f"acq2mat {acq_path} {tmpPath}{matFile}")      # OK, if using matfile to read exported data in MATLAB.
	# os.system(f"acq2hdf5 {acq_path} {tmpPath}{matFile}")   # Should work with HDF5 read
	
	print(f"\nRunning:, acq2txt --outfile={tmpPath}{txtFile} {acq_path}")
	os.system(f"acq2txt --outfile={tmpPath}{txtFile} {acq_path}")

	# 4. Reorder compatible data
	reorder_cmd = f"makeBIOPAC_compatible('{homePath}', {subID}, {sesID}, '{task}'); exit;"
	os.chdir(f"{homePath}/scripts/import")
	print("\nRunning:", reorder_cmd)
	os.system(f'matlab -nodesktop -nosplash -r "{reorder_cmd}"')

	# Remove unnecessary temporary folder
	os.system(f"rm -r {homePath}/data_physio/raw/tmp/")

	# 5. Preprocess compatible data
	tapas_cmd = f"tapas('{homePath}', {subID}, {sesID}, '{project}', '{task}'); exit;"
	print("\nRunning:", tapas_cmd)
	os.system(f'matlab -nodesktop -nosplash -r "{tapas_cmd}"')

if __name__ == "__main__":
    subID, sesID, project, task, homePath = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
    import_PHYSIO(subID, sesID, project, task, homePath)