##################################################################################
##################################################################################
## Script that performs the overhead for the ROC analysis and finds the optimal ##
## specificity cutoff as predicted by the average maximum Youden Index.         ##
##                                                                              ##
## Created by Joshua Toth, June 2019                                            ##
##################################################################################
##################################################################################

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
thrsh_data_home = home + 'data_by_threshold/'
archive = '/home/jtoth/Archive/Per_Server/'

prnt_file = file_home + 'Pipeline_prints.txt'
cluster_stat_file = file_home + 'Cluster_status.txt'

cutoff_dict = {'100': 1.00, '99': 0.99, '95': 0.95, '90': 0.90, '80': 0.80, '70': 0.70, '60': 0.60, '50': 0.50, '40': 0.40, '30': 0.30, '20': 0.20, '10': 0.10, '5': 0.05, '1': 0.01, '0': 0.00}
time_frames = {'1-Week': 1, '1-Month': 4, '3-Months': 13, '6-Months': 26, '1-Year': 52}
data_sets = ['All', 'Modeled']

########################################################################################################################
# First, the new data must be added to the data sets which are organized by time frame and by server Then, the same
# files must be checked to remove any structures past 1 year. Then, the ROC analysis could be performed for each
# data set. Lastly, get the average optimal cutoff specificity based on Youden's Indices.
########################################################################################################################

