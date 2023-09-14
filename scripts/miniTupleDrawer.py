#! /bin/env/python

import os
import re
import json
import array
import argparse
import random

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

def printEvents(tree):

    tree.SetBranchStatus("*", 0)
    tree.SetBranchStatus("RH_energy_MAHI",  1)
    tree.SetBranchStatus("RH_energy_MAHI_cutoff",  1)
    tree.SetBranchStatus("TP_energy_PFA1p", 1)
    tree.SetBranchStatus("TP_energy_PFA2",  1)

    tree.SetBranchStatus("nVtx", 1)
    tree.SetBranchStatus("run",  1)
    tree.SetBranchStatus("evt",  1)
    tree.SetBranchStatus("ls",   1)
    tree.SetBranchStatus("ieta", 1)
    tree.SetBranchStatus("iphi", 1)

    f = open("event_stats.txt", "w")

    # Loop over the entries in the tree
    for iEvent in range(tree.GetEntries()):

        tree.GetEntry(iEvent)
    
        rhET    = tree.GetLeaf("RH_energy_MAHI").GetValue()
        rhETcut = tree.GetLeaf("RH_energy_MAHI_cutoff").GetValue()
        pfa1pET = tree.GetLeaf("TP_energy_PFA1p").GetValue()
        pfa2ET  = tree.GetLeaf("TP_energy_PFA2").GetValue()

        nVtx = int(tree.GetLeaf("nVtx").GetValue())
        run  = int(tree.GetLeaf("run").GetValue())
        evt  = int(tree.GetLeaf("evt").GetValue())
        ls   = int(tree.GetLeaf("ls").GetValue())
        ieta = int(tree.GetLeaf("ieta").GetValue())
        iphi = int(tree.GetLeaf("iphi").GetValue())

        TPRH1 = -1.0
        TPRH2 = -1.0
        if rhET > 0.0:
            TPRH2 = pfa2ET / rhET 
            TPRH1 = pfa1pET / rhET

        keep = False
        if TPRH1 > 0.0 and (pfa1pET > 0.5 or pfa2ET > 0.5):
            if abs(ieta) <= 16:
                keep = True

        if keep:
            f.write("%.3f,%.3f,%.1f,%.1f,%.1f,%.1f,%d,%d,%d,%d,%d,%d\n"%(TPRH1,TPRH2,pfa1pET,pfa2ET,rhET,rhETcut,nVtx,run,ls,evt,ieta,iphi)) 

    f.close()

