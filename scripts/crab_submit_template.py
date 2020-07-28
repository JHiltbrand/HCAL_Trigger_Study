# template for crab submission.
# submit_jobs.py will insert definitions above
# if new L1TriggerObjects conditons have been specified with either
# a new tag or file

from CRABClient.UserUtilities import config
config = config()

config.General.requestName = 'hcalNtuples_PFA_' + "DATASET".split("/")[1]
config.General.transferLogs = True
config.General.transferOutputs = True

# Name of the CMSSW configuration file                                                                                                       
config.JobType.psetName = 'analyze_HcalTrig.py'
config.JobType.allowUndistributedCMSSW = True

config.JobType.pluginName = 'Analysis'
config.JobType.maxMemoryMB = 2500                                                                                                           
config.JobType.outputFiles = ['hcalNtuple.root']

config.Data.inputDataset = "DATASET"
config.Data.ignoreLocality = False
config.Data.inputDBS = 'global'
config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 1
config.Data.useParent = USEPARENT

# This string is used to construct the output dataset name                                                                                   
config.Data.outputDatasetTag = 'HcalNtuples_PFA_' + "DATASET".split("/")[1]

# These values only make sense for processing data                                                                                           
#    Select input data based on a lumi mask                                                                                                  
# Run2018D "https://cms-service-dqm.web.cern.ch/cms-service-dqm/CAF/certification/Collisions18/13TeV/Era/Prompt/Cert_320394-325273_13TeV_PromptReco_Collisions18_JSON_eraD.txt" 
config.Data.lumiMask = LUMIMASK

# Where the output files will be transmitted to                                                                                              
config.Site.storageSite = "T3_US_FNALLPC"
