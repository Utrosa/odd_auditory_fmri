#! /usr/bin/env python
# Time-stamp: <2026-01-24 m.utrosa@bcbl.eu>

# Import python packages
import bids, argparse, shutil, subprocess
from pathlib import Path

# Import custom-made functions
from scripts import grabber

def remove_volumes(file, quantity, location, out_path):
	'''
	Removes volumes from the start/end of a NIfTI file using FSL.

	Parameters:
	   file: BIDS object with a path attribute to a NIfTI file (output of grabber)
	   quantity: integer, the number of volumes to remove
	   location: string, indicating where volumes should be removed (start/end)
	   out_path: directory where the output file will be written

	Side effects:
	   Func and sbref bold images have removed volumes.

	Raises:
	   ValueError
	      If the quantity of volumes to removes all volumes or more.
	      If the location argument is specified incorrectly.
	'''

	in_file  = Path(file.path)
	out_path = Path(out_path)
	if not out_path.exists():
		out_path.mkdir(exist_ok=True, parents=True)
	out_file = out_path / in_file.name
	
	# Get the number of volumes
	nvols_start = subprocess.run(
					["fslnvols", str(in_file)],
					check=True,
					stdout=subprocess.PIPE,
					stderr=subprocess.PIPE,
					text=True,
					)
	print(nvols_start)
	nvols = int(nvols_start.stdout.strip())
	if quantity >= nvols:
		raise ValueError("Quantity removes all or more volumes.")

	# Set logic of removing volumes
	location = location.lower()
	if location == "end":
		nvols_keep = nvols - quantity
		fsl_cmd = ["fslroi", str(in_file), str(out_file), "0", str(nvols_keep)]

	elif location == "start":
		fsl_cmd = ["fslroi", str(in_file), str(out_file), str(quantity), str(nvols)]
	
	else:
		raise ValueError('Location must be either "start" or "end".')
	
	# Run the command to remove volumes and print status updates
	print(f"	nvols BEFORE: {nvols}")
	subprocess.run(fsl_cmd, check=True)
	nvols_end = subprocess.run(
				["fslnvols", str(out_file)],
				check=True,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				text=True,
				)
	print(nvols_end)
	nvols = int(nvols_end.stdout.strip())
	print(f"	nvols AFTER: {nvols}")

	return out_file

def remove_noise_scan(homePath, subID, sesID, n_noise_scans, overwrite=True):
	'''
	Remove noise scans from functional BOLD and SBREF images for a given subject/session.

	Parameters:
	   homePath: Project root directory.
	   subID: Subject identifier.
	   sesID: Session identifier.
	   n_noise_scans: The number of noise scans collected.
	   overwrite: If true, overwrites original bold images with no-noise-scan ones.
	'''

	homePath   = Path(homePath)
	funcPath   = (homePath / "data_MRI" / "sourcedata" / "raw"
				 / f"sub-{subID:02d}" / f"ses-{sesID:02d}" / "func")
	funcLayout = bids.layout.BIDSLayout(funcPath, validate=False)
	outPath    = funcPath / "no-noise-scan"

	# Remove noise scans from functional scans. This step should come AFTER NORDIC.
	bold_conf   = grabber.define_grabconf(subID, sesID, "bold", "nii.gz")
	bold_images = grabber.grab_BIDS_object(funcPath, funcLayout, bold_conf)
	
	print("\nRemoving volumes from:")
	for bold in bold_images:
		print(f"* {Path(bold.path).name}")
		out_file = remove_volumes(
						file = bold,
						quantity = n_noise_scans,
						location = "end",
						out_path = outPath,
					)

		# Move the file without the noise scan to func folder (overwrites data)
		if overwrite:
			movePath = funcPath / out_file.name
			if movePath.exists():
				movePath.unlink()
			shutil.move(str(out_file), str(movePath))

	# Remove noise scans from single-band reference images for Dresden sequences	
	sbref_conf   = grabber.define_grabconf(subID, sesID, "sbref", "nii.gz")
	sbref_images = grabber.grab_BIDS_object(funcPath, funcLayout, sbref_conf)
	
	for sbref in sbref_images:

		# ME sequences have sbref data per echo, and this data has no noise scans
		# but fMRIPrep maybe doesn't like that, so we enter func FH (nvols = 4)
		# if "Dresden" in sbref.path:
		# 	print("\nRemoving volumes from")
		# 	print(f"* {Path(sbref.path).name}")
		# 	out_file = remove_volumes(
		# 					file = sbref,
		# 					quantity = n_noise_scans,
		# 					location = "end",
		# 					out_path = outPath,
		# 				)
		print("\nRemoving volumes from:")
		print(f"* {Path(sbref.path).name}")
		out_file = remove_volumes(
						file = sbref,
						quantity = n_noise_scans,
						location = "end",
						out_path = outPath,
					)

		# Move the file without the noise scan to func folder (overwrites data)
		if overwrite:
			movePath = funcPath / out_file.name
			if movePath.exists():
				movePath.unlink()
			shutil.move(str(out_file), str(movePath))

	# Remove output path
	if overwrite:
		if outPath.exists():
			shutil.rmtree(outPath)	

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	
	parser.add_argument("homePath")
	parser.add_argument("subID", type=int)
	parser.add_argument("sesID", type=int)
	parser.add_argument("n_noise_scans", type=int)

	parser.add_argument(
		"--overwrite",
		action="store_true",
		help="Overwrite raw BOLD files with the ones with no noise scans."
		)

	args = parser.parse_args()

	remove_noise_scan(
		args.homePath,
		args.subID,
		args.sesID,
		args.n_noise_scans,
		overwrite=args.overwrite,
		)