##############################################################################
##############################################################################
## Script that organizes and runs all newly downloaded data through FEATURE.##
##                                                                          ##
## Created by Joshua Toth, June 2019                                        ##
##############################################################################
##############################################################################

import os, sys, time, datetime, string, commands, subprocess, math, pickle, shelve, shutil

home = '/home/jtoth/ResiRole/'
file_home = home + 'files/'
scripts_home = home + 'scripts/'
feature_home = home + 'FEATURE/'
data_home = home + 'data_by_week/quality_estimation/'
QSUB_home = feature_home + 'QSUB_scripts/'
foutput_home = feature_home + 'raw_output/'
archive = '/home/jtoth/Archive/FEATURE/'

prnt_file = file_home + 'Pipeline_prints.txt'
cluster_stat_file = file_home + 'Cluster_status.txt'

########################################################################################################################
# All new data is first sorted into per-structure directories in /FEATURE/struc_dirs/ and run through dssp. The summary
# file produced in this directory provides a full list of all structures and their models. Then, the FEATURE run is
# performed, all output files going to /FEATURE/raw_output/.
########################################################################################################################

# Parse and create directories
dirs = []
date_file = open(file_home + 'date_sync.txt', 'r')
for line in date_file:
    if 'NEW_DATES:' in line:
        dates = str(line.strip('\n').split('\t')[1].strip('[').strip(']')).split(',')
        for d in dates:
            date = d.strip(' ').strip('\'')
            dirs.append(date)
date_file.close()

qe_paths = {}  # {subdir: {struc: [models] }}
for subdir in dirs:
    qe_paths.update({subdir: {}})
    struc_dirs = os.listdir(data_home + subdir)
    for subdir2 in struc_dirs:
        id = subdir2.split('_')[0]
        chain = subdir2.split('_')[1]
        struc = id + '_' + chain
        server = 'model-' + subdir2.split('_')[2]
        proceed = True
        if subdir2.split('_')[3] != '1':      # Not actually entirely sure what this means - more than 1 model returned by a server for a structure? Just avoid for now
            proceed = False
        if proceed:
            if not os.path.isdir(feature_home + 'struc_dirs/' + id + '/' + chain):
                if not os.path.isdir(feature_home + 'struc_dirs/' + id):
                    os.system('mkdir ' + feature_home + 'struc_dirs/' + id)
                    os.system('mkdir ' + feature_home + 'struc_dirs/' + id + '/' + chain)
                else:
                    os.system('mkdir ' + feature_home + 'struc_dirs/' + id + '/' + chain)
            if not 'target.pdb' in os.listdir(feature_home + 'struc_dirs/' + id + '/' + chain + '/'):
                os.system('cp ' + data_home + subdir + '/' + subdir2 + '/target.pdb ' + feature_home + 'struc_dirs/' + id + '/' + chain + '/.')
                os.system(feature_home + 'dsspcmbi ' + feature_home + 'struc_dirs/' + id + '/' + chain + '/target.pdb > ' + feature_home + 'struc_dirs/' + id + '/' + chain + '/target.dssp')
                qe_paths[subdir].update({struc: []})
            qe_paths[subdir][struc].append(server)
            os.system('cp -p ' + data_home + subdir + '/' + subdir2 + '/model.pdb ' + feature_home + 'struc_dirs/' + id + '/' + chain + '/' + server + '.pdb')
            os.system(feature_home + 'dsspcmbi ' + feature_home + 'struc_dirs/' + id + '/' + chain + '/' + server + '.pdb > ' + feature_home + 'struc_dirs/' + id + '/' + chain + '/' + server + '.dssp')

os.chdir(feature_home + 'struc_dirs/')
for subdir in sorted(qe_paths.keys()):
    sum_file = open(feature_home + 'struc_dirs/summary_' + subdir + '.txt', 'w')
    for struc in sorted(qe_paths[subdir].keys()):
        sum_file.write(subdir + '\t' + struc + '\t' + ','.join(sorted(qe_paths[subdir][struc])) + '\n')
    sum_file.close()
    os.chdir(feature_home + 'struc_dirs/')
    os.system('cat summary_' + subdir + '.txt >> summary.txt')

    sum_file = open('/home/jtoth/ResiRole/FEATURE/struc_dirs/summary_' + subdir + '.txt', 'r')
    for line in sum_file:
        line = line.strip('\n')
        item = line.split('\t')
        if item[-1] != '':
            id = item[1].split('_')[0]
            chain = item[1].split('_')[1]
            model_set = item[-1]
            struc_sum_file = open(feature_home + 'struc_dirs/' + id + '/' + id + '_summary.txt', 'a+')
            struc_sum_file.write(subdir + '\t' + id.lower() + '\t' + chain + '\t' + model_set + '\n')
            struc_sum_file.close()
    sum_file.close()
    os.system('echo New data successfully parsed, summary file for week ' + subdir + ' created. >> ' + prnt_file)

# Create qsubs for cluster run, one qsub per pdb id
id_list = []
for date in dirs:
    sum_file = open(feature_home + 'struc_dirs/summary_' + date + '.txt', 'r')
    for line in sum_file:
        line = line.strip('\n')
        if line.split('\t')[-1] != '':
            pdb_id = line.split('\t')[1].split('_')[0].lower()
            id_list.append(pdb_id)

