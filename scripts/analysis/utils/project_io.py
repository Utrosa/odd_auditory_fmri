#! /usr/bin/env python
# Time-stamp: <2025-05-09 m.utrosa@bcbl.eu>

def grab_objects(subID, sesID, acqID, home_path,
				 mri_dir = "data_MRI",
				 log_dir = ("data_logs", "bids"),
				 art_dir = "data_physio"):
	
	import bids, grabber
	from pathlib import Path
	
	# Set up paths
	# TO-DO: set up a class for project paths
	# TO-DO: maybe not necessary to have import_LOG.py function ....
	base    = Path(home_path)
	mripath = base / mri_dir
	logpath = base.joinpath(*log_dir)
	artpath = base / art_dir

	for path in (mripath, logpath, artpath):
		if not path.exists():
			raise FileNotFoundError(f"Missing directory: {path}")

	# Set up layouts
	mri_layout = bids.layout.BIDSLayout(mripath, validate=False, derivatives=True)
	log_layout = bids.layout.BIDSLayout(logpath, validate=False)
	art_layout = bids.layout.BIDSLayout(artpath, validate=False)
	
	# Configuration
	## Log files
	log_conf   = grabber.define_grabconf(subID, sesID, "events", 	"tsv",    acquisition = acqID)
	
	## Funcional files
	bold_conf   = grabber.define_grabconf(subID, sesID, "bold",      "nii.gz", acquisition = acqID, space = "T1w") # space = "MNI152NLin2009cAsym"
	bold_object = grabber.grab_BIDS_object(mripath, mri_layout, bold_conf)
	
	## Outliers and confounds
	mask_conf  = grabber.define_grabconf(subID, sesID, "mask",      "nii.gz", acquisition = acqID, space = "T1w") # space = "MNI152NLin2009cAsym"
	conf_conf  = grabber.define_grabconf(subID, sesID, "confounds", "txt",    acquisition = acqID)
	out_conf   = grabber.define_grabconf(subID, sesID, "outliers",  "txt",    acquisition = acqID)
	
	## Transform files
	boldref_to_T1w_conf  = grabber.define_grabconf(subID, sesID, "xfm",  "txt")

	## Anatomical files
	sesID = 1 # SUB-OPTIMAL: BECAUSE ANATOMICAL STUFF WAS ONLY COLLECTED IN SES-01
	T1w_conf             = grabber.define_grabconf(subID, sesID, "T1w",  "nii.gz") # space = "MNI152NLin2009cAsym"
	T1w_to_MNI_conf      = grabber.define_grabconf(subID, sesID, "xfm",  "h5")

	# Grabbing files
	log_path   = grabber.grab_BIDS_object(logpath, log_layout, log_conf)[0].path
	bold_path  = bold_object[0].path
	mask_path  = grabber.grab_BIDS_object(mripath, mri_layout, mask_conf)[0].path
	conf_path  = grabber.grab_BIDS_object(artpath, art_layout, conf_conf)[0].path
	out_path   = grabber.grab_BIDS_object(artpath, art_layout, out_conf)[0].path
	T1w_path   = grabber.grab_BIDS_object(mripath, mri_layout, T1w_conf)[0].path
	T1w_to_MNI_path      = grabber.grab_BIDS_object(mripath, mri_layout, T1w_to_MNI_conf)[1].path
	orig_to_boldref_path = grabber.grab_BIDS_object(mripath, mri_layout, boldref_to_T1w_conf)[1].path
	boldref_to_T1w_path  = grabber.grab_BIDS_object(mripath, mri_layout, boldref_to_T1w_conf)[0].path

	# Extract repetition time with PyBIDS methods [sec]
	TR = bold_object[0].get_metadata()['RepetitionTime']

	return log_path, bold_path, mask_path, conf_path, out_path, T1w_path, T1w_to_MNI_path, orig_to_boldref_path, boldref_to_T1w_path, TR