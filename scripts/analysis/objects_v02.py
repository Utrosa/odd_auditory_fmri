#! /usr/bin/env python
# Time-stamp: <2025-05-09 m.utrosa@bcbl.eu>

def grab_objects(subID, sesID, acqID, homePath):
	import bids, grabber
	
	# Set up layout
	mripath   = f"{homePath}/data_MRI/"
	mriLayout = bids.layout.BIDSLayout(mripath, validate=False, derivatives=True)
	
	# TO-DO: maybe not necessary to have import_LOG.py function ....
	logpath   = f"{homePath}/data_logs/bids/"
	logLayout = bids.layout.BIDSLayout(logpath, validate=False)

	artpath    = f"{homePath}/data_physio/"
	artLayout  = bids.layout.BIDSLayout(artpath, validate=False)
	
	# Configuration
	## Log files
	log_conf   = grabber.define_grabconf(subID, sesID, "events", 	"tsv",    acquisition = acqID)
	
	## Funcional files
	bold_conf   = grabber.define_grabconf(subID, sesID, "bold",      "nii.gz", acquisition = acqID, space = "MNI152NLin2009cAsym")
	bold_object = grabber.grab_BIDS_object(mripath, mriLayout, bold_conf)
	
	## Outliers and confounds
	mask_conf  = grabber.define_grabconf(subID, sesID, "mask",      "nii.gz", acquisition = acqID, space = "MNI152NLin2009cAsym")
	conf_conf  = grabber.define_grabconf(subID, sesID, "confounds", "txt",    acquisition = acqID)
	out_conf   = grabber.define_grabconf(subID, sesID, "outliers",  "txt",    acquisition = acqID)
	
	## Anatomical files
	sesID = 1 # SUB-OPTIMAL: BECAUSE ANATOMICAL STUFF WAS ONLY COLLECTED IN SES-01
	T1w_conf   = grabber.define_grabconf(subID, sesID, "T1w",  "nii.gz", space = "MNI152NLin2009cAsym")
	T1w_toMNI_conf      = grabber.define_grabconf(subID, sesID, "xfm",  "h5")
	fsNative_toT1w_conf = grabber.define_grabconf(subID, sesID, "xfm",  "txt")
	
	# Grabbing files
	log_path   = grabber.grab_BIDS_object(logpath, logLayout, log_conf)[0].path
	bold_path  = bold_object[0].path
	mask_path  = grabber.grab_BIDS_object(mripath, mriLayout, mask_conf)[0].path
	conf_path  = grabber.grab_BIDS_object(artpath, artLayout, conf_conf)[0].path
	out_path   = grabber.grab_BIDS_object(artpath, artLayout, out_conf)[0].path
	T1w_path   = grabber.grab_BIDS_object(mripath, mriLayout, T1w_conf)[0].path
	T1w_toMNI_path      = grabber.grab_BIDS_object(mripath, mriLayout, T1w_toMNI_conf)[1].path
	fsNative_toT1w_path = grabber.grab_BIDS_object(mripath, mriLayout, fsNative_toT1w_conf)[0].path

	# Extract repetition time with PyBIDS methods [sec]
	TR = bold_object[0].get_metadata()['RepetitionTime']

	return log_path, bold_path, mask_path, conf_path, out_path, T1w_path, T1w_toMNI_path, fsNative_toT1w_path, TR