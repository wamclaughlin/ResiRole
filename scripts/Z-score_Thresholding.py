################################################################################
################################################################################
## Script that converts raw data to Z-scores and thresholds them accordingly. ##
##                                                                            ##
## Created by Joshua Toth, June 2019                                          ##
################################################################################
################################################################################
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

import os, sys, time, datetime, string, commands, subprocess, math, pickle, shelve, shutil

home = '' # Your home directory
file_home = home + 'files/'
scripts_home = home + 'scripts/'
feature_home = home + 'FEATURE/'
foutput_home = feature_home + 'raw_output/'

python_path = '/usr/bin/python2.7'

prnt_file = file_home + 'log.txt'

run_id = str(sys.argv[1])

########################################################################################################################
# Note: Z-score thresholding requires the collection of a large amount of function prediction instances from which to
# generate accurate mu and sigma values to be used in converting raw scores to z-scores. Ideally, these values would be
# from a database including as many structures as possible, such as all targets listed on the PDB. In our main study
# performed with ResiRole, we compiled resulting values from all structures released on the PDB from 2014-2018 and used
# mu and sigma values generated from these to convert raw scores. These same mu and sigma values are included with these
# programs in the file mu_sigma_table.txt. During automated updates of the ResiRole server, these values are continually
# updated as scores from newly released structures are generated. Additionally, thresholding is performed using values
# obtained in a benchmarking study (Buturovic, L., et al. High precision prediction of functional sites in protein
# structures. PloS one 2014;9(3):e91240.) included in the file seqfeature_cutoffs.txt.
#
########################################################################################################################
os.system('echo Converting and thresholding Z-scores for ' + run_id + ' . >> ' + prnt_file)

Fout_list = os.listdir(foutput_home)
# Local run to parse each output file.

for each in Fout_list:
    if run_id in str(each):
        os.system(python_path + ' ' + scripts_home + '/Sub_Parse_FEATURE_output.py ' + each)
