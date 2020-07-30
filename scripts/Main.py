###########################################################################
###########################################################################
## Main script to showcase the basic ResiRole pipeline.                  ##
##                                                                       ##
## Created by Joshua Toth, June 2020                                     ##
###########################################################################
###########################################################################
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

import os, sys, time, datetime, random

home = '' # Your home directory
file_home = home + 'files/'
scripts_home = home + 'scripts/'
download_home = home + 'quality_estimation/2020.07.18/' # path to your downloaded data. Currently specified is the example data
data_home = home + 'jobs/'

python_path = '/usr/bin/python2.7' # path to your python. The version of FEATURE employed was built in python2.7. It may run in newer versions.

prnt_file = file_home + 'log.txt'

# Basic ResiRole pipeline
########################################################################################################################

# Assign a unique, random run id to the job
run_id = str(random.randint(1, 1000))

while os.path.isdir(data_home + run_id):
    run_id = str(random.randint(1, 1000))

os.system('echo Beginning ' + run_id + ' analysis. Time: ' + str(time.strftime('%H:%M:%S', time.localtime())) + ' >> ' + prnt_file)

# move and appropriately rename downloaded files
os.system('mkdir ' + data_home + run_id)
os.system('mkdir ' + data_home + run_id + '/targets')
os.system('mkdir ' + data_home + run_id + '/models')
for strucdir in os.listdir(download_home):
    pdb_id = str(strucdir).split('_')[0] + '_' + str(strucdir).split('_')[1]
    modelnum = str(strucdir).split('_')[2]
    os.system('mv ' + download_home + strucdir + '/model.pdb ' + data_home + run_id + '/models/' + pdb_id + '_model-' + modelnum + '.pdb')
    os.system('mv ' + download_home + strucdir + '/target.pdb ' + data_home + run_id + '/targets/' + pdb_id + '.pdb')

##############################################
# Run all models and targets through FEATURE #
##############################################

os.system(python_path + ' ' + scripts_home + 'Run_Feature.py ' + run_id)

###################################################################
# Assign Z-scores and parse data into thresholds based on Z-score #
###################################################################

os.system(python_path + ' ' + scripts_home + 'Z-score_Thresholding.py ' + run_id)

############################################################################
# Perform ROC study of the data to determine optimum specificity threshold #
############################################################################

os.system(python_path + ' ' + scripts_home + 'ROC_Analysis.py ' + run_id)

#######################################################################################################################
# Calculate difference scores and model/target correlation coefficients for models using the optimum cutoff threshold #
#######################################################################################################################

os.system(python_path + ' ' + scripts_home + 'Z-Score_Analysis.py ' + run_id)

os.system('echo Analysis of job ' + run_id + ' complete. Time: ' + str(time.strftime('%H:%M:%S', time.localtime())) + ' >> ' + prnt_file)
########################################################################################################################