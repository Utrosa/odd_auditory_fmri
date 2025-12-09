import os, pydicom

# Specify project-specific info
sub = 1
ses = 1
pro = "SubCort_HighRes"

# Get directories and files
homeDir   = "/home/mutrosa/Documents/projects/select_fMRI/"
dicomFold = f"data_MRI/sourcedata/dicoms/sub-{sub:02d}_ses-{ses:02d}_{pro}/"

# DERIVATIVES WITH HORIZONTAL FMAP REGISTRATION -------------------------------
# seqFold   = "ME1_1.5mm_SMS2_TR880_28"  #ses-01
# seqFold   = "FH_ME1_1.5mm_SMS2_TR880_SBRef_35"  #ses-01
# seqFold   = "FH_ME1_1.5mm_SMS2_TR880_SBRef_Pha_36"  #ses-01

# seqFold = "ME1_1.75mm_SMS2_TR780_19" #ses-03
# seqFold = "FH_ME1_1.75mm_SMS2_TR780_SBRef_27" #ses-03 run-02
# seqFold = "FH_ME1_1.75mm_SMS2_TR780_SBRef_23" #ses-03 run-01
# seqFold = "FH_ME1_1.75mm_SMS2_TR780_SBRef_Pha_28" #ses-03 run-02
# seqFold = "FH_ME1_1.75mm_SMS2_TR780_SBRef_Pha_24" #ses-03 run-01

# seqFold = "ME3_1.75mm_SMS4_TR680_65" #ses-03
# seqFold = "FH_ME3_1.75mm_SMS4_TR680_SBRef_73" #ses-03 run-02
# seqFold = "FH_ME3_1.75mm_SMS4_TR680_SBRef_69" #ses-03 run-01
# seqFold = "FH_ME3_1.75mm_SMS4_TR680_SBRef_Pha_74" #ses-03 run-02
# seqFold = "FH_ME3_1.75mm_SMS4_TR680_SBRef_Pha_70" #ses-03 run-01

# DERIVATIVES WITH VERTICAL FMAP REGISTRATION ---------------------------------
# Dresden sequences have no phase reconstruction but the error is still there.
# seqFold   = "Dresden_1.5mm_SMS1_TR2100_noFatSat_12"  #ses-01
# seqFold   = "FH_Dresden_1.5mm_SMS1_TR2100_noFatSat_16"  #ses-01

# seqFold   = "Dresden_1.5mm_SMS1_TR2400_wFatSat_17"  #ses-01
# seqFold   = "FH_Dresden_1.5mm_SMS1_TR2400_wFatSat_24"  #ses-01

# The first sequence I got two FOVs for
# seqFold = "FH_ME3_SMS2_1.5mm_TR1600_SBRef_54" #ses-01 run-02
# seqFold = "FH_ME3_SMS2_1.5mm_TR1600_SBRef_49" #ses-01 run-01
# seqFold = "FH_ME3_SMS2_1.5mm_TR1600_SBRef_Pha_55" #ses-01 run-02
# seqFold = "FH_ME3_SMS2_1.5mm_TR1600_SBRef_Pha_50" #ses-01 run-01

## I NEED TO CHECK FMAPS NOT FH LOLOLO !!!
# seqFold="SE_AP_ME1_1.5mm_SMS2_TR880_31"
# seqFold="SE_PA_ME1_1.5mm_SMS2_TR880_33"
dicom_folder = homeDir+dicomFold+seqFold
print(dicom_folder)

## ----------------- Phase Encoding Direction ---------------------------------
files = [os.path.join(dicom_folder, f) for f in os.listdir(dicom_folder)]
for df in files:
	dicom_file = df
	ds = pydicom.dcmread(dicom_file, stop_before_pixels=True)

	# Find the PED in the header dataset
	shared_func_seq = ds.get((0x5200, 0x9229), None)
	if shared_func_seq:
	    for item in shared_func_seq:

	        # MR FOV/Geometry Sequence
	        fov_seq = item.get((0x0018, 0x9125), None)
	        if fov_seq:
	            for fov_item in fov_seq:
	                ped = fov_item.get((0x0018, 0x1312), None)
	                if ped:
	                    print("In-plane Phase Encoding Direction:", ped.value)

## ----------- RepetitionTimePreparation for anatomical scans ------------------

# seqFold = "t1_mp2rage_sag_p3_1iso_INV1_5"
# # seqFold = "t1_mp2rage_sag_p3_1iso_INV2_6"

# dicom_folder = homeDir+dicomFold+seqFold
# files = [os.path.join(dicom_folder, f) for f in os.listdir(dicom_folder)]
# for df in files:
# 	dicom_file = df
# 	ds = pydicom.dcmread(dicom_file, stop_before_pixels=True)

# 	# Find the RTE in the header dataset
# 	shared_func_seq = ds.get((0x5200, 0x9229), None)
# 	if shared_func_seq:
# 		for item in shared_func_seq:

# 			# MR Timing and Related Parameters Sequence
# 			timing_seq = item.get((0x0018, 0x9112), None)

# 			if timing_seq:
# 				for item in timing_seq:
# 					rtp = item.get((0x0018, 0x0080), None)
# 					print("RepetitionTimePreparation:", rtp.value)