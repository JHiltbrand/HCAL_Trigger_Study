#!/usr/bin/env python

# This is a pretty vanilla condor submission script for submitting jobs to run on DIGI-RAW files
# and produce HCAL ntuples

# An example call to this script would be:

# python submitHcalTrigNtuple.py --schemes PFA2 PFA1 --dataset /RelValNuGun/CMSSW_10_6_1_patch1-PU_106X_mcRun3_2021_realistic_v3_rsb-v2/GEN-SIM-DIGI-RAW --tag NuGun --filesPerJob 1

import os, sys, argparse, subprocess, shutil
from time import strftime

from algo_weights import pfaWeightsMap as pm
from dasgoHelpers import *

# Write .sh script to be run by Condor
def generate_job_steerer(workingDir, era, globalTag, schemeWeights, outputDir, needParent, copyLocal, CMSSW_VERSION):

    scriptFile = open("%s/runJob.sh"%(workingDir), "w")
    scriptFile.write("#!/bin/bash\n\n")
    scriptFile.write("JOB=$1\n");
    scriptFile.write("shift\n")
    scriptFile.write("RUN=$1\n");
    scriptFile.write("shift\n")
    scriptFile.write("LUMI1=$1\n");
    scriptFile.write("shift\n")
    scriptFile.write("LUMI2=$1\n");
    scriptFile.write("shift\n")

    scriptFile.write("CHILDPATH=$1\n");
    scriptFile.write("shift\n")
    scriptFile.write("CHILDFILE=$1\n");
    scriptFile.write("shift\n\n")

    if copyLocal:
        scriptFile.write("xrdcp --retry 3 ${CHILDPATH}/${CHILDFILE} . & pid=$!\n")
        scriptFile.write("PID_LIST+=\" $pid\"\n\n")


    if needParent:
        scriptFile.write("PARENTFILESTR=\"\"\n")
        scriptFile.write("PARENTPATH=$1\n");
        scriptFile.write("shift\n")
        scriptFile.write("PARENTFILES=$@\n\n")
        scriptFile.write("for PARENTFILE in ${PARENTFILES}; do {\n")

        if copyLocal:
            scriptFile.write("    xrdcp --retry 3 ${PARENTPATH}/${PARENTFILE} . & pid=$!\n")
            scriptFile.write("    PID_LIST+=\" $pid\";\n")
            scriptFile.write("    PARENTFILESTR=\"${PARENTFILESTR}'file://${PARENTFILE}',\";\n")

        else:
            scriptFile.write("    PARENTFILESTR=\"${PARENTFILESTR}'${PARENTPATH}/${PARENTFILE}',\";\n")

        scriptFile.write("} done\n\n")

    if copyLocal: scriptFile.write("wait $PID_LIST\n\n")

    scriptFile.write("export SCRAM_ARCH=slc7_amd64_gcc700\n\n")
    scriptFile.write("source /cvmfs/cms.cern.ch/cmsset_default.sh\n") 
    scriptFile.write("eval `scramv1 project CMSSW %s`\n\n"%(CMSSW_VERSION))
    scriptFile.write("tar -xf %s.tar.gz\n"%(CMSSW_VERSION))
    scriptFile.write("mv analyze_HcalTrig.py algo_weights.py %s/src\n"%(CMSSW_VERSION))
    scriptFile.write("cd %s/src\n"%(CMSSW_VERSION))
    scriptFile.write("ls -lrth\n\n")
    scriptFile.write("scramv1 b ProjectRename\n")
    scriptFile.write("eval `scramv1 runtime -sh`\n")

    if copyLocal: scriptFile.write("sed -i \"s|CHILDFILE|file://${CHILDFILE}|g\" analyze_HcalTrig.py\n")
    else:         scriptFile.write("sed -i \"s|CHILDFILE|${CHILDPATH}/${CHILDFILE}|g\" analyze_HcalTrig.py\n")

    scriptFile.write("sed -i \"s|'PARENTFILE'|${PARENTFILESTR}|g\" analyze_HcalTrig.py\n\n")

    scriptFile.write("sed -i \"s|RUN|${RUN}|g\" analyze_HcalTrig.py\n")
    scriptFile.write("sed -i \"s|LUMI1|${LUMI1}|g\" analyze_HcalTrig.py\n")
    scriptFile.write("sed -i \"s|LUMI2|${LUMI2}|g\" analyze_HcalTrig.py\n")

    scriptFile.write("cmsRun analyze_HcalTrig.py\n\n")
    scriptFile.write("xrdcp -f hcalNtuple.root %s/hcalNtuple_${JOB}.root 2>&1\n"%(outputDir))
    scriptFile.write("cd ${_CONDOR_SCRATCH_DIR}\n")
    scriptFile.write("rm -r %s\n"%(CMSSW_VERSION))
    scriptFile.close()