for data in data_sets:
    #if data == 'Modeled':
        # Here is where I would separate out the modeled structures from all data if I knew how to do that
    if data == 'All':
        dates = {}       # {index: week}
        strucs_file = open(file_home + 'date_sync.txt', 'r')
        for line in strucs_file:
            if line.startswith('%%%') or line.startswith('NEW_DATES') or line.startswith('YEAR_MARK'):
                continue
            else:
                index = int(line.strip('\n').split('\t')[0])
                week = line.strip('\n').split('\t')[1]
                dates.update({index: week})
        strucs_file.close()
        for frame in time_frames:
            path = output_home + 'All_Targets/' + frame + '/'

            invalid_frame = False
            startweek = len(dates.keys()) - time_frames[frame]
            endweek = len(dates.keys())
            if startweek < 0:
                invalid_frame = True
            if not invalid_frame:
                os.system('echo Running ROC on time frame ' + frame + ' >> ' + prnt_file)

                # Remove and archive old data and servers
                if frame == '1-Week':
                    os.system('rm -r ' + path + 'Per_Server/')      # For the week, just clear everything
                    os.system('mkdir ' + path + 'Per_Server/')
                else:
                    rm_file = open(file_home + 'strucs_rm.txt', 'r')    # For longer time frames, clear just those strucs and servers too old for the frame
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

                    for server in os.listdir(path + 'Per_Server/'):
                        if server in old_servs:             # clean up servers not seen in current time frame
                            os.chdir(path + 'Per_Server/')
                            os.system('rm -rf -- ' + server)
                        elif len(old_strucs) != 0:          # clean up stuctures over 1 year old in all other servers
                            for cutoff in cutoff_dict:
                                os.system('mv ' + path + 'Per_Server/' + server + '/Data/thrsh_' + cutoff + '.txt ' + path + 'Per_Server/' + server + '/Data/thrsh_' + cutoff + '_2.txt')
                                file = open(path + 'Per_Server/' + server + '/Data/thrsh_' + cutoff + '_2.txt', 'r')
                                new_file = open(path + 'Per_Server/' + server + '/Data/thrsh_' + cutoff + '.txt', 'w, a+')
                                if server not in os.listdir(archive):
                                    os.system('mkdir ' + archive + server)
                                archive_file = open(archive + server + '/' + 'thrsh_' + cutoff + '.txt', 'a+')
                                for line in file:
                                    for struc in old_strucs:
                                        if str(struc) in line:
                                            archive_file.write(line)
                                        else:
                                            new_file.write(line)
                                new_file.close()
                                file.close()
                                archive_file.close()
                                os.system('rm ' + path + 'Per_Server/' + server + '/Data/thrsh_' + cutoff + '_2.txt')

                # Add new data
                new_strucs = {}     # {week: {struc: [models]}}
                Ignore_list = []
                for i in range(startweek, endweek):
                    week = dates[i + 1]
                    new_strucs.update({week: {}})
                    for item in os.listdir(data_home + week):
                        target = {}     # {struc: {thrsh: 'collected'}}
                        if item.split('_')[3] == '1':
                            struc = item.split('_')[0] + '_' + item.split('_')[1]
                            server = 'model-' + item.split('_')[2]
                            if os.path.exists(thrsh_data_home + 'thrsh_0/target/' + struc + '.txt'):    # This ensures target data exists as parsed from FEATURE's output.
                                new_strucs[week].update({struc: []})
                                if struc not in target:
                                    target.update({struc: {}})
                                for cutoff in cutoff_dict:
                                    if cutoff not in target[struc]:
                                        if not os.path.isdir(path + 'Per_Server/target/'):
                                            os.system('mkdir ' + path + 'Per_Server/target/')
                                            os.system('mkdir ' + path + 'Per_Server/target/Data/')
                                            tfile = open(path + 'Per_Server/target/Data/thrsh_' + cutoff + '.txt', 'w')
                                            tfile.write('%%% All data for target separated by threshold %%%\n')
                                            tfile.close()
                                        os.system('cat ' + thrsh_data_home + 'thrsh_' + cutoff + '/target/' + struc + '.txt >> ' + path + 'Per_Server/target/Data/thrsh_' + cutoff + '.txt')
                                        target[struc].update({cutoff: 'collected'})
                                    if not os.path.isdir(path + 'Per_Server/' + server):
                                        os.system('mkdir ' + path + 'Per_Server/' + server)
                                        os.system('mkdir ' + path + 'Per_Server/' + server + '/Data/')
                                        mfile = open(path + 'Per_Server/' + server + '/Data/thrsh_' + cutoff + '.txt', 'w')
                                        mfile.write('%%% All data for server separated by threshold %%%\n')
                                        mfile.close()
                                    os.system('cat ' + thrsh_data_home + 'thrsh_' + cutoff + '/' + server + '/' + struc + '.txt >> ' + path + 'Per_Server/' + server + '/Data/thrsh_' + cutoff + '.txt')
                            else:
                                os.system('echo Structure ' + str(struc) + ' ignored due to lack of target data. >> ' + prnt_file)
                                if struc not in Ignore_list:
                                    Ignore_list.append(struc)

                # ROC         # when we get modeled data set will probably have to add another tag to the subs
                              # if jobs end up being too much could also split by cutoff as well. However, the counts program would have to be done differently
                for server in os.listdir(path + 'Per_Server/'):
                    if server != 'target':
                        template_file = open(file_home + 'ROC_template.txt', 'r')
                        qsub_file = open(QSUB_home + 'ROC_' + server + '_' + frame + '.sh', 'w')
                        for tline in template_file:
                            qline = tline
                            if ('<time_frame>' in tline):
                                qline = qline.replace('<time_frame>', '_' + frame)
                            if ('<server>' in tline):
                                qline = qline.replace('<server>', 'ROC_comp_' + server)
                            if ('<TARGET_RUN>' in tline):
                                trun_line = 'python ' + scripts_home + 'ROC_Calculations.py ' + server + ' ' + frame + ' ' + str(Ignore_list)
                                qline = qline.strip('\n').replace('<TARGET_RUN>', trun_line)
                            qsub_file.write(qline)

                        template_file.close()
                        qsub_file.close()
                

                for file in os.listdir(home + 'pipeline_sge/sge_err/'):
                    if 'ROC' in str(file):
                        os.system('rm ' + home + 'pipeline_sge/sge_err/' + file)
                for file in os.listdir(home + 'pipeline_sge/sge_out/'):
                    if 'ROC' in str(file):
                        os.system('rm ' + home + 'pipeline_sge/sge_out/' + file)

                os.system('echo Beginning ROC cluster run. Time: ' + str(time.strftime('%H:%M:%S', time.localtime())) + ' >> ' + prnt_file)
                qsub_list = os.listdir(QSUB_home)
                for job_name in sorted(qsub_list):
                    if 'ROC' in job_name and str(frame) in job_name:
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
                            if 'ROC' in str(file):
                                err_file = open(home + 'pipeline_sge/sge_err/' + file, 'r')
                                for line in err_file:
                                    frame = str(file).split('_')[-1].split('.')[0]
                                    serv = str(file).split('_')[-2]
                                    if 'Killed' in line or 'killed' in line:
                                        problem = True
                                        os.system('echo Memory overflow detected with job for ' + serv + '_' + frame + '. Resubmitting the qsub. If problem persists, pipeline will terminate. >> ' + prnt_file)
                                        job = 'ROC_' + serv + '_' + frame + '.sh'
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


                # Calculate avg specificity corresponding to max Youden and output for difference score and correlation analysis
                os.system('echo Calculating ideal specificity cutoff... >> ' + prnt_file)
                global_opt_spec = []
                for server in os.listdir(path + 'Per_Server/'):
                    try:
                        infile = open(path + 'Per_Server/' + server + '/ROC_per_function_results.txt', 'r')
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
                Opt_spec = round(sum(global_opt_spec) / len(global_opt_spec), 4)
                outfile = open(path + 'Optimal_Specificity_Report.txt', 'w')
                outfile.write('Global averaging of specificities corresponding to maximum Youden Indices yields:\t' + str(Opt_spec) + '\n')
                Diff = {}
                for cutoff in cutoff_dict:
                    diff = abs(Opt_spec - cutoff_dict[cutoff])
                    Diff.update({diff: cutoff})
                M = min(Diff.keys())
                spec = Diff[M]
                outfile.write('Closest Z-score specificity to implement at this cutoff:\t' + str(spec))
                outfile.close()

########################################################################################################################
# Notes:
# - When introducing the modeled dataset as opposed to all targets, this same code would be repeated, and it would
# probably be a good idea to add another tag to the cluster job names
# - Directories up to /Per_Server/ are manually created, but the code could automatically add in new servers and data