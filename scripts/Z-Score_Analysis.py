##################################################################################
##################################################################################
## Overhead for scripts that will perform the calculations of difference scores ##
## and correlation coefficients.                                                ##
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

import os, sys, time, datetime, math, numpy as np, scipy.stats as stats
from scipy.stats import pearsonr

home = '' # Your home directory
file_home = home + 'files/'
scripts_home = home + 'scripts/'
feature_home = home + 'FEATURE/'
output_home = home + 'output/'
thrsh_data_home = home + 'data_by_threshold/'

prnt_file = file_home + 'log.txt'

cutoff_dict = {'100': 1.00, '99': 0.99, '95': 0.95, '90': 0.90, '80': 0.80, '70': 0.70, '60': 0.60, '50': 0.50, '40': 0.40, '30': 0.30, '20': 0.20, '10': 0.10, '5': 0.05, '1': 0.01, '0': 0.00}

run_id = str(sys.argv[1])

########################################################################################################################
# This script will calculate difference scores and averages per structure as well as correlation scores and averages
# per modeling technique
########################################################################################################################

os.system('echo Running Z-Score analyses on all models and targets for job id = ' + run_id + '. >> ' + prnt_file)

Z_dict = {}
targets = {}
path = output_home + run_id + '/'
os.system('mkdir ' + path)
opt_spec = ''

# Load optimum specificity threshold
opt_spec_file = open(path + 'ROC/opt_spec_report.txt', 'r')
for line in opt_spec_file:
    if 'Global' in line:
        opt_spec = line.strip('\n').split('\t')[-1]
opt_spec_file.close()

#Gather target Z-scores'
for dir in os.listdir(thrsh_data_home + opt_spec):
    if run_id in str(dir):
        for file in os.listdir(thrsh_data_home + opt_spec + '/' + dir + '/'):
            if 'target' in str(file):
                pdb_id = str(file).split('_')[0] + '_' + str(file).split('_')[1]
                targets.update({pdb_id: {}})
                os.system('mkdir ' + path + pdb_id + '/')
                target_file = open(thrsh_data_home + run_id + '/' + file, 'r')
                for line in target_file:
                    if line.startswith('%%%'):
                        continue
                    line = line.strip('\n').split('\t')
                    state = line[-1]
                    if state == 'present':
                        function = line[-3]
                        res = line[1]
                        Z = float(line[-2])
                        combo = pdb_id + '|' + res
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
            else:
                model_file = open(thrsh_data_home + run_id + '/' + file, 'r')
                pdb_id = str(file).split('_')[0] + '_' + str(file).split('_')[1]
                server = str(file).split('_')[-1].split('.')[0]         # server is the model
                targets[pdb_id].update({server: 'y'})
                os.system('mkdir ' + path + pdb_id + '/' + server + '/')
                for line in model_file:
                    if line.startswith('%%%'):
                        continue
                    line = line.strip('\n').split('\t')
                    res = line[1]
                    combo = pdb_id + '|' + res
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
                model_file.close()

Corrscore_dict = {}
for pdb_id in targets:
    for server in targets[pdb_id]:
        if server not in Corrscore_dict:
            Corrscore_dict.update({server: {}})
        if not os.path.isdir(path + pdb_id + '/' + server + '/Difference_Score/'):
            os.system('mkdir ' + path + pdb_id + '/' + server + '/Difference_Score/')

        outfile1 = open(path + pdb_id + '/' + server + '/Difference_Score/' + pdb_id + '_' + server + '_diff_scores.txt', 'w')
        outfile1.write('###################################################################################################################################################\n')
        outfile1.write('%%% Report of difference scores for model ' + server + '. (function, struc|residue combo, target probability, difference score (model - target) %%%\n')
        outfile1.write('###################################################################################################################################################\n')

        for function in Z_dict:
            for combo in Z_dict[function]:
                if pdb_id in combo:
                    if server in Z_dict[function][combo]:
                        if function not in Corrscore_dict[server]:
                            Corrscore_dict[server].update({function: {'targetprobs': []}})
                            Corrscore_dict[server][function].update({'modellprobs': []})
                        Corrscore_dict[server][function]['modelprobs'].append(Z_dict[function][combo][server]['P'])
                        Corrscore_dict[server][function]['targetprobs'].append(Z_dict[function][combo]['target']['P'])
                        outfile1.write(function + '\t' + combo + '\t' + str(round(Z_dict[function][combo]['target']['P'], 4)) + '\t' + str(Z_dict[function][combo]['diff']) + '\n')
        outfile1.close()

