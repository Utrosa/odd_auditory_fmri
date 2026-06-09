#!/usr/bin/env python3
# Time-stamp: <2026-01-24 m.utrosa@bcbl.eu>

# Import python packages
import argparse, bids, csv, subprocess
from pathlib import Path

# Import custom-made functions
from scripts import grabber

def onset_correction(homePath, subID, sesID, acqIDs):
	'''
	Onsets were incorrectly registered during data collection of Pilot Study 2.
	This function corrects the error directly in the logfiles in func folder.
	'''
	homePath = Path(homePath)

	# Iterate over aquisitions
	for acqID in acqIDs:

		# Extract Repetition Time (TR) from the functional scan's metadata 
		mriPath     = homePath / "data_MRI" / "sourcedata" / "raw"
		mriLayout   = bids.layout.BIDSLayout(mriPath, validate=False, derivatives=False)
		bold_conf   = grabber.define_grabconf(subID, sesID, "bold", "nii.gz", acquisition = acqID)
		bold_object = grabber.grab_BIDS_object(mriPath, mriLayout, bold_conf)
		TR  	    = bold_object[0].get_metadata()['RepetitionTime'] # in seconds

		# Grab the logfile
		logConf   = grabber.define_grabconf(subID, sesID, "events", "tsv", task = "localizer", acquisition = acqID)
		logObject = grabber.grab_BIDS_object(mriPath, mriLayout, logConf)
		logPath   = Path(logObject[0].path)

		# Read the logfile
		with open(logPath, 'r') as infile:
			logTsv = csv.reader(infile,  delimiter=";")
			lines = list(logTsv)

		# Rewrite the logfile
		with open(logPath, 'w', newline = '') as outfile:
			writer = csv.writer(outfile, delimiter = "\t")

			for i, line in enumerate(lines):

				# Write the first 3 lines unchanged (software info, timestamp, header)
				if i <= 2:
					writer.writerow(line)

				# Correct onsets
				elif i==3:
					onset_start = 4 * TR
				
					t_original  = float(line[0])
					correction  = t_original - onset_start
					t_corrected = round((t_original - correction), 3)
					print(
						f"Replaced {round(float(line[0]), 3)} with {t_corrected}")
					line[0] = t_corrected
				else:
					t_corrected = round((float(line[0]) - correction), 3)
					print(f"Replaced {round(float(line[0]), 3)} with {t_corrected}")
					line[0] = t_corrected

					# Write & save corrected logfiles
					writer.writerow(line)

		print(f"\nFor {acqID} the correct onset is: {onset_start}")
		print(f"Saving corrected logfile to {str(logPath)}")

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("homePath")
	parser.add_argument("subID",  type=int)
	parser.add_argument("sesID",  type=int)
	parser.add_argument("acqIDs", nargs="+")
	args = parser.parse_args()

	onset_correction(args.homePath, args.subID, args.sesID, args.acqIDs)