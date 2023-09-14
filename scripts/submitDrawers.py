#!/usr/bin/env python

import os, sys, argparse, subprocess, shutil
from time import strftime

# Write .sh script to be run by Condor
def generate_job_steerer(user, workingDir, outputDir, filesPerJob):

    scriptFile = open("%s/runJob.sh"%(workingDir), "w")
    scriptFile.write("#!/bin/bash\n\n")

    scriptFile.write("source /cvmfs/sft.cern.ch/lcg/views/LCG_103/x86_64-centos7-gcc11-opt/setup.sh\n\n")

    scriptFile.write("JOB=$1\n");
    scriptFile.write("shift\n\n")

    scriptFile.write("hadd inputFile.root \"$@\"\n")
    scriptFile.write("ls -lrth\n\n")

    scriptFile.write("python miniTupleDrawer.py --inputFile ./inputFile.root\n\n")
    scriptFile.write("xrdcp -f hcalHistos.root %s/hcalHistos_${JOB}.root 2>&1\n\n"%(outputDir))
    scriptFile.write("xrdcp -f event_stats.txt %s/event_stats_${JOB}.txt 2>&1\n\n"%(outputDir))

    scriptFile.write("rm -rf *.root\n")

    scriptFile.close()

# Write Condor submit file 
def generate_condor_submit(workingDir, inputFiles, filesPerJob):

    condorSubmit = open("%s/condorSubmit.jdl"%(workingDir), "w")
    condorSubmit.write("Executable            =  %s/runJob.sh\n"%(workingDir))
    condorSubmit.write("Universe              =  vanilla\n")
    condorSubmit.write("Request_Memory        =  1.5 Gb\n")
    condorSubmit.write("Output                =  %s/logs/$(Cluster)_$(Process).stdout\n"%(workingDir))
    condorSubmit.write("Error                 =  %s/logs/$(Cluster)_$(Process).stderr\n"%(workingDir))
    condorSubmit.write("Log                   =  %s/logs/$(Cluster)_$(Process).log\n"%(workingDir))
    condorSubmit.write("Transfer_Input_Files  =  %s/miniTupleDrawer.py, %s/miniTupleDrawer_aux.py\n"%(workingDir,workingDir))

    iJob = 0
    filesAddedToJob = 0
    files = []
    for inputFile in inputFiles:
        
        files.append(inputFile)
        filesAddedToJob += 1

        if filesAddedToJob == filesPerJob or inputFile == inputFiles[-1]:
            condorSubmit.write("\nArguments       = %d %s\n"%(iJob, " ".join(files)))
            condorSubmit.write("Queue\n")
            iJob += 1

            files   = []
            filesAddedToJob = 0

    condorSubmit.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--noSubmit"   , dest="noSubmit"   , help="do not submit to cluster", default=False, action="store_true")
    parser.add_argument("--eosUser"    , dest="eosUser"    , help="User name for EOS"       , type=str , default="NULL")
    parser.add_argument("--tag"        , dest="tag"        , help="Unique tag"              , type=str , default="NULL")
    parser.add_argument("--filesPerJob", dest="filesPerJob", help="Files per job"           , type=int , default=1)

    args = parser.parse_args()

    USER = os.getenv("USER")

    tag          = args.tag
    EOSUSER      = USER if args.eosUser == "NULL" else args.eosUser
    inputDirStub = "/store/user/%s/HCAL_TRG/hcalNtuples/%s"%(EOSUSER,tag)
    noSubmit     = args.noSubmit
    filesPerJob  = args.filesPerJob
   
    hcalDir    = "%s/nobackup/HCAL_TRG"%(os.getenv("HOME"))
    taskDir    = strftime("%Y%m%d_%H%M%S")
    outputDir  = "root://cmseos.fnal.gov///store/user/%s/HCAL_TRG/hcalHistos/%s"%(EOSUSER, tag)
    workingDir = "%s/condor/%s_HISTOS_%s"%(hcalDir, tag, taskDir)

    eosStub = "root://cmseos.fnal.gov//"
    proc = subprocess.Popen(["xrdfs", "root://cmseos.fnal.gov", "ls", inputDirStub], stdout=subprocess.PIPE)
    inputFiles = proc.stdout.readlines()
    inputFiles = [eosStub + str(inputFile.decode("utf-8")).rstrip() for inputFile in inputFiles]

    if not os.path.exists(workingDir): os.makedirs(workingDir)
    
    # After defining the directory to work the job in and output to, make them
    subprocess.call(["xrdfs", "root://cmseos.fnal.gov", "mkdir", "-p", outputDir[23:]])
    
    # Send the cmsRun config to the working dir as well as the algo weights
    shutil.copy2("%s/scripts/miniTupleDrawer.py"%(hcalDir),     workingDir)
    shutil.copy2("%s/scripts/miniTupleDrawer_aux.py"%(hcalDir), workingDir)
  
    # Create directories to save logs
    os.makedirs("%s/logs"%(workingDir))

    # Make the .sh to run the show
    generate_job_steerer(USER, workingDir, outputDir, filesPerJob)

    # Write the condor submit file for condor to do its thing
    generate_condor_submit(workingDir, inputFiles, filesPerJob)    

    subprocess.call(["chmod", "+x", "%s/runJob.sh"%(workingDir)])

    if not args.noSubmit: os.system("condor_submit %s/condorSubmit.jdl"%(workingDir))
