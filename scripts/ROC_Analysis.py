##################################################################################
##################################################################################
## Script that performs the overhead for the ROC analysis and finds the optimal ##
## specificity cutoff as predicted by the average maximum Youden Index.         ##
##                                                                              ##
## Created by Joshua Toth, June 2019                                            ##
##################################################################################
##################################################################################
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

import os, sys, time, datetime, math, numpy as np

run_id = str(sys.argv[1])

home = '' # Your home directory
file_home = home + 'files/'
scripts_home = home + 'scripts/'
feature_home = home + 'FEATURE/'
foutput_home = home + 'raw_output/'
data_home = home + 'jobs/'
output_home = home + 'output/'
thrsh_data_home = home + 'data_by_threshold/'

prnt_file = file_home + 'log.txt'

cutoff_dict = {'100': 1.00, '99': 0.99, '95': 0.95, '90': 0.90, '80': 0.80, '70': 0.70, '60': 0.60, '50': 0.50, '40': 0.40, '30': 0.30, '20': 0.20, '10': 0.10, '5': 0.05, '1': 0.01, '0': 0.00}

########################################################################################################################
# ROC analysis has the objective of identifying the optimum specificity threshold for subsequent calculations.
# Functional predictions with scores above this threshold are used. The analysis takes the target dataset at 100%
# benchmark specificity as the set of 'gold standards' against which to judge the model dataset at all other specificity
# thresholds.
########################################################################################################################
os.system('echo Performing ROC analysis for job ' + run_id + ' . >> ' + prnt_file)

#
path = output_home + run_id + '/'
Ignore_list = []
target = {}     # {struc: {thrsh: 'collected'}}
for item in os.listdir(data_home + run_id + '/models/'):
    struc = item.split('_')[0] + '_' + item.split('_')[1]
    job_id = run_id + '_' + struc
    server = item.split('_')[2]
    if os.path.exists(thrsh_data_home + 'thrsh_0/' + job_id + '/target.txt'):    # This ensures target data exists as parsed from FEATURE's output.
        if struc not in target:
            target.update({struc: {}})
        for cutoff in cutoff_dict:
            if cutoff not in target[struc]:
                if not os.path.isdir(path + 'ROC/target/'):
                    os.system('mkdir ' + path + 'ROC/target/')
                    os.system('mkdir ' + path + 'ROC/target/Data/')
                    tfile = open(path + 'ROC/target/Data/thrsh_' + cutoff + '.txt', 'w')
                    tfile.write('%%% All data for target separated by threshold %%%\n')
                    tfile.close()
                os.system('cat ' + thrsh_data_home + 'thrsh_' + cutoff + '/' + job_id + '/target.txt >> ' + path + 'ROC/target/Data/thrsh_' + cutoff + '.txt')
                target[struc].update({cutoff: 'collected'})
            if not os.path.isdir(path + 'ROC/' + server):
                os.system('mkdir ' + path + 'ROC/' + server)
                os.system('mkdir ' + path + 'ROC/' + server + '/Data/')
                mfile = open(path + 'ROC/' + server + '/Data/thrsh_' + cutoff + '.txt', 'w')
                mfile.write('%%% All data for server separated by threshold %%%\n')
                mfile.close()
            os.system('cat ' + thrsh_data_home + 'thrsh_' + cutoff + '/' + job_id + '/' + server + '.txt >> ' + path + 'ROC/' + server + '/Data/thrsh_' + cutoff + '.txt')
    else:
        if struc not in Ignore_list:
            Ignore_list.append(struc)
os.system('echo Structures ' + str(Ignore_list) + ' ignored due to lack of target data. >> ' + prnt_file)


for item in os.listdir(data_home + run_id + '/models/'):
    struc = item.split('_')[0] + '_' + item.split('_')[1]
    job_id = run_id + '_' + struc
    server = item.split('_')[2]

    server_dict = {}  # {function: {cutoff: [stats]}
    missing_resis = {}  # {entry: <placeholder>}
    unusable_funcs = {}  # {function: {cutoff: [counts]}}

    # target values at 100 determine gold standard 'positive' or 'negative' for each prediction
    target_file = open(path + 'ROC/target/Data/thrsh_100.txt', 'r')
    targets = {}  # {entry: present/absent}
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

    for cutoff in cutoff_dict:
        infile = open(path + 'ROC/' + server + '/Data/thrsh_' + cutoff + '.txt', 'r')
        thrsh_dict = {}  # {function: [counts]}
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
                    if state == 'present':  # If both present, is true positive
                        if entry in targets:  # Another check to ensure target data is present
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
                            elif targets[entry] == 'absent':  # If model present but target absent, is false positive
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
                    elif state == 'absent':  # If both absent, is true negative
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
                            elif targets[entry] == 'present':  # If target present, but model absent, is false negative
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
        os.system('rm ' + temp_output_home + frame + '_' + server + '_thrsh_' + cutoff + '.txt')

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
            if int(p) < 10 or int(n) < 10:  # Set filter for minimum required instances
                if function not in unusable_funcs:
                    unusable_funcs.update({function: {}})
                unusable_funcs[function].update({cutoff: counts})
            else:  # Various ROC calculations
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
                    stats = [round(sens, 4), round(spec, 4), round(prec, 4), round(rec, 4), round(acc, 4),
                             round(F_score, 4), round(fdr, 4)]
                    server_dict[function].update({cutoff: stats})
                except:
                    stats = [round(sens, 4), round(spec, 4), prec, rec, acc, F_score, fdr]
                    server_dict[function].update({cutoff: stats})

    outfile = open(path + 'ROC/' + server + '/ROC_per_function_results.txt', 'w')  # Report back AUC, optimal specificity cutoff, and stats of each threshold
    outfile.write('%%% ROC results per function. (function, AUC, optimal spec threshold, {threshold: [sens, spec, prec, rec, acc, F_score, fdr]}) %%%\n')
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
                Y = abs(sens - (1 - spec))
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

# Calculate avg specificity corresponding to max Youden and output for subsequent analysis
os.system('echo Calculating ideal specificity cutoff... >> ' + prnt_file)
global_opt_spec = []
for server in os.listdir(data_home + run_id + '/models/'):
    try:
        infile = open(path + 'ROC/' + server + '/ROC_per_function_results.txt', 'r')
        server_opt_spec = []
        for line in infile:
            if line.startswith('%%%'):
                continue
            opt_spec = float(line.strip('\n').split('\t')[2])
            server_opt_spec.append(opt_spec)
        global_opt_spec.append(sum(server_opt_spec) / len(server_opt_spec))
        infile.close()
    except:
        if server != 'target':
            os.system('echo Could not find ROC info for server ' + server + '. >> ' + prnt_file)
Opt_spec = 90.0
try:
    Opt_spec = round(sum(global_opt_spec) / len(global_opt_spec), 4)
except:
    os.system('echo No data detected from ROC run. Using default 90 specificity. >> ' + prnt_file)
outfile2 = open(path + 'ROC/opt_spec_report.txt', 'w')
outfile2.write('Global averaging of specificities corresponding to maximum Youden Indices yields:\t' + str(Opt_spec) + '\n')
Diff = {}
for cutoff in cutoff_dict:
    diff = abs((Opt_spec/100) - cutoff_dict[cutoff])
    Diff.update({diff: cutoff})
M = min(Diff.keys())
spec = Diff[M]
outfile2.write('Closest Z-score specificity to implement at this cutoff:\t' + str(spec))
outfile2.close()

