################################################################################
################################################################################
## Script to parallelize the parisng of FEATURE output.                       ##
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

prnt_file = file_home + 'log.txt'
cutoff_dict = {'100': 1, '99': 2, '95': 3, '90': 4, '80': 5, '70': 6, '60': 7, '50': 8, '40': 9, '30': 10, '20': 11, '10': 12, '5': 13, '1': 14, '0': 15}
job = sys.argv[1]  # this is the FEATURE output file we are analyzing
job_id = job.split('.')[0].split('Results_')[-1] # this is the run_id + pdb_id from the file name
pdb_id = job_id.split('_')[1] + '_' + job_id.split('_')[2]

########################################################################################################################
# Each instance of this script loads the mu-sigma dictionary and the threshold cutoffs and writes an entry for each
# prediction in the given FEATURE output file in each cutoff file for the appropriate model (or the target). Each
# prediction is either present at a cutoff (has a z-score higher than the threshold) or absent (has a z-score lower
# than the threshold).
########################################################################################################################

# Load mu-sigma dictionary
mu_sig_dict = {}  # {model:[mu,sigma]}
model_file = open(file_home + 'mu_sigma_table.txt', 'r')
for line in model_file:
    line = line.strip('\n').split('\t')
    model = line[0]
    mu = float(line[1])
    sigma = float(line[2])
    mu_sig_dict[model] = [mu, sigma]

# Load cutoff values
model_stat = open(file_home + 'seqfeature_cutoffs.txt', 'r')
mod = {}  # {cutoff:{FEATURE_model:value}}
for line in model_stat:
    sp = line.split('\t')
    model = sp[0]
    for cutoff in cutoff_dict:
        index = cutoff_dict[cutoff]
        try:
            mod[cutoff][model] = sp[index]
        except:
            mod[cutoff] = {model: sp[index]}
model_stat.close()

# Find Z-scores and create an entry for each prediction for each threshold
cur_file = open(foutput_home + job, 'r')
spmodel = ''
threshold_dict = {}   # {entry: {cutoff: present/absent}}
for line in cur_file:
    line = line.strip('\n')
    if line != '':
        if (line.startswith('%#') == True):
            if ('Analyzing' in line):
                spmodel = line.split()[-1]
            continue
        sp = line.split('\t')
        if sp[0].split('.')[-1] == 'model':
            model = line.rstrip('.nb.model')
        elif line.find('Env_') != -1:
            anch_res_nm = sp[-1].split(':')[0][:3]
            anch_res_pos = sp[-1].split(':')[0][3:]
            raw_score = float(sp[1])
            mu = float(mu_sig_dict[model][0])
            sigma = float(mu_sig_dict[model][1])
            z_score = ((raw_score - mu) / sigma)
            entry = pdb_id + '\t' + anch_res_nm + '_' + anch_res_pos + '\t' + spmodel + '\t' + model + '\t' + str(z_score)
            for cutoff in cutoff_dict:
                thrsh_score = mod[cutoff][model]
                if float(z_score) >= float(thrsh_score):
                    if entry in threshold_dict:
                        threshold_dict[entry].update({cutoff: 'present'})
                    else:
                        threshold_dict.update({entry: {cutoff: 'present'}})
                else:
                    if entry in threshold_dict:
                        threshold_dict[entry].update({cutoff: 'absent'})
                    else:
                        threshold_dict.update({entry: {cutoff: 'absent'}})
cur_file.close()

# Output
for cutoff in cutoff_dict:
    try:
        os.system('mkdir ' + home + 'data_by_threshold/thrsh_' + cutoff)
        os.system('mkdir ' + home + 'data_by_threshold/thrsh_' + cutoff + '/' + job_id)
    except:
        os.system('mkdir ' + home + 'data_by_threshold/thrsh_' + cutoff + '/' + job_id)
    for entry in threshold_dict:
        spmodel = entry.split('\t')[2]
        try:
            thrsh_file = open(home + 'data_by_threshold/thrsh_' + cutoff + '/' + job_id + '/' + spmodel + '.txt', 'a')
            thrsh_file.write(entry + '\t' + threshold_dict[entry][cutoff] + '\n')
            thrsh_file.close()
        except:
            thrsh_file = open(home + 'data_by_threshold/thrsh_' + cutoff + '/' + job_id + '/' + spmodel + '.txt', 'w')
            thrsh_file.write(entry + '\t' + threshold_dict[entry][cutoff] + '\n')
            thrsh_file.close()