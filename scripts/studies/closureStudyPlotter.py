# This script runs on two HCAL ntuple files, assumed to be from the same GEN-SIM file(s) 
# and matches TPs between the files (same event, same iphi, same ieta) to the get the TP ET
# ratio.

# An example call to the script would be:
# python studies/closureStudyPlotter.py --nopu subpath/to/nopu/ntuples/ --pu subpath/to/ootpu/ntuples --minET 0.5 --tag WORSTTAGNAME

# The subpaths are assumed to be HCAL_Trigger_Study/hcalNtuples in the user's EOS area
# The last argument is the minimum TP ET to accept for both TPs in a match when computing the ratio

import sys, os, ROOT, subprocess, argparse
from pu2nopuMap import PU2NOPUMAP 

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat("")
ROOT.gStyle.SetFrameLineWidth(4)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

# The main looping function that takes in a TChain for nopu and oot pu files, finds the
# matched TPs and fills a raw 2D histogram with the ratio.
def eventLoop(minTPET, nopuChain, ootChain, outfile):

    outfile.cd()
    h3_ratio = ROOT.TH3F("tpET_ratio", ";i#eta;TP E_{T} Ratio;", 257, -0.25, 128.25, 720, -0.014, 19.986, 28, 0.5, 28.5)

    ootChain.SetBranchStatus("*", 0);      nopuChain.SetBranchStatus("*", 0)
    ootChain.SetBranchStatus("et", 1);     nopuChain.SetBranchStatus("et", 1)
    ootChain.SetBranchStatus("ieta", 1);   nopuChain.SetBranchStatus("ieta", 1)
    ootChain.SetBranchStatus("iphi", 1);   nopuChain.SetBranchStatus("iphi", 1)
    ootChain.SetBranchStatus("event", 1);  nopuChain.SetBranchStatus("event", 1)
    ootChain.SetBranchStatus("depth", 1);  nopuChain.SetBranchStatus("depth", 1)

    NEVENTS = ootChain.GetEntries()

    for iEvent in xrange(0, NEVENTS):

        ootChain.GetEntry(iEvent)
        nopuChain.GetEntry(PU2NOPUMAP[ootChain.event])

        if ootChain.event != nopuChain.event:
            print "EVENT MISMATCH, SKIPPING THIS EVENT ENTRY!"
            continue

        # Due to ordering of TPs in depth, ieta, iphi we can be smart about breaking out of the inner loop as soon as possible
        # Use the hotStart to move the starting line for the inner loop as we go along
        hotStart = 0
        for iTP in xrange(0, len(ootChain.ieta)):
            ieta = ootChain.ieta[iTP]
            iphi = ootChain.iphi[iTP]
            idepth = ootChain.depth[iTP]
            iET = ootChain.et[iTP]

            # Due to ordering once we hit HF ieta stop looping!
            if abs(ieta) > 28: break
            if iET <= minTPET: continue 

            for jTP in xrange(hotStart, len(nopuChain.ieta)):
                jeta = nopuChain.ieta[jTP]
                jphi = nopuChain.iphi[jTP]
                jdepth = nopuChain.depth[jTP]
                jET = nopuChain.et[jTP]
        
                # Due to ordering once we hit HF ieta stop looping! 
                if abs(jeta) > 28: break
                if jET <= minTPET: continue

                # If we passed in depth then there was no match; break the inner loop and go back to outer loop
                elif jdepth > idepth:
                    hotStart = jTP
                    break

                # For same depth, if we pass in phi there was and will not be a match 
                elif idepth == jdepth:

                    # If we pass in ieta then there is no match; break the inner loop and go back to outer loop
                    if jeta * ieta < 0 or (jeta < 0 and ieta < 0 and jeta < ieta) or (jeta > 0 and ieta > 0 and jeta > ieta):
                        hotStart = jTP
                        break

                    # If eta also match then check at phi level
                    elif jeta == ieta:

                        # If we pass in phi then there was no match; break the inner loop and go back to outer loop
                        if jphi > iphi:
                            hotStart = jTP
                            break

                        # Here we match in depth, ieta and phi
                        elif jphi == iphi:

                            # We are here so we must have found a match!
                            #print "category   PU | event %s | ieta %d | iphi %d | depth %d | TP ET %f]"%(ootChain.event, ieta, iphi, idepth, ootChain.et[iTP])
                            #print "category NOPU | event %s | ieta %d | iphi %d | depth %d | TP ET %f]\n"%(nopuChain.event, jeta, jphi, jdepth, nopuChain.et[jTP])
                            
                            if jET > 0:
                                etFrac = iET / jET
                                h3_ratio.Fill(jET, etFrac, abs(ieta))

                            hotStart = jTP
                            break

        print "Processed event %d => %d..."%(iEvent,NEVENTS)

    return h3_ratio

