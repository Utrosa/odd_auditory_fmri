def parse_logfile(logfilepath, n_rows_skipped = 3):
	"""
	Parse logfiles into design matrix in NiPype Bunch format.

	Parameters:
	    logfilepaths (list): List of file paths to logfiles.

	Returns:
	    list: A list of Bunch objects containing design information.
	"""
	import csv
	
	# Get info on stimuli onset, duration and key presses.
	sounds, silences, keypress, sound_prev = [], [], [], []
	with open(logfilepath, 'r') as logfile:

		# Skip rows with expyriment software info, timestamp and header
		for _ in range(n_rows_skipped):
			next(logfile)

		# Determine the delimiter of the logfiles automatically
		sample  = logfile.read(3000); logfile.seek(0)
		dialect = csv.Sniffer().sniff(sample, delimiters = [";", "\t" , ","])
		logTsv  = csv.reader(logfile, dialect)

		# Skip rows again (we're accessing log info differently).
		for _ in range(n_rows_skipped):
			next(logTsv)

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
			elif stim_file == 'n/a' and line[4] != 'n/a':
					keypress.append(event)
			else:
				print('WARNING: Skipping unrecognised line "{}"'.format(line))

		return sounds, silences, keypress

def localizer(logfilepath):
	
	from nipype.interfaces.base import Bunch
	sounds, silences, keypress = parse_logfile(logfilepath)
	
	# Incorporate into design info
	conditions = ['sound', 'silence', 'keypress']
	onsets     = [[on['onset'] for on in cond] for cond in [sounds, silences, keypress]]
	durations  = [[du['duration'] for du in cond] for cond in [sounds, silences, keypress]]
	
	design_info = Bunch(conditions = conditions,
				   		onsets     = onsets,
				   		durations  = durations)
	
	return design_info