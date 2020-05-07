##################################################################################
##################################################################################
## Overhead for scripts that will perform the calculations of difference scores ##
## and correlation coefficients.                                                ##
##                                                                              ##
## Created by Joshua Toth, June 2019                                            ##
##################################################################################
##################################################################################

import os, sys, time, datetime, string, commands, subprocess, math, pickle, shelve, shutil, numpy as np

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

prnt_file = file_home + 'Pipeline_prints.txt'
cluster_stat_file = file_home + 'Cluster_status.txt'

cutoff_dict = {'100': 1.00, '99': 0.99, '95': 0.95, '90': 0.90, '80': 0.80, '70': 0.70, '60': 0.60, '50': 0.50, '40': 0.40, '30': 0.30, '20': 0.20, '10': 0.10, '5': 0.05, '1': 0.01, '0': 0.00}
time_frames = {'1-Week': 1, '1-Month': 4, '3-Months': 13, '6-Months': 26, '1-Year': 52}
data_sets = ['All', 'Modeled']

########################################################################################################################
# Create Qsubs to run the per-server Z-score analysis on the cluster. It is currently organized such that there is one
# job per server which will output both the difference scores and correlation coefficients for all time frames for that
# server. Afterward, average these metrics and report before moving to the head-to-head part of the pipeline.
########################################################################################################################

os.system('echo Running Z-Score analyses on all servers. >> ' + prnt_file)