for pdb_id in id_list:
    template_file = open(file_home + 'feat_qsub_template.txt', 'r')
    qsub_file = open(QSUB_home + '/PMP_qe_' + pdb_id + '.sh', 'w')
    for tline in template_file:
        qline = tline
        if ('<JOB_NAME>' in tline):
            qline = qline.replace('<JOB_NAME>', 'PMP_qe_' + pdb_id)
        if ('<NODE_LIST>' in tline):
            qline = qline.replace('<NODE_LIST>', 'all.q@compute-0-0.local,all.q@compute-0-2.local,all.q@compute-0-3.local,all.q@compute-0-4.local,all.q@compute-0-5.local,all.q@compute-0-6.local,all.q@compute-0-8.local,all.q@compute-0-9.local,all.q@compute-0-10.local,all.q@compute-0-11.local,all.q@compute-0-12.local,all.q@compute-0-13.local,all.q@compute-0-14.local')
        if ('<PDB_ID>' in tline):
            qline = qline.replace('<PDB_ID>', pdb_id)
        if ('<RUN>' in tline):
            qline = qline.replace('<RUN>', '$MPIRUN -np $NSLOTS python ' + scripts_home + 'Run_FEATURE.py ' + pdb_id)
        qsub_file.write(qline)

    template_file.close()
    qsub_file.close()


# Perform the run
for file in os.listdir(feature_home + 'sge_err/'):
    os.system('rm ' + feature_home + 'sge_err/' + file)
for file in os.listdir(feature_home + 'sge_out/'):
    os.system('rm ' + feature_home + 'sge_out/' + file)

os.system('echo Beginning cluster run for FEATURE. Time: ' + str(time.strftime('%H:%M:%S', time.localtime())) + ' >> ' + prnt_file)
qsub_list = os.listdir(QSUB_home)
for job_name in sorted(qsub_list):
    if 'PMP' in job_name:
        os.system('qsub ' + QSUB_home + job_name)

os.system('echo ' + str(len(qsub_list)) + ' PDBIDs are being featurized... >> ' + prnt_file)

# cluster control loop, checks if jobs are still running and if not, checks that there were no errors. If uncorrectable errors are seen, the pipeline will terminate.
running = True
complete = False
watch_list = {}
while(running or not complete):
    time.sleep(600)
    os.system('qstat > ' + cluster_stat_file)
    f = open(cluster_stat_file, 'r')
    status = f.readlines()
    if len(status) == 0:
        running = False
        problem = False
        for file in os.listdir(feature_home + 'sge_err/'):
            err_file = open(feature_home + 'sge_err/' + file, 'r')
            for line in err_file:
                id = str(file).split('_')[1].split('.')[0]
                if 'Killed' in line or 'killed' in line:
                    problem = True
                    os.system('echo Memory overflow detected with job for ' + id + '. Resubmitting the qsub. If problem persists, pipeline will terminate. >> ' + prnt_file)
                    job = 'PMP_qe_' + id + '.sh'
                    if job not in watch_list:
                        watch_list.update({job: 1})
                    else:
                        watch_list[job] = watch_list[job] + 1
                    if watch_list[job] >= 5:
                        sys.exit()
                    else:
                        os.system('qsub ' + QSUB_home + job)
                elif 'Error' in line or 'error' in line:
                    if 'No PDB IDs' in line or 'Environment:' in line:   # This error means no applicable sites were found in the model passed to the program. Could be because
                        continue                                         # there are no residues of that type or because data is actually missing. Either way it is handled later.
                    else:
                        os.system('echo Error detected for job '+ id + '. Pipeline terminating. >> ' + prnt_file)
                        sys.exit()
        if not problem:
            complete = True
        else:
            complete = False
    else:
        running = True
        complete = False

os.system('echo FEATURE run complete at ' + str(time.strftime('%H:%M:%S', time.localtime())) + ' >> ' + prnt_file)

# Cleanup, structures older than a year can be removed from data and FEATURE directories
strucs_rm_file = open(file_home + 'strucs_rm.txt', 'r')
for line in strucs_rm_file:
    if line.startswith('1-Year:'):
        strucs = line.strip('\n').split('\t')[1].strip(']').strip('[').split(',')
        for struc in strucs:
            if struc == '':
                pass
            else:
                id = struc.split('_')[0]
                c = id.lower()
                if os.path.isdir(feature_home + 'struc_dirs/' + id):
                    os.system('cp -r ' + feature_home + 'struc_dirs/' + id + ' ' + archive + 'struc_dirs/' + id)
                    os.system('rm -rf ' + feature_home + 'struc_dirs/' + id + '/')
                if os.path.isdir(feature_home + 'run_files/' + struc):
                    os.system('cp -r ' + feature_home + 'run_files/' + struc + ' ' + archive + 'run_files/' + struc)
                    os.system('rm -rf ' + feature_home + 'run_files/' + struc + '/')
                for file in os.listdir(feature_home + 'PDB/'):
                    if c in file:
                        os.system('rm ' + feature_home + 'PDB/' + file)
                for file in os.listdir(feature_home + 'DSSP/'):
                    if c in file:
                        os.system('rm ' + feature_home + 'DSSP/' + file)
                for file in os.listdir(feature_home + 'QSUB_scripts/'):
                    if c in file:
                        os.system('rm ' + feature_home + 'QSUB_scripts/' + file)
                for file in os.listdir(feature_home + 'raw_output/'):
                    if c in file:
                        os.system('cp ' + feature_home + 'raw_output/' + file + ' ' + archive + 'output/' + file)
                        os.system('rm ' + feature_home + 'raw_output/' + file)
                for file in os.listdir(feature_home + 'sge_out/'):
                    if c in file:
                        os.system('rm ' + feature_home + 'sge_out/' + file)
                for file in os.listdir(feature_home + 'sge_err/'):
                    if c in file:
                        os.system('rm ' + feature_home + 'sge_err/' + file)
