###################################################################################
###################################################################################
## Script that sets up the head-to-head comparisons of servers and finds strucs  ##
## in common. Also controls Qsubs for the cluster run of the subsequent analysis ##
##                                                                               ##
## Created by Joshua Toth, June 2019                                             ##
###################################################################################
###################################################################################

import os, sys, time, datetime, string, commands, subprocess, math, pickle, shelve, shutil, itertools

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
archive = '/home/jtoth/Archive/Head_to_head/'

prnt_file = file_home + 'Pipeline_prints.txt'
cluster_stat_file = file_home + 'Cluster_status.txt'

cutoff_dict = {'100': 1.00, '99': 0.99, '95': 0.95, '90': 0.90, '80': 0.80, '70': 0.70, '60': 0.60, '50': 0.50, '40': 0.40, '30': 0.30, '20': 0.20, '10': 0.10, '5': 0.05, '1': 0.01, '0': 0.00}
time_frames = {'1-Week': 1, '1-Month': 4, '3-Months': 13, '6-Months': 26, '1-Year': 52}
data_sets = ['All', 'Modeled']

########################################################################################################################
# First, identify all possible combinations of servers present in each time frame's data. Set up directories and
# then identify the structures in common between each pair of servers. Then, run jobs to do each comparison's
# calculations and globally average the end results.
########################################################################################################################

os.system('echo Setting up head-to-head comparisons by finding structures in common between servers... >> ' + prnt_file)

