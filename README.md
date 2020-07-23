# HCAL Pulse Filter Study

This is a repository of scripts for extracting pulse filter weights, applying the weights and reconstructing trigger primitives, and making plots of end results. Several steps are outlined below to go from generating special PU-mixed files to extracting weights to applying the weights.

DISCLAIMER: Any file paths implicitly assumed are customized for the author and will not work out-of-the-box.

## Initializing a Workspace

First one needs to setup a working area for everything. If on LPC, making a `nobackup` area is not necessary as it exists by default. If not at LPC it is encouraged to make a `nobackup` folder as it is assumed by many scripts in this repository.

```
mkdir -p $HOME/nobackup
cd $HOME/nobackup/

git clone git@github.com:JHiltbrand/HCAL_Trigger_Study.git
cd HCAL_Trigger_Study

mkdir cmssw plots input
```

## Producing DIGI-RAW Files With and Without Pileup

Before we can proceed, we need to initialize a `CMSSW` area and compile:

```
cd $HOME/nobackup/HCAL_Trigger_Study/cmssw

mkdir puMixing
cd puMixing

cmsrel CMSSW_10_6_1_patch1
cd CMSSW_10_6_1_patch1/src
cmsenv

# Add this package to tweak
# PU mixing behavior
git cms-addpkg Mixing/Base

scram b -j8
```

The first step is to take a ttbar and/or nugun GEN-SIM file and produce two daughter RAW files for exactly two different pileup scenarios. One daughter file will have no pileup mixed in while the other file will have pileup mixed in for whichever special pileup scenario is being studied.

Possible centrally-produced GEN-SIM files to be used could be:

