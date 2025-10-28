def localizer(logfilepath):
	"""
	Parse logfiles into design matrix in NiPype Bunch format.

	Parameters:
	    logfilepaths (list): List of file paths to logfiles.

	Returns:
	    list: A list of Bunch objects containing design information.
	"""
	import csv
	from nipype.interfaces.base import Bunch
	
	# Get info on stimuli onset, duration and key presses.
	sounds, silences, keypress, sound_prev = [], [], [], []
	with open(logfilepath, 'r') as logfile:
		logTsv  = csv.reader(logfile, delimiter=";")

		next(logTsv) # Skip row with expyriment software info
		next(logTsv) # Skip row with experiment timestamp
		next(logTsv) # Skip header row

		for line in logTsv:
			event     = {'onset': float(line[0]), 'duration': float(line[1])}
			stim_file = line[2]

			# Silences
			if stim_file == 'null_event.wav':
				silences.append(event)

			# Sounds with key press during
			elif stim_file.startswith('s3'):
				if stim_file != sound_prev:
					sounds.append(event)
					sound_prev = stim_file
				else:
					if line[4] != 'n/a':
						keypress.append(event)

			# Sounds with key press after
			elif stim_file == 'n/a':
				if line[4] != 'n/a':
					keypress.append(event)
			else:
				print('WARNING: Skipping unrecognised line "{}"'.format(line))

	# Incorporate into design info
	conditions = ['sound', 'silence', 'keypress']
	onsets     = [[on['onset'] for on in cond] for cond in [sounds, silences, keypress]]
	durations  = [[du['duration'] for du in cond] for cond in [sounds, silences, keypress]]
	design_info = Bunch(conditions = conditions,
				   		onsets     = onsets,
				   		durations  = durations)
	return design_info