# Write Condor submit file 
def generate_condor_submit(workingDir, inputFileMap, childLumiMap, parentLumiMap, run, needParent):

    condorSubmit = open("%s/condorSubmit.jdl"%(workingDir), "w")
    condorSubmit.write("Executable           =  %s/runJob.sh\n"%(workingDir))
    condorSubmit.write("Universe             =  vanilla\n")
    condorSubmit.write("Requirements         =  OpSys == \"LINUX\" && Arch ==\"x86_64\"\n")
    condorSubmit.write("Request_Memory       =  2.5 Gb\n")
    condorSubmit.write("Output               =  %s/logs/$(Cluster)_$(Process).stdout\n"%(workingDir))
    condorSubmit.write("Error                =  %s/logs/$(Cluster)_$(Process).stderr\n"%(workingDir))
    condorSubmit.write("Log                  =  %s/logs/$(Cluster)_$(Process).log\n"%(workingDir))
    condorSubmit.write("Transfer_Input_Files =  %s/ntuple_maker.py, %s/runJob.sh, %s/%s.tar.gz\n"%(workingDir,workingDir,workingDir,os.getenv("CMSSW_VERSION")))
    condorSubmit.write("x509userproxy        =  $ENV(X509_USER_PROXY)\n\n")
    
    iJob = 0 
    for childFile, parentFiles in inputFileMap.iteritems():
        
        childName = childFile.split("/")[-1]; childPath = "/".join(childFile.split("/")[:-1])
        parentPath = "/".join(parentFiles[0].split("/")[:-1])

        childPath  = addRedirector(childPath, "root://cms-xrd-global.cern.ch/")
        parentPath = addRedirector(parentPath, "root://cms-xrd-global.cern.ch/")

        if needParent:
            for lumiRange in childLumiMap[childFile]:
                if   len(lumiRange) == 1: condorSubmit.write("Arguments       = %d %s %d %d %s %s %s "%(iJob, run, int(lumiRange[0]), int(lumiRange[0]), childPath, childName, parentPath))
                elif len(lumiRange) == 2: condorSubmit.write("Arguments       = %d %s %d %d %s %s %s "%(iJob, run, int(lumiRange[0]), int(lumiRange[1]), childPath, childName, parentPath))
                for parent in parentFiles:
                    for pLumiRange in parentLumiMap[parent]:
                        if (int(pLumiRange[0]) <= int(lumiRange[1]) and int(pLumiRange[1]) >= int(lumiRange[0])):
                            condorSubmit.write("%s "%(parent.split("/")[-1]))
                            break

                condorSubmit.write("\nQueue\n\n")
                iJob += 1

        else:
            for lumiRange in childLumiMap[childFile]:
                if   len(lumiRange) == 1: condorSubmit.write("Arguments       = %d %s %d %d %s %s\n"%(iJob, run, int(lumiRange[0]), int(lumiRange[0]), childPath, childName))
                elif len(lumiRange) == 2: condorSubmit.write("Arguments       = %d %s %d %d %s %s\n"%(iJob, run, int(lumiRange[0]), int(lumiRange[1]), childPath, childName))
                condorSubmit.write("Queue\n\n")
                iJob += 1
    
    condorSubmit.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--noSubmit"   , dest="noSubmit"   , help="do not submit to cluster", default=False, action="store_true")
    parser.add_argument("--scheme"     , dest="scheme"     , help="Which PFA scheme to use" , type=str , required=True)
    parser.add_argument("--dataset"    , dest="dataset"    , help="Unique path to dataset"  , type=str , default="50PU")
    parser.add_argument("--filelist"   , dest="filelist"   , help="Filelist for processing" , type=str , default="NULL")
    parser.add_argument("--depth"      , dest="depth"      , help="Do depth version"        , default=False, action="store_true")
    parser.add_argument("--mean"       , dest="mean"       , help="Do mean version"         , default=False, action="store_true")
    parser.add_argument("--needParent" , dest="needParent" , help="Need to need parent file", default=False, action="store_true")
    parser.add_argument("--copyLocal"  , dest="copyLocal"  , help="Need to need parent file", default=False, action="store_true")
    parser.add_argument("--lumiSplit"  , dest="lumiSplit"  , help="Split based on lumi"     , default=False, action="store_true")
    parser.add_argument("--lumiMask"   , dest="lumiMask"   , help="Lumi mask for CRAB"      , type=str , default="NULL")
    parser.add_argument("--crab"       , dest="crab"       , help="Submit to CRAB -_____-"  , default=False, action="store_true")
    parser.add_argument("--tag"        , dest="tag"        , help="Unique tag"              , type=str , default="NULL")
    parser.add_argument("--run"        , dest="run"        , help="Data run to process"     , type=str , default="1")
    parser.add_argument("--era"        , dest="era"        , help="Era of of dataset"       , type=str , default="Run3")
    parser.add_argument("--data"       , dest="data"       , help="Running on data"         , default=False, action="store_true")
    parser.add_argument("--globalTag"  , dest="globalTag"  , help="Global tag to use"       , type=str , default="110X_mcRun3_2021_v6")
    args = parser.parse_args()

    scheme      = args.scheme
    mean        = args.mean
    depth       = args.depth
    tag         = args.tag
    run         = args.run
    era         = args.era
    data        = args.data
    crab        = args.crab
    lumiMask    = args.lumiMask
    globalTag   = args.globalTag
    lumiSplit   = args.lumiSplit
    copyLocal   = args.copyLocal
    dataset     = args.dataset
    filelist    = args.filelist
    noSubmit    = args.noSubmit
    needParent  = args.needParent
   
    hcalDir = "%s/nobackup/HCAL_Trigger_Study"%(os.getenv("HOME"))

    phase = 0.0 if data else 3.0

    customStr = "\n"
    if "PFA2p" in scheme:
        customStr += "process.simHcalTriggerPrimitiveDigis.numberOfPresamplesHBQIE11 = 1\n"
        customStr += "process.simHcalTriggerPrimitiveDigis.numberOfPresamplesHEQIE11 = 1\n"
    
    elif "PFA1p" in scheme:
        customStr += "process.simHcalTriggerPrimitiveDigis.numberOfPresamplesHBQIE11 = 1\n"
        customStr += "process.simHcalTriggerPrimitiveDigis.numberOfPresamplesHEQIE11 = 1\n"
        customStr += "process.HcalTPGCoderULUT.contain1TSHB = True\n"
        customStr += "process.HcalTPGCoderULUT.containPhaseNSHB = %f\n"%(phase)
        customStr += "process.HcalTPGCoderULUT.contain1TSHE = True\n"
        customStr += "process.HcalTPGCoderULUT.containPhaseNSHE = %f\n"%(phase)
    
    elif "PFA1" in scheme:
        customStr += "process.HcalTPGCoderULUT.contain1TSHB = True\n"
        customStr += "process.HcalTPGCoderULUT.containPhaseNSHB = %f\n"%(phase)
        customStr += "process.HcalTPGCoderULUT.contain1TSHE = True\n"
        customStr += "process.HcalTPGCoderULUT.containPhaseNSHE = %f\n"%(phase)

    elif "PFAX" in scheme:
        customStr += "process.simHcalTriggerPrimitiveDigis.numberOfPresamplesHEQIE11 = 1\n"
        customStr += "process.HcalTPGCoderULUT.contain1TSHE = True\n"
        customStr += "process.HcalTPGCoderULUT.containPhaseNSHE = %f\n"%(phase)
    
    wStr = str(pm[scheme])
    wStr = wStr.replace("'", r'"')
    if scheme in pm and scheme != "PFA2": customStr += "process.simHcalTriggerPrimitiveDigis.weightsQIE11 = %s\n"%(wStr)
    if not crab: customStr += "process.source.lumisToProcess=cms.untracked.VLuminosityBlockRange(\"RUN:LUMI1-RUN:LUMI2\")\n"

    subprocess.call(["cat %s/scripts/analyze_HcalTrig_template.py > %s/scripts/analyze_HcalTrig.py"%(hcalDir, hcalDir)], shell=True)
    subprocess.call(["echo '%s' >> %s/scripts/analyze_HcalTrig.py"%(customStr, hcalDir)], shell=True)

    subprocess.call(["sed -i 's|GLOBALTAG|%s|g' analyze_HcalTrig.py"%(globalTag)], shell=True)
    subprocess.call(["sed -i 's|PROCESS|cms.Process(\"HCALNTUPLE\", eras.%s)|g' analyze_HcalTrig.py"%(era)], shell=True)

    # If submitting to CRAB, we don't have do a lot of stuff
    # just make the config file and go on our merry way
    if crab:

        subprocess.call(["sed -i 's|process.source.lumis|#process.source.lumis|g' analyze_HcalTrig.py"], shell=True)

        subprocess.call(["cat %s/scripts/crab_submit_template.py > %s/scripts/crab_submit.py"%(hcalDir,hcalDir)], shell=True)
        subprocess.call(["sed -i 's|PFA|%s|g' crab_submit.py"%(scheme)], shell=True)
        subprocess.call(["sed -i 's|USEPARENT|%s|g' crab_submit.py"%(str(needParent))], shell=True)
        subprocess.call(["sed -i 's|DATASET|%s|g' crab_submit.py"%(dataset)], shell=True)

        if lumiMask != "NULL": subprocess.call(["sed -i 's|LUMIMASK|\"%s\"|g' crab_submit.py"%(lumiMask)], shell=True)
        else:                  subprocess.call(["sed -i 's|config.Data.lumiMask|#config.Data.lumiMask|g' crab_submit.py"], shell=True)

        if not noSubmit: subprocess.call(["crab", "submit", "crab_submit.py"])

    # If not submitting to CRAB, do all the work ourselves
    else:

        # Get the list of input files to run over
        inputFiles = []
        if ".txt" in filelist:   inputFiles = open(filelist, "r").read().splitlines() 
        elif "/" not in dataset: inputFiles.append(dataset)
        else:                    inputFiles = files4Dataset(dataset)

        taskDir = strftime("%Y%m%d_%H%M%S")
        hcalDir = "%s/nobackup/HCAL_Trigger_Study"%(os.getenv("HOME"))

        # Get CMSSW environment
        CMSSW_BASE = os.getenv("CMSSW_BASE");  CMSSW_VERSION = os.getenv("CMSSW_VERSION")

        USER = os.getenv("USER")

        childParentFilePair = {}; childFileLumiPair = {}; parentFileLumiPair = {}
        for file in inputFiles:
            if lumiSplit: childFileLumiPair[file] = lumis4File(file)
            else:         childFileLumiPair[file] = [[1,10000]]

            if needParent:
                parents = getParents4File(file)
                needGparents = "RAW" not in parents[0]

                if needGparents:
                    gparents = []
                    for parent in parents: gparents += getParents4File(parent)
                    
                    for gparent in gparents:
                        if lumiSplit: parentFileLumiPair[gparent] = lumis4File(gparent)
                        else:         parentFileLumiPair[gparent] = [[1,10000]]

                    childParentFilePair[file] = gparents
                else:
                    for parent in parents:
                        if lumiSplit: parentFileLumiPair[parent] = lumis4File(parent)
                        else:         parentFileLumiPair[parent] = [[1,10000]]
                    childParentFilePair[file] = parents

            else: childParentFilePair[file] = "NULL"

        # Based on command line input, construct all versions of the weights to use
        # and submit jobs for each version
        if depth: scheme += "_DEPTH_AVE"

        if mean: scheme += "_MEAN"

        outputDir = "root://cmseos.fnal.gov///store/user/%s/HCAL_Trigger_Study/hcalNtuples/%s/%s"%(USER, tag, scheme)
        workingDir = "%s/condor/%s_%s_%s"%(hcalDir, scheme, tag, taskDir)
        
        # After defining the directory to work the job in and output to, make them
        subprocess.call(["eos", "root://cmseos.fnal.gov", "mkdir", "-p", outputDir[23:]])
        os.makedirs(workingDir)
        
        # Send the cmsRun config to the working dir as well as the algo weights
        shutil.copy2("%s/scripts/analyze_HcalTrig.py"%(hcalDir), workingDir)
        
        if outputDir.split("/")[-1] == "":  outputDir  = outputDir[:-1]
        if workingDir.split("/")[-1] == "": workingDir = workingDir[:-1]

        # Create directories to save logs
        os.makedirs("%s/logs"%(workingDir))

        # Make the .sh to run the show
        generate_job_steerer(workingDir, era, globalTag, scheme, outputDir, needParent, copyLocal, CMSSW_VERSION)

        # Write the condor submit file for condor to do its thing
        generate_condor_submit(workingDir, childParentFilePair, childFileLumiPair, parentFileLumiPair, run, needParent)    

        subprocess.call(["chmod", "+x", "%s/runJob.sh"%(workingDir)])

        subprocess.call(["tar", "--exclude-caches-all", "--exclude-vcs", "-zcf", "%s/%s.tar.gz"%(workingDir,CMSSW_VERSION), "-C", "%s/.."%(CMSSW_BASE), CMSSW_VERSION, "--exclude=tmp", "--exclude=bin"])
        
        if not args.noSubmit: os.system("condor_submit %s/condorSubmit.jdl"%(workingDir))