for data in data_sets:
    # if data == 'Modeled':
        # Here is where I would separate out the modeled structures from all data if I knew how to do that
    if data == 'All':
        path = output_home + 'All_Targets/'
        dates = {}  # {index: week}
        strucs_file = open(file_home + 'date_sync.txt', 'r')
        for line in strucs_file:
            if line.startswith('%%%') or line.startswith('NEW_DATES') or line.startswith('YEAR_MARK'):
                continue
            else:
                index = int(line.strip('\n').split('\t')[0])
                week = line.strip('\n').split('\t')[1]
                dates.update({index: week})
        strucs_file.close()

        '''
        for frame in time_frames:
            path = path + frame + '/'
            invalid_frame = False
            startweek = len(dates.keys()) - time_frames[frame]
            endweek = len(dates.keys())
            if startweek < 0:
                invalid_frame = True
            if not invalid_frame:

                # create Qsubs
                path = output_home + 'All_Targets/' + frame + '/Per_Server/'      # Splitting up by time frame is important because servers can come and go week by week
                for server in os.listdir(path):
                    if server != 'target':
                        template_file = open(file_home + 'Z-score_template.txt', 'r')
                        qsub_file = open(QSUB_home + 'Z-score_' + server + '_' + frame + '.sh', 'w')
                        for tline in template_file:
                            qline = tline
                            if ('<time_frame>' in tline):
                                qline = qline.replace('<time_frame>', '_' + frame)
                            if ('<server>' in tline):
                                qline = qline.replace('<server>', server)
                            if ('<TARGET_RUN>' in tline):
                                trun_line = 'python ' + scripts_home + 'Z-Score_Calculations.py ' + server + ' ' + frame
                                qline = qline.strip('\n').replace('<TARGET_RUN>', trun_line)
                            qsub_file.write(qline)

                        template_file.close()
                        qsub_file.close()

        # run Qsubs
        for file in os.listdir(home + 'pipeline_sge/sge_err/'):
            if 'Z' in str(file):
                os.system('rm ' + home + 'pipeline_sge/sge_err/' + file)
        for file in os.listdir(home + 'pipeline_sge/sge_out/'):
            if 'Z' in str(file):
                os.system('rm ' + home + 'pipeline_sge/sge_out/' + file)

        os.system('echo Beginning Z-score cluster run. Time: ' + str(time.strftime('%H:%M:%S', time.localtime())) + ' >> ' + prnt_file)
        qsub_list = os.listdir(QSUB_home)
        for job_name in sorted(qsub_list):
            if 'Z-score' in job_name:
                os.system('qsub ' + QSUB_home + job_name)

        # cluster control loop, checks if jobs are still running and if not, checks that there were no errors. If uncorrectable errors are seen, the pipeline will terminate.
        running = True
        complete = False
        watch_list = {}
        while (running or not complete):
            time.sleep(600)
            os.system('qstat > ' + cluster_stat_file)
            f = open(cluster_stat_file, 'r')
            status = f.readlines()
            if len(status) == 0:
                running = False
                problem = False
                for file in os.listdir(home + 'pipeline_sge/sge_err/'):
                    if 'Z' in str(file):
                        err_file = open(home + 'pipeline_sge/sge_err/' + file, 'r')
                        for line in err_file:
                            frame = str(file).split('_')[-1].split('.')[0]
                            serv = str(file).split('_')[-2]
                            if 'Killed' in line or 'killed' in line:
                                problem = True
                                os.system('echo Memory overflow detected with job for ' + serv + '_' + frame + '. Resubmitting the qsub. If problem persists, pipeline will terminate. >> ' + prnt_file)
                                job = 'Z-score_' + serv + '_' + frame + '.sh'
                                if job not in watch_list:
                                    watch_list.update({job: 1})
                                else:
                                    watch_list[job] = watch_list[job] + 1
                                if watch_list[job] >= 5:
                                    sys.exit()
                                else:
                                    os.system('qsub ' + QSUB_home + job)
                            elif 'Error' in line or 'error' in line:
                                os.system('echo Error detected for job ' + serv + '_' + frame + '. Pipeline terminating. >> ' + prnt_file)
                                sys.exit()
                if not problem:
                    complete = True
                else:
                    complete = False
            else:
                running = True
                complete = False

        
        os.system('echo Calculating averages of Z-score metrics. >> ' + prnt_file)
        '''
        for frame in time_frames:
            path = output_home + 'All_Targets/' + frame + '/Per_Server/'
            for server in os.listdir(path):
                if server != 'target':
                    diff_score_file = open(path + server + '/Difference_Score/' + server + '_diff_scores.txt', 'r')
                    diff_scores = []
                    for line in diff_score_file:
                        if line.startswith('%%%'):
                            continue
                        else:
                            score = abs(float(line.strip('\n').split('\t')[-1]))       # Use abs of diff score for averaging
                            diff_scores.append(score)
                    diff_score_file.close()
                    corr_score_file = open(path + server + '/Correlation_Score/' + server + '_corr_scores.txt', 'r')
                    corr_scores = []
                    for line in corr_score_file:
                        if line.startswith('%%%'):
                            continue
                        elif 'Error' in line:
                            continue
                        else:
                            r = float(line.strip('\n').split('\t')[1])
                            if r != 1.0 and r != -1.0:
                                z = .5 * (math.log((1.0 + r) / (1.0 - r)))
                                corr_scores.append(z)
                    corr_score_file.close()

                    outfile1 = open(path + server + '/Difference_Score/' + server + '_average.txt', 'w')
                    outfile1.write('%%% Average difference score for server %%%\n')
                    outfile1.write('Average = ' + str(round(sum(diff_scores) / len(diff_scores), 4)) + ' +/-' + str(round(np.std(diff_scores), 4)) + '\n')
                    outfile1.write('Calculated from ' + str(len(diff_scores)) + ' unique instances of functional predictions.')
                    outfile1.close()

                    Z = sum(corr_scores) / len(corr_scores)
                    R = round((math.exp(2 * Z) - 1.0) / (math.exp(2 * Z) + 1.0), 4)

                    outfile2 = open(path + server + '/Correlation_Score/' + server + '_average.txt', 'w')
                    outfile2.write('%%% Average correlation coefficient for server %%%\n')
                    outfile2.write('Average R = ' + str(R) + '; Average Z = ' + str(Z) + ' +/-' + str(round(np.std(corr_scores), 4)) + '\n')
                    outfile2.write('Calculated from ' + str(len(corr_scores)) + ' SeqFEATURE prediction models.')
                    outfile2.close()

########################################################################################################################
# Notes:
# - standard deviation reported is for the z-score converted r-values. This value would have to be back-converted to
# obtain a standard deviation for the averaged r-value
#
