##################################################################################
##################################################################################
## Script that calculates the difference scores per server based on the optimal ##
## specificity reported by the ROC study.                                       ##
##                                                                              ##
## Created by Joshua Toth, June 2019                                            ##
##################################################################################
##################################################################################

import os, sys, time, datetime, string, commands, subprocess, math, pickle, shelve, shutil, scipy.stats as stats
from scipy.stats import pearsonr

home = '/home/jtoth/ResiRole/'
file_home = home + 'files/'
scripts_home = home + 'scripts/'
feature_home = home + 'FEATURE/'
download_home = home + 'data_by_week/'
data_home = download_home + 'quality_estimation/'
QSUB_home = home + 'QSUB_scripts/'
output_home = '/home/jtoth/For_Display/'
foutput_home = feature_home + 'raw_output/'
thrsh_data_home = home + 'data_by_threshold/'

cutoff_dict = {'100': 1.00, '99': 0.99, '95': 0.95, '90': 0.90, '80': 0.80, '70': 0.70, '60': 0.60, '50': 0.50, '40': 0.40, '30': 0.30, '20': 0.20, '10': 0.10, '5': 0.05, '1': 0.01, '0': 0.00}
time_frames = {'1-Week': 1, '1-Month': 4, '3-Months': 13, '6-Months': 26, '1-Year': 52}
data_sets = ['All', 'Modeled']

server = str(sys.argv[1])
frame = str(sys.argv[2])

########################################################################################################################
# The Z-score probability difference calculation is straightforward; identify the target predictions in the appropriate
# threshold range, find the corresponding model predictions, and then calculate the difference between their
# probabilities. Results will be averaged per server in this script.
########################################################################################################################

for data in data_sets:
    #if data == 'Modeled':
        # Here is where I would separate out the modeled structures from all data if I knew how to do that
    if data == 'All':
        print 'Calculating for ' + frame
        path = output_home + 'All_Targets/' + frame + '/'
        opt_spec_file = open(path + 'Optimal_Specificity_Report.txt', 'r')
        thresh = ''
        Z_dict = {} # {function: {struc: {res: {'target': {'Z': Z_score}, {'P': prob}}, {server: {'Z': Z_score}, {'P': prob}}}}}}
        for line in opt_spec_file:
            if line.startswith('Closest'):
                thresh = str(line.strip('\n').split('\t')[1])

        print 'Gathering Z-scores...'

        path = path + 'Per_Server/'
        target_file = open(path + 'target/Data/thrsh_' + thresh + '.txt', 'r')
        for line in target_file:
            if line.startswith('%%%'):
                continue
            line = line.strip('\n').split('\t')
            state = line[-1]
            if state == 'present':
                function = line[-3]
                struc = line[0]
                res = line[1]
                Z = float(line[-2])
                combo = struc + '|' + res
                P_tar = stats.norm.cdf(Z)
                if function in Z_dict:
                    if combo in Z_dict[function]:
                        Z_dict[function][combo].update({'target': {'Z': Z}})
                    else:
                        Z_dict[function].update({combo: {'target': {'Z': Z}}})
                else:
                    Z_dict.update({function: {combo: {'target': {'Z': Z}}}})
                Z_dict[function][combo]['target'].update({'P': P_tar})
        target_file.close()

        print 'Finding differences and correlations...'
        server_file = open(path + server + '/Data/thrsh_' + thresh + '.txt', 'r')       # thresh taking from doesn't matter because the z-score is given with every line
        for line in server_file:
            if line.startswith('%%%'):
                continue
            line = line.strip('\n').split('\t')
            struc = line[0]
            res = line[1]
            combo = struc + '|' + res
            function = line[-3]
            if function in Z_dict:
                if combo in Z_dict[function]:
                    Z = float(line[-2])
                    P_mod = stats.norm.cdf(Z)
                    Z_dict[function][combo].update({server: {'Z': Z}})
                    Z_dict[function][combo][server].update({'P': P_mod})
                    P_tar = Z_dict[function][combo]['target']['P']
                    diff_score = round(float(P_mod) - float(P_tar), 4)
                    Z_dict[function][combo].update({'diff': diff_score})
        server_file.close()

        print 'Outputting...'
        if not os.path.isdir(path + server + '/Difference_Score/'):
            os.system('mkdir ' + path + server + '/Difference_Score/')
        if not os.path.isdir(path + server + '/Correlation_Score/'):
            os.system('mkdir ' + path + server + '/Correlation_Score/')
        outfile1 = open(path + server + '/Difference_Score/' + server + '_diff_scores.txt', 'w')
        outfile1.write('%%% Report of difference scores. (function, struc|residue combo, target probability, difference score (model - target) %%%\n')
        outfile2 = open(path + server + '/Correlation_Score/' + server + '_corr_scores.txt', 'w')
        outfile2.write('%%% Report of model vs target probability correlations (function, Pearson\'s R, associated p-value) %%%\n')
        for function in Z_dict:
            model_probs = []
            target_probs = []
            for combo in Z_dict[function]:
                if server in Z_dict[function][combo]:       # This check is necessary because the server may not have modeled the target or portions of the target
                    model_probs.append(Z_dict[function][combo][server]['P'])
                    target_probs.append(Z_dict[function][combo]['target']['P'])
                    outfile1.write(function + '\t' + combo + '\t' + str(round(Z_dict[function][combo]['target']['P'], 4)) + '\t' + str(Z_dict[function][combo]['diff']) + '\n')
            if len(target_probs) >= 30:
                r, p = pearsonr(target_probs, model_probs)
                outfile2.write(function + '\t' + str(round(r, 4)) + '\t' + str(round(p, 4)) + '\n')
            else:
                outfile2.write(function + '\t' + 'Error: only ' + str(len(target_probs)) + ' instances\n')
        outfile1.close()
        outfile2.close()

########################################################################################################################
# Notes:
# - Overwrites all old files from previous runs. This is not entirely necessary, it could be reworked to only run on new
# data and delete old data every cycle, as long as the correct output is given for averaging. If it is discovered that
# these jobs are taking too long on the cluster, doing this is the first recommended action to take.
# - Also runs on all time frames in a single job. This should not be problematic, as no data is remembered between
# iterations through each frame, but it could be separated if desired.