#############################################################################
#############################################################################
## Script to control the bookeeping of dates in data downloads from CAMEO. ##
##                                                                         ##
## Created by Joshua Toth, June 2019                                       ##
#############################################################################
#############################################################################

import os, sys, time, datetime, string, commands, subprocess, math, pickle, shelve, shutil, datetime

home = '/home/jtoth/ResiRole/'
file_home = home + 'files/'
scripts_home = home + 'scripts/'
feature_home = home + 'FEATURE/'
data_home = home + 'data_by_week/quality_estimation/'
QSUB_home = home + 'QSUB_scripts/'
output_home = '/home/jtoth/For_Display/'

prnt_file = file_home + 'Pipeline_prints.txt'

########################################################################################################################
# Update the date_sync file to the new list of dates that are considered for a year worth of data. This file contains a
# list of past dates and a number index to indicate what number week they were out of the past year such that index = 1
# is oldest and index = 52 is most recent week. If no new dates are seen, no update will occur and the rest of the
# pipeline will not run. If more than one new date is seen, the file will increment accordingly. This program is also
# responsible for creating files to keep track of those structures and servers that become too old in the accumulating
# data to be considered in certain time frames, strucs_rm.txt and servs_rm.txt. Later programs will read from these
# files to remove the appropriate structures and servers from the datasets.
########################################################################################################################

cur_dates = os.listdir(data_home)

new_dates = []
dates = {}      # {index: date}, index is week number where 1 = oldest and 52 = most recent
year_mark = 0
date_file = open(file_home + 'date_sync.txt', 'r')
for line in date_file:
    if '%%%' in line or 'NEW_DATES:' in line:
        continue
    elif line.startswith('YEAR_MARK:'):
        year_mark = int(line.strip('\n').split('\t')[1])
    else:
        index = int(line.strip('\n').split('\t')[1])
        date = line.strip('\n').split('\t')[0]
        dates.update({index: date})

date_file.close()

for date in cur_dates:
     if date not in dates.values():
        new_dates.append(date)

if len(new_dates) == 0:
    os.system('echo No new dates detected. Pipeline terminating. >> ' + prnt_file)
    sys.exit()

