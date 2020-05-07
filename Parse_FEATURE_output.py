################################################################################
################################################################################
## Script to parallelize the parisng of FEATURE output.                       ##
##                                                                            ##
## Created by Joshua Toth, June 2019                                          ##
################################################################################
################################################################################

import os, sys, time, datetime, string, commands, subprocess, math, pickle, shelve, shutil

home = '/home/jtoth/ResiRole/'
file_home = home + 'files/'
scripts_home = home + 'scripts/'
feature_home = home + 'FEATURE/'
download_home = home + 'data_by_week/'
data_home = download_home + 'quality_estimation/'
QSUB_home = home + 'QSUB_scripts/'
output_home = '/home/jtoth/For_Display/'
foutput_home = feature_home + 'raw_output/'

prnt_file = file_home + 'Pipeline_prints.txt'
cutoff_dict = {'100': 1, '99': 2, '95': 3, '90': 4, '80': 5, '70': 6, '60': 7, '50': 8, '40': 9, '30': 10, '20': 11, '10': 12, '5': 13, '1': 14, '0': 15}
job = sys.argv[1]  # this is the FEATURE output file we are analyzing

########################################################################################################################
# Each instance of this script loads the mu-sigma dictionary and the threshold cutoffs and writes an entry for each
# prediction in the given FEATURE output file in each cutoff file for the appropriate server. Each prediction is either
# present at a cutoff (has a z-score higher than the threshold) or absent (has a z-score lower than the threshold). The
# output from here goes into /data_by_threshold/ before it is transfered to the For_CAMEO directory.
########################################################################################################################

struc = job.split('.')[0].split('PMP_qe_')[-1]

# Load mu-sigma dictionary
mu_sig_dict = {}  # {model:[mu,sigma]}
model_file = open(file_home + 'mu_sigma_maker.txt', 'r')
for line in model_file:
    line = line.strip('\n').split('\t')
    model = line[0]
    mu = float(line[1])
    sigma = float(line[2])
    mu_sig_dict[model] = [mu, sigma]

# Load cutoff values
model_stat = open(file_home + 'seqfeature_cutoffs_new.txt', 'r')
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
server = ''
threshold_dict = {}   # {entry: {cutoff: present/absent}}
for line in cur_file:
    line = line.strip('\n')
    if line != '':
        if (line.startswith('%#') == True):
            if ('Analyzing' in line):
                server = line.split()[-1]
            continue
        sp = line.split('\t')
        if sp[0].split('.')[-1] == 'model':
            model = line.rstrip('.nb.model')
        elif line.find('Env_') != -1:
            pdb = str(job).split('_')[2]
            chain = str(job).split('.')[0].split('_')[3]
            struc = pdb.upper() + '_' + chain
            anch_res_nm = sp[-1].split(':')[0][:3]
            anch_res_pos = sp[-1].split(':')[0][3:]
            raw_score = float(sp[1])
            mu = float(mu_sig_dict[model][0])
            sigma = float(mu_sig_dict[model][1])
            z_score = ((raw_score - mu) / sigma)
            entry = struc + '\t' + anch_res_nm + '_' + anch_res_pos + '\t' + server + '\t' + model + '\t' + str(z_score)
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
    for entry in threshold_dict:
        server = entry.split('\t')[2]
        if not os.path.isdir(home + 'data_by_threshold/thrsh_' + cutoff + '/' + server + '/'):
            os.system('mkdir ' + home + 'data_by_threshold/thrsh_' + cutoff + '/' + server + '/')
        try:
            thrsh_file = open(home + 'data_by_threshold/thrsh_' + cutoff + '/' + server + '/' + struc + '.txt', 'a')
            thrsh_file.write(entry + '\t' + threshold_dict[entry][cutoff] + '\n')
            thrsh_file.close()
        except:
            thrsh_file = open(home + 'data_by_threshold/thrsh_' + cutoff + '/' + server + '/' + struc + '.txt', 'w')
            thrsh_file.write(entry + '\t' + threshold_dict[entry][cutoff] + '\n')
            thrsh_file.close()