for data in data_sets:
    #if data == 'Modeled':
    if data == 'All':
        dates = {}  # {index: week}
        date_file = open(file_home + 'date_sync.txt', 'r')
        for line in date_file:
            if line.startswith('%%%') or line.startswith('NEW_DATES') or line.startswith('YEAR_MARK'):
                continue
            else:
                index = int(line.strip('\n').split('\t')[0])
                week = line.strip('\n').split('\t')[1]
                dates.update({index: week})
        date_file.close()
        for frame in time_frames:
            path = output_home + 'All_Targets/' + frame + '/'

            invalid_frame = False
            startweek = len(dates.keys()) - time_frames[frame]
            endweek = len(dates.keys())
            if startweek < 0:
                invalid_frame = True
            if not invalid_frame:
                path = path + 'Head_to_head/'
                if not os.path.isdir(path):
                    os.system('mkdir ' + path)
                server_combs = {}   # {server1: {server2: [common_strucs]}}
                servers = os.listdir(output_home + 'All_Targets/' + frame + '/Per_Server/')
                servers.remove('target')
                d = []
                for x in itertools.combinations(sorted(servers), 2):    # this returns an iteratable of tuples of all combinations of servers for the time frame
                    if x[0] in server_combs:
                        server_combs[x[0]].update({x[1]: []})
                    else:
                        server_combs.update({x[0]: {x[1]: []}})
                strucs_file = open(feature_home + 'struc_dirs/summary.txt', 'r')
                for line in strucs_file:       # if the structure was modeled by both servers during the time frame, add it to the list
                    if line.startswith('%%%'):
                        continue
                    models = line.strip('\n').split('\t')[-1].split(',')
                    struc = line.strip('\n').split('\t')[1]
                    date = line.strip('\n').split('\t')[0]
                    for server1 in server_combs:
                        if server1 in models:
                            for server2 in server_combs[server1]:
                                if server2 in models:
                                    for index in dates:
                                        if dates[index] == date:
                                            if index > startweek:
                                                server_combs[server1][server2].append(struc)
                strucs_file.close()

                # Remove and archive old data and servers
                if frame == '1-Week':
                    os.chdir(path)
                    os.system('rm -rf -- Head_to_head')
                else:
                    rm_file = open(file_home + 'strucs_rm.txt', 'r')
                    old_strucs = []
                    for line in rm_file:
                        if line.startswith('%%%'):
                            continue
                        elif line.startswith(frame):
                            strucs = line.strip('\n').split('\t')[1].strip(']').strip('[').split(',')
                            for struc in strucs:
                                old_strucs.append(struc)
                    rm_file.close()

                    rm_file2 = open(file_home + 'servs_rm.txt', 'r')
                    old_servs = []
                    for line in rm_file2:
                        if line.startswith('%%%'):
                            continue
                        else:
                            line = line.strip('\n').split('\t')
                            server = line[0]
                            record = line[1]
                            if int(record) - time_frames[frame] > 0:
                                old_servs.append(server)
                    rm_file2.close()

                    for comp_dir in os.listdir(path):
                        model1 = str(comp_dir).split('_')[0]
                        model2 = str(comp_dir).split('_')[1]
                        if model1 in old_servs or model2 in old_servs:
                            os.system('rm -r ' + path + comp_dir + '/')
                        elif len(old_strucs) != 0:
                            if os.path.isdir(path + comp_dir + '/Per_Structure/Difference_Score/'):
                                for struc_dir in os.listdir(path + comp_dir + '/Per_Structure/Difference_Score/'):
                                    if str(struc_dir) in old_strucs:
                                        if comp_dir not in os.listdir(archive):
                                            os.system('mkdir ' + archive + comp_dir)
                                            os.system('mkdir ' + archive + comp_dir + '/Difference_Score/')
                                            os.system('mkdir ' + archive + comp_dir + '/Correlation_Score/')
                                        os.system('cp -r ' + path + comp_dir + '/Per_Structure/Difference_Score/' + struc_dir + ' ' + archive + comp_dir + '/Difference_Score/' + struc_dir)
                                        os.chdir(path + comp_dir + '/Per_Structure/Difference_Score/')
                                        os.system('rm -rf -- ' + struc_dir)
                                        os.system('cp -r ' + path + comp_dir + '/Per_Structure/Correlation_Score/' + struc_dir + ' ' + archive + comp_dir + '/Correlation_Score/' + struc_dir)
                                        os.chdir(path + comp_dir + '/Per_Structure/Correlation_Score/')
                                        os.system('rm -rf -- ' + struc_dir)

                # make new directories and an output file of strucs in common
                for server1 in server_combs:
                    for server2 in server_combs[server1]:
                        if not os.path.isdir(path + server1 + '_' + server2 + '/'):
                            os.system('mkdir ' + path + server1 + '_' + server2 + '/')
                            os.system('mkdir ' + path + server1 + '_' + server2 + '/Overall/')
                            os.system('mkdir ' + path + server1 + '_' + server2 + '/Per_Structure/')
                        strucs_in_common = open(path + server1 + '_' + server2 + '/structures.txt', 'w')
                        strucs_in_common.write('%%% List of structures in common between the two given servers for the given time frame %%%\n')
                        for struc in server_combs[server1][server2]:
                            strucs_in_common.write(struc + '\n')
                        strucs_in_common.close()

                        # Qsubs and cluster run
                        template_file = open(file_home + 'head_to_head_template.txt', 'r')  # make qubs
                        qsub_file = open(QSUB_home + 'HTH_' + frame + '_' + server1 + '_' + server2 + '.sh', 'w')
                        for tline in template_file:
                            qline = tline
                            if ('<server1>' in tline):
                                qline = qline.replace('<server1>', server1)
                            if ('<server2>' in tline):
                                qline = qline.replace('<server2>', server2)
                            if ('<frame>' in tline):
                                qline = qline.replace('<frame>', frame)
                            if ('<TARGET_RUN>' in tline):
                                trun_line = 'python ' + scripts_home + 'Head_To_Head_Comparisons_Analysis.py ' + frame + ' ' + server1 + ' ' + server2
                                qline = qline.strip('\n').replace('<TARGET_RUN>', trun_line)
                            qsub_file.write(qline)

                        template_file.close()
                        qsub_file.close()

                for file in os.listdir(home + 'pipeline_sge/sge_err/'):
                    if 'HTH' in str(file) and frame in str(file):
                        os.system('rm ' + home + 'pipeline_sge/sge_err/' + file)
                for file in os.listdir(home + 'pipeline_sge/sge_out/'):
                    if 'HTH' in str(file) and frame in str(file):
                        os.system('rm ' + home + 'pipeline_sge/sge_out/' + file)

                os.system('echo Beginning head-to-head cluster run. Time: ' + str(time.strftime('%H:%M:%S', time.localtime())) + ' >> ' + prnt_file)
                qsub_list = os.listdir(QSUB_home)
                for job_name in sorted(qsub_list):
                    if 'HTH' in job_name and frame in job_name:
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
                            if 'HTH' in str(file):
                                err_file = open(home + 'pipeline_sge/sge_err/' + file, 'r')
                                for line in err_file:
                                    frame = str(file).split('_')[1]
                                    serv1 = str(file).split('_')[2]
                                    serv2 = str(file).split('_')[3]
                                    if 'Killed' in line or 'killed' in line:
                                        problem = True
                                        os.system('echo Memory overflow detected with job for ' + frame + '_' + serv1 + '_' + serv2 + '. Resubmitting the qsub. If problem persists, pipeline will terminate. >> ' + prnt_file)
                                        job = 'HTH_' + frame + '_' + serv1 + '_' + serv2 + '.sh'
                                        if job not in watch_list:
                                            watch_list.update({job: 1})
                                        else:
                                            watch_list[job] = watch_list[job] + 1
                                        if watch_list[job] >= 5:
                                            sys.exit()
                                        else:
                                            os.system('qsub ' + QSUB_home + job)
                                    elif 'Error' in line or 'error' in line:
                                        os.system('echo Error detected for job ' + frame + '_' + serv1 + '_' + serv2 + '. Pipeline terminating. >> ' + prnt_file)
                                        sys.exit()
                        if not problem:
                            complete = True
                        else:
                            complete = False
                    else:
                        running = True
                        complete = False

########################################################################################################################
# Notes:
# - all head-to-head directories are created dynamically as necessary
# - comparisons are based on the servers seen in each time frame, so if a new server becomes active, its data will not
# necessarily be included in the longer time frames until it is active on CAMEO for that duration. Likewise, if a server
# goes inactive, its data will begin to be phased out from the shortest time frames.
# - cluster runs organized per comparison and per time frame, so there are a lot of jobs. It may be possible to combine
# all time frames into one job in the future if this is problematic.
