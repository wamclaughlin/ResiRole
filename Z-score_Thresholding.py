################################################################################
################################################################################
## Script that converts raw data to Z-scores and thresholds them accordingly. ##
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

update = str(sys.argv[1])   # Just a dead end as of now

########################################################################################################################
# To update the Z-dictionary, the previous dictionary is read in and new data added to it each week. The scores come
# only from the target structures. Scores from old structures (beyond 1 year) are not removed because accuracy of the
# scores will only improve with more data. Therefore, the Z-dictionary is set to continue growing indefinitely, but the
# files produced here for old structures are cleaned up.
########################################################################################################################

#if update == 'True':                   # For if we ever want to go down the route of updating at particular intervals
#elif update == 'False':                # rather than each week
new_ids = []
date_file = open(file_home + 'date_sync.txt', 'r')
for line in date_file:
    if line.startswith('NEW_DATES:'):
        dates = line.strip('\n').split('\t')[1].strip('[').strip(']').split(',')
        for d in dates:
            date = d.strip(' ').strip('\'')
            subdirs = os.listdir(data_home + date + '/')
            for struc in subdirs:
                id = struc.split('_')[0].lower()
                new_ids.append(id)
date_file.close()

# update dictionary
os.system('echo Updating Z-dictionary and thresholding results... >> ' + prnt_file)
z_dictionary = {}   # {model: [raw_scores]}
prev_z_file = open(file_home + 'Z_dictionary.txt', 'r')
for line in prev_z_file:
    model = line.strip('\n').split('\t')[0]
    s = line.strip('\n').split('\t')[1].split(',')
    scores = []
    for score in s:
        score = float(score.strip('\''))
        scores.append(score)
    z_dictionary.update({model: scores})

Fout_list = os.listdir(foutput_home)
for id in new_ids:
    for file in Fout_list:
        if id in str(file):
            with open(foutput_home + file, 'r') as f:
                for line in f:
                    if 'Analyzing target' in line:
                        for line in f:
                            line = line.strip('\n')
                            if line != '':
                                sp = line.split('\t')
                                if sp[0].split('.')[-1] == 'model':
                                    model = line.rstrip('.nb.model')
                                    key = model
                                elif line.find('Env_') != -1:
                                    pdb = sp[0].split('_')[1]
                                    chain = sp[-1].split(':')[1].split('@')[0]
                                    raw_score = float(sp[1])
                                    if key in z_dictionary:
                                        z_dictionary[key].append(raw_score)
                                    else:
                                        z_dictionary.update({key: [raw_score]})
            f.close()

dict_file = open(file_home + 'Z_dictionary.txt', 'w')
for key in sorted(z_dictionary.keys()):
    dict_file.write(str(key) + '\t' + ','.join([str(x) for x in z_dictionary[key]]) + '\t' + str(len(z_dictionary[key])) + '\n')
dict_file.close()

# Update Mu and Sigma
mu_sig_dict = {}  # {model:[mu,sigma]}
mu_sig_file = open(file_home + 'mu_sigma_maker.txt', 'w')
for k, v in z_dictionary.iteritems():
    model = k
    score_list = v
    mu = (sum(score_list)) / (float(len(score_list)))
    differences = [x - mu for x in score_list]
    sq_differences = [d ** 2 for d in differences]
    ssd = sum(sq_differences)
    variance = ssd / (float(len(score_list)) - 1.0)
    sigma = math.sqrt(variance)
    mu_sig_file.write(model + '\t' + str(mu) + '\t' + str(sigma) + '\n')
mu_sig_file.close()


Fout_list = os.listdir(foutput_home)
# Local parallel run to parse each output file.

for each in Fout_list:
    os.system('/usr/local/bin/python2.7 ' + scripts_home + '/Parse_FEATURE_output.py ' + each)



'''
max_processes = 20
processes = set()
for each in Fout_list:
    processes.add(subprocess.Popen(['/usr/local/bin/python2.7', scripts_home + '/Parse_FEATURE_output.py', each]))
    if (len(processes) >= max_processes):
        os.wait()
        processes.difference_update([p for p in processes if p.poll() is not None])

for p in processes:
    if p.poll() is None:
        try:
            p.wait()
        except:
            continue
'''

















