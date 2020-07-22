import FWCore.ParameterSet.Config as cms
from Configuration.StandardSequences.Eras import eras

import sys, os

from algo_weights import pfaWeightsMap
from Configuration.AlCa.GlobalTag import GlobalTag

if len(sys.argv) < 4:
    print("An example call to cmsRun: 'cmsRun analyze_HcalTrig.py 0 PFA3p_PER_IETA 50PU'")
    exit()

job = str(sys.argv[2])
PFA = str(sys.argv[3])

inputFile = []
for aFile in sys.argv[4:]: inputFile.append(aFile)

# Only way to pass python list to cms object
readFiles = cms.untracked.vstring()
readFiles.extend(inputFile)

isData = "DATA" in inputFile

# Intialize the process based on the era
process = 0
if isData: process = cms.Process('RAW2DIGI', eras.Run2_2018)
else:      process = cms.Process('RAW2DIGI', eras.Run3)

# Import of standard configurations
process.load('Configuration.StandardSequences.Services_cff')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.EventContent.EventContent_cff')
process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
process.load('Configuration.StandardSequences.MagneticField_AutoFromDBCurrent_cff')
process.load('Configuration.StandardSequences.RawToDigi_Data_cff')
process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
process.load("SimCalorimetry.HcalTrigPrimProducers.hcaltpdigi_cff")
process.load("RecoLocalCalo.Configuration.hcalLocalReco_cff")

# Set the global tag if we are running on MC or data 
process.GlobalTag = GlobalTag(process.GlobalTag, '110X_mcRun3_2021_realistic_v6', '')

print "Using PeakFinderAlgorithm %s"%(PFA)
if "PFA2p" in PFA:
    print "Only using 3 samples"
    process.simHcalTriggerPrimitiveDigis.numberOfPresamplesHBQIE11 = 1
    process.simHcalTriggerPrimitiveDigis.numberOfPresamplesHEQIE11 = 1

elif "PFA2" in PFA:
    print "Only using 2 samples"

elif "PFA1p" in PFA:
    print "Only using 2 sample"
    process.simHcalTriggerPrimitiveDigis.numberOfPresamplesHBQIE11 = 1
    process.simHcalTriggerPrimitiveDigis.numberOfPresamplesHEQIE11 = 1
    process.HcalTPGCoderULUT.contain1TSHB = True
    process.HcalTPGCoderULUT.containPhaseNSHB = 3.0
    process.HcalTPGCoderULUT.contain1TSHE = True
    process.HcalTPGCoderULUT.containPhaseNSHE = 3.0

elif "PFA1" in PFA:
    print "Only using 1 sample"
    process.HcalTPGCoderULUT.contain1TSHB = True
    process.HcalTPGCoderULUT.containPhaseNSHB = 3.0
    process.HcalTPGCoderULUT.contain1TSHE = True
    process.HcalTPGCoderULUT.containPhaseNSHE = 3.0
elif "PFAX" in PFA:
    print "Using mixed samples"
    process.simHcalTriggerPrimitiveDigis.numberOfPresamplesHEQIE11 = 1
    process.HcalTPGCoderULUT.contain1TSHE = True
    process.HcalTPGCoderULUT.containPhaseNSHE = 3.0

if PFA in pfaWeightsMap:
    print "Using weights: "
    print pfaWeightsMap[PFA]
    process.simHcalTriggerPrimitiveDigis.weightsQIE11 = pfaWeightsMap[PFA] 

else:
    print "No weights defined for algo \"%s\"; defaulting to PFA2 weights!"%(PFA)

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(-1)
)

# Input source, here a few different pre-defined sets of files
if "DATA" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '110X_dataRun2_v12', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/data/Run2018D/JetHT/RAW/v1/000/324/021/00000/DC207766-1C12-DC44-B679-89EB77C5EE2A.root', # LS 44 of Run 324021        
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/data/Run2018D/JetHT/RAW/v1/000/324/021/00000/0B051695-EFBF-3F47-874D-92DE9278FA75.root', # LS 45 of Run 324021
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/data/Run2018D/JetHT/RAW/v1/000/324/021/00000/9318ED7A-17EB-6644-9DE8-1FF212666945.root', # LS 49 of Run 324021
        ),
        secondaryFileNames = cms.untracked.vstring(),
#        eventsToProcess = cms.untracked.VEventRange("324021:19599270-324021:19599270"),

    )

