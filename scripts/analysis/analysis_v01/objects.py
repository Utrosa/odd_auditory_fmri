#! /usr/bin/env python
# Time-stamp: <2025-05-09 m.utrosa@bcbl.eu>

# Import python packages
import bids, os, sys

# Import custom-made functions (scripts)
# from scripts import grabber
import grabber

def grab_objects(subID, sesID, acqID, homePath):

	# Initialize
	objects = {}

	# Set up layout
	mripath   = f"{homePath}/data_MRI/"
	mriLayout = bids.layout.BIDSLayout(mripath, validate=False, derivatives=True)
	
	# TO-DO: maybe not necessary to have import_LOG.py function ....
	logpath   = f"{homePath}/data_logs/bids/"
	logLayout = bids.layout.BIDSLayout(logpath, validate=False)

	artpath    = f"{homePath}/data_physio/"
	artLayout  = bids.layout.BIDSLayout(artpath, validate=False)
	
	# Configuration
	log_conf   = grabber.define_grabconf(subID, sesID, "events", 	"tsv",    acquisition = acqID)
	bold_conf  = grabber.define_grabconf(subID, sesID, "bold",      "nii.gz", acquisition = acqID, space = "T1w")
	mask_conf  = grabber.define_grabconf(subID, sesID, "mask",      "nii.gz", acquisition = acqID, space = "T1w")
	xfm_conf   = grabber.define_grabconf(subID, sesID, "xfm",       "h5")
	conf_conf  = grabber.define_grabconf(subID, sesID, "confounds", "txt",    acquisition = acqID)
	out_conf   = grabber.define_grabconf(subID, sesID, "outliers",  "txt",    acquisition = acqID)
	T1w_conf   = grabber.define_grabconf(subID, sesID, "T1w",  "nii.gz")
	toNat_conf = grabber.define_grabconf(subID, sesID, "xfm",  "txt")
	
	# Grabbing files
	log_object   = grabber.grab_BIDS_object(logpath, logLayout, log_conf)
	bold_object  = grabber.grab_BIDS_object(mripath, mriLayout, bold_conf)
	mask_object  = grabber.grab_BIDS_object(mripath, mriLayout, mask_conf)
	xfm_object   = grabber.grab_BIDS_object(mripath, mriLayout, xfm_conf)
	conf_object  = grabber.grab_BIDS_object(artpath, artLayout, conf_conf)
	out_object   = grabber.grab_BIDS_object(artpath, artLayout, out_conf)
	T1w_object   = grabber.grab_BIDS_object(mripath, mriLayout, T1w_conf)
	toNat_object = grabber.grab_BIDS_object(mripath, mriLayout, toNat_conf)

	# Add to directories
	objects["logfiles"]     = log_object
	objects["preproc_bold"] = bold_object
	objects["native_mask"]  = mask_object
	objects["confounds"]    = conf_object
	objects["outliers"]     = out_object
	objects["xfm"]          = xfm_object
	objects["T1w"] 			= T1w_object
	objects["toNative"] 	= toNat_object

	return objects