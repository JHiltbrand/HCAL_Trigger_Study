#!/usr/bin/env python

# This is a pretty vanilla condor submission script for submitting jobs to run on DIGI-RAW files
# and produce HCAL ntuples

# An example call to this script would be:

# python submitHcalTrigNtuple.py --schemes PFA2 PFA1 --dataset /RelValNuGun/CMSSW_10_6_1_patch1-PU_106X_mcRun3_2021_realistic_v3_rsb-v2/GEN-SIM-DIGI-RAW --tag NuGun --filesPerJob 1

import os, sys, argparse, subprocess, shutil
from time import strftime

# With either a local EOS directory or dataset from DAS, get the list of files
def files4Dataset(dataset):

    onEOS = os.getenv("USER") in dataset

    # If my name is in the path then we are on EOS
    if onEOS: proc = subprocess.Popen(['xrdfs', 'root://cmseos.fnal.gov', 'ls', dataset], stdout=subprocess.PIPE) 

    # Construct dasgoclient call and make it, reading back the standard out to get the list of files
    else:     proc = subprocess.Popen(['dasgoclient', '--query=file dataset=%s'%(dataset)], stdout=subprocess.PIPE)

    files = proc.stdout.readlines();  files = [file.rstrip() for file in files]

    # Prep the files for insertion into cmsRun config by adding the global redirector
    returnFiles = []
    for file in files:
        if onEOS: returnFiles.append(file.replace("/store/", "root://cmsxrootd.fnal.gov///store/"))
        else:     returnFiles.append(file.replace("/store/", "root://cmsxrootd.fnal.gov///store/"))

    return returnFiles 

# Write .sh script to be run by Condor
def generate_job_steerer(workingDir, schemeWeights, outputDir, CMSSW_VERSION):

    scriptFile = open("%s/runJob.sh"%(workingDir), "w")
    scriptFile.write("#!/bin/bash\n\n")
    scriptFile.write("JOB=$1\n")
    scriptFile.write("shift\n")
    scriptFile.write("INPUTFILES=$@\n\n")
    scriptFile.write("export SCRAM_ARCH=slc7_amd64_gcc700\n\n")
    scriptFile.write("source /cvmfs/cms.cern.ch/cmsset_default.sh\n") 
    scriptFile.write("eval `scramv1 project CMSSW %s`\n\n"%(CMSSW_VERSION))
    scriptFile.write("tar -xf %s.tar.gz\n"%(CMSSW_VERSION))
    scriptFile.write("rm %s.tar.gz\n"%(CMSSW_VERSION))
    scriptFile.write("mv algo_weights.py analyze_HcalTrig.py %s/src\n\n"%(CMSSW_VERSION))
    scriptFile.write("cd %s/src\n"%(CMSSW_VERSION))
    scriptFile.write("scramv1 b ProjectRename\n")
    scriptFile.write("eval `scramv1 runtime -sh`\n\n")
    scriptFile.write("cmsRun analyze_HcalTrig.py ${JOB} %s ${INPUTFILES}\n\n"%(schemeWeights))
    scriptFile.write("xrdcp -f hcalNtuple_${JOB}.root %s 2>&1\n"%(outputDir))
    scriptFile.write("cd ${_CONDOR_SCRATCH_DIR}\n")
    scriptFile.write("rm -r %s\n"%(CMSSW_VERSION))
    scriptFile.close()