# Routine that is called for each individual histogram that is to be 
# drawn from the input tree. All information about what to draw, selections,
# and weights is contained in the histOps dictionary
def makeNDhisto(histName, histOps, outfile, tree):

    variable = histOps["variable"]
    dimCheck = variable
    varList = [variable]
    if variable.__class__.__name__ == "list":
       dimCheck = variable[0]
       varList = variable

    dim = 1
    foundSingleColons = re.findall(r'(?<!:):(?!:)', dimCheck)
    dim += len(foundSingleColons)

    outfile.cd()

    temph = None
    if   dim == 1:
        if "xedges" in histOps:
            temph = ROOT.TH1F(histName, "", histOps["xbins"], histOps["xedges"])
        else:
            temph = ROOT.TH1F(histName, "", histOps["xbins"], histOps["xmin"], histOps["xmax"])
    elif dim == 2:
        if  "xedges" in histOps and "yedges" in histOps:
            temph = ROOT.TH2F(histName, "", histOps["xbins"], histOps["xedges"], histOps["ybins"], histOps["yedges"])

        elif "xedges" in histOps and "yedges" not in histOps:
            temph = ROOT.TH2F(histName, "", histOps["xbins"], histOps["xedges"], histOps["ybins"], histOps["ymin"], histOps["ymax"])

        elif "xedges" not in histOps and "yedges" in histOps:
            temph = ROOT.TH2F(histName, "", histOps["xbins"], histOps["xmin"], histOps["xmax"], histOps["ybins"], histOps["yedges"])

        elif "xedges" not in histOps and "yedges" not in histOps:
            temph = ROOT.TH2F(histName, "", histOps["xbins"], histOps["xmin"], histOps["xmax"], histOps["ybins"], histOps["ymin"], histOps["ymax"])


    for var in varList:
        # To efficiently TTree->Draw(), we will only "activate"
        # necessary branches. So first, disable all branches
        tree.SetBranchStatus("*", 0)

        selection = histOps["selection"]
        weight    = histOps["weight"]
        
        # Make one big string to extract all relevant branch names from
        concatStr = selection + "," + var
        concatStr = concatStr + "," + weight

        # The idea is to turn the concatStr into a comma separated list of branches
        # Parenthesis can simply be removed, operators are simply replace with a comma
        # After all replacements, the string is split on the comma and filtered for empty strings
        expressions = re.findall(r'(\w+::\w+)', concatStr)
        for exp in expressions:
            concatStr = concatStr.replace(exp, "")
        concatStr = re.sub("[()]", "", concatStr)
        for replaceStr in ["abs", "&&", "||", "==", "<=", ">=", ">", "<", "*", ".", "/", "+", "-", ":"]:
            concatStr = concatStr.replace(replaceStr, ",")
        branches = list(filter(bool, concatStr.split(",")))

        # Here, the branches list will be names of branches and strings of digits
        # The digits are residual cut expressions like NGoodJets_pt30>=7 ==> "NGoodJets_pt30", "7"
        # So if a supposed branch name can be turned into an int, then it is not a legit branch name
        for branch in branches:
            try:
                int(branch)
                continue
            except:
                tree.SetBranchStatus(branch, 1)

        # For MC, we multiply the selection string by our chosen weight in order
        # to fill the histogram with an event's corresponding weight
        drawExpression = "%s>>+%s"%(var, histName)
        tree.Draw(drawExpression, "(%s)*(%s)"%(weight,selection))
      
    temph = ROOT.gDirectory.Get(histName)
    temph.Sumw2()

    temph.Write(histName, ROOT.TObject.kOverwrite)

# Main function that a given pool process runs, the input TTree is opened
# and the list of requested histograms are drawn to the output ROOT file
def processFile(outputDir, inputFile, histograms, treeName):

    infile = ROOT.TFile.Open(inputFile,  "UPDATE"); infile.cd()
    if infile == None:
        print("Could not open input ROOT file \"%s\""%(inputFile))
        return

    tree = infile.Get(treeName)

    if tree == None:
        print("Could not get tree \"%s\" from input ROOT file \"%s\""%(treeName, inputFile))
        return

    printEvents(tree)

    outfile = ROOT.TFile.Open("%s/hcalHistos.root"%(outputDir), "RECREATE")

    for histName, histOps in histograms.items():
        makeNDhisto(histName, histOps, outfile, tree)

    outfile.Close()

if __name__ == "__main__":
    usage = "%miniTupleDrawer [options]"
    parser = argparse.ArgumentParser(usage)
    parser.add_argument("--inputFile", dest="inputFile", help="Path to infile",     required=True                  )
    parser.add_argument("--outputDir", dest="outputDir", help="path to output",     default="./"                   )
    parser.add_argument("--tree",      dest="tree",      help="TTree name to draw", default="HcalCompareChains/TPs")
    parser.add_argument("--options",   dest="options",   help="options file",       default="miniTupleDrawer_aux"  )
    args = parser.parse_args()
    
    # The auxiliary file contains many "hardcoded" items
    # describing which histograms to get and how to draw
    # them. These things are changed often by the user
    # and thus are kept in separate sidecar file.
    importedGoods = __import__(args.options)
    
    # Names of histograms, rebinning
    histograms = importedGoods.histograms
    
    inputFile = args.inputFile
    outputDir = args.outputDir
    treeName  = args.tree
    
    # The draw histograms and their host ROOT files are kept in the output
    # folder in the user's condor folder. This then makes running a plotter
    # on the output exactly like running on histogram output from an analyzer
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    # The processFile function is attached to each process
    processFile(outputDir, inputFile, histograms, treeName)
