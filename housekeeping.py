import argparse
import logging
import os
import shutil
import sys
import time
from subprocess import call

import yaml

yamlFound = None
print("current script: %s" % (__file__))
for file in os.listdir(os.path.dirname(__file__)):
    if file.endswith(".yaml"):
        yamlFound = file
try:
    print("used yaml file is: %s") % os.path.join(os.path.dirname(__file__), yamlFound)
except:
    print("no yaml file found")
    pass

parser = argparse.ArgumentParser(description="arguments")
parser.add_argument('-logPath', dest='logPath', help='provide path for logs',nargs='?')
parser.add_argument('-createTask', dest='createTask', help='should task be created? (windows scheduled task)',nargs='?')
args = parser.parse_args()

if args.createTask not in ['yes', 'no']:
    sys.exit("createTask argument should be 'yes' or 'no'")

logPath = args.logPath
if not logPath:
    if not os.name == 'posix': logPath = 'c:/temp'; python = "c:/python27/python.exe"
    else: logPath = '/tmp'; python = "/usr/bin/python"
else:
    if not os.name == 'posix':
        python = "c:/python27/python.exe"
    else:
        python = "/usr/bin/python"

if not os.path.exists(logPath):
    os.makedirs(logPath)


# LOGGING
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)-16s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename=os.path.join(logPath,'%s_%s.log') % (os.path.basename(__file__), time.strftime('%Y%m%d%H%M%S')),
                    filemode='w')
logger = logging.StreamHandler()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)-16s %(levelname)-8s %(message)s')
logger.setFormatter(formatter)
logging.getLogger('').addHandler(logger)
# END LOGGING

# VARIABLES
if os.path.exists("config.yaml"):
    yamlFile = "config.yaml"
else:
    yamlFile = yamlFound

try:
    yamlFile
except:
    raise
executableFile = os.path.abspath(os.path.join(os.path.basename(__file__)))
stream = open(os.path.join(os.path.dirname(__file__), yamlFile), 'r')
yamlStream = yaml.load(stream)


def check_age(path):
    try:
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(path)
        ageInDays = round((time.time() - ctime)/(3600*24))
        return(ageInDays)
    except:
        logging.error("cannot stat the file '%s', access denied?" % path)
        return 0

def delete_files_by_age(extension='log', age=10, path="c:/testing_workspace", *args):
    if len(args) > 0:
        dirPattern = args[0]
        for root, dirs, files in os.walk(path):
            for dir in dirs:
                if str(dir).__contains__(str(dirPattern)):
                    dirPath = os.path.join(root,dir)
                    if checkAge(dirPath) > age:
                        itsAge = checkAge(dirPath)
                        logging.info("deleting %s, age is: %s days" % (os.path.join(path,dir),itsAge))
                        try:
                            shutil.rmtree(os.path.join(root,dir))
                        except:
                            logging.error("cannot remove %s" % (os.path.join(root,dir)))
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(extension):
                filepath = os.path.join(root,file)
                if checkAge(filepath) > age:
                    try:
                        itsAge = checkAge(filepath)
                        logging.info("removing %s, age is: %s days" % (filepath,itsAge))
                        os.remove(filepath)
                    except:
                        logging.error("cannot delete %s, but proceeding with rest" % filepath)

def create_scheduled_task(recycleWeekDay, recycleWeekDayTime, executableFile, taskName):
    removeScheduledTaskCmd = "SCHTASKS /Delete /TN %s /F" % (taskName)
    addScheduledTaskCmd = "SCHTASKS /Create /NP /SC weekly /D %s /TN %s /ST %s /TR \"%s\"" % (recycleWeekDay,taskName,recycleWeekDayTime,python + " " + executableFile + " -createTask no -logPath %s") % (logPath)
    logging.info("command for removing scheduled task is: %s" % removeScheduledTaskCmd)
    logging.info("command for adding scheduled task is: %s" % addScheduledTaskCmd)

    call(removeScheduledTaskCmd,shell=True)
    call(addScheduledTaskCmd,shell=True)

try:
    for resource, settings in yamlStream['removeOldFiles']['c_drive'].items():
        try:
            path = settings['path']
            extensions = settings['extensions']
            age = settings['age']
        except:
            logging.error("yaml structure is not as expected, it should contain path, extension and age in it's structure" % (yamlFile))
        for extension in extensions.split(','):
            try:
                delete_files_by_age(extensions,age,path)
            except:
                logging.error("cannot delete extension %s on %s" % (extension,path))
        try:
            dirPatterns = settings['dirPatterns']
            for dirPattern in dirPatterns.split(','):
                delete_files_by_age(extension,age,path,dirPattern)
        except: IOError
except:
    raise

if args.createTask == "yes" and os.path.exists(os.path.normpath(python)):
    print(yamlStream['removeOldFilesSchedule'])
    try:
        recycleWeekDay = yamlStream['removeOldFilesSchedule']['days']
        recycleWeekDayTime = yamlStream['removeOldFilesSchedule']['time']
        taskName = yamlStream['removeOldFilesSchedule']['taskname']
        create_scheduled_task(recycleWeekDay,recycleWeekDayTime,executableFile,taskName)
    except:
        logging.warn("incorrectly enabled task?")
    try:
        src = os.path.join(os.path.dirname(__file__),"yaml")
        dst = os.path.join("yaml")
        if not os.path.exists(dst): os.makedirs(dst)
        if not os.path.exists(dst):
            shutil.copytree(src,dst)
            logging.info("copied yaml lib to %s" % dst)
    except:
        logging.error("cannot copy %s to %s" % (src,dst))
else:
    if not os.path.exists(python):
        logging.error("%s doesn't exist" % python)








