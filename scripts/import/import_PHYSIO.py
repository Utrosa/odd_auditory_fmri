#!/usr/bin/env python
# Time-stamp: <10-02-2026 m.utrosa@bcbl.eu>
"""
Prerequisites:
- For python: phys2bids; bioread
- For matlab: Signal Processing; Statistics and Machine Learning

Manual preparation of physiological data from BIOPAC:
   - Turn on the Physio computer in the MRI room (on the left, up in the air).
   - Open FileZilla.
   - Upload all .acq files:
     from: /.../<project_name>/
     to:   /<project_root>/data_physio/sourcedata/.
"""

# Import python packages
import bids, subprocess, shutil, sys, warnings
from pathlib import Path

# Import custom-made functions
from scripts import grabber

def import_PHYSIO(subID, sesID, project, task, homePath):
	"""
	Import raw physiological data and organize them into a BIDS-compliant structure.

	Parameters:
	    subID: Subject identifier.
	    sesID: Session identifier.
	    project: Project name as entered in the Siemens computer.
	    task: Name of the experimental task that the subject was doing.
	    homePath: Base directory of the project.
	
	Raises:
	    FileNotFoundError if required BIOPAC files are missing.
	    ValueError if .acq files are not found (due to incorrect name).
	"""

	# 1. Physio data import -------------------------------------------------------------
	homePath   = Path(homePath)
	physioPath = homePath / "data_physio" / "sourcedata"
	if not physioPath.exists():
		raise FileNotFoundError(f"Physio folder not found: {physioPath}")

	# Find .acq files following BIDS-compliant naming convention
	physioLayout = bids.layout.BIDSLayout(physioPath, validate=False)
	physio_conf  = grabber.define_grabconf(subID, sesID, "physio", "acq")
	acq_object   = grabber.grab_BIDS_object(physioPath, physioLayout, physio_conf)
	if len(acq_object) == 0:
		files = "\n".join(item.name for item in physioPath.iterdir())
		raise ValueError(f"\nUnexpected physio name format: \n{files}")

	# Check the amount of .acq files collected. Expecting one file per session.
	acq_path = Path(acq_object[0].path)
	if len(acq_object) > 1:
		warnings.warn(
			f"\nMultiple BIOPAC files found ({len(acq_object)})"
			f"For subject {subID}, session {sesID} using {acq_object[1].name}.")
	print(f"\nPhysio folder: {physioPath}")
	print(f"\nGrabbing: {acq_path.name}")

	# 2. Create a temporary folder to store TAPAS-compatible data -----------------------
	rawPath = homePath / "data_physio" / "raw" 
	rawPath.mkdir(exist_ok=True, parents=True)
	tmpPath = rawPath / "tmp"
	tmpPath.mkdir(exist_ok=True, parents=True)

	# 3. Transform .acq files to .mat and/or .txt ---------------------------------------
	acqFile = Path(acq_path.name)
	matFile = acqFile.with_suffix(".mat")
	txtFile = acqFile.with_suffix(".txt")
	matout  = tmpPath / matFile
	txtout  = tmpPath / txtFile

	print(f"\nRunning:, acq2mat {acq_path} {matout}")
	subprocess.run(
		["acq2mat", str(acq_path), str(matout)],
		check=True)
	
	warnings.warn("\nAssuming that matfile is used to read PHYSIO data in MATLAB.")
	
	# Alternative:
	# os.system(f"acq2hdf5 {acq_path} {tmpPath}{matFile}")
	# Should work with HDF5 read
	
	print(f"\nRunning:, acq2txt --outfile={txtout} {acq_path}")
	subprocess.run(
		["acq2txt", f"--outfile={txtout}", str(acq_path)],
		check=True
		)

	# 4. Reorder compatible data --------------------------------------------------------
	reorder_cmd = f"makeBIOPAC_compatible('{homePath}', {subID}, {sesID}, '{task}'); exit;"
	importPath  = homePath / "scripts" / "import"
	
	print("\nRunning:", reorder_cmd)
	subprocess.run(
		["matlab", "-nodesktop", "-nosplash", "-r", reorder_cmd],
		cwd=importPath,
		check=True
		)

	# Remove unnecessary temporary folder
	if tmpPath.exists():
		shutil.rmtree(tmpPath)

	# 5. Preprocess compatible data -----------------------------------------------------
	tapas_cmd = f"tapas('{homePath}', {subID}, {sesID}, '{project}', '{task}'); exit;"
	print("\nRunning:", tapas_cmd)
	subprocess.run(
		["matlab", "-nodesktop", "-nosplash", "-r", tapas_cmd],
		cwd=importPath,
		check=True
		)

if __name__ == "__main__":
	subID, sesID, project, task, homePath = (
    	int(sys.argv[1]),
    	int(sys.argv[2]),
    	sys.argv[3],
    	sys.argv[4],
    	sys.argv[5]
    	)
	import_PHYSIO(subID, sesID, project, task, homePath)