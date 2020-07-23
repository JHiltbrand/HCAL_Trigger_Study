#!/usr/bin/env python

import sys, os, ROOT, numpy, argparse, math, fnmatch
from collections import defaultdict
from pu2nopuMap import PU2NOPUMAP 

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat("")
ROOT.gStyle.SetFrameLineWidth(4)
ROOT.gStyle.SetPaintTextFormat("3.2f")
ROOT.gErrorIgnoreLevel = ROOT.kWarning
ROOT.gStyle.SetEndErrorSize(0)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

# The WeightExtractor class is supplied a pulse filter scheme name, an input file for the PU case, an input
# file for the NOPU case and a output path to store everything. The Extractor can separately be used
# to loop over events and extract events and then can be used to generate final results (weight distributions
# with fits, tables of weights and histograms).
class WeightExtractor:

    def __init__(self, scheme, data, inputFilePU, inputFileNOPU, outputPath, withDepth):

        self.outPath = outputPath              # Base outpath to write everything to
        self.cacheLoc = "%s/root"%(outputPath) # Location to cache histograms in root file

        self.withDepth = withDepth # Toggle if we should be extracting on per-depth basis

        self.nopuUsed = inputFileNOPU != "NULL" # Special case when there is no NOPU file

        self.data = data # Switch if we are running on data or not (will change how things are run

        # _My_ use of word "sample" is any TS >= SOI
        if scheme == "PFA2pp":
            self.tpPresamples = 2              # PFA2pp uses two presamples
            self.tpSamples = 2                 # SOI and SOI+1 are used to sample signal pulse
            self.nWeights = 2
        elif scheme == "PFA2p":
            self.tpPresamples = 1              # PFA2p uses two SOI and SOI+1 fully and SOI-1 presample
            self.tpSamples = 2                 # SOI and SOI+1 are used to sample non-PU pulse
            self.nWeights = 1
        elif scheme == "PFA1p":
            self.tpPresamples = 1              # PFA1 uses SOI fully and SOI-1 presample to subtract
            self.tpSamples = 1                 # Only SOI is used to sample non-PU pulse
            self.nWeights = 1
        elif scheme == "PFA1pp":
            self.tpPresamples = 2              # PFA1p uses SOI fully and SOI-2 and SOI-1 presamples to subtract
            self.tpSamples = 1                 # Only SOI is used to sample non-PU pulse
            self.nWeights = 2

        self.SOI    = 3                                      # SOI for 8TS digi is always 3
        self.offset = 3                                      # We need this offset to scan 8TS digi starting from 0
        self.event  = -1                                     # Current event we are looking at
        self.scheme = scheme                                 # Which pulse filtering scheme 
        self.ts2Cut = 3                                      # Requirement on TS2 (SOI-1) > n ADC
        self.rebin  = 2                                      # Rebin factor for weight histograms
        self.iWeights = list(xrange(self.nWeights+1, 1, -1)) # List of i weights 
        self.ts2Cuts  = list(xrange(-1,4,4))                 # List of selections on SOI-1 to make

        self.HBHEMap = {"HB" :  {1  : [0, 1, 2, 3, 4],       2  : [0, 1, 2, 3, 4],       3  : [0, 1, 2, 3, 4],       4  : [0, 1, 2, 3, 4],
                                 5  : [0, 1, 2, 3, 4],       6  : [0, 1, 2, 3, 4],       7  : [0, 1, 2, 3, 4],       8  : [0, 1, 2, 3, 4], 
                                 9  : [0, 1, 2, 3, 4],       10 : [0, 1, 2, 3, 4],       11 : [0, 1, 2, 3, 4],       12 : [0, 1, 2, 3, 4],
                                 13 : [0, 1, 2, 3, 4],       14 : [0, 1, 2, 3, 4],       15 : [0, 1, 2, 3, 4],       16 : [0, 1, 2, 3, 4]},
                        "HE1" : {17 : [0, 2, 3],             18 : [0, 1, 2, 3, 4, 5],    19 : [0, 1, 2, 3, 4, 5, 6], 20 : [0, 1, 2, 3, 4, 5, 6]}, 
                        "HE2" : {21 : [0, 1, 2, 3, 4, 5, 6], 22 : [0, 1, 2, 3, 4, 5, 6], 23 : [0, 1, 2, 3, 4, 5, 6], 24 : [0, 1, 2, 3, 4, 5, 6],
                                 25 : [0, 1, 2, 3, 4, 5, 6], 26 : [0, 1, 2, 3, 4, 5, 6], 27 : [0, 1, 2, 3, 4, 5, 6], 28 : [0, 1, 2, 3, 4, 5, 6]}
        }

        self.weightHistos = {}             # Map ieta,depth,iWeight to 1D histo of said weight 
        self.averagePulseWeights = {}      # Map of depth,ieta,iWeight to weight from average pulses 
        self.averagePulseStatErrors = {}   # Maps depth,ieta,TS2 Cut,iWeight to a stat error for the average pulse-derived weight
        self.averagePulseSystErrors = {}   # Maps depth,ieta,iWeight to a syst error for the average pulse-derived weight
        self.fitWeights = {}               # Maps depth,ieta,iWeight to a weight extracted from fit of distribution
        self.fitStatErrors = {}            # Maps depth,ieta,iWeight to a statistical error on the fit weight 
        self.fitSystErrors = {}            # Maps depth,ieta,iWeight to a systematic error on the fit weight 
        self.meanWeights = {}              # Maps depth,ieta,iWeight to a weight extracted from mean of distribution
        self.meanStatErrors = {}           # Maps depth,ieta,iWeight to a statistical error on the mean weight 
        self.meanSystErrors = {}           # Maps depth,ieta,iWeight to a systematic error on the mean weight 
        self.meanRMSErrors = {}            # Maps depth,ieta,iWeight to the RMS of the weight distribution
        self.pulseShapesPU = {}            # Average pulse shapes for PU mapped by ieta,depth
        self.pulseShapesNOPU = {}          # Average pulse shapes for NOPU mapped by ieta,depth
        self.ietaDensity = {}              # Number of matched pulses mapped by ieta,depth

        # Initialize map of histos if not loading from cache file
        if not gFromCache:
            self.tfilepu = ROOT.TFile.Open(inputFilePU, "r")
            self.ttreepu = self.tfilepu.Get("compareReemulRecoSeverity9/events")

            if self.nopuUsed:
                self.tfilenopu = ROOT.TFile.Open(inputFileNOPU, "r")
                self.ttreenopu = self.tfilenopu.Get("compareReemulRecoSeverity9/events")

            for subdet, ietaMap in self.HBHEMap.iteritems():
                for ieta, depths in ietaMap.iteritems():
                    for depth in depths:

                        if self.withDepth and depth == 0 or not self.withDepth and depth > 0: continue

                        for ts2Cut in self.ts2Cuts:
                            # This if-statement is a lame hack since we don't need this histo for every ieta
                            if ieta == 27: self.ietaDensity.setdefault(depth, {}).setdefault(ts2Cut, ROOT.TH1F("depth%d_nTPs_TS2gt%d"%(depth,ts2Cut), "depth%d_nTPs_TS2gt%d"%(depth,ts2Cut), 28, 0.5, 28.5))

                        iname = "ieta%d_depth%d"%(ieta,depth)
                        for weight in self.iWeights:
                            wname = iname+"_w%d"%(weight)
                            for ts2Cut in self.ts2Cuts:
                                tname = wname+"_TS2gt%d"%(ts2Cut)
                                self.weightHistos.setdefault(depth, {}).setdefault(ieta, {}).setdefault(weight, {}).setdefault(ts2Cut, ROOT.TH1F(tname, tname, 7200, -50.0, 50.0))

                        for ts2Cut in self.ts2Cuts:
                            tname1 = iname+"_pulsePU_TS2gt%d"%(ts2Cut)
                            self.pulseShapesPU.setdefault(depth, {}).setdefault(ieta, {}).setdefault(ts2Cut, ROOT.TH2F(tname1, tname1, 8, -3.5, 4.5, 2049, -0.5, 2048.5))

                            if self.nopuUsed:
                                tname2 = iname+"_pulseNOPU_TS2gt%d"%(ts2Cut)
                                self.pulseShapesNOPU.setdefault(depth, {}).setdefault(ieta, {}).setdefault(ts2Cut, ROOT.TH2F(tname2, tname2, 8, -3.5, 4.5, 2049, -0.5, 2048.5))

    def eventLoop(self, eventRange): 

        # If eventRange goes unset, then the eventLoop should not be run
        if eventRange[0] == -1 or len(eventRange) == 2: return

        # Use special case -2 to run over all events in the TTree
        if eventRange[0] == -2: eventRange = xrange(0, self.ttreepu.GetEntries())

        # At the beginning, only initialize branches we need.
        # Hopefully this speeds up processing
        self.ttreepu.SetBranchStatus("*", 0)
        self.ttreepu.SetBranchStatus("ieta", 1)
        self.ttreepu.SetBranchStatus("iphi", 1)
        self.ttreepu.SetBranchStatus("event", 1)
        self.ttreepu.SetBranchStatus("depth", 1)

        if self.nopuUsed:
            self.ttreenopu.SetBranchStatus("*", 0)               
            self.ttreenopu.SetBranchStatus("ieta", 1)
            self.ttreenopu.SetBranchStatus("iphi", 1)
            self.ttreenopu.SetBranchStatus("event", 1)
            self.ttreenopu.SetBranchStatus("depth", 1)

            for iTS in xrange(0,8): self.ttreenopu.SetBranchStatus("ts%d"%(iTS), 1)

        for iTS in xrange(0,8): self.ttreepu.SetBranchStatus("ts%d"%(iTS), 1)

        print "Constructing per-ieta, per-event 8TS pulses"
        for iEvent in eventRange:

            puSuccess = self.ttreepu.GetEntry(iEvent)
            if puSuccess == 0:
                print "Could not get entry %d!"%(iEvent)
                break

            if self.nopuUsed:
                self.ttreenopu.GetEntry(PU2NOPUMAP[self.ttreepu.event])
                if self.ttreepu.event != self.ttreenopu.event:
                    print "EVENT MISMATCH, SKIPPING THIS EVENT ENTRY!"
                    continue

            self.event = self.ttreepu.event

            # Due to ordering of TPs in depth, ieta, iphi we can be smart about breaking out of the inner loop as soon as possible
            # Use the hotStart to move the starting line for the inner loop as we go along
            hotStart = 0
            for iTP in xrange(0, len(self.ttreepu.ieta)):
                ieta = self.ttreepu.ieta[iTP]
                iphi = self.ttreepu.iphi[iTP]
                idepth = self.ttreepu.depth[iTP]

                # Due to ordering once we hit HF ieta stop looping!
                if abs(ieta) > 28: break 

                # Always kill 8TS with 0 in TS3
                if self.ttreepu.ts3[iTP] == 0: continue

                # Start big if case, first if we are doing traditional running on MC with PU and NOPU info
                if self.nopuUsed:

                    for jTP in xrange(hotStart, len(self.ttreenopu.ieta)):
                        jeta = self.ttreenopu.ieta[jTP]
                        jphi = self.ttreenopu.iphi[jTP]
                        jdepth = self.ttreenopu.depth[jTP]
            
                        # Due to ordering once we hit HF ieta stop looping! 
                        if abs(jeta) > 28: break 

                        # Always kill 8TS with 0 in TS3, we want physics here!
                        elif self.ttreenopu.ts3[jTP] == 0: continue

                        # If we passed in depth then there was no match; break the inner loop and go back to outer loop
                        elif jdepth > idepth:
                            hotStart = jTP
                            break

                        # For same depth, if we pass in phi there was and will not be a match 
                        elif idepth == jdepth:

                            # If we pass in ieta then there is no match; break the inner loop and go back to outer loop
                            if (jeta - ieta) * jeta > 0:
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
                                    #print "category   PU | event %s | ieta %d | iphi %d | depth %d | 8TS [%d, %d, %d, %d, %d, %d, %d, %d]"%(self.ttreepu.event, ieta, iphi, idepth, self.ttreepu.ts0[iTP], self.ttreepu.ts1[iTP],self.ttreepu.ts2[iTP],self.ttreepu.ts3[iTP],self.ttreepu.ts4[iTP],self.ttreepu.ts5[iTP],self.ttreepu.ts6[iTP],self.ttreepu.ts7[iTP])
                                    #print "category NOPU | event %s | ieta %d | iphi %d | depth %d | 8TS [%d, %d, %d, %d, %d, %d, %d, %d]\n"%(self.ttreenopu.event, jeta, jphi, jdepth, self.ttreenopu.ts0[jTP], self.ttreenopu.ts1[jTP],self.ttreenopu.ts2[jTP],self.ttreenopu.ts3[jTP],self.ttreenopu.ts4[jTP],self.ttreenopu.ts5[jTP],self.ttreenopu.ts6[jTP],self.ttreenopu.ts7[jTP])

                                    puPulse    = numpy.zeros((8,1));    nopuPulse    = numpy.zeros((8,1))
                                    puPulse[0] = self.ttreepu.ts0[iTP]; nopuPulse[0] = self.ttreenopu.ts0[jTP]
                                    puPulse[1] = self.ttreepu.ts1[iTP]; nopuPulse[1] = self.ttreenopu.ts1[jTP]
                                    puPulse[2] = self.ttreepu.ts2[iTP]; nopuPulse[2] = self.ttreenopu.ts2[jTP]
                                    puPulse[3] = self.ttreepu.ts3[iTP]; nopuPulse[3] = self.ttreenopu.ts3[jTP]
                                    puPulse[4] = self.ttreepu.ts4[iTP]; nopuPulse[4] = self.ttreenopu.ts4[jTP]
                                    puPulse[5] = self.ttreepu.ts5[iTP]; nopuPulse[5] = self.ttreenopu.ts5[jTP]
                                    puPulse[6] = self.ttreepu.ts6[iTP]; nopuPulse[6] = self.ttreenopu.ts6[jTP]
                                    puPulse[7] = self.ttreepu.ts7[iTP]; nopuPulse[7] = self.ttreenopu.ts7[jTP]

                                    for ts2Cut in self.ts2Cuts:
                                        if self.ttreepu.ts2[iTP] > ts2Cut:
                                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill(-3, self.ttreepu.ts0[iTP]); self.pulseShapesNOPU[idepth][abs(ieta)][ts2Cut].Fill(-3, self.ttreenopu.ts0[jTP])
                                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill(-2, self.ttreepu.ts1[iTP]); self.pulseShapesNOPU[idepth][abs(ieta)][ts2Cut].Fill(-2, self.ttreenopu.ts1[jTP])
                                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill(-1, self.ttreepu.ts2[iTP]); self.pulseShapesNOPU[idepth][abs(ieta)][ts2Cut].Fill(-1, self.ttreenopu.ts2[jTP])
                                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 0, self.ttreepu.ts3[iTP]); self.pulseShapesNOPU[idepth][abs(ieta)][ts2Cut].Fill( 0, self.ttreenopu.ts3[jTP])
                                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 1, self.ttreepu.ts4[iTP]); self.pulseShapesNOPU[idepth][abs(ieta)][ts2Cut].Fill( 1, self.ttreenopu.ts4[jTP])
                                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 2, self.ttreepu.ts5[iTP]); self.pulseShapesNOPU[idepth][abs(ieta)][ts2Cut].Fill( 2, self.ttreenopu.ts5[jTP])
                                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 3, self.ttreepu.ts6[iTP]); self.pulseShapesNOPU[idepth][abs(ieta)][ts2Cut].Fill( 3, self.ttreenopu.ts6[jTP])
                                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 4, self.ttreepu.ts7[iTP]); self.pulseShapesNOPU[idepth][abs(ieta)][ts2Cut].Fill( 4, self.ttreenopu.ts7[jTP])
                                            self.ietaDensity[idepth][ts2Cut].Fill(abs(ieta))

                                            weights = self.extractWeights(puPulse, nopuPulse)

                                            for ts in self.iWeights: self.weightHistos[idepth][abs(ieta)][ts][ts2Cut].Fill(weights[ts-1])
    
                                    hotStart = jTP
                                    break

                # Next check if we are running in nu-gun mode (no NOPU info)
                elif not self.nopuUsed and not self.data:
    
                    # We are here so we must have found a match!
                    #print "category   PU | event %s | ieta %d | iphi %d | depth %d | 8TS [%d, %d, %d, %d, %d, %d, %d, %d]"%(self.ttreepu.event, ieta, iphi, idepth, self.ttreepu.ts0[iTP], self.ttreepu.ts1[iTP],self.ttreepu.ts2[iTP],self.ttreepu.ts3[iTP],self.ttreepu.ts4[iTP],self.ttreepu.ts5[iTP],self.ttreepu.ts6[iTP],self.ttreepu.ts7[iTP])

                    puPulse    = numpy.zeros((8,1))
                    nopuPulse  = numpy.zeros((8,1))
                    puPulse[0] = self.ttreepu.ts0[iTP]
                    puPulse[1] = self.ttreepu.ts1[iTP]
                    puPulse[2] = self.ttreepu.ts2[iTP]
                    puPulse[3] = self.ttreepu.ts3[iTP]
                    puPulse[4] = self.ttreepu.ts4[iTP]
                    puPulse[5] = self.ttreepu.ts5[iTP]
                    puPulse[6] = self.ttreepu.ts6[iTP]
                    puPulse[7] = self.ttreepu.ts7[iTP]

                    for ts2Cut in self.ts2Cuts:
                        if self.ttreepu.ts2[iTP] > ts2Cut:
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill(-3, self.ttreepu.ts0[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill(-2, self.ttreepu.ts1[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill(-1, self.ttreepu.ts2[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 0, self.ttreepu.ts3[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 1, self.ttreepu.ts4[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 2, self.ttreepu.ts5[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 3, self.ttreepu.ts6[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 4, self.ttreepu.ts7[iTP])
                            self.ietaDensity[idepth][ts2Cut].Fill(abs(ieta))

                            weights = self.extractWeights(puPulse, nopuPulse)
                            
                            for ts in self.iWeights: self.weightHistos[idepth][abs(ieta)][ts][ts2Cut].Fill(weights[ts-1])

                # If we hit this then we are running on data (no NOPU info)
                # Method only makes sense for PFA1p by looking at fraction SOI+1/SOI
                elif self.data:

                    puPulse    = numpy.zeros((8,1))
                    puPulse[0] = self.ttreepu.ts0[iTP]
                    puPulse[1] = self.ttreepu.ts1[iTP]
                    puPulse[2] = self.ttreepu.ts2[iTP]
                    puPulse[3] = self.ttreepu.ts3[iTP]
                    puPulse[4] = self.ttreepu.ts4[iTP]
                    puPulse[5] = self.ttreepu.ts5[iTP]
                    puPulse[6] = self.ttreepu.ts6[iTP]
                    puPulse[7] = self.ttreepu.ts7[iTP]

                    # For running on iso bunch data, the pulse is only in TS3 so apply TS2 cut to TS3---a bit hacky
                    for ts2Cut in self.ts2Cuts:
                        if self.ttreepu.ts3[iTP] > ts2Cut:
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill(-3, self.ttreepu.ts0[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill(-2, self.ttreepu.ts1[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill(-1, self.ttreepu.ts2[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 0, self.ttreepu.ts3[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 1, self.ttreepu.ts4[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 2, self.ttreepu.ts5[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 3, self.ttreepu.ts6[iTP])
                            self.pulseShapesPU[idepth][abs(ieta)][ts2Cut].Fill( 4, self.ttreepu.ts7[iTP])
                            self.ietaDensity[idepth][ts2Cut].Fill(abs(ieta))

                            # For iso bunch data and thinking about PFA1p, the weight is simply how much of
                            # the pulse is in SOI+1 given SOI, so trivially calculate that here
                            weights = [-999.0, float(self.ttreepu.ts4[iTP])/float(self.ttreepu.ts3[iTP])]
                            
                            for ts in self.iWeights: self.weightHistos[idepth][abs(ieta)][ts][ts2Cut].Fill(weights[ts-1])
   
            print "Processed event %d => %d..."%(iEvent,eventRange[-1])
        
        # At the very end of the event loop, write the histograms to the cache file
        self.writeHistograms(eventRange)

    # Method for writing the histograms filled during eventLoop to the cache root file
    def writeHistograms(self, eventRange):
        outfile = ROOT.TFile.Open("histoCache_%d.root"%(eventRange[0]), "RECREATE"); outfile.cd()

        # After looping over all events, write out all the histograms to the cache file
        for subdet, ietaMap in self.HBHEMap.iteritems():
            for ieta, depths in ietaMap.iteritems():
                for depth in depths:

                    if self.withDepth and depth == 0 or not self.withDepth and depth > 0: continue

                    for ts2Cut in self.ts2Cuts:

                        self.pulseShapesPU[depth][ieta][ts2Cut].Write(self.pulseShapesPU[depth][ieta][ts2Cut].GetName())

                        if self.nopuUsed: self.pulseShapesNOPU[depth][ieta][ts2Cut].Write(self.pulseShapesNOPU[depth][ieta][ts2Cut].GetName())

                        for iWeight in self.iWeights:
                            self.weightHistos[depth][ieta][iWeight][ts2Cut].Write(self.weightHistos[depth][ieta][iWeight][ts2Cut].GetName())

        for depth, ts2Dict in self.ietaDensity.iteritems():
            for ts2Cut, histo in ts2Dict.iteritems():
                histo.Write(histo.GetName())

        outfile.Close()
    
    # Method for loading in the histograms from the cache file
    def loadHistograms(self):
        
        cacheFilePath = self.cacheLoc + "/histoCache.root"
        if gFromCache and os.path.isfile(cacheFilePath):

            print "Reloading histograms from cache location \"%s\""%(cacheFilePath)
            f = ROOT.TFile.Open(cacheFilePath)

            # Make a dictionary of TTrees from the file to be split
            for key in f.GetListOfKeys():
                obj = key.ReadObj(); obj.SetDirectory(0)
                keyName = str(key.GetName()); chunks = keyName.split("_")

                if fnmatch.fnmatch(keyName, "*_w?_*"):
                    ieta = int(chunks[0].split("ieta")[1]); depth = int(chunks[1].split("depth")[1]); ts2Cut = int(chunks[-1].split("TS2gt")[1]); weight = int(chunks[-2].split("w")[1])
                    self.weightHistos.setdefault(depth, {}).setdefault(ieta, {}).setdefault(weight, {}).setdefault(ts2Cut, obj)

                elif "nTPs" in keyName:
                    depth = int(chunks[0].split("depth")[1]); ts2Cut = int(chunks[-1].split("TS2gt")[1])
                    self.ietaDensity.setdefault(depth, {}).setdefault(ts2Cut, obj)

                elif "pulsePU" in keyName:
                    ieta = int(chunks[0].split("ieta")[1]); depth = int(chunks[1].split("depth")[1]); ts2Cut = int(chunks[-1].split("TS2gt")[1])
                    self.pulseShapesPU.setdefault(depth, {}).setdefault(ieta, {}).setdefault(ts2Cut, obj)

                elif "pulseNOPU" in keyName:
                    ieta = int(chunks[0].split("ieta")[1]); depth = int(chunks[1].split("depth")[1]); ts2Cut = int(chunks[-1].split("TS2gt")[1])
                    self.pulseShapesNOPU.setdefault(depth, {}).setdefault(ieta, {}).setdefault(ts2Cut, obj)

            f.Close()

    def extractWeights(self, puPulse, nopuPulse, debug=False):

        # Don't try to extract weights with an empty pulse
        if numpy.count_nonzero(puPulse) == 0: 

            weights = numpy.zeros((2,1))
            weights[0] = -999.0; weights[1] = -999.0

            return weights

        toPrint = ""
        toPrint += "\n\n"
        toPrint += "event: " + str(self.event) + "\n"
        toPrint += "puPulse: " + str(puPulse) + "\n"
        toPrint += "nopuPulse: " + str(nopuPulse) + "\n"

        # Each row will be a 4TS window
        # = [SOI-2, SOI-1, SOI,   SOI+1
        #    SOI-1, SOI,   SOI+1, SOI+2
        #    SOI,   SOI+1, SOI+2, SOI+3
        #    SOI+1, SOI+2, SOI+3, SOI+4]
        puTSMatrix = numpy.zeros((4,4))

        # Vector of 4TS sums for 0PU
        nopuTSMatrix = numpy.zeros((4,4))

        # Fill out the samples matrix and vector of sums
        for ts in xrange(0, puPulse.size):
            for tpts in xrange(0,4):

                idx = ts+self.SOI+tpts-self.offset
                if ts > 3: break 
                if idx >= puPulse.size: break 

                puTSMatrix[ts][tpts] = puPulse[idx]
                nopuTSMatrix[ts][tpts] = nopuPulse[idx]

        soiMask = numpy.zeros((4,1))
        if self.tpSamples == 2: soiMask[2:4] = numpy.ones((2,1))
        elif self.tpSamples == 1: soiMask[2] = 1

        puSums = numpy.matmul(puTSMatrix,soiMask)
        nopuSums = numpy.matmul(nopuTSMatrix,soiMask)
        puContrib = numpy.subtract(nopuSums, puSums)

        W = numpy.array([-999.0,-999.0])
        coeffs = 0; sums = 0
        if self.tpPresamples == 1:
            coeffs = puTSMatrix[1][1]
            sums = puContrib[1]
        elif self.tpPresamples == 2:
            coeffs = puTSMatrix[0:2,0:2]
            sums = puContrib[0:2]

        # Thus, sums = coeffs x W ===> W = coeffs^-1 x sums
        if self.tpPresamples == 1:
            try: W[1] = float(sums) / float(coeffs)
            except: return W
        elif self.tpPresamples == 2:
            try: W = numpy.matmul(numpy.linalg.inv(coeffs), sums)
            except: return W

        toPrint += "weights: " + str(W) + "\n"

        #print "W: " + str(W)
        if debug and int(W[1]) == W[1]: print toPrint

        return W

    # Method for drawing average pulse for given pileup scenario
    def drawPulseShapes(self, category):

        # Avoid problems of trying to draw histos that don't exist
        if not self.nopuUsed and category == "NOPU": return

        name = "pulse" + category; histo = 0
        for subdet, ietaMap in self.HBHEMap.iteritems():
            for ieta, depths in ietaMap.iteritems():
                for depth in depths:

                    if self.withDepth and depth == 0 or not self.withDepth and depth > 0: continue

                    for ts2Cut in self.ts2Cuts:
                    
                        if ts2Cut != -1: continue 

                        if   category == "PU":   histo = self.pulseShapesPU[depth][ieta][ts2Cut]
                        elif category == "NOPU": histo = self.pulseShapesNOPU[depth][ieta][ts2Cut]
                        else: continue

                        # No need to print out empty plot (for ieta, depth that does not exist...)
                        if histo.GetEntries() == 0: continue

                        cname = "c_i%d_d%d_TS2gt%d_%s"%(ieta,depth,ts2Cut,category)
                        canvas = ROOT.TCanvas(cname, cname, 2400, 2400); canvas.cd()
                        ROOT.gPad.SetRightMargin(0.13)
                        ROOT.gPad.SetLeftMargin(0.12)

                        averagePulse = histo.ProfileX("prof_i%d_d%d_TSgt%d_%s"%(ieta,depth,ts2Cut,category),1,-1)

                        histo.SetContour(255)
                        theTitle = "|i#eta| = %d"%(ieta)
                        if depth != 0: theTitle += ", Depth = %d"%(depth)
                        histo.SetTitle(theTitle)
                        histo.GetYaxis().SetTitle("Linearized ADC")
                        histo.GetXaxis().SetTitle("BX")
                        histo.GetYaxis().SetRangeUser(0,35)

                        histo.GetYaxis().SetLabelSize(0.045); histo.GetYaxis().SetTitleSize(0.051); histo.GetYaxis().SetTitleOffset(1.05)
                        histo.GetXaxis().SetLabelSize(0.045); histo.GetXaxis().SetTitleSize(0.051); histo.GetXaxis().SetTitleOffset(0.95)
                        histo.GetZaxis().SetLabelSize(0.045); 

                        histo.Draw("COLZ")

                        averagePulse.SetLineWidth(5)
                        averagePulse.SetMarkerSize(5)
                        averagePulse.SetMarkerStyle(20)
                        averagePulse.SetMarkerColor(ROOT.kBlack)
                        averagePulse.SetLineColor(ROOT.kBlack)
                        averagePulse.Draw("EP SAME")
    
                        canvas.SetLogz()

                        outPath = "%s/PulseShapes/ieta%d/depth%d/TS2gt%d/%s"%(self.outPath,ieta,depth,ts2Cut,category)
                        if not os.path.exists(outPath): os.makedirs(outPath)
                        canvas.SaveAs(outPath + "/AveragePulse.pdf")

    # Method for drawing histogram of an extracted weight with its fit
    def drawWeightHisto(self, ieta, depth, iWeight, rebin, ts2Cut, rebinHistos, rebinFits, rebinFitWeights, rebinMeanWeights, includeFit = False):

        if ts2Cut != self.ts2Cut: return 

        weightHisto = rebinHistos[rebin]; histoFit = rebinFits[rebin]
        fitWeight    = rebinFitWeights[rebin];    meanWeight    = rebinMeanWeights[rebin]

        histoRMS = weightHisto.GetStdDev()

        canvas = ROOT.TCanvas("c_i%d_d%d_w%d_r%d_TS2gt%d"%(ieta,depth,iWeight,rebin,ts2Cut), "c_i%d_d%d_w%d_r%d_TS2gt%d"%(ieta,depth,iWeight,rebin,ts2Cut), 2600, 2400); canvas.cd()
        canvas.SetGridx()
        canvas.SetGridy()
        ROOT.gPad.SetRightMargin(0.03)
        ROOT.gPad.SetLeftMargin(0.15)
        ROOT.gPad.SetTopMargin(0.02)

        weightHisto.GetXaxis().SetRangeUser(-9,3)

        ietaStr = "|i#eta| = %d"%(ieta)
        x2 = 0.4
        if depth != 0:
            ietaStr += ", Depth = %d"%(depth)
            x2 = 0.5

        ietaText = ROOT.TPaveText(0.2, 0.89, x2, 0.95, "trNDC")
        ietaText.SetFillColor(ROOT.kWhite); ietaText.SetTextAlign(12); ietaText.SetTextFont(63); ietaText.SetTextSize(140)
        ietaText.AddText(ietaStr)

        weightHisto.SetTitle("")
        weightHisto.GetXaxis().SetTitle("w_{SOI-%d}"%(3-iWeight))
        weightHisto.GetYaxis().SetTitle("A.U.")
        weightHisto.GetYaxis().SetLabelSize(0.048); weightHisto.GetYaxis().SetTitleSize(0.054); weightHisto.GetYaxis().SetTitleOffset(1.45)
        weightHisto.GetXaxis().SetLabelSize(0.048); weightHisto.GetXaxis().SetTitleSize(0.054); weightHisto.GetXaxis().SetTitleOffset(0.9)

        weightHisto.SetLineWidth(4)
        weightHisto.SetLineColor(ROOT.kBlue+2)

        histoFit.SetLineColor(ROOT.kRed)
        histoFit.SetLineWidth(5)
        histoFit.SetLineStyle(7)

        someText = 0
        if includeFit: someText = ROOT.TPaveText(0.21, 0.62, 0.56, 0.86, "trNDC")
        else:          someText = ROOT.TPaveText(0.21, 0.62, 0.46, 0.86, "trNDC") 

        if includeFit:
            someText.AddText("Peak (Fit) = %3.2f"%(fitWeight))
            someText.AddText("#chi^{2} / ndf = %3.2f / %d"%(histoFit.GetChisquare(), histoFit.GetNDF()))
        someText.AddText("Mean = %3.2f"%(meanWeight))
        someText.AddText("RMS = %3.2f"%(histoRMS))
        someText.AddText("Entries = %d"%(weightHisto.GetEntries()))
        someText.SetTextAlign(12)
        someText.SetTextSize(0.035)
        someText.SetFillColor(ROOT.kWhite);

        weightHisto.Draw("HIST")
        if includeFit: histoFit.Draw("SAME")
        someText.Draw("SAME")
        ietaText.Draw("SAME")
    
        outPath = "%s/Fits/ieta%d/depth%d/SOI-%d/TS2gt%d"%(self.outPath,ieta,depth,3-iWeight,ts2Cut)
        if not os.path.exists(outPath): os.makedirs(outPath)
        canvas.SaveAs(outPath + "/WeightDistribution_rebin%d.pdf"%(rebin))

    # Method for getting weights from fit of weight distribution
    def extractFitWeights(self, save = False, includeFit = False):

        for subdet, ietaMap in self.HBHEMap.iteritems():
            for ieta, depths in ietaMap.iteritems():
                for depth in depths:

                    if self.withDepth and depth == 0 or not self.withDepth and depth > 0: continue

                    for ts2Cut in self.ts2Cuts:

                        if ts2Cut != self.ts2Cut: continue

                        for iWeight in self.iWeights:

                            histo = 0
                            try: histo = self.weightHistos[depth][ieta][iWeight][ts2Cut]
                            except: continue
                            if histo.Integral() == 0:
                                self.fitWeights.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, -999)
                                self.fitStatErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, -999)
                                self.fitSystErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, -999)
                                self.meanWeights.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, -999)
                                self.meanStatErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, -999)
                                self.meanSystErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, -999)
                                self.meanRMSErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, -999)

                                continue 

                            numEntries = float(histo.GetEntries())
                            histo.Scale(1./histo.Integral())

                            # Keys of these dictionaries correspond to rebinnings
                            rebinHistos     = {1 : 0, 2 : 0, 3 : 0, 4 : 0}
                            rebinFits       = {1 : 0, 2 : 0, 3 : 0, 4 : 0}
                            rebinFitWeights    = numpy.zeros((5,1)); rebinMeanWeights    = numpy.zeros((5,1))
                            rebinFitStatErrors = numpy.zeros((5,1)); rebinMeanStatErrors = numpy.zeros((5,1)) 
                            for rebin in rebinHistos.keys(): rebinHistos[rebin] = histo.Rebin(rebin, "r%d_i%d_d%d_w%d_TS2gt%d"%(rebin,ieta,depth,iWeight,ts2Cut))

                            for rebin, rHisto in rebinHistos.iteritems():

                                masterFunc = 0
                                name1 = "f1_i%d_d%d_r%d_w%d_TS2gt%d"%(ieta,depth,rebin,iWeight,ts2Cut); funcString1 = "[0]*TMath::CauchyDist(x, [1], [2])*TMath::Landau(-x, [3], [4])"; theFunc1 = 0

                                theFunc1 = ROOT.TF1(name1, funcString1, -5, 2.0)

                                theFunc1.SetParameters(0.2, -0.3, 2.5, 0.3, 2.5)
                                theFunc1.SetParNames("A", "mu", "sigma", "lmu", "lsigma")
                                theFunc1.SetParLimits(0, 0.0, 5.0)
                                theFunc1.SetParLimits(1, -5.0, 0.0)
                                theFunc1.SetParLimits(2, 0.0, 5.0)
                                theFunc1.SetParLimits(3, 0.0, 5.0)
                                theFunc1.SetParLimits(3, 0.0, 25.0)

                                name2 = "f2_i%d_d%d_r%d_w%d_TS2gt%d"%(ieta,depth,rebin,iWeight,ts2Cut); funcString2 = "[0]*TMath::Gaus(x, [1], [2])*TMath::Landau(-x, [3], [4])"; theFunc2 = 0

                                theFunc2 = ROOT.TF1(name2, funcString2, -5, 2.0)

                                theFunc2.SetParameters(0.2, -0.3, 2.5, 0.3, 2.5)
                                theFunc2.SetParNames("A", "mu", "sigma", "lmu", "lsigma")
                                theFunc2.SetParLimits(0, 0.0, 5.0)
                                theFunc2.SetParLimits(1, -5.0, 0.0)
                                theFunc2.SetParLimits(2, 0.0, 5.0)
                                theFunc2.SetParLimits(3, 0.0, 5.0)
                                theFunc2.SetParLimits(3, 0.0, 25.0)

                                rHisto.Fit(name1, "QMREWL") # https://root.cern.ch/doc/master/classTH1.html#a63eb028df86bc86c8e20c989eb23fb2a
                                rHisto.Fit(name2, "QMREWL") # https://root.cern.ch/doc/master/classTH1.html#a63eb028df86bc86c8e20c989eb23fb2a
                                
                                chi1ndf = 0; chi2ndf = 0 
                                try: chi1ndf = theFunc1.GetChisquare() / theFunc1.GetNDF()
                                except: chi1ndf = 999999
                                try: chi2ndf = theFunc2.GetChisquare() / theFunc2.GetNDF()
                                except: chi2ndf = 999998

                                #if ieta <= 20: masterFunc = theFunc1
                                #else: masterFunc = theFunc2

                                if   chi1ndf > 0 and chi1ndf < chi2ndf: masterFunc = theFunc1
                                elif chi2ndf > 0 and chi2ndf < chi1ndf: masterFunc = theFunc2
                                else: masterFunc = theFunc1

                                masterFunc.SetNpx(1000);

                                # Get weight from peak of fit function (the mode)
                                # Stat error is the "width" parameter of the fit / number of entries
                                rebinFitWeights[rebin] = masterFunc.GetMaximumX(-5.0,5.0)
                                rebinFitStatErrors[rebin] = masterFunc.GetParameter("sigma") / math.sqrt(numEntries) 
                                rebinFits[rebin] = masterFunc

                                # Get the weight from the simple mean of the distribution
                                # The stat error here is the simple stddev / number of entries
                                rebinMeanWeights[rebin] = rHisto.GetMean() 
                                rebinMeanStatErrors[rebin] = rHisto.GetStdDev() / math.sqrt(numEntries)

                            # From the five different fits of the histogram determine the standard dev of the weights 
                            theFitWeight = rebinFitWeights[self.rebin]; theFitStatError = rebinFitStatErrors[self.rebin]
                            theFitSystError = abs(numpy.amax(rebinFitWeights[1:])-numpy.amin(rebinFitWeights[1:]))
                            self.fitWeights.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, theFitWeight)
                            self.fitStatErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, theFitStatError)
                            self.fitSystErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, theFitSystError)

                            # From the five different raw histograms determine the standard dev of the means 
                            theMeanWeight = rebinMeanWeights[self.rebin]; theMeanStatError = rebinMeanStatErrors[self.rebin]
                            theMeanSystError = abs(numpy.amax(rebinMeanWeights[1:])-numpy.amin(rebinMeanWeights[1:]))
                            self.meanWeights.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, theMeanWeight)
                            self.meanStatErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, theMeanStatError)
                            self.meanSystErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, theMeanSystError)
                            self.meanRMSErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, rHisto.GetStdDev())

                            if save:
                                for rebin in xrange(1,5):
                                    self.drawWeightHisto(ieta, depth, iWeight, rebin, ts2Cut, rebinHistos, rebinFits, rebinFitWeights, rebinMeanWeights, includeFit) 

    # Method for calculating the averaged-over-depth weight for each ieta and average-over-depth for HB, HE1, HE2
    def getDepthAverageWeightsAndErrors(self, weightDict, statErrorDict, systErrorDict):

        # Intialize some temporary dictionaries
        depthAverageWeights = {}; depthAverageStatErrors = {}; depthAverageSystErrors = {}
        ietaDensityDepthSum = {}
        for subdet, ietaMap in self.HBHEMap.iteritems():
            for ieta in ietaMap.keys():
                ietaDensityDepthSum[ieta] = 0 
                for iWeight in self.iWeights:
                    depthAverageWeights.setdefault(ieta, {}).setdefault(iWeight, -999)
                    depthAverageStatErrors.setdefault(ieta, {}).setdefault(iWeight, 0.0)
                    depthAverageSystErrors.setdefault(ieta, {}).setdefault(iWeight, 0.0)

        subDetDepthAverageWeights = {"HB" : {}, "HE1" : {}, "HE2" : {}}; subDetDepthAverageStatErrors = {"HB" : {}, "HE1" : {}, "HE2" : {}}; subDetDepthAverageSystErrors = {"HB" : {}, "HE1" : {}, "HE2" : {}}
        subDetDensity = {"HB" : 0, "HE1" : 0, "HE2" : 0}
        for det, wDict in subDetDepthAverageWeights.iteritems():
            for iWeight in self.iWeights:
                subDetDepthAverageWeights[det][iWeight]    = -999 
                subDetDepthAverageStatErrors[det][iWeight] = 0.0 
                subDetDepthAverageSystErrors[det][iWeight] = 0.0 

        # Sum over the depths of each ieta to calculate the total TPs in that ieta
        for subdet, ietaMap in self.HBHEMap.iteritems():
            for ieta, depths in ietaMap.iteritems():
                for depth in depths:

                    if self.withDepth and depth == 0 or not self.withDepth and depth > 0: continue

                    ietaDensityDepthSum[ieta] += self.ietaDensity[depth][self.ts2Cut].GetBinContent(ieta)
                    subDetDensity[subdet]     += self.ietaDensity[depth][self.ts2Cut].GetBinContent(ieta) 

        # Now compute summed-over-depth average weight for each ieta
        for subdet, ietaMap in self.HBHEMap.iteritems():
            for ieta, depths in ietaMap.iteritems():
                for depth in depths:

                    if self.withDepth and depth == 0 or not self.withDepth and depth > 0: continue

                    depthTPs = self.ietaDensity[depth][self.ts2Cut].GetBinContent(ieta)

                    # Empty ietaDensity means we aren't looking at this depth...
                    if depthTPs == 0: continue

                    for iWeight in self.iWeights:

                        # Not very clean way of getting weight from extra dictionary or not
                        weight    = weightDict[depth][ieta][iWeight][self.ts2Cut]
                        statError = statErrorDict[depth][ieta][iWeight][self.ts2Cut]
                        systError = systErrorDict[depth][ieta][iWeight][self.ts2Cut]

                        if weight == -999: continue
                        
                        if depthAverageWeights[ieta][iWeight]        == -999: depthAverageWeights[ieta][iWeight] += 999
                        if subDetDepthAverageWeights[subdet][iWeight]  == -999: subDetDepthAverageWeights[subdet][iWeight] += 999

                        depthAverageWeights[ieta][iWeight] += weight * depthTPs / float(ietaDensityDepthSum[ieta])
                        subDetDepthAverageWeights[subdet][iWeight]  += weight * depthTPs / float(subDetDensity[subdet])

                        depthAverageStatErrors[ieta][iWeight] += statError * depthTPs / float(ietaDensityDepthSum[ieta])
                        subDetDepthAverageStatErrors[subdet][iWeight]  += statError * depthTPs / float(subDetDensity[subdet])

                        depthAverageSystErrors[ieta][iWeight] += systError * depthTPs / float(ietaDensityDepthSum[ieta])
                        subDetDepthAverageSystErrors[subdet][iWeight]  += systError * depthTPs / float(subDetDensity[subdet])

        return depthAverageWeights, subDetDepthAverageWeights, depthAverageStatErrors, depthAverageSystErrors, subDetDepthAverageStatErrors, subDetDepthAverageSystErrors

    # Method for writing out a text file summarizing all the extracted weights
    def getWeightSummary(self, version):

        summary = open("%s/weightSummary%s.txt"%(self.outPath,version), "w")

        # Initialize variables to hold maps to versions of weights and errors
        weights = 0;    depthAverageWeights = 0;    subdetDepthAverageWeights = 0
        statErrors = 0; depthAverageStatErrors = 0; subdetDepthAverageStatErrors = 0
        systErrors = 0; depthAverageSystErrors = 0; subdetDepthAverageSystErrors = 0
        rmsErrors  = 0;

        if   version == "Fit":  weights = self.fitWeights;  statErrors = self.fitStatErrors;  systErrors = self.fitSystErrors
        elif version == "Mean": weights = self.meanWeights; statErrors = self.meanStatErrors; systErrors = self.meanSystErrors
        else: return

        rmsErrors = self.meanRMSErrors

        depthAverageWeights, subdetDepthAverageWeights, depthAverageStatErrors, \
        depthAverageSystErrors, subdetDepthAverageStatErrors, subdetDepthAverageSystErrors \
        = self.getDepthAverageWeightsAndErrors(weights, statErrors, systErrors)

        for iWeight in self.iWeights:
            str2Write = "\nwSOI-%d:\n"%(3-iWeight)

            for subdet, ietaMap in self.HBHEMap.iteritems():

                if self.withDepth:
                    for ieta, depths in ietaMap.iteritems():

                        ietaStr = "%d"%(ieta)
                        str2Write += "ieta%s, depthAve, "%(ietaStr)
                        
                        if depthAverageWeights[ieta][iWeight] == -999: continue
                        else:
                            statError = depthAverageStatErrors[ieta][iWeight]
                            systError = depthAverageSystErrors[ieta][iWeight]
                            weightStr = "%3.2f"%(depthAverageWeights[ieta][iWeight]); weightStr = weightStr.rjust(5)
                            str2Write += "weight%s, stat%3.2f, syst%3.2f\n"%(weightStr,statError,systError)

                for ieta, depths in ietaMap.iteritems():

                    for depth in depths:

                        if self.withDepth and depth == 0 or not self.withDepth and depth > 0: continue

                        if weights[depth][ieta][iWeight][self.ts2Cut] == -999: continue
                        else: 
                            ietaStr = "%d"%(ieta)
                            str2Write += "ieta%s, "%(ietaStr)

                            weightStr = "%3.2f"%(weights[depth][ieta][iWeight][self.ts2Cut]); weightStr = weightStr.rjust(5)
                            statError = statErrors[depth][ieta][iWeight][self.ts2Cut]
                            systError = systErrors[depth][ieta][iWeight][self.ts2Cut]
                            rmsError  = rmsErrors[depth][ieta][iWeight][self.ts2Cut]
                            str2Write += "depth%d, weight%s, stat%3.2f, syst%3.2f, rms%3.2f\n"%(depth,weightStr,statError,systError,rmsError)

                    # When we have just printed a line about the last ieta in one of the subdets (HB, HE1, HE2)
                    # Print out the subdet average line for the respective subdet
                    if ieta == 16 or ieta == 20 or ieta == 28:

                        detStr = "ieta%s"%(subdet)
                        detStr = detStr.rjust(3)

                        str2Write += "%s, "%(detStr)

                        if self.withDepth: str2Write += "depthAve, "
                        else:              str2Write += "depth0, "

                        if subdetDepthAverageWeights[subdet][iWeight] == -999: continue
                        else:
                            statError = subdetDepthAverageStatErrors[subdet][iWeight]
                            systError = subdetDepthAverageSystErrors[subdet][iWeight]
                            weightStr = "%3.2f"%(subdetDepthAverageWeights[subdet][iWeight]); weightStr = weightStr.rjust(5)
                            str2Write += "weight%s, stat%3.2f, syst%3.2f\n"%(weightStr,statError,systError)

            summary.write(str2Write)                   
        summary.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--tag"       , dest="tag"       , help="Unique tag for output"    , type=str     , default="TAG")
    parser.add_argument("--fromCache" , dest="fromCache" , help="Read from cache file"     , default=False, action="store_true")
    parser.add_argument("--data"      , dest="data"      , help="Deriving weights for data", default=False, action="store_true")
    parser.add_argument("--pu"        , dest="pu"        , help="Path to PU file"          , type=str     , default="NULL")
    parser.add_argument("--nopu"      , dest="nopu"      , help="Path to NOPU file"        , type=str     , default="NULL")
    parser.add_argument("--depth"     , dest="depth"     , help="Extract per-depth"        , default=False, action="store_true")
    parser.add_argument("--scheme"    , dest="scheme"    , help="Which pulse filter scheme", type=str     , default="ALGO")
    parser.add_argument("--evtRange"  , dest="evtRange"  , help="Start and number"         , type=int     , nargs="+", default=[-1,1])
    args = parser.parse_args()

    # Intend for things to work inside sandbox environment
    HOME = os.getenv("HOME")
    USER = os.getenv("USER")

    # If for some reason the USER is not defined default to author's
    if USER == None: USER = "jhiltb"

    SANDBOX = HOME + "/nobackup/HCAL_Trigger_Study"
    INPUTLOC = "root://cmseos.fnal.gov//store/user/%s/HCAL_Trigger_Study/WeightExtraction"%(USER)

    outPath = "%s/plots/Weights/%s/%s"%(SANDBOX,args.scheme,args.tag)
    gFromCache = args.fromCache

    # The fromCache option is the main flag to decide if we are looping over events and extracting raw weights
    # or if we are reading back the raw histograms and producing the final results of the weights extraction
    if not gFromCache:

        eventRange = xrange(args.evtRange[0], args.evtRange[0]+args.evtRange[1]) 

        if args.data: eventRange = xrange(-2, 2)

        # Construct the anticipated file path format
        PUFile = args.pu 

        # If running on NuGun samples there is not a NOPU.root
        noPUFile = args.nopu

        # Finally, make an extractor and begin the event loop
        theExtractor = WeightExtractor(args.scheme, args.data, PUFile, noPUFile, outPath, args.depth)
        theExtractor.eventLoop(eventRange)

    else:
        theExtractor = WeightExtractor(args.scheme, "NULL", "NULL", outPath, args.depth)

        theExtractor.loadHistograms()
        theExtractor.extractFitWeights(save=True, includeFit=False)
        theExtractor.getWeightSummary("Mean")
        theExtractor.getWeightSummary("Fit")

        #theExtractor.drawPulseShapes("PU")
        #if args.nopu != "": theExtractor.drawPulseShapes("NOPU")
