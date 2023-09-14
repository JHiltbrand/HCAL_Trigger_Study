#!/usr/bin/env python

# This is a pretty vanilla condor submission script for submitting jobs to run on DIGI-RAW files
# and produce HCAL ntuples

# An example call to this script would be:

import os, sys, argparse, subprocess, shutil
from time import strftime

from dasgoHelpers import *

# Write .sh script to be run by Condor
def generate_job_steerer(user, workingDir, era, globalTag, outputDir, needParent, CMSSW_VERSION, filesPerJob):

    scriptFile = open("%s/runJob.sh"%(workingDir), "w")
    scriptFile.write("#!/bin/bash\n\n")

    scriptFile.write("JOB=$1\n");
    scriptFile.write("shift\n\n")

    scriptFile.write("CHILDRENSTR=\"\"\n")
    scriptFile.write("for ((i=1; i<=%d; i++)); do\n"%(filesPerJob))
    scriptFile.write("    CHILDRENSTR+=\"\\\"$1\\\"\"\n")
    scriptFile.write("    if [ \"$i\" != %d ]; then\n"%(filesPerJob))
    scriptFile.write("        CHILDRENSTR+=\",\"\n")
    scriptFile.write("    fi\n")
    scriptFile.write("    shift\n")
    scriptFile.write("done\n\n")

    if needParent:
        scriptFile.write("PARENTSSTR=\"\"\n")
        scriptFile.write("for ((i=1; i<=$#; i++)); do\n")
        scriptFile.write("    PARENTSSTR+=\"\\\"${!i}\\\"\"\n")
        scriptFile.write("    if [ \"$i\" != $# ]; then\n")
        scriptFile.write("        PARENTSSTR+=\",\"\n")
        scriptFile.write("    fi\n")
        scriptFile.write("done\n\n")

    scriptFile.write("export SCRAM_ARCH=slc7_amd64_gcc10\n\n")
    scriptFile.write("source /cvmfs/cms.cern.ch/cmsset_default.sh\n") 
    scriptFile.write("eval `scramv1 project CMSSW %s`\n\n"%(CMSSW_VERSION))
    scriptFile.write("tar -xf %s.tar.gz\n"%(CMSSW_VERSION))

    scriptFile.write("mv analyze_HcalDebug.py CERT_LUMI_2022.json %s/src\n"%(CMSSW_VERSION))
    scriptFile.write("cd %s/src\n"%(CMSSW_VERSION))
    scriptFile.write("ls -lrth\n\n")

    scriptFile.write("scramv1 b ProjectRename\n")
    scriptFile.write("eval `scramv1 runtime -sh`\n")

    scriptFile.write("sed -i \"s|CHILDFILE|${CHILDRENSTR}|g\" analyze_HcalDebug.py\n")
    scriptFile.write("sed -i \"s|PARENTFILE|${PARENTSSTR}|g\" analyze_HcalDebug.py\n\n")

    scriptFile.write("cmsRun analyze_HcalDebug.py\n\n")
    scriptFile.write("xrdcp -f hcalNtuple.root %s/hcalNtuple_${JOB}.root 2>&1\n"%(outputDir))
    scriptFile.write("\n rm -rf *.root\n")

    scriptFile.close()

