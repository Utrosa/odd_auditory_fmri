#! /usr/bin/env python
# Time-stamp: <2025-15-07 m.utrosa@bcbl.eu>

import bids

def define_grabconf(subject, session, suffix, extension, **kwargs):
	"""
	Prepare a config dictionary for grabbing BIDS-formatted files.
	
	Arguments:
		subject     (int): 1, 2, ...
		session     (int): 1, 2, ...
		suffix      (str): 'events', 'T1w', 'physio'
		extension   (str): 'tsv', 'nii.gz' => without dots !!
	
	Optional **kwargs:
		task        (str): 'localizer'
		acquisition (str): 'DresdenNoFat'
		direction   (str): 'AP' or 'PA'
		inv         (int): 1 or 2

	Returns: 
		a configuration dictionary
	"""
	grabconf = {
				'subject'    : f"{subject:02d}",
				'session'    : f"{session:02d}",
				'suffix'     : suffix,
				'extension'  : extension,
				}
	for k, value in kwargs.items():
		grabconf[k] = value

	return grabconf

def grab_BIDS_object(filepath, layout, grabconf):
	"""
	Use BIDSLayout to find BIDS objects matching the grabconf.

	Parameters:
		filepath (str)   : the path to the BIDS-compliant data folder
		layout   (class) : the output of BIDSLayout
		grabconf (dict)  : the output of define_grabconf() function

	Returns:
		a list of target file paths
	"""

	# Define filters to select only the files of interest
	filters = {}

	if grabconf.get('subject'):
		filters['subject'] = grabconf['subject']
	if grabconf.get('session'):
		filters['session'] = grabconf['session']
	if grabconf.get('suffix'):
		filters['suffix'] = grabconf['suffix']
	if grabconf.get('extension'):
		filters['extension'] = grabconf['extension']

	if grabconf.get('task'):
		filters['task'] = grabconf['task']
	if grabconf.get('acquisition'):
		filters['acquisition'] = grabconf['acquisition']
	if grabconf.get('direction'):
		filters['direction'] = grabconf['direction']
	if grabconf.get('inv'):
		filters['inv'] = grabconf['inv']
	if grabconf.get('space'):
		filters['space'] = grabconf['space']

	# Get filepaths
	target_BIDSobjects = layout.get(**filters)

	return target_BIDSobjects