# Write Condor submit file 
def generate_condor_submit(workingDir, inputFiles, filesPerJob, CMSSW_VERSION):

    condorSubmit = open("%s/condorSubmit.jdl"%(workingDir), "w")
    condorSubmit.write("Executable           =  %s/runJob.sh\n"%(workingDir))
    condorSubmit.write("Universe             =  vanilla\n")
    condorSubmit.write("Requirements         =  OpSys == \"LINUX\" && Arch ==\"x86_64\"\n")
    condorSubmit.write("Request_Memory       =  2.5 Gb\n")
    condorSubmit.write("Output               =  %s/logs/$(Cluster)_$(Process).stdout\n"%(workingDir))
    condorSubmit.write("Error                =  %s/logs/$(Cluster)_$(Process).stderr\n"%(workingDir))
    condorSubmit.write("Log                  =  %s/logs/$(Cluster)_$(Process).log\n"%(workingDir))
    condorSubmit.write("x509userproxy        =  $ENV(X509_USER_PROXY)\n")
    condorSubmit.write("Transfer_Input_Files =  %s/analyze_HcalTrig.py, %s/algo_weights.py, %s/%s.tar.gz\n\n"%(workingDir, workingDir, workingDir, CMSSW_VERSION))

    numFilesProc = 0; iJob = 0; iterator = 0; inFileStr = ""
    for inputFile in inputFiles:
    
        if numFilesProc == len(inputFiles): break
    
        inFileStr += "%s "%(inputFile)
        numFilesProc += 1; iterator += 1
        if iterator == filesPerJob or numFilesProc == len(inputFiles):
    
            condorSubmit.write("Arguments = %d %s\n"%(iJob, inFileStr))
            condorSubmit.write("Queue\n\n")
    
            iJob += 1; iterator = 0; inFileStr = ""

    condorSubmit.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--noSubmit"   , dest="noSubmit"   , help="do not submit to cluster", default=False, action="store_true")
    parser.add_argument("--schemes"    , dest="schemes"    , help="Which PFA scheme to use" , type=str , nargs="+", required=True)
    parser.add_argument("--versions"   , dest="versions"   , help="List versions of weights", type=str , nargs="+", default=[""])
    parser.add_argument("--updown"     , dest="updown"     , help="Do up/down variations"   , default=False, action="store_true")
    parser.add_argument("--dataset"    , dest="dataset"    , help="Unique path to dataset"  , type=str , default="50PU")
    parser.add_argument("--depth"      , dest="depth"      , help="Do depth version"        , default=False, action="store_true")
    parser.add_argument("--mean"       , dest="mean"       , help="Do mean version"         , default=False, action="store_true")
    parser.add_argument("--tag"        , dest="tag"        , help="Unique tag"              , type=str , default="NULL")
    parser.add_argument("--filesPerJob", dest="filesPerJob", help="Files per job"           , type=int , default=5)
    args = parser.parse_args()

    schemes     = args.schemes
    versions    = args.versions
    mean        = args.mean
    depth       = args.depth
    tag         = args.tag
    dataset     = args.dataset
    noSubmit    = args.noSubmit
    filesPerJob = args.filesPerJob
   
    variations = [""]
    if args.updown:
        variations.append("_UP")
        variations.append("_DOWN")

    # Get the list of input files to run over
    inputFiles = []
    if "/" not in dataset: inputFiles.append(dataset)
    else: inputFiles = files4Dataset(dataset)

    taskDir = strftime("%Y%m%d_%H%M%S")
    hcalDir = "%s/nobackup/HCAL_Trigger_Study"%(os.getenv("HOME"))

    # Get CMSSW environment
    CMSSW_BASE = os.getenv("CMSSW_BASE");  CMSSW_VERSION = os.getenv("CMSSW_VERSION")

    USER = os.getenv("USER")

    # Based on command line input, construct all versions of the weights to use
    # and submit jobs for each version
    for scheme in schemes:
        for version in versions:
            for variation in variations:

                schemeWeights = scheme
                if depth: schemeWeights += "_DEPTH_AVE"

                if version: schemeWeights += "_%s"%(version)
        
                if mean: schemeWeights += "_MEAN"

                if variation: schemeWeights += variation
                
                outputDir = "root://cmseos.fnal.gov///store/user/%s/HCAL_Trigger_Study/hcalNtuples/%s/%s"%(USER, tag, schemeWeights)
                workingDir = "%s/condor/%s_%s_%s"%(hcalDir, schemeWeights, tag, taskDir)
                
                # After defining the directory to work the job in and output to, make them
                subprocess.call(["eos", "root://cmseos.fnal.gov", "mkdir", "-p", outputDir[23:]])
                os.makedirs(workingDir)
                
                # Send the cmsRun config to the working dir as well as the algo weights
                shutil.copy2("%s/scripts/analyze_HcalTrig.py"%(hcalDir), workingDir)
                shutil.copy2("%s/scripts/algo_weights.py"%(hcalDir), workingDir)
                
                if outputDir.split("/")[-1] == "":  outputDir  = outputDir[:-1]
                if workingDir.split("/")[-1] == "": workingDir = workingDir[:-1]

                # Create directories to save logs
                os.makedirs("%s/logs"%(workingDir))

                # Make the .sh to run the show
                generate_job_steerer(workingDir, schemeWeights, outputDir, CMSSW_VERSION)

                # Make the jdl to hold condor's hand
                generate_condor_submit(workingDir, inputFiles, filesPerJob, CMSSW_VERSION)

                subprocess.call(["chmod", "+x", "%s/runJob.sh"%(workingDir)])

                subprocess.call(["tar", "--exclude-caches-all", "--exclude-vcs", "-zcf", "%s/%s.tar.gz"%(workingDir,CMSSW_VERSION), "-C", "%s/.."%(CMSSW_BASE), CMSSW_VERSION, "--include=tmp", "--include=python"])
                
                if args.noSubmit: continue
                
                os.system("condor_submit %s/condorSubmit.jdl"%(workingDir))