elif "JCH" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'root://cms-xrd-global.cern.ch///store/data/Run2018D/ZeroBias/AOD/PromptReco-v2/000/325/022/00000/152B8905-53EB-F14A-85B1-4BD28EB15B42.root',
        ),
        secondaryFileNames = cms.untracked.vstring(
            'root://cms-xrd-global.cern.ch///store/data/Run2018D/ZeroBias/RAW/v1/000/325/022/00000/1415A9FB-887E-7142-BAE8-E5B73636D240.root',
            'root://cms-xrd-global.cern.ch///store/data/Run2018D/ZeroBias/RAW/v1/000/325/022/00000/321385A5-0E6A-F741-8BF8-DCB84987802D.root',
            'root://cms-xrd-global.cern.ch///store/data/Run2018D/ZeroBias/RAW/v1/000/325/022/00000/B0DE4C15-12BC-554E-B795-FFB8C5CD748F.root',
        ),
    )


elif "TTbar_NOPU_OOT" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-NOPU123.root',
    
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "TTbar_25PU_OOT" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-50PU-OOT1_106X_25.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-50PU-OOT2_106X_25.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-50PU-OOT3_106X_25.root',
    
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "TTbar_50PU_OOT" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_0_pre4/RelValTTbar_13/GEN-SIM-DIGI-RAW/106X_upgrade2021_realistic_v4-v1/20000/TTbar-DIGI-RAW-50PU-OOT_1.root',
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_0_pre4/RelValTTbar_13/GEN-SIM-DIGI-RAW/106X_upgrade2021_realistic_v4-v1/20000/TTbar-DIGI-RAW-50PU-OOT_2.root',
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_0_pre4/RelValTTbar_13/GEN-SIM-DIGI-RAW/106X_upgrade2021_realistic_v4-v1/20000/TTbar-DIGI-RAW-50PU-OOT_3.root',
    
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "TTbar_75PU_OOT" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-50PU-OOT1_106X_75.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-50PU-OOT2_106X_75.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-50PU-OOT3_106X_75.root',
    
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "TTbar_100PU_OOT" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-50PU-OOT1_106X_100.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-50PU-OOT2_106X_100.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-50PU-OOT3_106X_100.root',
    
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "TTbar_25PU" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-PU1_106X_25.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-PU2_106X_25.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-PU3_106X_25.root',
    
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "TTbar_50PU" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-PU1_106X_50.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-PU2_106X_50.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-PU3_106X_50.root',

        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "TTbar_75PU" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-PU1_106X_75.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-PU2_106X_75.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-PU3_106X_75.root',
    
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "TTbar_100PU" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-PU1_106X_100.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-PU2_106X_100.root',
            'file:///uscmst1b_scratch/lpc1/3DayLifetime/jhiltbra/TTbar-DIGI-RAW-PU3_106X_100.root',
    
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "NuGun_25PU_OOT" in inputFile:
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_1_patch1/RelValNuGun/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3/10000/NuGun-DIGI-RAW-25PU_OOT.root',
        ),
        secondaryFileNames = cms.untracked.vstring(),

    )

elif "NuGun_50PU_OOT" in inputFile:
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_1_patch1/RelValNuGun/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3/10000/NuGun-DIGI-RAW-50PU_OOT_BX-1.root',
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "NuGun_75PU_OOT" in inputFile:
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_1_patch1/RelValNuGun/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3/10000/NuGun-DIGI-RAW-75PU_OOT_BX-1.root',
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "NuGun_100PU_OOT" in inputFile:
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_1_patch1/RelValNuGun/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_v3/10000/NuGun-DIGI-RAW-100PU_OOT.root',
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "TTbar_NOPU" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_0_pre4/RelValTTbar_13/GEN-SIM-DIGI-RAW/106X_upgrade2021_realistic_v4-v1/20000/TTbar-DIGI-RAW-NOPU.root',
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "TimeSlew_NOPU" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'root://cmseos.fnal.gov///store/user/jhiltbra/HCAL_Trigger_Study/relval/CMSSW_10_6_1/RelValTTbar_14TeV/GEN-SIM-DIGI-RAW/106X_mcRun3_2021_realistic_TimeSlew0_v3-v1/10000/TTbar-DIGI-RAW-NOPU123-FixedSlew.root',
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )

elif "TEST" in inputFile:
    process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2021_realistic_v4', '')
    process.source = cms.Source("PoolSource",
        fileNames = cms.untracked.vstring(
            'file:NuGun-DIGI-RAW-100PU_OOT.root',
        ),
        secondaryFileNames = cms.untracked.vstring(),
    )
else:
    process.source = cms.Source("PoolSource",
        fileNames = readFiles,
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
