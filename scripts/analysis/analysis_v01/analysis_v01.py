#! /usr/bin/env python
# Time-stamp: <2025-04-09 m.utrosa@bcbl.eu>

# Import python packages
import os, shutil, glob
from nipype import Node
import nipype.pipeline.engine as pe         # pipeline engine
import nipype.algorithms.modelgen as model  # model specification
from nipype.interfaces import freesurfer, spm, fsl, ants, nipy, c3

# Import custom-made functions (scripts)
import objects as obj
from designs import localizer
import filter_betas as fb

# Task-Specific Parameters
subIDs   = [2]
sesIDs   = [1, 2]
acqIDs   = [
			"DresdenNoFat", "DresdenWFat", "ME1TR880", "ME3TR1600", "ME3TR1100",
			"ME3TR850", "ME3TR700", "DresdenNoFat175", "DresdenWFat175", 
			"ME1TR780", "ME3TR1180", "ME3TR770", "ME3TR680"
			]
task      = "localizer"
homePath  ='/home/mutrosa/Documents/projects/localizer_fMRI'
tmp_dir   = homePath + '/scripts/analysis/tmp'
MNI       = homePath + "/templates/mni_icbm152_t1_tal_nlin_sym_09b_hires.nii"
hrf_dervs = [0, 0]
volterra  = False
contrasts = {'localizer': [('localizer', 'T', ['sound', 'silence'], [1, -1])]}

# Preparing data and design
for subID in subIDs:
	for sesID in sesIDs:
		for acqID in acqIDs:

			objects   = obj.grab_objects(subID, sesID, acqID, homePath)
			if len(objects["preproc_bold"]) == 0:
				print(f"Skipping sub-{subID:02d} ses-{sesID:02d} acq-{acqID}: no data found.")
				continue # Skipp current inner loop iteration if no BOLD data found

			print(f"\nANALYZING: sub-{subID:02d} ses-{sesID:02d} acq-{acqID}\n")
			data      = objects["preproc_bold"][0].path
			events    = objects["logfiles"][0].path
			outliers  = objects["outliers"][0].path
			confounds = objects["confounds"][0].path
			T1w       = objects["T1w"][0].path
			#regt      = objects["toNative"][1].path # The 2nd element is from T1w to fsnative.
			warp      = objects["xfm"][1].path      # The 2nd element is from T1w to MNI.
			
			# Parse each event log into a Nipype Bunch
			design_bunch = [localizer(events)]

			# Extract repetition time with PyBIDS methods [sec]
			repetition_time = objects["preproc_bold"][0].get_metadata()['RepetitionTime']

			# Unzip nii files
			unzip = Node(freesurfer.MRIConvert(out_type='nii'), name = f'unzip_sub-{subID:02d}_acq-{acqID}')
			unzip.base_dir = tmp_dir
			unzip.inputs.in_file = data
			unzip.run()
			preprocdata = unzip.result.outputs.out_file

			# Modeler
			modeler = pe.Node(model.SpecifySPMModel(), name = f'modeler_sub-{subID:02d}_acq-{acqID}')
			modeler.base_dir 					   = tmp_dir
			modeler.inputs.concatenate_runs        = False
			modeler.inputs.input_units             = 'secs'
			modeler.inputs.output_units            = 'secs'
			modeler.inputs.time_repetition         = repetition_time
			modeler.inputs.high_pass_filter_cutoff = 128
			modeler.inputs.subject_info            = design_bunch
			modeler.inputs.functional_runs         = preprocdata
			modeler.inputs.outlier_files           = outliers
			modeler.inputs.realignment_parameters  = confounds
			modeler.run()

			# Designer
			designer = pe.Node(spm.Level1Design(), name = f'designer_sub-{subID:02d}_acq-{acqID}')
			designer.base_dir 						 = tmp_dir
			designer.inputs.bases                    = {'hrf': {'derivs': hrf_dervs}}
			designer.inputs.timing_units             = 'secs'
			designer.inputs.interscan_interval       = repetition_time
			designer.inputs.session_info             = modeler.result.outputs.session_info
			designer.inputs.volterra_expansion_order = (2 if volterra else 1)
			designer.run()

			# Estimator
			estimator = pe.Node(spm.EstimateModel(), name = f'estimator_sub-{subID:02d}_acq-{acqID}')
			estimator.base_dir 				   = tmp_dir
			estimator.inputs.estimation_method = {'Classical': 1}
			estimator.inputs.spm_mat_file      = designer.result.outputs.spm_mat_file
			estimator.run()

			# Estimator results
			beta_images_func = estimator.result.outputs.beta_images    # a list of filepaths
			residuals_func   = estimator.result.outputs.residual_image # a filepath to ResMS.nii
			spmmat           = estimator.result.outputs.spm_mat_file   # a filepath to SPM.mat
			filtered_betas_func, descriptions = fb.filter_betas(spmmat, beta_images_func)

			# descriptions = ['sound_run-01', 'silence_run-01', 'constant_run-01'] --- IS THIS CORRECT?

			# Contrast estimation
			contrastor = pe.Node(spm.EstimateContrast(), name = f'contrastor_sub-{subID:02d}_acq-{acqID}')
			contrastor.base_dir 			 = tmp_dir
			contrastor.inputs.contrasts      = contrasts["localizer"]
			contrastor.inputs.spm_mat_file   = estimator.result.outputs.spm_mat_file
			contrastor.inputs.beta_images    = estimator.result.outputs.beta_images
			contrastor.inputs.residual_image = estimator.result.outputs.residual_image
			contrastor.run()

			# Contrastor results
			con_image = contrastor.result.outputs.con_images
			t_image   = contrastor.result.outputs.spmT_images

			# For storing results in a non-temporary folder
			os.makedirs('results', exist_ok=True)

			# Move data from T1 to MNI space with ANTS	
			warper = Node(ants.ApplyTransforms(), name = f'warper_sub-{subID:02d}_acq-{acqID}')
			warper.base_dir 			         = tmp_dir
			warper.inputs.input_image_type 		 = 3
			warper.inputs.interpolation   		 = 'Linear'
			warper.inputs.invert_transform_flags = [False]  # transform flag = 0
			warper.inputs.args 					 = '--float'
			warper.inputs.transforms 			 = warp
			warper.inputs.reference_image        = MNI      # upsample to 0.4 mm
			warper.inputs.input_image 			 = t_image
			warper.run()

			# Convert to .nii.gz
			prev_out = warper.result.outputs.output_image
			zipper   = Node(freesurfer.MRIConvert(out_type='niigz'), name = f'zipper_sub-{subID:02d}_acq-{acqID}')
			zipper.base_dir       = tmp_dir
			zipper.inputs.in_file = prev_out
			zipper.run()

			# Save
			warped_file = zipper.result.outputs.out_file
			filename    = os.path.basename(warped_file).strip(".nii.gz") + f"_sub-{subID:02d}_acq-{acqID}.nii.gz"
			shutil.copy(warped_file, os.path.join('results', filename))