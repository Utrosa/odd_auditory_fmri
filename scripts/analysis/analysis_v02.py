#! /usr/bin/env python
# Time-stamp: <2025-04-09 m.utrosa@bcbl.eu>

# Import python packages
from nipype import Node, Workflow, IdentityInterface, Function
import nipype.algorithms.modelgen as model
from nipype.interfaces import freesurfer, spm, ants
from nipype.interfaces.io import DataSink

# Import custom-made functions (scripts)
import grabber
from objects_v02 import grab_objects
from designs_v02 import localizer

# -------------------------------------------------------------------------------------------------
# 00. Experiment Parameters
# -------------------------------------------------------------------------------------------------
sub_list   = [4]
ses_list   = [2]

# For sub-01
# acqID_list = ["DresdenNoFat", "DresdenWFat", "ME1TR880", "ME3TR1600", "ME3TR1100", "ME3TR850", "ME3TR700"]

# For sub-02
# acqID_list = ["DresdenNoFat", "DresdenWFat", "ME1TR880", "ME3TR1600"]

# For sub-03
# acqID_list = ["DresdenNoFat", "DresdenWFat", "ME1TR880", "ME3TR1600", "ME3TR1100", "ME3TR850", "ME3TR700"]
# acqID_list = ["DresdenNoFat175", "DresdenWFat175", "ME1TR780", "ME3TR1180", "ME3TR770", "ME3TR680"]

# For sub-04
# acqID_list = ["DresdenNoFat", "DresdenWFat", "ME1TR880"]
acqID_list = ["ME3TR1600", "ME3TR1100", "ME3TR850", "ME3TR700", "DresdenNoFat175", "DresdenWFat175",
  			  "ME1TR780", "ME3TR1180", "ME3TR770", "ME3TR680"]

homePath   = '/home/mutrosa/Documents/projects/localizer_fMRI'
tmp_dir    = homePath + '/scripts/analysis/tmp'
out_dir    = homePath + "/results"
hrf_dervs  = [0, 0] # using the canonical hrf (without derivatives)
volterra   = False
contrasts  = [('localizer', 'T', ['sound', 'silence'], [1, -1])]
MNI        = homePath + "/templates/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz" # the same as in fMRIprep !

# -------------------------------------------------------------------------------------------------
# 01. Specify Nodes
# -------------------------------------------------------------------------------------------------
# Infosource: set up a function-free node to iterate over the list of acquisition names.
# The Identity Interface allows to create Nodes that only work with strings (parameters)!
infosource = Node(IdentityInterface(fields = ['subID', 'sesID', 'acqID']),
				  name = "infosource")
infosource.iterables = [('subID', sub_list),
						('sesID', ses_list),
						('acqID', acqID_list)]

# Datasink: create output folder for important outputs
datasink = Node(DataSink(base_directory = tmp_dir,
                         container = out_dir),
                name = "datasink")

# Output substitutions: correct Datasink output folder structure
substitutions = []
subjFolders = [('_acqID_%s_sesID_%s_subID_%s' % (acq, ses, sub),
				'sub-0%s/ses-0%s/acq-%s' % (sub, ses, acq))
               for acq in acqID_list
               for ses in ses_list
               for sub in sub_list]
substitutions.extend(subjFolders)
datasink.inputs.substitutions = substitutions

# Define a Node that extracts filepaths for all files required for the analysis.
infohandle = Node(Function(input_names  = ["subID", "sesID", "acqID", "homePath"],
						   output_names = ["log_path", "bold_path", "mask_path", "conf_path", "out_path", "T1w_path", "T1w_toMNI_path", "fsNative_toT1w_path", "TR"], 
						   function = grab_objects),
				name = "infohandle")
infohandle.inputs.homePath = homePath

# Extract information needed to specify a model in the form of a Bunch object.
# Provide info for the Bunch through parsing the event files.
design_bunch = Node(Function(input_names  = ["logfilepath"],
							 output_names = ["design_info"],
							 function = localizer),
					name = "design_bunch")

