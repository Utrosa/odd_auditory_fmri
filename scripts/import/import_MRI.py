#!/usr/bin/env python
# Time-stamp: <10-02-2026 m.utrosa@bcbl.eu>
"""
Prerequisites:
- Install dcm2bids and dcm2niix in a Python 3.8+ environment.

Manual DICOM preparation (BCBL workflow):
1. Copy DICOM files from the BCBL servers:
   - Open the Citrix Workspace app and log in with your username and password.
   - If the app fails, connect via https://gateway.bcbl.eu/.
   - Open the "My Network Folder" app.
   - For pilot data, navigate to G:\\Exchange.
   - For non-pilot data, navigate to G:\\<project_name>.
   - Copy all data to your personal folder: F:\\<username>.
2. In your personal folder, move DICOMs to:
   /<project_root>/data_MRI/sourcedata/dicoms/
3. If necessary, unzip folders:
   Run `unzip <foldername>` in your terminal.

IMPORTANT:
- Always verify that the DICOM dataset is complete.
- Automatic uploads from the scanner may fail.
- If files are missing, request data re-upload by emailing MRI lab staff
  with the subID, sesID, and scan date.
"""

# Import python packages
import argparse, bids, shutil, subprocess
from pathlib import Path

# Import custom-made functions
from scripts import grabber

