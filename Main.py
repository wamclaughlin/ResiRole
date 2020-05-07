###########################################################################
###########################################################################
## Main script controlling automated run sequence for ResiRole pipeline. ##
##                                                                       ##
## Created by Joshua Toth, June 2019                                     ##
###########################################################################
###########################################################################

import os, sys, time, datetime, string, commands, subprocess, math, pickle, shelve, shutil, urllib as url

home = '/home/jtoth/ResiRole/'
file_home = home + 'files/'
scripts_home = home + 'scripts/'
feature_home = home + 'FEATURE/'
download_home = home + 'data_by_week/'
data_home = download_home + 'quality_estimation/'
QSUB_home = home + 'QSUB_scripts/'
output_home = '/home/jtoth/For_Display/'
web_tab_home = '/home/jtoth/Web_Tables/'

prnt_file = file_home + 'Pipeline_prints.txt'

########################################################################################################################

# The weekly pipeline:

for file in os.listdir(file_home):
    if file == 'Pipeline_prints.txt':
        os.system('rm ' + file_home + 'Pipeline_prints.txt')

##############################################################
# Gather weekly data from CAMEO into appropriate directories #
##############################################################
os.system('echo Beginning weekly analysis pipeline. Time: ' + str(time.strftime('%H:%M:%S', time.localtime())) + ' >> ' + prnt_file)

error = False

try:
    os.chdir(home)
    os.system('rm *.gz')
except:
    pass

try:
    link = 'https://www.cameo3d.org/static/downloads/quality_estimation/1-year/raw_targets-1-year.public.tar.gz'
    url.urlretrieve(link, home + 'raw_targets-1-year.public.tar.gz')

    os.chdir(home)
    os.system('tar -zxvf raw_targets-1-year.public.tar.gz -C ' + download_home)     # This will unpack new week's data to existing directory
except:
    os.system('echo Error in link retrieval. Halting execution. >> ' + prnt_file)
    error = True

if error:
    sys.exit()      # Kill the run if there is a problem with initial data retrieval.

######################################################################################################
# Update the date synchronization file to present and check if Z-score thresholds are due for update #
######################################################################################################

os.system('/usr/local/bin/python2.7 ' + scripts_home + 'Date_Sync.py')

update = False
if 'update_time.txt' in os.listdir(file_home):
    update = True

##########################################################
# Run new data through FEATURE and remove old structures #
##########################################################

os.system('/usr/local/bin/python2.7 ' + scripts_home + 'Featurize_New_Data.py')

#######################################################################################################################
# Assign Z-scores and parse data appropraitely for the per-server analysis, or replenish all data with new thresholds #
#######################################################################################################################

os.system('/usr/local/bin/python2.7 ' + scripts_home + 'Z-score_Thresholding.py ' + str(update))

######################################################################################################################
# Perform the ROC analysis per server to find the average Youden Index which identifies the optimal cutoff threshold #
######################################################################################################################

os.system('/usr/local/bin/python2.7 ' + scripts_home + 'ROC_Analysis.py')

#######################################################################################################################
# Calculate difference scores and model/target correlation coefficients per server using the optimal cutoff threshold #
#######################################################################################################################

os.system('/usr/local/bin/python2.7 ' + scripts_home + 'Z-Score_Analysis.py')

###############################################################################################################
# Parse and re-group the data to examine common subsets and per-structure performance. Then, run the analyses #
###############################################################################################################

os.system('/usr/local/bin/python2.7 ' + scripts_home + 'Head_To_Head_Comparisons_Setup.py')

os.system('echo Weekly analysis pipeline run complete. Time: ' + str(time.strftime('%H:%M:%S', time.localtime())) + ' >> ' + prnt_file)
########################################################################################################################

os.system('/usr/local/bin/python2.7 ' + scripts_home + 'Make_Web_Tables.py')

for file in os.listdir(web_tab_home + 'Avg_tables/'):
    os.system('scp ' + web_tab_home + 'Avg_tables/' + file + ' root@204.139.53.103:/opt/tomcat8/webapps/ResiRole/tables/' + file)

os.system('scp ' + web_tab_home + 'Other/header.jsp root@204.139.53.103:/opt/tomcat8/webapps/ResiRole/header.jsp')


# Notes:
# - See the README file in the main directory for more information