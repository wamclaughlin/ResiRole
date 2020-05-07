#################################################################################
#################################################################################
## Script that performs ROC analysis and finds the optimal specificity cutoff. ##
## as predicted by the average maximum Youden Index.                           ##
##                                                                             ##
## Created by Joshua Toth, June 2019                                           ##
#################################################################################
#################################################################################

import os, sys, time, datetime, string, commands, subprocess, math, numpy as np

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

cutoff_list = ['0', '1', '5', '10', '20', '30', '40', '50', '60', '70', '80', '90', '95', '99', '100']

server = str(sys.argv[1])
frame = str(sys.argv[2])
I = str(sys.argv[3]).strip(']').strip('[').split(',')
Ignore_List = []
for item in I:
    Ignore_List.append(item.strip('\''))

########################################################################################################################
# For each server, compile counts of each SeqFEATURE model at each threshold by referencing target data. Use these
# counts to find sensitivity, specificity, among other values from which ROC curves could be constructed. Then, find the
# specificity at which the maximum Youden Index occurs in each curve and average these. Return all this data succinctly
# in the server directories /ROC/.
########################################################################################################################

server_dict = {}    # {function: {cutoff: [stats]}
missing_resis = {}  # {entry: <placeholder>}
unusable_funcs = {} # {function: {cutoff: [counts]}}

path = output_home + 'All_Targets/' + frame + '/Per_Server/'

print 'Collecting target matrix...'

#target values at 100 determine 'positive' or 'negative'
target_file = open(path + 'target/Data/thrsh_100.txt', 'r')

targets = {}    # {entry: present/absent}
for line in target_file:
    if line.startswith('%%%'):
        continue
    else:
        line = line.strip('\n').split('\t')
        struc = line[0]
        function = line[3]
        res = line[1]
        entry = function + '|' + struc + '|' + res
        state = line[-1]
        if state == 'present':
            targets[entry] = 'present'
        elif state == 'absent':
            targets[entry] = 'absent'

target_file.close()

