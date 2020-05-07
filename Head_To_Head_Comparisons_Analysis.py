#######################################################################################
#######################################################################################
## Script that reorganizes/recalculates Z-score metrics for head-to-head comparisons ##
## of servers based on their common structures.                                      ##
##                                                                                   ##
## Created by Joshua Toth, June 2019                                                 ##
#######################################################################################
#######################################################################################

import os, sys, time, datetime, string, commands, subprocess, math, pickle, shelve, shutil, scipy.stats as stats, numpy as np
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

frame = str(sys.argv[1])
server1 = str(sys.argv[2])
server2 = str(sys.argv[3])
servers = [server1, server2]

########################################################################################################################
# For the given time frame and comparison, search the per-server data to pull all relevant instances and recalculate
# correlations. Final averaging is reported per comparison.
########################################################################################################################
for data in data_sets:
    # if data == 'Modeled:
    if data == 'All':
        path = output_home + 'All_Targets/' + frame + '/Head_to_head/' + server1 + '_' + server2 + '/'
        path2 = output_home + 'All_Targets/' + frame + '/Per_Server/'

        print 'Making head-to-head directories.'
        if not os.path.isdir(path + 'Overall/Difference_Score'):
            os.system('mkdir ' + path + 'Overall/Difference_Score/')
            os.system('mkdir ' + path + 'Overall/Correlation_Score/')
        if not os.path.isdir(path + 'Per_Structure/Difference_Score'):
            os.system('mkdir ' + path + 'Per_Structure/Difference_Score/')
            os.system('mkdir ' + path + 'Per_Structure/Correlation_Score/')

        for server in servers:
            print 'Analyzing server ' + server + '...'
            data_dict = {} # {struc: {'diff_score': {entry: score}}, {'correlation': {function: {res: {'target': P}, {'model': P}}}}}

            strucs_file = open(path + 'structures.txt', 'r')        # Assemble dictionary for server
            for line in strucs_file:
                if line.startswith('%%%'):
                    continue
                else:
                    struc = line.strip('\n')
                    data_dict.update({struc: {'diff_score': {}}})
                    data_dict[struc].update({'correlation': {}})
            strucs_file.close()

            if len(data_dict.keys()) == 0:
                outfile1 = open(path + 'Overall/Difference_Score/Cannot_Compare.txt', 'w')
                outfile1.write('Servers share no structures in common, and therefore head-to-head analyses cannot be performed.')
                outfile1.close()
                outfile2 = open(path + 'Overall/Correlation_Score/Cannot_Compare.txt', 'w')
                outfile2.write('Servers share no structures in common, and therefore head-to-head analyses cannot be performed.')
                outfile2.close()
                outfile3 = open(path + 'Per_Structure/Difference_Score/Cannot_Compare.txt', 'w')
                outfile3.write('Servers share no structures in common, and therefore head-to-head analyses cannot be performed.')
                outfile3.close()
                outfile4 = open(path + 'Per_Structure/Correlation_Score/Cannot_Compare.txt', 'w')
                outfile4.write('Servers share no structures in common, and therefore head-to-head analyses cannot be performed.')
                outfile4.close()
            else:
                ds_file = open(path2 + server + '/Difference_Score/' + server + '_diff_scores.txt', 'r')
                for line in ds_file:
                    if line.startswith('%%%'):
                        continue
                    else:
                        line = line.strip('\n').split('\t')
                        struc = line[1].split('|')[0]
                        if struc in data_dict:
                            function = line[0]
                            res = line[1].split('|')[1]
                            target_P = float(line[2])
                            diff = float(line[3])
                            model_P = target_P + diff
                            entry = function + '|' + res
                            data_dict[struc]['diff_score'].update({entry: diff})
                            if function in data_dict[struc]['correlation']:
                                data_dict[struc]['correlation'][function].update({res: {'target': target_P}})
                            else:
                                data_dict[struc]['correlation'].update({function: {res: {'target': target_P}}})
                            data_dict[struc]['correlation'][function][res].update({'model': model_P})
                ds_file.close()

                # cleanup problematic strucs (the same strucs as would appear in the ignore list for ROC)
                delete = []
                for struc in data_dict:
                    if len(data_dict[struc]['diff_score'].keys()) == 0:
                        delete.append(struc)
                for struc in delete:
                    del data_dict[struc]

                # Overall files and averages
                print 'Outputting overall data for server...'
                outfile1 = open(path + 'Overall/Difference_Score/' + server + '_diff_scores.txt', 'w')
                outfile1.write('%%% Difference scores from functional predictions on structures considered for server + ' + server + ' in this comparison %%%\n')
                diff_scores = []
                for struc in data_dict:
                    for entry in data_dict[struc]['diff_score']:
                        function = entry.split('|')[0]
                        res = entry.split('|')[1]
                        combo = struc + '|' + res
                        diff = data_dict[struc]['correlation'][function][res]['model'] - data_dict[struc]['correlation'][function][res]['target']
                        diff_scores.append(abs(diff))
                        outfile1.write(function + '\t' + combo + '\t' + str(data_dict[struc]['correlation'][function][res]['target']) + '\t' + str(diff) + '\n')
                outfile1.close()

                avg_outfile1 = open(path + 'Overall/Difference_Score/' + server + '_average.txt', 'w')
                avg_outfile1.write('%%% Average difference score for server among structures in this comparison %%%\n')
                avg_outfile1.write('Average = ' + str(round(sum(diff_scores) / len(diff_scores), 4)) + ' +/-' + str(round(np.std(diff_scores), 4)) + '\n')
                avg_outfile1.write('Calculated from ' + str(len(diff_scores)) + ' unique instances of functional predictions.')
                avg_outfile1.close()

                outfile2 = open(path + 'Overall/Correlation_Score/' + server + '_corr_scores.txt', 'w')
                outfile2.write('%%% Pearson correlation coefficient from functional predictions on structures considered for server ' + server + ' in this comparison %%%\n')
                corr_scores = []
                for function in os.listdir(feature_home + 'FEATURE_prediction_models/'):
                    function = function.strip('.nb.model')
                    model_probs = []
                    target_probs = []
                    for struc in data_dict:
                        if function in data_dict[struc]['correlation']:
                            for res in data_dict[struc]['correlation'][function]:
                                model_probs.append(data_dict[struc]['correlation'][function][res]['model'])
                                target_probs.append(data_dict[struc]['correlation'][function][res]['target'])
                    if len(target_probs) >= 30:          # we require at least 30 target instances to attempt to calculate a correlation
                        r, p = pearsonr(target_probs, model_probs)
                        try:
                            t = r / 1.0
                        except:
                            outfile2.write(function + '\tPearson-r undefined\n')
                            continue
                        outfile2.write(function + '\t' + str(round(r, 4)) + '\t' + str(round(p, 4)))
                        if p < 0.05:
                            if r != 1.0 and r != -1.0:
                                z = .5 * (math.log((1.0 + r) / (1.0 - r)))
                                corr_scores.append(z)
                                outfile2.write('\n')
                            else:
                                outfile2.write('\tproblem\n')
                                print function, 'had a perfect negative correlation and could not be converted to a z-score.'
                        else:
                            outfile2.write('\n')
                outfile2.close()

                if len(corr_scores) != 0:
                    Z1 = sum(corr_scores) / len(corr_scores)
                    R1 = round((math.exp(2 * Z1) - 1.0) / (math.exp(2 * Z1) + 1.0), 4)
                    avg_outfile2 = open(path + 'Overall/Correlation_Score/' + server + '_average.txt', 'w')
                    avg_outfile2.write('%%% Average correlation coefficient for server among structures in this comparison %%%\n')
                    avg_outfile2.write('Average R = ' + str(R1) + '; Average Z = ' + str(Z1) + ' +/-' + str(round(np.std(corr_scores), 4)) + '\n')
                    avg_outfile2.write('Calculated from ' + str(len(corr_scores)) + ' SeqFEATURE prediction models.')
                    avg_outfile2.close()
                else:
                    avg_outfile2 = open(path + 'Overall/Correlation_Score/' + server + '_average.txt', 'w')
                    avg_outfile2.write('%%% Average correlation coefficient for server among structures in this comparison %%%\n')
                    avg_outfile2.write('Error: No correlation scores were found for this server.')
                    avg_outfile2.close()

                # Per-structure files and averages
                print 'Outputting per-structure data for server...'
                for struc in data_dict:
                    ds_path = path + 'Per_Structure/Difference_Score/' + struc + '/'
                    corr_path = path + 'Per_Structure/Correlation_Score/' + struc + '/'
                    if not os.path.isdir(ds_path):
                        os.system('mkdir ' + ds_path)
                    if not os.path.isdir(corr_path):
                        os.system('mkdir ' + corr_path)

                    s_outfile1 = open(ds_path + server + '_diff_scores.txt', 'w')
                    s_outfile1.write('%%% Difference scores from functional predictions on structure ' + struc + ' from server ' + server + ' %%%\n')
                    diff_scores = []
                    for entry in data_dict[struc]['diff_score']:
                        function = entry.split('|')[0]
                        res = entry.split('|')[1]
                        combo = struc + '|' + res
                        diff = data_dict[struc]['correlation'][function][res]['model'] - data_dict[struc]['correlation'][function][res]['target']
                        diff_scores.append(abs(diff))
                        s_outfile1.write(function + '\t' + combo + '\t' + str(data_dict[struc]['correlation'][function][res]['target']) + '\t' + str(diff) + '\n')
                    s_outfile1.close()

                    s_avg_outfile1 = open(ds_path + server + '_average.txt', 'w')
                    s_avg_outfile1.write('%%% Average difference score for server for the structure %%%\n')
                    s_avg_outfile1.write('Average = ' + str(round(sum(diff_scores) / len(diff_scores), 4)) + ' +/-' + str(round(np.std(diff_scores), 4)) + '\n')
                    s_avg_outfile1.write('Calculated from ' + str(len(diff_scores)) + ' unique instances of functional predictions.')
                    s_avg_outfile1.close()

                    s_outfile2 = open(corr_path + server + '_corr_scores.txt', 'w')
                    s_outfile2.write('%%% Pearson correlation coefficient from functional predictions on structure ' + struc + ' from server ' + server + ' %%%\n')
                    corr_scores = []
                    for function in data_dict[struc]['correlation']:
                        model_probs = []
                        target_probs = []
                        for res in data_dict[struc]['correlation'][function]:
                            model_probs.append(data_dict[struc]['correlation'][function][res]['model'])
                            target_probs.append(data_dict[struc]['correlation'][function][res]['target'])
                        if len(target_probs) >= 3:
                            r, p = pearsonr(target_probs, model_probs)
                            try:
                                t = r / 1.0
                            except:
                                s_outfile2.write(function + '\tPearson-r undefined\n')
                                continue
                            s_outfile2.write(function + '\t' + str(round(r, 4)) + '\t' + str(round(p, 4)))
                            if p < 0.05:
                                if r != 1.0 and r != -1.0:
                                    z = .5 * (math.log((1.0 + r) / (1.0 - r)))
                                    corr_scores.append(z)
                                    s_outfile2.write('\n')
                                else:
                                    s_outfile2.write('\tproblem!\n')
                                    print struc, function, 'had a perfect correlation and could not be converted to a z-score.'
                            else:
                                s_outfile2.write('\n')
                    s_outfile2.close()

                    if len(corr_scores) != 0:
                        Z2 = sum(corr_scores) / len(corr_scores)
                        R2 = round((math.exp(2 * Z2) - 1.0) / (math.exp(2 * Z2) + 1.0), 4)
                        s_avg_outfile2 = open(corr_path + server + '_average.txt', 'w')
                        s_avg_outfile2.write('%%% Average correlation coefficient among predictions for the structure in this comparison %%%\n')
                        s_avg_outfile2.write('Average R = ' + str(R2) + '; Average Z = ' + str(Z2) + ' +/-' + str(round(np.std(corr_scores), 4)) + '\n')
                        s_avg_outfile2.write('Calculated from ' + str(len(corr_scores)) + ' SeqFEATURE prediction models.')
                        s_avg_outfile2.close()
                    else:
                        s_avg_outfile2 = open(corr_path + server + '_average.txt', 'w')
                        s_avg_outfile2.write('%%% Average correlation coefficient among predictions for the structure in this comparison %%%\n')
                        s_avg_outfile2.write('Error: No correlation scores were found for this structure.')
                        s_avg_outfile2.close()
print 'Done.'
########################################################################################################################
# Notes:
# - produces same output as Z-score analysis programs but for each comparison and for each structure within, working one
# server at a time.
# - As of now, we are requiring at least 30 instances of a target prediction above the Youden-predicted threshold to
# attempt to calculate a correlation for a function, and we require the p-value be significant (<.05) for averaging. For
# individual structures, the threshold is instead 3 instances because there would hardly ever be over 30 predictions in
# a single structure. Note, however, that this lower requirement makes the metric less meaningful on the per-structure
# level.
# - If any correlation results in r = -1.0, this is problematic because it cannot be converted to a z-score. However,
# this is a rather rare occurrence and probably will only ever present itself in the 1-week data when there are few
# instances. As of now, if this does happen, the score is reported but is not included in the average.
# - Standard deviation reported is for the converted z-scores, this would have to be back-converted to get the standard
# deviation for the average correlation coefficient.