def import_MRI(subID, sesID, anatID, project, homePath, acq_list, nordic=True, tidy=True):
	"""
	Import raw MRI data and organize it into a BIDS-compliant structure.

	Parameters:
	    subID: Subject identifier.
	    sesID: Session identifier.
	    anatID: Session number in which anatomical data was collected.
	    project: Project name as entered in the Siemens computer.
	    homePath: Base directory of the project.
	    acq_list: List of acquisition labels for functional scans.
	    nordic: If True, NORDIC denoising is applied to functional scans.
	    tidy: If True, denoised BOLD files overwrite raw BOLD files.

	Side effects:
	    Creates and modifies files on disk, including:
	    - BIDS-formatted directories
	    - Background-corrected T1w (MP2RAGE) images
	    - Noise-corrected functional images

	Raises:
	    FileNotFoundError if required DICOM or configuration files are missing.
	    RuntimeError if expected NORDIC outputs are not generated.
	"""

	# 1. BIDS data import ---------------------------------------------------------
	# Define project roots
	homePath   = Path(homePath)
	SOURCEDATA = homePath / "data_MRI" / "sourcedata"
	IMPORT     = homePath / "scripts" / "import"
	dataPath   = SOURCEDATA / "raw"
	dataPath.mkdir(exist_ok=True)
	print(f"\nOutput BIDS folder: {dataPath}")
	
	# Find dicom folder using BCBL naming convention
	dicomFold = (
		SOURCEDATA 
		/ "dicoms"
		/ f"sub-{subID:02d}_ses-{sesID:02d}_{project}"
	)
	if not dicomFold.exists():
		raise FileNotFoundError(f"DICOM folder not found: {dicomFold}")
	else:
		print(f"\nDICOM folder: {dicomFold}")

	# Find the configuration file
	confFile = IMPORT / f"conf_{project}.json"
	if not confFile.exists():
		raise FileNotFoundError(f"Configuration file not found: {confFile}")
	else:
		print(f"\nConfiguration file: {confFile}")

	# Run dcm2bids
	bids_cmd = [
		"dcm2bids",
		"-d", str(dicomFold),
		"-p", f"{subID:02d}",
	    "-s", f"{sesID:02d}",
		"-c", str(confFile),
		"-o", str(dataPath),
	]
	print("\nRunning:", " ".join(bids_cmd))
	subprocess.run(bids_cmd, check=True)

	# Remove unnecessary tmp folder
	tmp_dir = dataPath / "tmp_dcm2bids"

	if tmp_dir.exists():
		shutil.rmtree(tmp_dir)

	# 2. Remove background noise from MP2RAGE UNI image ---------------------------
	# Code: https://github.com/srikash/MPRAGEise?tab=readme-ov-file
	
	# Remove background noise only for the session in which anatomical data
	# were acquired.
	if sesID == anatID:

		anatPath   = dataPath / f"sub-{subID:02d}" / f"ses-{sesID:02d}" / "anat"
		anatLayout = bids.layout.BIDSLayout(anatPath, validate=False)

		INV2_img_conf = grabber.define_grabconf(subID, sesID, "MP2RAGE", "nii.gz", inv=2)
		UNI_img_conf  = grabber.define_grabconf(subID, sesID, "UNIT1", "nii.gz")

		INV2_img = grabber.grab_BIDS_object(anatPath, anatLayout, INV2_img_conf)[0]
		UNI_img  = grabber.grab_BIDS_object(anatPath, anatLayout, UNI_img_conf)[0]

		mprageise = IMPORT / "MPRAGEise.py"
		mp2rage_cmd = [
			str(mprageise),
			"-i", INV2_img.path,
			"-u", UNI_img.path,
			"-o", str(anatPath),
			]
		print("\nRunning:", mp2rage_cmd)
		subprocess.run(mp2rage_cmd, check=True)
		
		# Create a new json file for the unbiased clean T1 image.
		old_json = anatPath / f"sub-{subID:02d}_ses-{sesID:02d}_UNIT1.json"
		# new_json = anatPath / f"sub-{subID:02d}_ses-{sesID:02d}_T1w.json"
		# if old_json.exists():
		# 	old_json.rename(new_json)

		# Remove redundant UNI image
		Path(UNI_img.path).unlink()
		
		# Rename the denoised T1 image
		anatLayout = bids.layout.BIDSLayout(anatPath, validate=False, reset_database=True)
		T1_conf = grabber.define_grabconf(subID, sesID, "T1w", "nii.gz")
		T1_img  = grabber.grab_BIDS_object(anatPath, anatLayout, T1_conf)[1]
		denoised_T1_name = anatPath / f"sub-{subID:02d}_ses-{sesID:02d}_UNIT1.nii.gz"
		print(f"\nRenaming {T1_img.filename} as {denoised_T1_name.name}")
		Path(T1_img.path).rename(denoised_T1_name)

	else:
		print(f"\nMP2RAGE background-correction not applied for session {sesID:02d}.\n")

	# 3. Denoise functional images with NORDIC -------------------------------------
	# Code: https://github.com/SteenMoeller/NORDIC_Raw/tree/main)
	if nordic:
		funcPath   = dataPath / f"sub-{subID:02d}" / f"ses-{sesID:02d}" / "func"
		nordPath   = funcPath / "denoised" 
		funcLayout = bids.layout.BIDSLayout(funcPath, validate=False)

		for ac in acq_list:
			bold_img_conf = grabber.define_grabconf(subID, sesID, "bold", "nii.gz", acquisition=ac)
			bold_img = grabber.grab_BIDS_object(funcPath, funcLayout, bold_img_conf)
			
			# BOLD and their phase images are expected to appear in alternating order:
			# magnitude first, phase second.
			for i in range(0, len(bold_img), 2):

				# Functional images must not have a "part-phase" label in the filename
				bold = bold_img[i].path
				if "part-phase" in bold:
					raise ValueError(f"Unexpected phase label in BOLD file: {bold}")

				# Phase images must have "part-phase" according to BIDS-specification
				phase = bold_img[i + 1].path
				if "part-phase" not in phase:
					raise ValueError(f"Phase file missing 'part-phase' label: {phase}")
				
				# Run NORDING through MATLAB
				nordic_cmd = (
					 f"addpath('{IMPORT.as_posix()}'); "
					 f"nordic('{bold}', '{phase}', '{nordPath.as_posix()}'); "
					  "exit;")
				print("\nRunning:", nordic_cmd)
				subprocess.run(
					["matlab", "-nodesktop", "-nosplash", "-r", nordic_cmd,],
					check=True,)

				# Tidy mode:
				# - overwrite original BOLD images with denoised outputs
				if tidy:
					bold_orig_path = Path(bold)
					bold_denoised_path = nordPath / bold_orig_path.name
					if not bold_denoised_path.exists():
						raise RuntimeError(f"NORDIC output missing: {bold_denoised_path}")
					
					print(f"Moving denoised file [{bold_denoised_path}] to {bold_orig_path}.")
					shutil.move(bold_denoised_path, bold_orig_path)
		
		# Remove the nordPath
		if tidy:
			if nordPath.exists():
				shutil.rmtree(nordPath)
	else:
		print("\nConfirmation: NORDIC denoising is not applied.\n")

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("subID",  type=int)
	parser.add_argument("sesID",  type=int)
	parser.add_argument("anatID", type=int)
	parser.add_argument("project")
	parser.add_argument("homePath")
	parser.add_argument("acq_list", nargs="+")
	parser.add_argument(
		"--nordic",
		action="store_true",
		help="Applies NORDIC denoising to main functional scans (not sbref/FH scans)."
		)
	parser.add_argument(
		"--tidy",
		action="store_true",
		help="Overwrite raw BOLD files with denoised ones & remove phase data."
		)
	args = parser.parse_args()
	import_MRI(
		args.subID,
		args.sesID,
		args.anatID,
		args.project,
		args.homePath,
		args.acq_list,
		nordic=args.nordic,
		tidy=args.tidy
		)