# 2D histo of TP ET correlation for given range of ieta and range of TP ET
def etRatioIetaSlicer(outfile, histo, ietaRange = []):

    outfile.cd()

    htemp = histo.Clone()

    h2 = 0; ietaStr = ""
    if len(ietaRange) == 0:
        htemp.GetZaxis().SetRange(1, htemp.GetZaxis().GetNbins())
    elif len(ietaRange) == 1:
        htemp.GetZaxis().SetRange(htemp.GetZaxis().FindBin(ietaRange[0]),htemp.GetZaxis().FindBin(ietaRange[0]))
        ietaStr = "ieta%d"%(ietaRange[0])
    elif len(ietaRange) == 2:
        htemp.GetZaxis().SetRange(htemp.GetZaxis().FindBin(ietaRange[0]),htemp.GetZaxis().FindBin(ietaRange[1]))
        ietaStr = "ieta%dto%d"%(ietaRange[0],ietaRange[1])

    htemp.GetZaxis().SetBit(ROOT.TAxis.kAxisRange)
    h2 = htemp.Project3D("yx")

    h2.SetTitle("")
    h2.GetXaxis().SetTitle("TP E_{T} [GeV] (t#bar{t}+0PU)")
    h2.GetYaxis().SetTitle("E_{T,OOTPU} / E_{T,0PU}")

    h2.Write("TP_ETRatio_%s"%(ietaStr))

# The analysis method does the handling of the input file path and gets the list of files.
# From there the TChains are created and passed to the eventLoop
def analysis(NOPUFileDir, OOTFileDir, minTPET, tag):

    USER = os.getenv("USER")
    HOME = os.getenv("HOME")
    HCALNTUPLES = "/eos/uscms/store/user/%s/HCAL_Trigger_Study/hcalNtuples/"%(USER)

    onEOS = "store" in NOPUFileDir

    # Determine which set of weights for which filter was used
    # when running on the no pileup and pileup samples
    nopuStub = ""; puStub = ""
    for sub in NOPUFileDir.split("/"):
        if "PFA" in sub:
            nopuStub = sub
            break
    for sub in OOTFileDir.split("/"):
        if "PFA" in sub:
            puStub = sub
            break

    outDir = "%s/nobackup/HCAL_Trigger_Study/input/Closure/%s/%s_NOPU_vs_%s_PU/TPETgt%0.1f"%(HOME, tag, nopuStub, puStub, minTPET)
    if not os.path.exists(outDir): os.makedirs(outDir)

    outFilePath = outDir + "/closure.root"
    outFile = ROOT.TFile.Open(outFilePath, "RECREATE")

    cNOPU = ROOT.TChain("compareReemulRecoSeverity9/events", "NOPU")
    cOOT  = ROOT.TChain("compareReemulRecoSeverity9/events", "OOT")

    # Whether on EOS or locally, get the list of files to run on 
    proc = subprocess.Popen(["xrdfs", "root://cmseos.fnal.gov", "ls", HCALNTUPLES + NOPUFileDir], stdout=subprocess.PIPE)
    allItems = proc.stdout.readlines();  allItems = [item.rstrip() for item in allItems]

    # Add only honest root files to TChain
    for item in allItems:
        
        if ".root" not in item: continue
        if "ratio" in item:     continue
    
        cNOPU.AddFile("root://cmseos.fnal.gov/"+item)

    # Whether on EOS or locally, get the list of files to run on 
    proc = subprocess.Popen(["xrdfs", "root://cmseos.fnal.gov", "ls", HCALNTUPLES + OOTFileDir], stdout=subprocess.PIPE)
    allItems = proc.stdout.readlines();  allItems = [item.rstrip() for item in allItems]

    # Add only honest root files to TChain
    for item in allItems:
        
        if ".root" not in item: continue
        if "ratio" in item:     continue
    
        cOOT.AddFile("root://cmseos.fnal.gov/"+item)

    tpRatioHisto = eventLoop(minTPET, cNOPU, cOOT, outFile)    

    for ieta in xrange(1,29): etRatioIetaSlicer(outFile, tpRatioHisto, ietaRange = [ieta])

    print "Done writing to ==> \"%s\""%(outFilePath)
    outFile.Close()
   
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--tag"  , dest="tag"  , type=str  , default=""    , help="Unique tag for output")
    parser.add_argument("--minET", dest="minET", type=float, default=0.0   , help="minEt selection")
    parser.add_argument("--nopu" , dest="nopu" , type=str  , default="NULL", help="Path to inputs for nopu")
    parser.add_argument("--pu"   , dest="pu"   , type=str  , default="NULL", help="Path to inputs for pu") 
    args = parser.parse_args()

    NOPUFileDir = args.nopu
    OOTFileDir  = args.pu
    tag = args.tag
    minTPET = args.minET    

    analysis(NOPUFileDir, OOTFileDir, minTPET, tag)