**ttbar:**
[/RelValTTbar_13/CMSSW_10_6_0_pre4-106X_upgrade2021_realistic_v4-v1/GEN-SIM](https://cmsweb.cern.ch/das/request?input=dataset%3D%2FRelValTTbar_13%2FCMSSW_10_6_0_pre4-106X_upgrade2021_realistic_v4-v1%2FGEN-SIM&instance=prod/global)

**nugun:**
[/RelValNuGun/CMSSW_10_6_1_patch1-106X_mcRun3_2021_realistic_v3_rsb-v1/GEN-SIM](https://cmsweb.cern.ch/das/request?view=list&limit=50&instance=prod%2Fglobal&input=dataset%3D%2FRelValNuGun%2FCMSSW_10_6_1_patch1-106X_mcRun3_2021_realistic_v3_rsb-v1%2FGEN-SIM)

With these GEN-SIM input files we can use `cmsDriver.py` to make a `cmsRun` configuration file for completing the GEN-SIM-DIGI-RAW step. In the case of mixing in pileup one can call `cmsDriver.py` a la:

```
cmsDriver.py
  --pileup_input das:/RelValMinBias_13/CMSSW_10_6_0_pre4-106X_upgrade2021_realistic_v4-v1/GEN-SIM \
  --filein das:/PUT/DAS/PATH/HERE \
  --era Run3 \
  --eventcontent RAW \
  -s DIGI:pdigi_valid,L1,DIGI2RAW \
  --datatier RAW \
  --pileup AVE_50_BX_25ns \
  --geometry DB:Extended \
  --conditions 106X_upgrade2021_realistic_v4 \
  --fileout ootpu_cfg.py \
  --no_exec
```

As the process of mixing in pileup is intensive, it is recommended that instead of specifying all three GEN-SIM files as input to just specify each one in its own configuration file to be able to run in parallel. To configure for mixing in only out-of-time pileup, open up the generated python configuration file `ootpu_cfg.py` and make sure the following lines are configuring the mixing module:

```
process.mix.input.nbPileupEvents.averageNumber = cms.double(50.000000)
process.mix.input.manage_OOT = cms.untracked.bool(True)
process.mix.input.OOT_type = cms.untracked.string("Poisson")
process.mix.input.Special_Pileup_Studies = cms.untracked.string("Fixed_ITPU_Vary_OOTPU")
process.mix.bunchspace = cms.int32(25)
process.mix.minBunch = cms.int32(-10)
process.mix.maxBunch = cms.int32(4)
```

An equivalent `cmsRun` configuration file can be made for the case of no pileup and can be done by excluding the `--pileup_input` and `--pileup` flags and changing the name passed as `--fileout` when calling `cmsDriver.py`. After running `cmsRun ootpu_cfg.py` and waiting for many hours one will have a RAW root file with pileup mixed in.

## Making HCAL Ntuples

RAW files---like those produced during pileup mixing---are processed with the `cms-hcal-trigger` framework to produce manageable and simple-to-use ROOT TTrees (ntuples) with quantities that are relevant to extracting weights and studying trigger primitives.

To start, we setup a second CMSSW release (assuming working on LPC) and pull in some customized code:

```
cd $HOME/nobackup/HCAL_Trigger_Study/cmssw

mkdir puSub
cd puSub

cmsrel CMSSW_11_0_2
cd CMSSW_11_0_2/src
cmsenv

scram b -j8

git cms-merge-topic --unsafe JHiltbrand:110X_hcalPUSub_dev
git clone git@github.com:JHiltbrand/cms-hcal-debug.git Debug/HcalDebug
git checkout -b 110X_hcalPUSub_dev --track origin/110X_hcalPUSub_dev

scram b -j8
```

**For making ntuples to be used for weights extraction it is important to turn off pulse containment correction in `CalibCalorimetry/HcalTPGAlgos/src/HcaluLUTTPGCoder.cc` by commenting out the line:**

**```containmentCorrection = containmentCorrection2TSCorrected;```**

**then recompile again.**

Once these steps are completed one can process some RAW files and make ntuples for extracting pulse filter weights or studying trigger primitives.

### Generating HCAL Ntuples Locally
We can make ntuples by running `cmsRun` locally using the `analyze_HcalTrig_dev.py` configuration file. An example of doing this would be:

```
cd $HOME/nobackup/HCAL_Trigger_Study/scripts

cmsRun analyze_HcalTrig_dev.py FunName PFA2 TTbar_OOT
cmsRun analyze_HcalTrig_dev.py FunName PFA2 NOPU
```


* Here the argument `PFA2` is scheme that we would like to use when making trigger primitives.
* The argument `FunName` will be used to give the output ntuple file a unique name, in this case `hcalNtuple_FunName.root`.
* The `TTbar_OOT` or `NOPU` argument is parsed by the script and used to determine which GEN-SIM-DIGI-RAW files will be run on based on if-statement in the script. This if-statement is intended to be modified in order to run over a given set of files.

### Batch Generation of Ntuples
The other way of generating ntuples is to submit jobs to LPC condor or CRAB. This is most pertinent when running over entire datasets with many RAW files. Submitting to either condor or CRAB is acheived with the `submitHcalTrigNtuple.py` script.
A host of command line options are available:

```
--tag        = A unique tag to keep the output organized in a unique folder.
--mean       = Make ntuples using mean version of weights.
--depth      = Make ntuples using depth averaged version of weights.
--dataset    = A DAS-friendly path to a dataset.
--updown     = Make ntuples with the up/down variation of the specified weights.
--schemes    = The filter scheme to be used for TP reconstruction.
--crab       = Submit jobs to CRAB.
--era        = Which era was the dataset created.
--data       = Are we running on data?
--lumiMask   = When submitting to CRAB... a json file for running on certain runs/lumis
--globalTag  = The global tag to be used for reconstruction
--lumiSplit  = When submitting to condor... should jobs be split by lumi chunks?
--copyLocal  = When submitting to condor... should the RAW/AOD files be copied to worker node.
--filelist   = When submitting to condor... a list of DAS-friendly paths to files to be run over.
--run        = When submitting to condor... which run is being run over?
--needParent = When wanting to run on RAW + AOD for RECO information.
--noSubmit   = Don't submit to condor/CRAB
```

Thus, for example, to generate ntuples when reconstructing with the PFA1p with the per-ieta weights (including RECO information) one could submit to condor a la:

 ```
 python submitHcalTrigNtuples.py \
     --tag 20200527 \
     --dataset /TTbar_14TeV_TuneCP5_Pythia8/Run3Summer19DR-106X_mcRun3_2021_realistic_v3-v2/GEN-SIM-DIGI-RAW \
     --schemes PFA1p_PER_IETA \
     --era Run3 \
     --globalTag 110X_mcRun3_2021_v6 \
     --lumiSplit \
     --needParent
 ```
 
In this case, the output ROOT files with the HCAL ntuples will be placed at:

```
root://cmseos.fnal.gov///store/user/${USERNAME}/HCAL_Trigger_Study/hcalNtuples/TTbar/20200527/PFA1p_PER_IETA"
```
 
An equivalent form for submitting to CRAB would be:
 ```
 python submitHcalTrigNtuples.py \
     --crab \
     --tag 20200527 \
     --dataset /TTbar_14TeV_TuneCP5_Pythia8/Run3Summer19DR-106X_mcRun3_2021_realistic_v3-v2/GEN-SIM-DIGI-RAW \
     --schemes PFA1p_PER_IETA \
     --era Run3 \
     --globalTag 110X_mcRun3_2021_v6 \
     --needParent
 ```
 
Here, the `crab_submit_template.py` is referenced and contains some of the options that had to be passed manually when submitting to condor. The output files will be delivered to:

```
root://cmseos.fnal.gov///store/user/${USERNAME}/TTbar_14TeV_TuneCP5_Pythia8/HcalNtuples_PFA1p_PER_IETA_20200527/
```

### Making an Event Map

When we produce ntuple files using no pileup and out-of-time pileup DIGI-RAW files (for weights extraction), although all the same events are present in each, the events are not necessarily in the same order. To help speedup looping over the events tree while extracting weights, one needs to generate an event map that maps an event record in the OOT PU file to the same event record in the NOPU file. This is done by running `makeEventMap.py`. A call such as:

```
python makeEventMap.py --oot
```

will generate a python file `eventMap_NoContain_NoDepth_OOT.py` with a python dictionary called `PU2NOPUMAP`. Copy this dictionary into the `pu2nopuMap.py` script.

## Step 3: Extracting Pulse Filter Weights

Weight extraction is done by the `weightExtraction.py` script in the `extraction` subfolder. The script is run in two successive executions. The first execution is intended for looping over the events in the HCAL ntuple files and extracts raw weights and writes raw histograms to a cache file. Then the script is run again to process the cache for making final plots and text files. This allows trivial plotting changes to be done quickly without having to loop over all the events again. Several commandline options can be specified and are documented below:

```
--tag       = A unique tag to keep the output organized in its own folder.
--data      = Are we running on data?
--fromCache = Read back in cache file for making final plots and txt files (second step).
--contain   = When extracting weights, read input files from within a "Contain" subfolder ("NoContain" default)
--depth     = When extracting weights, read input files from within a "WithDepth" subfolder ("NoDepth" default)
--oot       = When extracting weights, read the OOT.root file instead of the 50PU.root file.
--nugun     = When extracting weights, assume we are running on nugun files (there will be no NOPU.root).
--scheme    = Specify which pulse filter to extract weights for (PFA1p, PFA1pp, PFA2p, PFA2pp)
--evtRange  = First element is starting event to process and second element is number of events to process.
```

A particular file/folder structure is anticipated when accessing the HCAL ntuple files. Most of the file path is built up based on the specified command line options. An example call of the `weightExtraction.py` script to extract no-depth weights for PFA1p, running over 100 events and starting at event 527 (in the OOT pileup file) would be:

```
python scripts/weightExtraction.py --oot --depth --scheme PFA1p --tag WithDepth_TTbar_OOT --evtRange 527 100
```

This will make an output file in `$HOME/nobackup/HCAL_Trigger_Study/plots/Weights/PFA1p/WithDepth_TTbar_OOT/root/histoCache_527.root`

Since this script is also used to run in batch mode, each job would gets its own unique number and the above directory would be filled with `histoCache_XYZ.root` files. These need to be hadded together into a single `histoCache.root` file which will be looked for by the script when specifying the `--fromCache` option.

### Running on LPC Condor

A condor submission script, `submitWeightExtraction.py` is provided to submit jobs and speed up the extraction of weights when running on an entire input file. An example call to this script would be:

```
python scripts/submitWeightExtraction.py --oot --depth --scheme PFA1p --tag WithDepth_TTbar_OOT --nJobs 90
```

The output files will be placed in the same location mentioned when running locally and one needs to hadd these files.

```
cd $HOME/nobackup/HCAL_Trigger_Study/plots/Weights/PFA1p/TP/WithDepth_TTbar_OOT/root
hadd histoCache.root histoCache_*
```

## Step 4: Applying the Weights and Generating New Ntuples

When extracting weights for a pulse filter scheme `weightExtraction.py` will produce a `weightSummary(Mean/Fit)Python.py` file that will have the weights formatted in the correct format to be used by the trigger primitive reconstruction algorithm in CMSSW. To use these weights, copy them into the `algo_weights.py` file---into the `pfaWeightsMap`---in the `scripts` folder. This script gets used anytime `cmsRun analyze_HcalTrig.py` is run. Whatever key names are provided in the `pfaWeightsMap` dictionary can be used on the command line when running `analyze_HcalTrig.py` (see above section).

Contrary to when generating ntuples to extract weights with, ensure that pulse containment is un-commented in `CalibCalorimetry/HcalTPGAlgos/src/HcaluLUTTPGCoder.cc` and recompile.
