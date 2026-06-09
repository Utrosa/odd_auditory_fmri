#!/usr/bin/env python
# Time-stamp: <10-02-2026 m.utrosa@bcbl.eu>
"""
Manual preparation of logfiles.

Steps:
   - Open FileZilla on the MRI computer (Windows 10; option 2).
   - Transfer logfiles from:
     C:/Users/Experimental User/Desktop/<project_name>/bids_output
     to:
     /<project_root>/data_logs
"""

# Import python packages
import argparse, csv, bids, shutil
from pathlib import Path

# Import custom-made functions
from scripts import grabber

def import_LOG(homePath, subID, sesID, acqIDs):
	'''
	Import events.tsv files and organize them according to BIDS standard.

	Parameters:
	   homePath: Base directory of the project.
	   subID: Subject identifier.
	   sesID: Session identifier.
	   acqIDs: List of acquisition labels in order of data collection.
	
	Raises:
	   FileNotFoundError
	      If logfiles are missing.
	   ValueError
	      If the numbers of acquisition IDs and logfiles do not match.
	      If the logfile name format is unexpected.
	'''
	
	# Define directories and paths relative to project root.
	homePath = Path(homePath)
	rawFold  = homePath / "data_logs" / "sourcedata"
	outPath  = (homePath / "data_MRI" / "sourcedata" / "raw"
				/ f"sub-{subID:02d}" / f"ses-{sesID:02d}" / "func")
	bidsPath = homePath / "data_logs" / "bids"
	bidsPath.mkdir(exist_ok=True, parents=True)

	# Find logfiles
	logLayout = bids.layout.BIDSLayout(rawFold, validate=False)
	logConf   = grabber.define_grabconf(subID, sesID, "events", "tsv", task = "localizer")
	logfiles  = grabber.grab_BIDS_object(rawFold, logLayout, logConf)

	# Check whether logfile exists.
	if not logfiles:
		raise FileNotFoundError(
			f"No logfiles found for sub-{subID:02d}, ses-{sesID:02d} in {rawFold}."
			)
	
	# Ensure that we have an events file for each acquisition
	if len(acqIDs) != len(logfiles):
		raise ValueError(
			f"Lengths of acquisition IDs ({len(acqIDs)})" 
			f"and logfiles ({len(logfiles)}) do not match.")

	for count, lf in enumerate(logfiles):
		
		# Get the acqID
		acqID = acqIDs[count]
		acqID = acqID.strip()

		# Parse filename to find timestamp part
		oldName = Path(lf.path).name
		ts = oldName.find("ts")
		ev = oldName.find("_events")

		# Raise error if filename parsing fails
		if ev == -1 or ts == -1:
			raise ValueError(f"Unexpected logfile name format: {oldName}")

		# Define new name
		before_ts = oldName[:ts]
		after_ev  = oldName[ev:]
		newName   = before_ts + f"acq-{acqID}" + after_ev
		print(f"\nRenaming log:\n from {oldName}\n to {newName}")

		# Output paths
		out_file = outPath / newName
		bids_file = bidsPath / newName

		# Remove the first two rows by reading the original log file.
		with open(lf.path, "r", newline="") as infile:
			reader = csv.reader(infile, delimiter=";")
			rows   = list(reader)[2:]

		# Write modified logfie to the new locations under the new filename
		# Ensure that the output is tab-separated
		with open(out_file, "w", newline="") as outfile:
			writer = csv.writer(outfile, delimiter="\t")
			writer.writerows(rows)
		with open(bids_file, "w", newline="") as bidsfile:
			writer = csv.writer(bidsfile, delimiter="\t")
			writer.writerows(rows)

		# Print update messages in the terminal
		print(
			f"\nGrabbing from: {lf.path}"
			f"\nCopying to: \n{out_file} and \n{bidsPath}")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Import BIDS-compatible logfiles.")
	parser.add_argument("homePath")
	parser.add_argument("subID",  type=int)
	parser.add_argument("sesID",  type=int)
	parser.add_argument("acqIDs", nargs="+")
	args = parser.parse_args()

	import_LOG(
		args.homePath,
		args.subID,
		args.sesID,
		args.acqIDs
		)