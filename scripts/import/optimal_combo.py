#!/usr/bin/env python
# Time-stamp: <10-02-2026 m.utrosa@bcbl.eu>
"""
Optimally combine multi-echo fMRI images using the t2smap workflow from tedana.

Reference
---------
DOI: 10.21105/joss.03669
https://github.com/ME-ICA/tedana
"""

# Import python packages
import argparse, bids, json
from tedana import workflows
from pathlib import Path

# Import custom-made functions
from scripts import grabber

def optimal_combo(subID, sesID, task, homePath, me_acqIDs):
	'''
	Optimally combine multi-echo fMRI data with tedana's t2smap workflow.

	Parameters:
	    subID: Subject identifier.
	    sesID: Session identifier.
	    task: Name of the experimental task that the subject was asked to do.
	    homePath: Base directory of the project.
	    me_acqIDs: List of multi-echo acquisition labels.
	'''
	# Directories
	homePath = Path(homePath)
	out_dir =  homePath / "data_MRI" / "sourcedata" / "t2smap"
	raw_dir  = homePath / "data_MRI" / "sourcedata" / "raw"
	out_dir.mkdir(exist_ok=True, parents=True)

	# Grab data per multi-echo (ME) acquisition
	me_files = {}
	me_jsons = {}
	sbref_files = {}
	sbref_jsons = {}

	for acqID in me_acqIDs:

		# Grab bold images
		raw_layout = bids.layout.BIDSLayout(raw_dir, validate=False)
		func_conf  = grabber.define_grabconf(subID, sesID, "bold", "nii.gz", acquisition=acqID)
		func_img   = grabber.grab_BIDS_object(raw_dir, raw_layout, func_conf)
		me_files[acqID] = [f.path for f in func_img if "part-phase" not in f.path]

		# Grab json files for these bold images (not part-phase)
		func_json_conf  = grabber.define_grabconf(subID, sesID, "bold", "json", acquisition=acqID)
		func_json_img   = grabber.grab_BIDS_object(raw_dir, raw_layout, func_json_conf)
		me_jsons[acqID] = [fj.path for fj in func_json_img if "part-phase" not in fj.path]

		# Grab single-band references
		sbref_conf = grabber.define_grabconf(subID, sesID, "sbref", "nii.gz", acquisition=acqID)
		sbref_img  = grabber.grab_BIDS_object(raw_dir, raw_layout, sbref_conf)
		sbref_files[acqID] = [sb.path for sb in sbref_img]

		# Grab json files for sbref
		sbref_json_conf = grabber.define_grabconf(subID, sesID, "sbref", "json", acquisition=acqID)
		sbref_json_img  = grabber.grab_BIDS_object(raw_dir, raw_layout, sbref_json_conf)
		sbref_jsons[acqID] = [sbj.path for sbj in sbref_json_img]

	# Exctract echo times from json files and convert seconds → msec
	# ---- Functional images ----
	func_echo_times = {}
	for me in me_jsons:
		values = me_jsons[me]
		e_times = []
		for e in values:
			with open(e, "r") as f:
				metadata = json.load(f)
				e_times.append(metadata["EchoTime"] * 1000)
		func_echo_times[me] = e_times

	# ---- Single-band reference images ----
	sbref_echo_times = {}
	for me in sbref_jsons:
		values = sbref_jsons[me]
		e_times = []
		for e in values:
			with open(e, "r") as f:
				metadata = json.load(f)
				e_times.append(metadata["EchoTime"] * 1000)
		sbref_echo_times[me] = e_times
	
	# Optimally combine echos
	for me in me_files:
		print(f"\n*** Combining echos for acquisition ID: {me} ***\n")

		# ---- Functional images ----
		combined_me = workflows.t2smap_workflow(
							data = me_files[me],        # echos in ascending order
							tes  = func_echo_times[me], # in milliseconds
							out_dir  = out_dir,
							prefix   = f"sub-{subID:02d}_ses-{sesID:02d}_task-{task}_acq-{me}",
							fittype  = 'curvefit', # {‘loglin’, ‘curvefit’}, optional
							fitmode  = 'all', # {‘all’, ‘ts’}, optional
							combmode = 't2s'  # ‘t2s’ (Posse 1999), ‘paid’ (Poser)
						)

		# ---- Single-band reference images ----
		combined_me = workflows.t2smap_workflow(
							data = sbref_files[me],      # echos in ascending order
							tes  = sbref_echo_times[me], # in milliseconds
							out_dir  = out_dir,
							prefix   = f"sub-{subID:02d}_ses-{sesID:02d}_task-{task}_acq-{me}_sbref",
							fittype  = 'curvefit', # {‘loglin’, ‘curvefit’}, optional
							fitmode  = 'all', # {‘all’, ‘ts’}, optional
							combmode = 't2s'  # ‘t2s’ (Posse 1999), ‘paid’ (Poser)
						)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("subID",  type=int)
	parser.add_argument("sesID",  type=int)
	parser.add_argument("task")
	parser.add_argument("homePath")
	parser.add_argument("me_acqIDs", nargs="+")
	args = parser.parse_args()

	optimal_combo(
		args.subID,
		args.sesID,
		args.task,
		args.homePath,
		args.me_acqIDs
	)