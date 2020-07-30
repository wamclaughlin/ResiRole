##############################################################################
##############################################################################
## Script that organizes and runs all newly downloaded data through FEATURE.##
##                                                                          ##
## Created by Joshua Toth, June 2019                                        ##
##############################################################################
##############################################################################
'''
ResiRole, a program for the assessment of structural models according to the similarity of functional site predictions

between the structure model and reference structure.


Copyright (C) 2020  Joshua Toth, Paul DePietro, Juergan Haas, and William McLaughlin


This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public

License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later

version.


This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied

warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.


You should have received a copy of the GNU General Public License along with this program.  If not, see

<http://www.gnu.org/licenses/>. If not, register with ResiRole forum at the URL

protein.som.geisinger.edu/ResiRole/forum.jsp
'''

import os, sys, time, datetime

run_id = str(sys.argv[1])

home = '' # Your home directory
file_home = home + 'files/'
scripts_home = home + 'scripts/'
feature_home = home + 'FEATURE/'
foutput_home = home + 'raw_output/'
data_home = home + 'jobs/'
output_home = home + 'output/'

python_path = '/usr/bin/python2.7'

prnt_file = file_home + 'log.txt'

os.system('echo Performing FEATURE run for job ' + run_id + ' . >> ' + prnt_file)

# Set environmental variables required by FEATURE. Note the PATH variable should include your standard bin.
os.environ['FEATURE_DIR'] = 'Pipeline/FEATURE/feature-3.0.0/src'
os.environ['PATH'] = 'Pipeline/FEATURE/feature-3.0.0/src:Pipeline/FEATURE/feature-3.0.0/tools/bin:/bin'
os.environ['PYTHONPATH'] = 'Pipeline/FEATURE/feature-3.0.0/tools/lib'
os.environ['DSSP_DIR'] = 'Pipeline/FEATURE/DSSP'
os.environ['PDB_DIR'] = 'Pipeline/FEATURE/PDB'

dir = data_home + run_id + '/'