for cutoff in cutoff_list:

    infile = open(path + server + '/Data/thrsh_' + cutoff + '.txt', 'r')

    print 'Collecting ' + server + ' matrix...'

    thrsh_dict = {}     # {function: [counts]}

    for line in infile:
        if line.startswith('%%%'):
            continue
        else:
            line = line.strip('\n').split('\t')
            struc = line[0]
            res = line[1]
            if struc not in Ignore_List:
                function = line[3]
                entry = function + '|' + struc + '|' + res
                state = line[-1]
                if state == 'present':                          # If both present, is true positive
                    if entry in targets:                            # Another check to ensure target data is present
                        if targets[entry] == 'present':
                            if function in thrsh_dict:
                                counts = thrsh_dict[str(function)]
                                p_count = int(counts[0]) + 1
                                n_count = counts[1]
                                tp_count = counts[2]
                                fp_count = counts[3]
                                tn_count = counts[4]
                                fn_count = counts[5]
                                tp_count = int(tp_count) + 1
                                counts = [p_count, n_count, tp_count, fp_count, tn_count, fn_count]
                                thrsh_dict[str(function)] = counts
                            else:
                                thrsh_dict[str(function)] = [1, 0, 1, 0, 0, 0]
                        elif targets[entry] == 'absent':        # If model present but target absent, is false positive
                            if function in thrsh_dict:
                                counts = thrsh_dict[str(function)]
                                p_count = counts[0]
                                n_count = int(counts[1]) + 1
                                tp_count = counts[2]
                                fp_count = counts[3]
                                tn_count = counts[4]
                                fn_count = counts[5]
                                fp_count = int(fp_count) + 1
                                counts = [p_count, n_count, tp_count, fp_count, tn_count, fn_count]
                                thrsh_dict[str(function)] = counts
                            else:
                                thrsh_dict[str(function)] = [0, 1, 0, 1, 0, 0]
                    else:
                        if entry not in missing_resis:
                            missing_resis.update({entry: 'Q'})
                elif state == 'absent':                         # If both absent, is true negative
                    if entry in targets:
                        if targets[entry] == 'absent':
                            if function in thrsh_dict:
                                counts = thrsh_dict[str(function)]
                                p_count = counts[0]
                                n_count = int(counts[1]) + 1
                                tp_count = counts[2]
                                fp_count = counts[3]
                                tn_count = counts[4]
                                fn_count = counts[5]
                                tn_count = int(tn_count) + 1
                                counts = [p_count, n_count, tp_count, fp_count, tn_count, fn_count]
                                thrsh_dict[str(function)] = counts
                            else:
                                thrsh_dict[str(function)] = [0, 1, 0, 0, 1, 0]
                        elif targets[entry] == 'present':       # If target present, but model absent, is false negative
                            if function in thrsh_dict:
                                counts = thrsh_dict[str(function)]
                                p_count = int(counts[0]) + 1
                                n_count = counts[1]
                                tp_count = counts[2]
                                fp_count = counts[3]
                                tn_count = counts[4]
                                fn_count = counts[5]
                                fn_count = int(fn_count) + 1
                                counts = [p_count, n_count, tp_count, fp_count, tn_count, fn_count]
                                thrsh_dict[str(function)] = counts
                            else:
                                thrsh_dict[str(function)] = [1, 0, 0, 0, 0, 1]
                    else:
                        if entry not in missing_resis:
                            missing_resis.update({entry: 'Q'})

    infile.close()

    print 'Calculating results...'

    for function in thrsh_dict:
        if function not in server_dict:
            server_dict.update({function: {}})
        counts = thrsh_dict[function]
        p = counts[0]
        n = counts[1]
        tp = counts[2]
        fp = counts[3]
        tn = counts[4]
        fn = counts[5]
        if int(p) < 10 or int(n) < 10:                # Set filter for minimum required instances
            if function not in unusable_funcs:
                unusable_funcs.update({function: {}})
            unusable_funcs[function].update({cutoff: counts})
        else:                                       # Various ROC calculations
            sens = float(tp) / p
            spec = float(tn) / n
            prec, rec, acc, F_score, fdr = 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'
            try:
                prec = float(tp) / (tp + fp)
                rec = float(tp) / (tp + fn)
                acc = float(tp + tn) / (p + n)
                F_score = float(2 * tp) / (2 * tp + fp + fn)
                fdr = float(fp) / (fp + tp)
            except:
                pass
            try:
                stats = [round(sens, 4), round(spec, 4), round(prec, 4), round(rec, 4), round(acc, 4), round(F_score, 4), round(fdr, 4)]
                server_dict[function].update({cutoff: stats})
            except:
                stats = [round(sens, 4), round(spec, 4), prec, rec, acc, F_score, fdr]
                server_dict[function].update({cutoff: stats})

print 'Outputting...'

#print server_dict

outfile = open(path + server + '/ROC_per_function_results.txt', 'w')    # Report back AUC, optimal specificity cutoff, and stats of each threshold
outfile.write('%%% ROC results per function. (AUC, optimal spec threshold, {threshold: [sens, spec, prec, rec, acc, F_score, fdr]}) %%%\n')
for function in server_dict:
    if function not in unusable_funcs:
        ROC_sens = []
        ROC_spec = []
        Youden = {}
        for cutoff in cutoff_list:
            stats = server_dict[function][cutoff]
            sens = stats[0]
            spec = stats[1]
            ROC_sens.append(sens)
            ROC_spec.append(spec)
            Y = abs(sens - spec)
            Youden.update({Y: float(cutoff)})
        AUC = abs(np.trapz(ROC_sens, ROC_spec))
        outfile.write(function + '\t' + str(round(AUC, 4)) + '\t')
        M = max(Youden.keys())
        for Y in Youden:
            if Y == M:
                opt_spec = Youden[Y]
                outfile.write(str(opt_spec) + '\t')
        outfile.write(str(server_dict[function]) + '\n')

outfile.close()

########################################################################################################################
# Notes:
# - This does ROC per server. If it is ever desired to split jobs further, say, per cutoff, the code will have to be
# re-worked because info from all cutoffs is necessary for the final calculations
# - Minimum instance filter is implemented here
# - If any other ROC statistics are ever desired, they can be obtained from the dictionaries created in this file