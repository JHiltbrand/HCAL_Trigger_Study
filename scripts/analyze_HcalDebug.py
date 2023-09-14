import FWCore.ParameterSet.Config as cms

from Configuration.StandardSequences.Eras import eras
from Configuration.AlCa.GlobalTag import GlobalTag
import FWCore.PythonUtilities.LumiList as LumiList

process = cms.Process("HCALTP", eras.Run3)

process.load('Configuration.StandardSequences.Services_cff')
process.load('SimGeneral.HepPDTESSource.pythiapdt_cfi')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.EventContent.EventContent_cff')
process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
process.load('Configuration.StandardSequences.RawToDigi_Data_cff')
process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')

process.GlobalTag = GlobalTag(process.GlobalTag, "124X_dataRun3_Prompt_v10", "")

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(-1),
    output = cms.optional.untracked.allowed(cms.int32, cms.PSet)
)

process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring(CHILDFILE),
    #secondaryFileNames = cms.untracked.vstring(PARENTFILE),
)

process.source.lumisToProcess = LumiList.LumiList(filename = "CERT_LUMI_2022.json").getVLuminosityBlockRange()

process.configurationMetadata = cms.untracked.PSet(
    annotation = cms.untracked.string('analyze nevts:10000'),
    name = cms.untracked.string('Applications'),
    version = cms.untracked.string('$Revision: 1.19 $')
)

process.load("SimCalorimetry.HcalTrigPrimProducers.hcaltpdigi_cff")

process.simHcalTriggerPrimitiveDigis.inputUpgradeLabel = [
    "hcalDigis",
    "hcalDigis" 
]

process.simHcalTriggerPrimitiveDigis.overrideDBweightsAndFilterHB = cms.bool(True)
process.simHcalTriggerPrimitiveDigis.overrideDBweightsAndFilterHE = cms.bool(True)

process.HcalTPGCoderULUT.overrideDBweightsAndFilterHB = cms.bool(True)
process.HcalTPGCoderULUT.overrideDBweightsAndFilterHE = cms.bool(True)

process.HcalTPGCoderULUT.contain2TSHB = cms.bool(True)
process.HcalTPGCoderULUT.contain2TSHE = cms.bool(True)

process.simHcalTriggerPrimitiveDigis.numberOfFilterPresamplesHBQIE11 = 0
process.simHcalTriggerPrimitiveDigis.numberOfFilterPresamplesHEQIE11 = 0

process.HcalCompareChains = cms.EDAnalyzer("HcalCompareChains",
                                           triggerPrimitives_pfa1p=cms.InputTag("hcalDigis", "", "HCALTP"),
                                           triggerPrimitives_pfa2=cms.InputTag("simHcalTriggerPrimitiveDigis", "", "HCALTP"),
                                           recHits=cms.InputTag('hbhereco'),
                                           maxVtx=cms.uint32(100)
                                    )

process.TFileService = cms.Service("TFileService",
                                   closeFileFast = cms.untracked.bool(True),
                                   fileName = cms.string('hcalNtuple.root')
)

process.startjob = cms.Path(process.hcalDigis*process.simHcalTriggerPrimitiveDigis*process.HcalCompareChains)
    
process.schedule = cms.Schedule(process.startjob)

from PhysicsTools.PatAlgos.tools.helpers import associatePatAlgosToolsTask
associatePatAlgosToolsTask(process)

from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete
process = customiseEarlyDelete(process)
