import bioread, glob, os, shutil

# Ensure that you have all the BIDS-compliant folders, ... run this command only once!!
os.system("dcm2bids_scaffold")


# 1. Adjust parameters for your subject/session
# Activate the correct conda environment: conda activate dcm2bids
subID    = "JGG"      # Subject ID (uppercase letters)
sesID    = 1          # Session number (e.g.: 00, 01, or 02)
project  = "SUBCORT_HIGHRES"
homePath = '/home/mutrosa/Documents/projects/localizer_fMRI'

# 2. Generate sidecar files, which contain information needed for setting up conf.json correctly
helper_command =  f"dcm2bids_helper -d {homePath}/rawData/MRI_raw/{sesID:02d}_{project}_{subID} " # DICOM directory(ies) or archive(s)
helper_command += f"-o {homePath}/preproc_data/sidecars/sub-{subID}/ses-{sesID:02d}" 			  # Output directory
os.system(helper_command)