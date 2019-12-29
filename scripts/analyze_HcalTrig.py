import FWCore.ParameterSet.Config as cms
from Configuration.StandardSequences.Eras import eras

import sys, os

from algo_weights import pfaWeightsMap
from Configuration.AlCa.GlobalTag import GlobalTag

if len(sys.argv) < 4:
    print("An example call to cmsRun: 'cmsRun analyze_HcalTrig.py PFA3p_PER_IETA 50PU 0'")
    exit()

PFA       = str(sys.argv[2])
inputFile = str(sys.argv[3])
job       = str(sys.argv[4])

isMC = inputFile == "OOT" or inputFile == "NOPU" or inputFile == "50PU" or "mcRun" in inputFile

# Intialize the process based on the era
process = 0
if isMC: process = cms.Process('RAW2DIGI', eras.Run3)
else:    process = cms.Process('RAW2DIGI', eras.Run2_2018)

# Import of standard configurations
process.load('Configuration.StandardSequences.Services_cff')
process.load('SimGeneral.HepPDTESSource.pythiapdt_cfi')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.EventContent.EventContent_cff')
process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
process.load('Configuration.StandardSequences.MagneticField_AutoFromDBCurrent_cff')
process.load('Configuration.StandardSequences.RawToDigi_Data_cff')
process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
process.load("SimCalorimetry.HcalTrigPrimProducers.hcaltpdigi_cff")
process.load("RecoLocalCalo.Configuration.hcalLocalReco_cff")

process.options = cms.untracked.PSet(

)

# Set the global tag if we are running on MC or data 
if isMC: process.GlobalTag = GlobalTag(process.GlobalTag, '106X_mcRun3_2021_realistic_v3', '')
else:    process.GlobalTag = GlobalTag(process.GlobalTag, '103X_dataRun2_Prompt_v3', '')

print "Using PeakFinderAlgorithm %s"%(PFA)
if "1" not in PFA:
    print "Only using 2 samples"
    process.simHcalTriggerPrimitiveDigis.numberOfSamples = 2
else:
    print "Only using 1 sample"
    process.simHcalTriggerPrimitiveDigis.numberOfSamples = 1

process.simHcalTriggerPrimitiveDigis.numberOfPresamples = 0

if PFA in pfaWeightsMap:
    print "Using weights: "
    print pfaWeightsMap[PFA]
    process.simHcalTriggerPrimitiveDigis.PeakFinderAlgorithmWeights = pfaWeightsMap[PFA] 
else:
    print "No weights defined for algo \"%s\"; defaulting to zero weights!"%(PFA)

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(-1)
)