for targ_file in os.listdir(dir + 'targets/'):

    # Setup - run each structure through dssp and copy files to appropriate directories
    mod_set = []
    pdb_id = str(targ_file).split('.')[0]
    pdb_id_short = pdb_id.split('_')[0].lower()
    run_id2 = run_id + '_' + pdb_id
    os.system(feature_home + 'dsspcmbi ' + dir + 'targets/' + targ_file + ' > ' + dir + 'targets/' + pdb_id + '.dssp')
    for mod_file in os.listdir(dir + 'models/'):
        if pdb_id in str(mod_file):
            mod_set.append(str(mod_file.split('.')[0]))
            os.system(feature_home + 'dsspcmbi ' + dir + 'models/' + mod_file + ' > ' + dir + 'models/' + str(mod_file.split('.')[0]) + '.dssp')

    out_file = foutput_home + 'FeatResults_' + run_id2 + '.txt'
    os.system('echo %# Analysis of ' + pdb_id + ' > ' + out_file)
    for pmp_model in mod_set:
        os.system('echo %# Analyzing ' + pmp_model + ' >> ' + out_file)
        os.system('cp -p ' + dir + 'models/' + pmp_model + '.pdb ' + feature_home + 'PDB/pdb' + pdb_id_short + '.ent') # Is this right?
        os.system('cp -p ' + dir + 'models/' + pmp_model + '.dssp ' + feature_home + 'DSSP/' + pdb_id_short + '.dssp')
        if not os.path.isdir(feature_home + 'run_files/' + run_id2 + '/'):
            os.system('mkdir ' + feature_home + 'run_files/' + run_id2 + '/')
        os.system('mkdir ' + feature_home + 'run_files/' + run_id2 + '/' + pmp_model + '/')
        envs_list = os.listdir(feature_home + 'FEATURE_prediction_models/')

        # FEATURE run for each structure prediction model
        for model in envs_list:
            if model.find('model') != -1 and model[0] != '.':
                sp = model.split('.')
                atom = sp[-3]
                residue = sp[-4]
                try:
                    os.system('mkdir ' + feature_home + 'run_files/' + run_id2 + '/' + pmp_model + '/' + model + '/')
                    os.system('mkdir ' + feature_home + 'run_files/' + run_id2 + '/' + pmp_model + '/' + model + '/backup_hits/')
                    # run atomselector
                    os.system(python_path + ' Pipeline/FEATURE/feature-3.0.0/tools/bin/atomselector.py -r ' + residue + ' -a ' + atom + ' ' + pdb_id_short + ' > ' + feature_home + 'run_files/' + run_id2 + '/' + pmp_model + '/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.ptf')
                    # run featurize
                    os.system('featurize -P ' + feature_home + 'run_files/' + run_id2 + '/' + pmp_model + '/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.ptf >' + feature_home + 'run_files/' + run_id2 + '/' + pmp_model + '/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.ff')
                    # run scoreit
                    os.system('scoreit -a ' + feature_home + 'FEATURE_prediction_models/' + model + ' ' + feature_home + 'run_files/' + run_id2 + '/' + pmp_model + '/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.ff' + ' > ' + feature_home + 'run_files/' + run_id2 + '/' + pmp_model + '/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.hits')
                    os.system('sort -k2 -n -r ' + feature_home + 'run_files/' + run_id2 + '/' + pmp_model + '/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.hits > ' + feature_home + 'run_files/' + run_id2 + '/' + pmp_model + '/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.hits.sorted')
                    # gather, backup, and print all output
                    os.system('echo \"' + model + '\" >> ' + out_file)
                    os.system('cp -p ' + feature_home + 'run_files/' + run_id2 + '/' + pmp_model + '/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.hits.sorted ' + feature_home + 'run_files/' + run_id2 + '/' + pmp_model + '/' + model + '/backup_hits/' + pdb_id_short + '_' + residue + '_' + atom + '.hits.sorted')
                    # files are concatenated to the out_file
                    os.system('cat ' + feature_home + 'run_files/' + run_id2 + '/' + pmp_model + '/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.hits.sorted >> ' + out_file)
                except:
                    os.system('echo ' + pmp_model + ' ' + model + ' had an error... >> ' + prnt_file)

        # cleanup - optional
        #os.system('rm ' + feature_home + 'PDB/pdb' + pdb_id_short + '.ent')  # cleanup
        #os.system('rm ' + feature_home + 'DSSP/' + pdb_id_short + '.dssp')

    # FEATURE run for target
    os.system('echo %# Analyzing ' + pdb_id + '_target >> ' + out_file)
    os.system('cp -p ' + dir + 'targets/' + pdb_id + '.pdb ' + feature_home + 'PDB/pdb' + pdb_id_short + '.ent')  # Is this right?
    os.system('cp -p ' + dir + 'targets/' + pdb_id + '.dssp ' + feature_home + 'DSSP/' + pdb_id_short + '.dssp')
    os.system('mkdir ' + feature_home + 'run_files/' + run_id2 + '/target/')

    envs_list = os.listdir(feature_home + 'FEATURE_prediction_models/')
    for model in envs_list:
        if model.find('model') != -1 and model[0] != '.':
            sp = model.split('.')
            atom = sp[-3]
            residue = sp[-4]
            try:
                os.system('mkdir ' + feature_home + 'run_files/' + run_id2 + '/target/' + model + '/')
                os.system('mkdir ' + feature_home + 'run_files/' + run_id2 + '/target/' + model + '/backup_hits/')
                # run atomselector
                os.system(python_path + ' Pipeline/FEATURE/feature-3.0.0/tools/bin/atomselector.py -r ' + residue + ' -a ' + atom + ' ' + pdb_id_short + ' > ' + feature_home + 'run_files/' + run_id2 + '/target/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.ptf')
                # run featurize
                os.system('featurize -P ' + feature_home + 'run_files/' + run_id2 + '/target/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.ptf >' + feature_home + 'run_files/' + run_id2 + '/target/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.ff')
                # run scoreit
                os.system('scoreit -a ' + feature_home + 'FEATURE_prediction_models/' + model + ' ' + feature_home + 'run_files/' + run_id2 + '/target/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.ff' + ' > ' + feature_home + 'run_files/' + run_id2 + '/target/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.hits')
                os.system('sort -k2 -n -r ' + feature_home + 'run_files/' + run_id2 + '/target/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.hits > ' + feature_home + 'run_files/' + run_id2 + '/target/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.hits.sorted')
                # gather and concatenate output, then delete repetitive intermediate files
                os.system('echo \"' + model + '\" >> ' + out_file)
                os.system('cat ' + feature_home + 'run_files/' + run_id2 + '/target/' + model + '/' + pdb_id_short + '_' + residue + '_' + atom + '.hits.sorted >> ' + out_file)
            except:
                os.system('echo target had an error... >> ' + prnt_file)

    #os.system('rm ' + feature_home + 'PDB/pdb' + pdb_id_short + '.ent')  # cleanup
    #os.system('rm ' + feature_home + 'DSSP/' + pdb_id_short + '.dssp')

os.system('echo FEATURE run complete at ' + str(time.strftime('%H:%M:%S', time.localtime())) + ' >> ' + prnt_file)

########################################################################################################################
# Notes:
# - FEATURE program version 3.0.0 used. (Halperin, I., et al. The FEATURE framework for protein function annotation:
# modeling new functions, improving performance, and extending to novel applications. BMC Genomics 2008;9 Suppl 2:S2.)
# - As currently setup, FEATURE scores all possible residues in a structure against all possible SeqFEATURE models.
# - There are different run options available, see the FEATURE reference manual.
# - SeqFEATURE models: (Wu, S., Liang, M.P. and Altman, R.B. The SeqFEATURE library of 3D functional site models:
# comparison to existing methods and applications to protein function annotation. Genome biology 2008;9(1):1.)
