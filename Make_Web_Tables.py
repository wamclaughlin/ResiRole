###########################################################################
###########################################################################
## Script to pull all data from the automation into html tables.         ##
##                                                                       ##
## Created by Joshua Toth, September 2019                                ##
###########################################################################
###########################################################################

import os, sys, time, datetime, string, commands, subprocess, math, pickle, shelve, shutil, urllib as url

output_home = '/home/jtoth/For_Display/'
web_tab_home = '/home/jtoth/Web_Tables/'
file_home = '/home/jtoth/ResiRole/files/'

time_frames = {'1-Week': 1, '1-Month': 4, '3-Months': 13, '6-Months': 26, '1-Year': 52}
data_sets = ['All', 'Modeled']
server_names = {'model-4': 'HHPredB', 'model-5': 'IntFOLD', 'model-11': 'Robetta', 'model-12': 'IntFOLD2-TS', 'model-13': 'M4T', 'model-17': 'Phyre2', 'model-20': 'SWISS-MODEL', 'model-22': 'RaptorX', 'model-27': 'Princeton-TEMPLATE', 'model-30': 'SPARKS-X', 'model-31': 'NaiveBlitz', 'model-32': 'RBO-Aleph', 'model-33': 'IntFOLD3-TS', 'model-36': 'NaiveBLAST', 'model-58': 'IntFOLD4-TS', 'model-61': 'PRIMO', 'model-62': 'PRIMO_BST_3D', 'model-63': 'PRIMO_HHS_3D', 'model-64': 'PRIMO_HHS_CL', 'model-65': 'PRIMO_BST_CL', 'model-68': 'SWISS-MODEL_Beta', 'model-70': 'M4T-SMOTIF-TF', 'model-75': 'IntFOLD5-TS'}
server_urls = {'model-4': 'toolkit.tuebingen.mpg.de/hhpred/', 'model-5': 'reading.ac.uk/bioinf/IntFOLD/', 'model-11': 'www.robetta.org', 'model-12': 'reading.ac.uk/bioinf/IntFOLD/', 'model-13': 'manaslu.fiserlab.org/M4T/', 'model-17': 'www.sbg.bio.ic.ac.uk/phyre2/html/page.cgi?id=index', 'model-20': 'swissmodel.expasy.org/interactive/', 'model-22': 'raptorx.uchicago.edu/StructurePrediction/predict/', 'model-27': '/atlas.princeton.edu/template/', 'model-30': 'sparks-lab.org/yueyang/server/SPARKS-X/index.php', 'model-31': '', 'model-32': 'compbio.robotics.tu-berlin.de/rbo_aleph/', 'model-33': 'reading.ac.uk/bioinf/nFOLD/', 'model-36': '', 'model-58': 'www.reading.ac.uk/bioinf/IntFOLD/', 'model-61': 'primo.rubi.ru.ac.za', 'model-62': 'primo.rubi.ru.ac.za', 'model-63': 'primo.rubi.ru.ac.za', 'model-64': 'primo.rubi.ru.ac.za', 'model-65': 'primo.rubi.ru.ac.za', 'model-68': 'beta.swissmodel.expasy.org/interactive/', 'model-70': 'manaslu.fiserlab.org/M4T/', 'model-75': 'reading.ac.uk/bioinf/IntFOLD/'}
date_objs = {} #{frame: date_obj}