for server in Corrscore_dict:
    if not os.path.isdir(path + 'Correlation_Score/'):
        os.system('mkdir ' + path + 'Correlation_Score/')
    outfile2 = open(path + 'Correlation_Score/' + server + '_corr_scores.txt', 'w')
    outfile2.write('#################################################################################################################################\n')
    outfile2.write('%%% Report of model vs target probability correlations for model ' + server + '. (function, Pearson\'s R, associated p-value) %%%\n')
    outfile2.write('#################################################################################################################################\n')

    for function in Corrscore_dict[server]:
        if len(Corrscore_dict[server][function]['targetprobs']) >= 10:
            r, p = pearsonr(Corrscore_dict[server][function]['targetprobs'], Corrscore_dict[server][function]['modelprobs'])
            outfile2.write(function + '\t' + str(round(r, 4)) + '\t' + str(round(p, 4)) + '\n')
        else:
            outfile2.write(function + '\t' + 'Error: only ' + str(len(Corrscore_dict[server][function]['targetprobs'])) + ' instances\n')
    outfile2.close()

os.system('echo Calculating averages of Z-score metrics. >> ' + prnt_file)

for pdb_id in targets:
    for server in targets[pdb_id]:
        diff_score_file = open(path + pdb_id + '/' + server + '/Difference_Score/' + pdb_id + '_' + server + '_diff_scores.txt', 'r')
        diff_scores = []
        for line in diff_score_file:
            if line.startswith('%%%') or '#' in line:
                continue
            else:
                score = abs(float(line.strip('\n').split('\t')[-1]))       # Use abs of diff score for averaging
                diff_scores.append(score)
        diff_score_file.close()

        outfile1 = open(path + pdb_id + '/' + server + '/Difference_Score/' + pdb_id + '_' + server + '_avg_diff.txt', 'w')
        outfile1.write('###########################################\n')
        outfile1.write('%%% Average difference score for server %%%\n')
        outfile1.write('###########################################\n')
        outfile1.write('Average = ' + str(round(sum(diff_scores) / len(diff_scores), 4)) + ' +/-' + str(round(np.std(diff_scores), 4)) + '\n')
        outfile1.write('Calculated from ' + str(len(diff_scores)) + ' unique instances of functional predictions.')
        outfile1.close()

for server in Corrscore_dict:
    corr_score_file = open(path + '/Correlation_Score/' + server + '_corr_scores.txt', 'r')
    corr_scores = []
    for line in corr_score_file:
        if line.startswith('%%%') or '#' in line:
            continue
        elif 'Error' in line:
            continue
        else:
            r = float(line.strip('\n').split('\t')[1])
            if r != 1.0 and r != -1.0:
                z = .5 * (math.log((1.0 + r) / (1.0 - r)))
                corr_scores.append(z)
        corr_score_file.close()
    try:
        Z = sum(corr_scores) / len(corr_scores)
        R = round((math.exp(2 * Z) - 1.0) / (math.exp(2 * Z) + 1.0), 4)
        outfile2 = open(path + pdb_id + '/' + server + '/Correlation_Score/' + pdb_id + '_' + server + '_avg_corr.txt', 'w')
        outfile2.write('##################################################\n')
        outfile2.write('%%% Average correlation coefficient for server %%%\n')
        outfile2.write('##################################################\n')
        outfile2.write('Average R = ' + str(R) + '; Average Z = ' + str(Z) + ' +/-' + str(round(np.std(corr_scores), 4)) + '\n')
        outfile2.write('Calculated from ' + str(len(corr_scores)) + ' SeqFEATURE prediction models.')
        outfile2.close()
    except:
        outfile2 = open(path + pdb_id + '/' + server + '/Correlation_Score/' + pdb_id + '_' + server + '_avg_corr.txt', 'w')
        outfile2.write('##################################################\n')
        outfile2.write('%%% Average correlation coefficient for server %%%\n')
        outfile2.write('##################################################\n')
        outfile2.write('Insufficient data')
        outfile2.close()



########################################################################################################################
# Notes:
# - standard deviation reported is for the z-score converted r-values. This value would have to be back-converted to
# obtain a standard deviation for the averaged r-value