# Input source, here a few different pre-defined sets of files
if inputFile == "OOT":
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            #'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/NuGun-DIGI-RAW-50PU-OOT_FORREAL.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_0_pre4/RelValNuGun/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3_50PU/20000/NuGun-DIGI-RAW-50PU_OOT.root',
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_0_pre4/RelValTTbar_13/GEN-SIM-DIGI-RAW/106X_upgrade2021_realistic_v4-v1_50PU/20000/TTbar-DIGI-RAW-50PU-OOT_1.root',
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_0_pre4/RelValTTbar_13/GEN-SIM-DIGI-RAW/106X_upgrade2021_realistic_v4-v1_50PU/20000/TTbar-DIGI-RAW-50PU-OOT_2.root',
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_0_pre4/RelValTTbar_13/GEN-SIM-DIGI-RAW/106X_upgrade2021_realistic_v4-v1_50PU/20000/TTbar-DIGI-RAW-50PU-OOT_3.root',
    
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )
elif inputFile == "NOPU":
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_0_pre4/RelValTTbar_13/GEN-SIM-DIGI-RAW/106X_upgrade2021_realistic_v4-v1_50PU/20000/TTbar-DIGI-RAW-NOPU.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_0_pre4/RelValTTbar_13/GEN-SIM-DIGI-RAW/106X_upgrade2021_realistic_v4-v1_50PU/20000/TTbar-DIGI-RAW-0PU123.root',
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )
elif inputFile == "50PU": 
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/043D2BF4-43C5-614F-BD81-D3C88968DD54.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/0FD371C3-32CA-6F4B-BCF4-013E0E73E988.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/1E38A61E-9906-6C4C-A286-524E5A59FB08.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/2AB2AC8F-C73A-0E42-8273-5FC1DC8C51E1.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/31958CF2-326B-6147-A06B-E51D7F493A33.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/31A48641-DF74-E244-970A-A69360E555E5.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/3FEE5DBF-DBDB-354E-9621-511A6908B009.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/56CE3E5D-6B17-9848-850B-B64142220B27.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/61FCF587-60D7-534A-8840-42C5736DD89D.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/64CD68F1-F9DE-554A-A997-BC4C2D1D3555.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/65E41851-B549-B24C-936A-040D5E0FB438.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/72978C5E-F4AC-ED4A-AD24-0CEEEB914300.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/79337207-D3E7-1A4A-8ECB-78ACBA3EFC43.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/9D068ED9-57BA-374A-99B4-188A8B017283.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/9D73926A-B466-004C-ABBD-50747ABE5565.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/9D922D01-3F40-314C-B50C-BB63B3B7A32F.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/AF74BABA-08FF-7D44-A577-A3C29343DD15.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/C756B891-8A34-EE43-B927-71806654289A.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/D24BCD6F-D41B-8143-AFB3-A6205999FD12.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/D8F3426D-B596-7B49-95D0-3C854169407C.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/DF4E49C7-1447-AF43-A86C-170AB21A8384.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/E727ABB5-7B1D-D74B-9D4B-682D5230388D.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/EEFEF44C-05F0-874B-B69D-C1F19A5AC94C.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/F68D0E05-BE8A-3344-9A65-33091666B3EE.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/mc/Run3Summer19DR/TTbar_14TeV_TuneCP5_Pythia8/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3-v2/130000/FDF31EC8-D103-AE49-B3CA-9E58F67C07F1.root',

        ),
        secondaryFileNames = cms.untracked.vstring(),
    )
elif inputFile == "DATA":
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            # High PU
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/Run2018D/JetHT/RAW/v1/000/324/021/00000/LS0044.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/Run2018D/JetHT/RAW/v1/000/324/021/00000/LS0045.root',
            #'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/Run2018D/JetHT/RAW/v1/000/324/021/00000/LS0049.root',

            # Low PU
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/Run2018D/JetHT/RAW/v1/000/324/021/00000/LS0800.root',
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/Run2018D/JetHT/RAW/v1/000/324/021/00000/LS0802.root',
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )
else:
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring('%s'%(inputFile),),
        secondaryFileNames = cms.untracked.vstring(),
    )

process.options = cms.untracked.PSet()

# Production Info
process.configurationMetadata = cms.untracked.PSet(
    annotation = cms.untracked.string('analyze nevts:-1'),
    name = cms.untracked.string('Applications'),
    version = cms.untracked.string('$Revision: 1.19 $')
)

# Make an analysis path
process.startjob = cms.Path(                                                   
  process.hcalDigis*                                                                        
  process.hfprereco*
  process.hfreco*
  process.hbheprereco

)

# Path and EndPath definitions
process.endjob_step = cms.EndPath(process.endOfProcess)

# Schedule definition
process.schedule = cms.Schedule(process.startjob,process.endjob_step)      
from PhysicsTools.PatAlgos.tools.helpers import associatePatAlgosToolsTask
associatePatAlgosToolsTask(process)

# Automatic addition of the customisation function from Debug.HcalDebug.customize
from Debug.HcalDebug.customize import use_data_reemul_tp,compare_raw_reemul_tp,compare_reemul_reco_sev9 

process =  use_data_reemul_tp(process)

#call to customisation function compare_raw_reemul_tp imported from Debug.HcalDebug.customize
#process = compare_raw_reemul_tp(process)

#call to customisation function compare_reemul_reco_sev9 imported from Debug.HcalDebug.customize
process = compare_reemul_reco_sev9(process)

process.TFileService.fileName=cms.string('hcalNtuple_%s.root'%(job))

# Add early deletion of temporary data products to reduce peak memory need
from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete
process = customiseEarlyDelete(process)
