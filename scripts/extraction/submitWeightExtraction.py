#!/usr/bin/env python

# This is a condor submission script for submitting weight extraction jobs. Many of the args are
# passed straight to weightExtraction.py at runtime.

# An example call to the script would be:

# python submitWeightExtraction.py --oot --depth --algo PFA1p --tag WithDepth_TTbar_OOT --nJobs 90

import sys, os, argparse, shutil, time

date_and_time=time.strftime("%Y%m%d_%H%M%S")

usage = "usage: %prog [options]"
parser = argparse.ArgumentParser(usage)
parser.add_argument("--tag"     , dest="tag"     , help="Unique tag for output"   , type=str     , required=True)
parser.add_argument("--scheme"  , dest="scheme"  , help="Which reco scheme"       , type=str     , required=True)
parser.add_argument("--contain" , dest="contain" , help="With pulse containment"  , default=False, action="store_true")
parser.add_argument("--depth"   , dest="depth"   , help="Extract with depth"      , default=False, action="store_true")
parser.add_argument("--oot"     , dest="oot"     , help="Use OOT sample"          , default=False, action="store_true")
parser.add_argument("--pu"      , dest="pu"      , help="Level of PU in sample"   , type=str     , default="50PU")
parser.add_argument("--nugun"   , dest="nugun"   , help="Use nu gun samples"      , default=False, action="store_true")
parser.add_argument("--noSubmit", dest="noSubmit", help="do not submit to cluster", default=False, action="store_true")
parser.add_argument("--nJobs"   , dest="nJobs"   , help="number of jobs"          , type=int     , default=30)

arg = parser.parse_args()

# Everything will work inside sandbox
HOME = os.getenv("HOME")
SANDBOX = HOME + "/nobackup/HCAL_Trigger_Study"

NEVENTS = 9000
nJobs = arg.nJobs
eventsPerJob = 9000 / arg.nJobs

exeName = "weightExtraction.py"
exeStub = "python %s"%(exeName)
exeStub += " --scheme %s"%(arg.scheme)
exeStub += " --pu %s"%(arg.pu)

if arg.contain: exeStub += " --contain"
if arg.depth:   exeStub += " --depth"
if arg.oot:     exeStub += " --oot"
if arg.nugun:   exeStub += " --nugun"

taskStub   = arg.scheme + "_" + arg.tag + "_" + date_and_time
outputDir  = "%s/plots/Weights/%s/%s/root"%(SANDBOX,arg.scheme,arg.tag)
workingDir = "%s/condor/%s"%(SANDBOX,taskStub)

if not os.path.exists(outputDir):  os.makedirs(outputDir)
if not os.path.exists(workingDir): os.makedirs(workingDir)

exeFile = "%s/scripts/extraction/%s"%(SANDBOX,exeName);    shutil.copy2(exeFile, workingDir)
mapFile = "%s/scripts/extraction/pu2nopuMap.py"%(SANDBOX); shutil.copy2(mapFile, workingDir)

if outputDir.split("/")[-1]  == "": outputDir  = outputDir[:-1]
if workingDir.split("/")[-1] == "": workingDir = workingDir[:-1]

# Create directories to save log, submit, and mac files if they don't already exist
os.mkdir("%s/logs"%(workingDir))

# Write .sh script to be run by Condor
scriptFile = open("%s/runJob.sh"%(workingDir), "w")
scriptFile.write("#!/bin/bash\n\n")
scriptFile.write("STARTEVENT=$1\n")
scriptFile.write("NUMEVENTS=$2\n\n")
scriptFile.write("export SCRAM_ARCH=slc7_amd64_gcc700\n")
scriptFile.write("source /cvmfs/cms.cern.ch/cmsset_default.sh\n") 
scriptFile.write("eval `scramv1 project CMSSW CMSSW_10_4_0_patch1`\n")
scriptFile.write("cd CMSSW_10_4_0_patch1/src\n")
scriptFile.write("eval `scramv1 runtime -sh`\n")
scriptFile.write("cd ./../..\n")
scriptFile.write("%s --evtRange ${STARTEVENT} ${NUMEVENTS}\n"%(exeStub))
scriptFile.write("ls -l\n")
scriptFile.write("cd ${_CONDOR_SCRATCH_DIR}\n")
scriptFile.write("rm -r weightExtraction.py CMSSW_10_4_0_patch1\n")
scriptFile.close()

# Write Condor submit file 
condorSubmit = open("%s/condorSubmit.jdl"%(workingDir), "w")
condorSubmit.write("Executable          =  %s\n"%(scriptFile.name))
condorSubmit.write("Universe            =  vanilla\n")
condorSubmit.write("Requirements        =  OpSys == \"LINUX\" && Arch ==\"x86_64\"\n")
condorSubmit.write("Request_Memory      =  2.5 Gb\n")
condorSubmit.write("Should_Transfer_Files = YES\n")
condorSubmit.write("WhenToTransferOutput = ON_EXIT\n")
condorSubmit.write("Output = %s/logs/$(Cluster)_$(Process).stdout\n"%(workingDir))
condorSubmit.write("Error = %s/logs/$(Cluster)_$(Process).stderr\n"%(workingDir))
condorSubmit.write("Log = %s/logs/$(Cluster)_$(Process).log\n"%(workingDir))

condorSubmit.write("Transfer_Input_Files = %s/%s, %s/pu2nopuMap.py\n"%(workingDir,exeName,workingDir))

condorSubmit.write("x509userproxy = $ENV(X509_USER_PROXY)\n\n")

for iJob in xrange(0,nJobs):

    condorSubmit.write("transfer_output_remaps = \"histoCache_%d.root = %s/histoCache_%d.root\"\n" %(iJob*eventsPerJob, outputDir, iJob*eventsPerJob))
    condorSubmit.write("Arguments       = %d %d\n"%(iJob*eventsPerJob, eventsPerJob))
    condorSubmit.write("Queue\n\n")

condorSubmit.close()

os.system("chmod +x %s"%(scriptFile.name))

if arg.noSubmit: quit()

os.system("condor_submit " + condorSubmit.name)
