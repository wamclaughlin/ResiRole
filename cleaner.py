import os,sys,time

home = '/home/jtoth/ResiRole/'
feature_home = home + 'FEATURE/run_files/'

for struc in os.listdir(feature_home):
    subdir1 = feature_home + struc + '/'
    for model in os.listdir(subdir1):
        subdir2 = subdir1 + model + '/'
        for f_model in os.listdir(subdir2):
            os.chdir(subdir2 + f_model + '/')
            print 'a'
            os.system('rm *.hits')
            os.system('rm *.sorted')
            os.system('rm -rf backup_hits/')


