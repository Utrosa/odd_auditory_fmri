#! /usr/bin/env python
# Optimally combine multi-echo fMRI images
# Using t2smap workflow from tedana
# DOI: 10.21105/joss.03669
# Time-stamp: <08-12-2025 m.utrosa@bcbl.eu>

# Import python packages
import bids, json, os, sys
from tedana import workflows

# Import custom-made functions
from scripts import grabber

def optimal_combo(subID, sesID, task, homePath):

	# Study-specific parameters
	if sesID == 1:
		me_acq = ["ME3TR1100", "ME3TR1600", "ME3TR700", "ME3TR850"] # ses-01
	else: 
		me_acq = ["ME3TR1180", "ME3TR680", "ME3TR770"] # ses-02 or ses-03

	# Directories
	out_dir  = os.path.join(homePath, "data_MRI/sourcedata/t2smap")
	func_dir = os.path.join(homePath, "data_MRI/sourcedata/denoised/")
	raw_dir  = os.path.join(homePath, "data_MRI/sourcedata/raw/")

	# Grab data per multi-echo (ME) acquisition
	me_files = {}
	me_jsons = {}
	sbref_files = {}
	sbref_jsons = {}

	for acqID in me_acq:

		# Grab functional images
		func_layout = bids.layout.BIDSLayout(func_dir, validate=False)
		func_config = grabber.define_grabconf(subID, sesID, "bold", "nii.gz", acquisition=acqID)
		func_img    = grabber.grab_BIDS_object(func_dir, func_layout, func_config)
		me_files[acqID] = [f.path for f in func_img]

		# Grab json files for bold images (not part-phase)
		raw_layout = bids.layout.BIDSLayout(raw_dir, validate=False)
		func_json_config = grabber.define_grabconf(subID, sesID, "bold", "json", acquisition=acqID)
		func_json_img    = grabber.grab_BIDS_object(raw_dir, raw_layout, func_json_config)
		me_jsons[acqID] = [fj.path for fj in func_json_img if "part-phase" not in fj.path]

		# Grab single-band references
		sbref_config = grabber.define_grabconf(subID, sesID, "sbref", "nii.gz", acquisition=acqID)
		sbref_img    = grabber.grab_BIDS_object(raw_dir, raw_layout, sbref_config)
		sbref_files[acqID] = [sb.path for sb in sbref_img]

		# Grab json files for sbref
		sbref_json_config = grabber.define_grabconf(subID, sesID, "sbref", "json", acquisition=acqID)
		sbref_json_img    = grabber.grab_BIDS_object(raw_dir, raw_layout, sbref_json_config)
		sbref_jsons[acqID] = [sbj.path for sbj in sbref_json_img]

	# Exctract echo times from json files and convert seconds → msec
	func_echo_times = {}
	for me in me_jsons:
		values = me_jsons[me]
		e_times = []
		for e in values:
			with open(e, "r") as f:
				metadata = json.load(f)
				e_times.append(metadata["EchoTime"] * 1000)
		func_echo_times[me] = e_times

	sbref_echo_times = {}
	for me in sbref_jsons:
		values = sbref_jsons[me]
		e_times = []
		for e in values:
			with open(e, "r") as f:
				metadata = json.load(f)
				e_times.append(metadata["EchoTime"] * 1000)
		sbref_echo_times[me] = e_times
	
	# Combine echos
	for me in me_files:

		print(f"\n*** Combining echos for acquisition ID: {me} ***\n")

		# Functional images
		combined_me = workflows.t2smap_workflow(
							data = me_files[me],   # echos in ascending order
							tes  = func_echo_times[me], # in milliseconds
							out_dir = out_dir,
							prefix  = f"sub-{subID:02d}_ses-{sesID:02d}_task-{task}_acq-{me}",
							fittype = 'curvefit', # {‘loglin’, ‘curvefit’}, optional
							fitmode  = 'all', # {‘all’, ‘ts’}, optional
							combmode = 't2s'  # ‘t2s’ (Posse 1999), ‘paid’ (Poser)
						)

		# Single-band reference images
		combined_me = workflows.t2smap_workflow(
							data = sbref_files[me],   # echos in ascending order
							tes  = sbref_echo_times[me], # in milliseconds
							out_dir = out_dir,
							prefix  = f"sub-{subID:02d}_ses-{sesID:02d}_task-{task}_acq-{me}_sbref",
							fittype = 'curvefit', # {‘loglin’, ‘curvefit’}, optional
							fitmode  = 'all', # {‘all’, ‘ts’}, optional
							combmode = 't2s'  # ‘t2s’ (Posse 1999), ‘paid’ (Poser)
						)

def rename_t2smap(folder):
    for filename in os.listdir(folder):
        os.makedirs(folder + "/renamed", exist_ok=True)
        old_path = os.path.join(folder, filename)
        new_path = os.path.join(folder + "/renamed", filename)
        name = os.path.basename(filename)

        if "desc-optcom" in name:
            shutil.copy(old_path, new_path)
            if "sbref" in name:
                idx = name.index("sbref") + len("sbref")
                new_name = name[:idx] + ".nii.gz"
                new_dir = os.path.join(folder + "/renamed", new_name)
                print(f"Renaming: {filename} → {new_name}")
                os.rename(new_path, new_dir)

            # For remaining "desc-optcom_"
            else:
                idx = name.index("_desc")
                new_name = name[:idx] + "_bold.nii.gz"
                new_dir = os.path.join(folder + "/renamed", new_name)
                print(f"Renaming: {filename} → {new_name}")
                os.rename(new_path, new_dir)

if __name__ == "__main__":
    subID, sesID, task, homePath = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
    optimal_combo(subID, sesID, task, homePath)
    rename_t2smap(homePath)