# Unzip funcional image (preprocessed BOLD).
unzip = Node(freesurfer.MRIConvert(out_type = 'nii'),
			 name = 'unzip')

# SpecifyModel: generate SPM-specific godel.
modeler = Node(model.SpecifySPMModel(concatenate_runs = False,
									 input_units  = 'secs',
									 output_units = 'secs',
									 high_pass_filter_cutoff = 128),
			   name = 'modeler')

# Level1Design: generate an SPM design matrix.
designer = Node(spm.Level1Design(bases = {'hrf': {'derivs': hrf_dervs}},
								 timing_units = 'secs',
								 volterra_expansion_order = (2 if volterra else 1)),
				name = 'designer')

# Estimate Model: estimate the parameters of the model.
estimator = Node(spm.EstimateModel(estimation_method = {'Classical': 1}),
				 name = 'estimator')

# Contrast Estimation
contrastor = Node(spm.EstimateContrast(contrasts = contrasts),
				  name = 'contrastor')

# Move data from T1 to MNI space with ANTS.
warper = Node(ants.ApplyTransforms(reference_image = MNI,
								   dimension = 3,
								   interpolation = 'Linear',
								   invert_transform_flags = [False], # transform flag = 0
								   args = '--float'),
			 name = 'warper')

# Convert to .nii.gz
zipper = Node(freesurfer.MRIConvert(out_type='niigz'), name = 'zipper')

# -------------------------------------------------------------------------------------------------
# 02. Connect the Nodes
# -------------------------------------------------------------------------------------------------
l1_localizer = Workflow(name = "l1_localizer")
l1_localizer.base_dir = tmp_dir
l1_localizer.connect([(infosource, infohandle, [("subID", "subID"),
												("sesID", "sesID"),
												("acqID", "acqID")])])
l1_localizer.connect([(infohandle, design_bunch, [("log_path", "logfilepath")])])
l1_localizer.connect([(infohandle, unzip, [("bold_path", "in_file")])])
l1_localizer.connect([
				(unzip, modeler, [("out_file", "functional_runs")]),
				(infohandle, modeler, [("out_path", "outlier_files"),
									   ("conf_path", "realignment_parameters")]),
				(design_bunch, modeler, [("design_info", "subject_info")]),
				(infohandle, modeler, [("TR", "time_repetition")])
				])
l1_localizer.connect([
				(modeler, designer, [("session_info", "session_info")]),
				(infohandle, designer, [("TR", "interscan_interval")])
				])
l1_localizer.connect([
				(designer, estimator, [("spm_mat_file", "spm_mat_file")])
				])
l1_localizer.connect([
				(estimator, contrastor, [("spm_mat_file", "spm_mat_file")]),
				(estimator, contrastor, [("beta_images", "beta_images")]),
				(estimator, contrastor, [("residual_image", "residual_image")]),
				])
l1_localizer.connect([
				(infohandle, warper, [("T1w_toMNI_path", "transforms")]),
				(contrastor, warper, [("spmT_images", "input_image")])
				])
l1_localizer.connect([
				(warper, zipper, [("output_image", "in_file")])
				])
l1_localizer.connect([
				(contrastor, datasink, [('spm_mat_file', '1stLevel.@spm_mat'),
                                        ('spmT_images', '1stLevel.@T'),
                                        ('con_images', '1stLevel.@con')])
				])
l1_localizer.connect([
				(zipper, datasink, [('out_file', '1stLevel.@T_warped')])
				])

# -------------------------------------------------------------------------------------------------
# 03. Visualize the Workflow
# -------------------------------------------------------------------------------------------------
l1_localizer.write_graph(graph2use = 'colored', format = 'png', simple_form = True)

# -------------------------------------------------------------------------------------------------
# 04. Run the Workflow
# -------------------------------------------------------------------------------------------------
res = l1_localizer.run()