for date in new_dates:
    x = len(dates.keys())
    y = 0
    increment = 1
    if x != 0:
        y = max(dates.keys())
    strucs_rm_file = open(file_home + 'strucs_rm.txt', 'w')
    strucs_rm_file.write('%%% Lists of target structures whose data are to be removed and archived on the current weekly cycle. %%%\n')
    if x >= 5:      # if there is more than 1 month of data, need to refresh the month range
        prev_date = dates[y]
        d1 = datetime.date(int(prev_date.split('.')[0]), int(prev_date.split('.')[1]), int(prev_date.split('.')[2]))
        d2 = datetime.date(int(date.split('.')[0]), int(date.split('.')[1]), int(date.split('.')[2]))
        diff = d2 - d1
        increment = (diff.days / 7)    # sometimes a week is skipped, so cannot always just add +1 to the index
        index = y + increment
        dates.update({index: date})
        for i in range(len(dates.keys()), max(dates.keys())):   # This fills in any skipped indices with a copy of the previous date; helps keep the dates to remove consistent.
            dates.update({i: prev_date})
        year_mark = year_mark + increment
        rm_date_12 = ''
        rm_date_6 = ''
        rm_date_3 = ''
        rm_date_1 = ''
        if x >= 14:         # if more than 3 months of data
            if x >= 27:         # if more than half a year of data
                if x == 52:         # if a full year of data
                    rm_date_12 = dates[1]
                    rm_date_6 = dates[26]
                    rm_date_3 = dates[39]
                    rm_date_1 = dates[48]

                    i = 1
                    while i != index:   # increment the weekly index every week after a year
                        repl_date = dates[i + 1]
                        dates.update({i: repl_date})
                        i = i + 1

                    os.chdir(data_home)     # clean up oldest directory so not holding more than one year of data at any time
                    os.system('rmdir -rf ' + rm_date_12)
                else:
                    rm_date_6 = dates[x - 26]
                    rm_date_3 = dates[x - 13]
                    rm_date_1 = dates[x - 4]
            else:
                rm_date_3 = dates[x - 13]
                rm_date_1 = dates[x - 4]
        else:
            rm_date_1 = dates[x - 4]

        strucs_rm_file.write('1-Year:\t')
        if rm_date_12 != '':
            strucs = []
            for dir in os.listdir(data_home + rm_date_12):
                if str(dir).split('_')[0] + '_' + str(dir).split('_')[1] not in strucs:
                    strucs.append(str(dir).split('_')[0] + '_' + str(dir).split('_')[1])
            strucs_rm_file.write(str(strucs) + '\n')
        else:
            strucs_rm_file.write('\n')
        strucs_rm_file.write('6-Months:\t')
        if rm_date_6 != '':
            strucs = []
            for dir in os.listdir(data_home + rm_date_6):
                if str(dir).split('_')[0] + '_' + str(dir).split('_')[1] not in strucs:
                    strucs.append(str(dir).split('_')[0] + '_' + str(dir).split('_')[1])
            strucs_rm_file.write(str(strucs) + '\n')
        else:
            strucs_rm_file.write('\n')
        strucs_rm_file.write('3-Months:\t')
        if rm_date_3 != '':
            strucs = []
            for dir in os.listdir(data_home + rm_date_3):
                if str(dir).split('_')[0] + '_' + str(dir).split('_')[1] not in strucs:
                    strucs.append(str(dir).split('_')[0] + '_' + str(dir).split('_')[1])
            strucs_rm_file.write(str(strucs) + '\n')
        else:
            strucs_rm_file.write('\n')
        strucs2 = []
        for dir in os.listdir(data_home + rm_date_1):
            if str(dir).split('_')[0] + '_' + str(dir).split('_')[1] not in strucs2:
                strucs2.append(str(dir).split('_')[0] + '_' + str(dir).split('_')[1])
        strucs_rm_file.write('1-Month:\t' + str(strucs2) + '\n')

    elif len(dates.keys()) == 0: # if nothing yet, first time run
        dates.update({1: date})
        year_mark = year_mark + 1
    else:                        # else just add the next index
        prev_date = dates[y]
        d1 = datetime.date(int(prev_date.split('.')[0]), int(prev_date.split('.')[1]), int(prev_date.split('.')[2]))
        d2 = datetime.date(int(date.split('.')[0]), int(date.split('.')[1]), int(date.split('.')[2]))
        diff = d2 - d1
        increment = (diff.days / 7)
        index = y + increment
        dates.update({index: date})
        for i in range(len(dates.keys()), max(dates.keys())):
            dates.update({i: prev_date})
        year_mark = year_mark + increment

    strucs_rm_file.close()

    servs_rm_file_in = open(file_home + 'servs_rm.txt', 'r')
    servs = {}      # {server: weeks without being seen}
    for line in servs_rm_file_in:
        if line.startswith('%%%'):
            continue
        else:
            line = line.strip('\n').split('\t')
            server = line[0]
            record = line[1]
            servs.update({server: int(record)})
    servs_rm_file_in.close()
    week_servs = []
    for entry in os.listdir(data_home + date + '/'):
        server = 'model-' + str(entry).split('_')[2]
        if server not in week_servs:
            week_servs.append(server)
    for server in servs:
        if server in week_servs:
            servs.update({server: 1})
        else:
            record = servs[server]
            servs.update({server: record + increment})
    for server in week_servs:
        if server not in servs:
            servs.update({server: 1})
    servs_rm_file = open(file_home + 'servs_rm.txt', 'w')
    servs_rm_file.write('%%% List of modeling servers and the most recent week in which they were encountered in the data %%%\n')
    for server in servs:
        servs_rm_file.write(server + '\t' + str(servs[server]) + '\n')
    servs_rm_file.close()

if year_mark == 53:
    update_file = open(file_home + 'update_time.txt', 'w')
    update_file.write('Date synchronization indicates current week is the first week of a new year. Z-dictionary update recommended.')
    update_file.close()
    year_mark = 1
elif year_mark == 2:
    os.chdir(file_home)
    os.system('rm update_time.txt')

outfile = open(file_home + 'date_sync.txt', 'w')
outfile.write('%%% Dates for past year\'s worth of data (1 = oldest, 52 = most recent) %%%' + '\n')
for week in dates:
    date = dates[week]
    outfile.write(str(week) + '\t' + date + '\n')
outfile.write('NEW_DATES:\t' + str(new_dates) + '\n')
outfile.write('YEAR_MARK:\t' + str(year_mark) + '\n')

outfile.close()

os.system('echo Date syncing and update successful. Current week = ' + str(year_mark) + ' >> ' + prnt_file)