for frame in time_frames:
    for set in data_sets:
        if set == 'All':
            path = output_home + 'All_Targets/' + frame + '/Per_Server/'

            # Gather time frame's data
            data_dict = {}  #{server: {'Diff': {'Avg': avg}, {'Std': std}}, {'Corr': {'Avg': avg}, {'Std': std}}}
            for server in os.listdir(path):
                if server != 'target':
                    data_dict.update({server: {}})
                    data_dict[server].update({'Diff': {}})
                    data_dict[server].update({'Corr': {}})
                    diffscore_report = open(path + server + '/Difference_Score/' + server + '_average.txt', 'r')
                    for line in diffscore_report:
                        if line.startswith('Average'):
                            diff_avg = line.strip('\n').split('=')[1].split('+')[0]
                            diff_std = line.strip('\n').split('=')[1].split('-')[1]
                            data_dict[server]['Diff'].update({'Avg': diff_avg})
                            data_dict[server]['Diff'].update({'Std': diff_std})
                    diffscore_report.close()
                    corrscore_report = open(path + server + '/Correlation_Score/' + server + '_average.txt', 'r')
                    for line in corrscore_report:
                        if line.startswith('Average'):
                            corr_avg = float(line.strip('\n').split('=')[1].split('+')[0])
                            z_avg = round(.5 * (math.log((1.0 + corr_avg) / (1.0 - corr_avg))), 4)
                            z_std = line.strip('\n').split('=')[1].split('-')[1]
                            data_dict[server]['Corr'].update({'Corr_Avg': str(corr_avg)})
                            data_dict[server]['Corr'].update({'Z_Avg': str(z_avg)})
                            data_dict[server]['Corr'].update({'Std': z_std})
                    corrscore_report.close()

            # Make the javascript for the table
            table_entry = '\t\t\t[\'Structure Prediction Technique\', \'Average Difference Score\',  \'Std Dev Difference Score\', \'Average Correlation Score (Pearson <i>r</i>)\', \'Average Correlation Score (Converted Z-Score)\', \'Std Dev Correlation Score (Converted Z-Score)\', \'Weblink\']'
            for server in data_dict:
                if server_urls[server] != '':
                    table_entry = table_entry + ',\n\t\t\t[\'' + server_names[server] + '\', ' + data_dict[server]['Diff']['Avg'] + ', ' + data_dict[server]['Diff']['Std'] + ', ' + data_dict[server]['Corr']['Corr_Avg'] + ', ' + data_dict[server]['Corr']['Z_Avg'] + ', ' + data_dict[server]['Corr']['Std'] + ', \'<a href="http://' + server_urls[server] + '">' + server_names[server] + '</a>\']'
                else:
                    table_entry = table_entry + ',\n\t\t\t[\'' + server_names[server] + '\', ' + data_dict[server]['Diff']['Avg'] + ', ' + data_dict[server]['Diff']['Std'] + ', ' + data_dict[server]['Corr']['Corr_Avg'] + ', ' + data_dict[server]['Corr']['Z_Avg'] + ', ' + data_dict[server]['Corr']['Std'] + ', \'\']'
            # Make the javascript for the dates and time frame
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
            startweek = len(dates.keys()) - time_frames[frame]
            endweek = len(dates.keys())
            if frame == '1-Week':
                date_obj = str(frame) + ' (' + dates[startweek + 1] + ')'
                date_objs.update({frame: date_obj})
            else:
                date_obj = '\t\t' + str(frame) + ' (' + dates[startweek + 1] + ' - ' + dates[endweek] + ')'
                date_objs.update({frame: date_obj})
            gen_date = '\t\tTable generated on ' + str(datetime.date.today())

            # write the file using the template
            template = open(file_home + 'web_table_template.txt', 'r')
            outfile = open(web_tab_home + 'Avg_tables/Metrics_Table_' + frame + '.jsp', 'w')
            for line in template:
                if '<<TABLE_ENTRY>>' in line:
                    outfile.write(table_entry)
                elif '<<FRAME_DATE>>' in line:
                    outfile.write(date_obj)
                elif '<<GEN_DATE>>' in line:
                    outfile.write(gen_date)
                else:
                    outfile.write(line)
            outfile.close()
            template.close()

# Write the date ranges to the header file
header_temp = open(file_home + 'web_header_template.txt', 'r')
header_outfile = open(web_tab_home + 'Other/header.jsp', 'w')
for line in header_temp:
    if '<<FRAME' in line:
        for frame in date_objs:
            if frame in line:
                header_outfile.write('\t\t\t' + date_objs[frame])
    else:
        header_outfile.write(line)
header_outfile.close()
header_temp.close()