# Write Condor submit file 
def generate_condor_submit(workingDir, inputFileMap, data, needParent, filesPerJob):

    condorSubmit = open("%s/condorSubmit.jdl"%(workingDir), "w")
    condorSubmit.write("Executable            =  %s/runJob.sh\n"%(workingDir))
    condorSubmit.write("Universe              =  vanilla\n")
    condorSubmit.write("Request_Memory        =  1.5 Gb\n")
    condorSubmit.write("Output                =  %s/logs/$(Cluster)_$(Process).stdout\n"%(workingDir))
    condorSubmit.write("Error                 =  %s/logs/$(Cluster)_$(Process).stderr\n"%(workingDir))
    condorSubmit.write("Log                   =  %s/logs/$(Cluster)_$(Process).log\n"%(workingDir))
    condorSubmit.write("Transfer_Input_Files  =  %s/analyze_HcalDebug.py, %s/CERT_LUMI_2022.json, %s/%s.tar.gz\n"%(workingDir,workingDir,workingDir,os.getenv("CMSSW_VERSION")))

    iJob = 0
    filesAddedToJob = 0
    childrenFiles = []
    parentsFiles  = []
    for childFile, parentFiles in inputFileMap.items():
        
        if filesAddedToJob == filesPerJob:
            if needParent:
                condorSubmit.write("\nArguments       = %d %s %s\n"%(iJob, " ".join(childrenFiles), " ".join(parentsFiles)))
            else:
                condorSubmit.write("\nArguments       = %d %s\n"%(iJob, " ".join(childrenFiles)))

            condorSubmit.write("Queue\n")
            iJob += 1

            childrenFiles   = []
            parentsFiles    = []
            filesAddedToJob = 0

        childrenFiles.append(addRedirector(childFile, "root://cms-xrd-global.cern.ch/"))
        parentsFiles = addRedirectors(parentFiles, "root://cms-xrd-global.cern.ch/")

        filesAddedToJob += 1

    condorSubmit.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--noSubmit"   , dest="noSubmit"   , help="do not submit to cluster", default=False, action="store_true")
    parser.add_argument("--fileset"    , dest="fileset"    , help="Files for processing"    , type=str , default="NULL")
    parser.add_argument("--needParent" , dest="needParent" , help="Need to need parent file", default=False, action="store_true")
    parser.add_argument("--eosUser"    , dest="eosUser"    , help="User name for EOS"       , type=str , default="NULL")
    parser.add_argument("--tag"        , dest="tag"        , help="Unique tag"              , type=str , default="NULL")
    parser.add_argument("--era"        , dest="era"        , help="Era of of dataset"       , type=str , default="Run3")
    parser.add_argument("--globalTag"  , dest="globalTag"  , help="Global tag to use"       , type=str , default="124X_dataRun3_Prompt_v10")
    parser.add_argument("--filesPerJob", dest="filesPerJob", help="Files per job"           , type=int , default=1)

    args = parser.parse_args()

    tag         = args.tag
    era         = args.era
    EOSUSER     = args.eosUser
    globalTag   = args.globalTag
    fileset     = args.fileset
    noSubmit    = args.noSubmit
    needParent  = args.needParent
    filesPerJob = args.filesPerJob
   
    hcalDir = "%s/nobackup/HCAL_TRG"%(os.getenv("HOME"))

    # Get the list of input files to run over
    inputFiles = []
    if ".txt" in fileset: inputFiles = open(fileset, "r").read().splitlines() 
    elif "/"  in fileset: inputFiles = files4Dataset(fileset)
    else:                 inputFiles.append(fileset)

    data = "store/data" in inputFiles[0]

    subprocess.call(["cat %s/scripts/analyze_HcalDebug_template.py > %s/scripts/analyze_HcalDebug.py"%(hcalDir, hcalDir)], shell=True)

    subprocess.call(["sed -i 's|GLOBALTAG|\"%s\"|g' analyze_HcalDebug.py"%(globalTag)], shell=True)
    subprocess.call(["sed -i 's|PROCESS|cms.Process(\"HCALTP\", eras.%s)|g' analyze_HcalDebug.py"%(era)], shell=True)

    taskDir = strftime("%Y%m%d_%H%M%S")
    hcalDir = "%s/nobackup/HCAL_TRG"%(os.getenv("HOME"))

    # Get CMSSW environment
    CMSSW_BASE    = os.getenv("CMSSW_BASE")
    CMSSW_VERSION = os.getenv("CMSSW_VERSION")

    USER = os.getenv("USER")

    childParentFilePair = {}
    for file in inputFiles:
        if needParent:
            parents = getParents4File(file)
            needGparents = "RAW" not in parents[0]

            if needGparents:
                gparents = []
                for parent in parents: gparents += getParents4File(parent)
                
                childParentFilePair[file] = gparents
            else:
                childParentFilePair[file] = parents

        else: childParentFilePair[file] = "NULL"

    outputDir = "root://cmseos.fnal.gov///store/user/%s/HCAL_TRG/hcalNtuples/%s"%(EOSUSER, tag)
    workingDir = "%s/condor/%s_%s"%(hcalDir, tag, taskDir)

    if not os.path.exists(workingDir): os.makedirs(workingDir)
    
    # After defining the directory to work the job in and output to, make them
    subprocess.call(["xrdfs", "root://cmseos.fnal.gov", "mkdir", "-p", outputDir[23:]])
    
    # Send the cmsRun config to the working dir as well as the algo weights
    shutil.copy2("%s/scripts/analyze_HcalDebug.py"%(hcalDir), workingDir)
    shutil.copy2("%s/scripts/CERT_LUMI_2022.json"%(hcalDir), workingDir)
   
    # Create directories to save logs
    os.makedirs("%s/logs"%(workingDir))

    # tar up the current working CMSSW area
    subprocess.call(["tar", "--exclude-caches-all", "--exclude-vcs", "-zcf", "%s/%s.tar.gz"%(workingDir,CMSSW_VERSION), "-C", "%s/.."%(CMSSW_BASE), CMSSW_VERSION, "--exclude=tmp", "--exclude=external", "--exclude=config"])

    # Make the .sh to run the show
    generate_job_steerer(USER, workingDir, era, globalTag, outputDir, needParent, CMSSW_VERSION, filesPerJob)

    # Write the condor submit file for condor to do its thing
    generate_condor_submit(workingDir, childParentFilePair, data, needParent, filesPerJob)    

    subprocess.call(["chmod", "+x", "%s/runJob.sh"%(workingDir)])

    if not args.noSubmit: os.system("condor_submit %s/condorSubmit.jdl"%(workingDir))
