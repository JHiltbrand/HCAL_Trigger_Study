import os
import glob
import optparse 
import subprocess

from samples import SampleCollection

def red(string):
     CRED = "\033[91m"
     CEND = "\033[0m"
     return CRED + str(string) + CEND

# List things in a specified path (no wildcards) and handle
# whether path is to EOS or just somewhere locally
# If on EOS, then use the proper xrdfs ls command to get the list
# Process the return and format into a clean list of strings
def listPath(path, onEOS=False):

    proc = None
    if onEOS:
        proc = subprocess.Popen(["xrdfs", "root://cmseos.fnal.gov", "ls", path], stdout=subprocess.PIPE)
    else:
        proc = subprocess.Popen(["ls", path], stdout=subprocess.PIPE)

    payload = proc.stdout.readlines()

    lines = []
    for line in payload:
        line = str(line).rstrip("\n")

        # Check the size, if clearly a broken file (< 512 bytes) do not count as "done"
        if ".root" in line:

            proc = subprocess.Popen(["xrdfs", "root://cmseos.fnal.gov", "stat", line], stdout=subprocess.PIPE)
            info = proc.stdout.readlines()
            size = None
            for stat in info:
                if "Size" in stat:
                    size = stat.partition("Size:")[-1].replace(" ", "").rstrip()
                    break
                else:
                    continue
                    
            if int(size) < 512:
                continue

        # Ensure that each element in the list has its full path
        if not onEOS:
            line = path + "/" + line
        lines.append(line)

    return lines

# Use the list of log files for a particular job folder and the
# corresponding ROOT files in the output directory on EOS to determine
# which jobs did not complete, and also the number of files per job that was run
def getMissingJobs(rootFiles, logFiles):

    # Subfunction to take a list of files and extract the job ID
    def extractJobs(listOfFiles, checkError = False):

        jobIDs = []
        for f in listOfFiles:

            filename = os.path.basename(f).rpartition(".")[0]
            temp   = filename.partition("_")[-1]
            chunks = temp.rpartition("_")

            jobid     = int(chunks[-1])

            if checkError:
                try:
                    subprocess.check_output("grep \"TNet\" %s"%(os.path.abspath(f).replace(".log", ".stderr")), shell=True)
                except:
                    jobIDs.append(jobid)
            else:
                jobIDs.append(jobid)

        sortedJobIDs = sorted(jobIDs)

        return sortedJobIDs

    finishedJobs = extractJobs(rootFiles)
    totalJobs    = extractJobs(logFiles)
    errFreeJobs  = extractJobs(logFiles, checkError=True)
      
    missingJobs = []
    for jobID in totalJobs:
        if jobID not in finishedJobs or jobID not in errFreeJobs: 
            missingJobs.append(jobID)

    return missingJobs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--noSubmit"   , dest="noSubmit"   , help="do not submit to cluster", default=False, action="store_true")
    parser.add_argument("--fileset"    , dest="fileset"    , help="Files for processing"    , type=str , default="NULL")
    parser.add_argument("--needParent" , dest="needParent" , help="Need to need parent file", default=False, action="store_true")
    parser.add_argument("--eosUser"    , dest="eosUser"    , help="User name for EOS"       , type=str , default="NULL")
    parser.add_argument("--tag"        , dest="tag"        , help="Unique tag"              , type=str , default="NULL")
    parser.add_argument("--era"        , dest="era"        , help="Era of of dataset"       , type=str , default="Run3")
    parser.add_argument("--globalTag"  , dest="globalTag"  , help="Global tag to use"       , type=str , default="124X_dataRun3_HLT_v4")
    parser.add_argument("--filesPerJob", dest="filesPerJob", help="Files per job"           , type=int , default=1)
    parser.add_argument("--jobDir"     , dest="jobDir"     , help="Name of job directory"   , type=str , 

    args = parser.parse_args()

    userName = os.environ["USER"]

    hostName = os.environ["HOSTNAME"]

    redirector = "root://cmseos.fnal.gov/"
    workingDir = os.path.basename(args.jobDir)
    eosDir     = "/store/user/%s/HCAL_TRG/hcalNtuples/%s"%(userName, args.jobDir)

    rootFiles = listPath(eosDir, onEOS=True)

    nJob = 0
    
    logFiles  = glob.glob(workingDir + "/logs/*.log")
    missingJobs = getMissingJobs(rootFiles, logFiles)

    oldCondorJDL = open(workingDir + "/condorSubmit.jdl", "r")
    condorLines = oldCondorJDL.readlines()
    oldCondorJDL.close()

    newCondorJDL = open(workingDir + "/condorSubmit_redux.jdl", "w")

    for line in condorLines:
        if "Queue" in line:
            continue

        if "Arguments" in line:
            aJobID = int(line.partition("= ")[-1].partition(" ")[0])
            if aJobID in missingJobs:
                newCondorJDL.write(line)
                nJob += 1
        else:
            newCondorJDL.write(line)
            
    # No need to try and submit if there are no missing jobs
    if not args.noSubmit and nJob > 0: 
        os.system("echo 'condor_submit condorSubmit.jdl'")
        os.system('condor_submit condorSubmit.jdl')
    else:
        print "------------------------------------------"
        print "Number of Jobs:", nJob
        print "------------------------------------------"

if __name__ == "__main__":
    main()
