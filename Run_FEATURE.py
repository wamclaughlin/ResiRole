###########################################################################
###########################################################################
## Run script for FEATURE, designed to work with qsubs.			         ##
##                                                                       ##
## Created by Joshua Toth, June 2019                                     ##
###########################################################################
###########################################################################

import os,sys,time

home = '/home/jtoth/ResiRole/'
file_home = home + 'files/'
scripts_home = home + 'scripts/'
feature_home = home + 'FEATURE/'
data_home = home + 'data_by_week/quality_estimation'
QSUB_home = feature_home + 'QSUB_scripts/'
foutput_home = feature_home + 'raw_output/'
pred_models_home = '/export2/home/jtoth/ResiRole/FEATURE/FEATURE_prediction_models/'
pdb_home = feature_home + 'PDB/'
dssp_home = feature_home + 'DSSP/'

########################################################################################################################
# Runs all functional prediction models on all residues in the model or target structure specified. To work properly,
# FEATURE needs to see the .pdb/.ent and .dssp files in the directories specified by the path variables in the qsub
# shell scripts, as well as have a matching lowercase pdb id given to it. This program is designed to handle one model
# or target of one pdb id + chain combination at a time and then delete the .ent and .dssp files for the previous run.
# However, output for everything can be found in FEATURE/raw_output and the intermediate files in FEATURE/run_files.
########################################################################################################################

pdb_id = sys.argv[1]
id_file = open(feature_home + 'struc_dirs/' + pdb_id.upper() + '/' + pdb_id.upper() + '_summary.txt', 'r')

for line in id_file:
	line = line.strip('\n').split('\t')
	chain = line[2]
	model_set = set(line[-1].split(','))
	struc = pdb_id.upper() + '_' + chain
	out_file = foutput_home + 'PMP_qe_' + pdb_id + '_' + chain + '.txt'

	os.system('echo %# Analysis of ' + struc + ' >> ' + out_file)

	for pmp_model in model_set:
		# Setup
		os.system('echo %# Analyzing ' + pmp_model + ' >> ' + out_file)
		print 'Analyzing PMP model ' + pmp_model
		os.system('cp -p ' + feature_home + 'struc_dirs/' + pdb_id.upper() + '/' + chain + '/' + pmp_model + '.pdb ' + feature_home + 'PDB/pdb' + pdb_id + '.ent')
		os.system('cp -p ' + feature_home + 'struc_dirs/' + pdb_id.upper() + '/' + chain + '/' + pmp_model + '.dssp ' + feature_home + 'DSSP/' + pdb_id + '.dssp')
		if not os.path.isdir(feature_home + 'run_files/' + struc + '/'):
			os.system('mkdir ' + feature_home + 'run_files/' + struc + '/')
		os.system('mkdir ' + feature_home + 'run_files/' + struc + '/' + pmp_model + '/')
		envs_list = os.listdir(pred_models_home)

		# FEATURE run for each structural prediction model
		for model in envs_list:
			if model.find('model') != -1 and model[0] != '.':
				sp = model.split('.')
				atom = sp[-3]
				residue = sp[-4]
				try:
					os.system('mkdir ' + feature_home + 'run_files/' + struc + '/' + pmp_model + '/' + model + '/')
					os.system('mkdir ' + feature_home + 'run_files/' + struc + '/' + pmp_model + '/' + model + '/backup_hits/')
					#print 'running atomselector...'
					os.system('atomselector.py -r ' + residue + ' -a ' + atom + ' ' + pdb_id + ' > ' + feature_home + 'run_files/' + struc + '/' + pmp_model + '/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.ptf')
					#print 'running featurize...'
					os.system('featurize -P ' + feature_home + 'run_files/' + struc + '/' + pmp_model + '/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.ptf >' + feature_home + 'run_files/' + struc + '/' + pmp_model + '/' + model + '/' + pdb_id + '_'+ residue + '_' + atom + '.ff')
					#print 'running scoreit...'
					os.system('scoreit -a ' + pred_models_home + model + ' ' + feature_home + 'run_files/' + struc + '/' + pmp_model + '/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.ff' + ' > ' + feature_home + 'run_files/' + struc + '/' + pmp_model + '/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.hits')
					os.system('sort -k2 -n -r ' + feature_home + 'run_files/' + struc + '/' + pmp_model + '/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.hits > ' + feature_home + 'run_files/' + struc + '/' + pmp_model + '/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.hits.sorted')
					#gather, backup, and print all output
					os.system('echo \"' + model + '\" >> ' + out_file)
					os.system('cp -p ' + feature_home + 'run_files/' + struc + '/' + pmp_model + '/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.hits.sorted ' + feature_home + 'run_files/' + struc + '/' + pmp_model + '/' + model + '/backup_hits/' + pdb_id + '_' + residue + '_' + atom + '.hits.sorted')
					os.system('cat ' + feature_home + 'run_files/' + struc + '/' + pmp_model + '/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.hits.sorted >> ' + out_file)
				except:
					print pmp_model + ' ' + model, ' had an error...'

		#cleanup
		os.system('rm ' + pdb_home + 'pdb' + pdb_id + '.ent')		#cleanup
		os.system('rm ' + dssp_home + pdb_id + '.dssp')

	# Target is handled as its own instance of a PMP model
	os.system('echo %# Analyzing target >> ' + out_file)
	print 'Analyzing target...'
	os.system('cp -p ' + feature_home + 'struc_dirs/' + pdb_id.upper() + '/' + chain + '/target.pdb ' + feature_home + 'PDB/pdb' + pdb_id + '.ent')
	os.system('cp -p ' + feature_home + 'struc_dirs/' + pdb_id.upper() + '/' + chain + '/target.dssp ' + feature_home + 'DSSP/' + pdb_id + '.dssp')
	os.system('mkdir ' + feature_home + 'run_files/' + struc + '/target/')

	envs_list = os.listdir(pred_models_home)
	for model in envs_list:
		if model.find('model') != -1 and model[0] != '.':
			sp = model.split('.')
			atom = sp[-3]
			residue = sp[-4]
			try:
				os.system('mkdir ' + feature_home + 'run_files/' + struc + '/target/' + model + '/')
				os.system('mkdir ' + feature_home + 'run_files/' + struc + '/target/' + model + '/backup_hits/')
				# run atomselector
				os.system('atomselector.py -r ' + residue + ' -a ' + atom + ' ' + pdb_id + ' > ' + feature_home + 'run_files/' + struc + '/target/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.ptf')
				# run featurize
				os.system('featurize -P ' + feature_home + 'run_files/' + struc + '/target/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.ptf >' + feature_home + 'run_files/' + struc + '/target/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.ff')
				# run scoreit
				os.system('scoreit -a ' + pred_models_home + model + ' ' + feature_home + 'run_files/' + struc + '/target/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.ff' + ' > ' + feature_home + 'run_files/' + struc + '/target/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.hits')
				os.system('sort -k2 -n -r ' + feature_home + 'run_files/' + struc + '/target/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.hits > ' + feature_home + 'run_files/' + struc + '/target/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.hits.sorted')
				# gather and concatenate output, then delete repetitive intermediate files
				os.system('echo \"' + model + '\" >> ' + out_file)
				os.system('cat ' + feature_home + 'run_files/' + struc + '/target/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.hits.sorted >> ' + out_file)
				os.chdir(feature_home + 'run_files/' + struc + '/target/' + model + '/')
				os.system('rm ' + feature_home + 'run_files/' + struc + '/target/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.hits')
				os.system('rm ' + feature_home + 'run_files/' + struc + '/target/' + model + '/' + pdb_id + '_' + residue + '_' + atom + '.hits.sorted')
			except:
				print 'target had an error...'

	print 'Done. FEATURE successfully run on ' + struc