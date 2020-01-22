#!/usr/bin/env python

import sys, os, ROOT, numpy, argparse, math
from pu2nopuMap import PU2NOPUMAP 
from collections import defaultdict

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat("")
ROOT.gStyle.SetFrameLineWidth(4)
ROOT.gStyle.SetPaintTextFormat("3.2f")
ROOT.gStyle.SetErrorX(0)
ROOT.gErrorIgnoreLevel = ROOT.kWarning
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

class WeightExtractor:

    def __init__(self, scheme, inputFilePU, outputPath):

        self.outPath = outputPath              # Base outpath to write everything to
        self.cacheLoc = "%s/root"%(outputPath) # Location to cache histograms in root file

        # _My_ use of word "sample" is any TS >= SOI
        if scheme == "PFA2pp":
            self.tpPresamples = 2          # PFA2pp uses two presamples
            self.tpSamples = 2             # SOI and SOI+1 are used to sample non-PU pulse
        elif scheme == "PFA2p":
            self.tpPresamples = 1          # PFA2p uses two SOI and SOI+1 fully and SOI-1 presample
            self.tpSamples = 2             # SOI and SOI+1 are used to sample non-PU pulse
        elif scheme == "PFA1p":
            self.tpPresamples = 1          # PFA1 uses SOI fully and SOI-1 presample to subtract
            self.tpSamples = 1             # Only SOI is used to sample non-PU pulse
        elif scheme == "PFA1pp":
            self.tpPresamples = 2          # PFA1p uses SOI fully and SOI-2 and SOI-1 presamples to subtract
            self.tpSamples = 1             # Only SOI is used to sample non-PU pulse

        self.SOI      = 3                  # SOI for 8TS digi is always 3
        self.offset   = 3                  # We need this offset to scan 8TS digi starting from 0
        self.event    = -1                 # Current event we are looking at
        self.scheme   = scheme             # Which pulse filter scheme 
        self.ts2Cut   = -1                  # Requirement on TS2 (SOI-1) > n ADC
        self.rebin    = 2                  # Rebin factor for weight histograms
        self.ts2Cuts  = list(xrange(-1,5)) # List of selections on SOI-1 to make
        self.depths   = list(xrange(0,7))  # List of all possible depths (not all for any given ieta!)
        self.iWeights = list(xrange(1,3))  # List of i weights 

        self.HBHEieta = list(xrange(1,29))
        self.HBieta   = list(xrange(1,17))
        self.HE1ieta  = list(xrange(17,21))
        self.HE2ieta  = list(xrange(21,29))

        self.weightHistos = {}             # Map ieta,depth,iWeight to 1D histo of said weight 
        self.averagePulseWeights = {}      # Map of depth,ieta,iWeight to weight from average pulses 
        self.corrHistos = {}               # Map of depth,ieta to w1 vs w2
        self.fitWeights = {}               # Maps depth,ieta,iWeight to a weight extracted from fit of distribution
        self.fitStatErrors = {}            # Maps depth,ieta,iWeight to a statistical error on the fit weight 
        self.fitSystErrors = {}            # Maps depth,ieta,iWeight to a systematic error on the fit weight 
        self.meanWeights = {}              # Maps depth,ieta,iWeight to a weight extracted from mean of distribution
        self.meanStatErrors = {}           # Maps depth,ieta,iWeight to a statistical error on the mean weight 
        self.meanSystErrors = {}           # Maps depth,ieta,iWeight to a systematic error on the mean weight 
        self.averagePulseStatErrors = {}   # Maps depth,ieta,TS2 Cut,iWeight to a stat error for the average pulse-derived weight
        self.averagePulseSystErrors = {}   # Maps depth,ieta,iWeight to a syst error for the average pulse-derived weight
        self.statErrors = {}               # Maps depth,ieta,iWeight to a statistical error on the weight 
        self.systErrors = {}               # Maps depth,ieta,iWeight to a systematic error on the weight 
        self.pulseShapesPU = {}            # Average pulse shapes for PU mapped by ieta,depth
        self.ietaDensity = {}              # Number of matched pulses mapped by ieta,depth

        # Initialize map of histos if not loading from cache file
        if not gFromCache:
            self.tfilepu = ROOT.TFile.Open(inputFilePU, "r")
            self.ttreepu = self.tfilepu.Get("compareReemulRecoSeverity9/events")

            for depth in self.depths:
                for ts2Cut in self.ts2Cuts:
                    self.ietaDensity.setdefault(depth, {}).setdefault(ts2Cut, ROOT.TH1F("depth%d_nTPs_TS2gt%d"%(depth,ts2Cut), "depth%d_nTPs_TS2gt%d"%(depth,ts2Cut), 28, 0.5, 28.5))

                for ieta in self.HBHEieta:
                    iname = "ieta%d_depth%d"%(ieta,depth)
                    for ts2Cut in self.ts2Cuts:
                        tname = iname+"_wcorr_TS2gt%d"%(ts2Cut)
                        self.corrHistos.setdefault(depth, {}).setdefault(ieta, {}).setdefault(ts2Cut, ROOT.TH2F(tname, tname, 360, -50.0, 50.0, 360, -50.0, 50.0))

                    for weight in self.iWeights:
                        wname = iname+"_w%d"%(weight)
                        for ts2Cut in self.ts2Cuts:
                            tname = wname+"_TS2gt%d"%(ts2Cut)
                            self.weightHistos.setdefault(depth, {}).setdefault(ieta, {}).setdefault(weight, {}).setdefault(ts2Cut, ROOT.TH1F(tname, tname, 720, -50.0, 50.0))

                    for ts2Cut in self.ts2Cuts:
                        tname1 = iname+"_pulsePU_TS2gt%d"%(ts2Cut)
                        self.pulseShapesPU.setdefault(depth, {}).setdefault(ieta, {}).setdefault(ts2Cut, ROOT.TH2F(tname1, tname1, 8, -3.5, 4.5, 2049, -0.5, 2048.5))

    def eventLoop(self, eventRange): 

        if eventRange[0] == -1 or len(eventRange) == 2: return

        self.ttreepu.SetBranchStatus("*", 0);    
        self.ttreepu.SetBranchStatus("ieta", 1); 
        self.ttreepu.SetBranchStatus("iphi", 1); 
        self.ttreepu.SetBranchStatus("event", 1);
        self.ttreepu.SetBranchStatus("depth", 1);

        for iTS in xrange(0,8):
            self.ttreepu.SetBranchStatus("ts%d"%(iTS), 1)

        print "Constructing per-ieta, per-event 8TS pulses"
        for iEvent in eventRange:

            self.ttreepu.GetEntry(iEvent)

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

                # Always kill all-0 8TS
                if self.ttreepu.ts0[iTP] + self.ttreepu.ts1[iTP] + self.ttreepu.ts2[iTP]\
                 + self.ttreepu.ts3[iTP] + self.ttreepu.ts4[iTP] + self.ttreepu.ts5[iTP]\
                 + self.ttreepu.ts6[iTP] + self.ttreepu.ts7[iTP] < 1: continue

                print "category   PU | event %s | ieta %d | iphi %d | depth %d | 8TS [%d, %d, %d, %d, %d, %d, %d, %d]"%(self.ttreepu.event, ieta, iphi, idepth, self.ttreepu.ts0[iTP], self.ttreepu.ts1[iTP],self.ttreepu.ts2[iTP],self.ttreepu.ts3[iTP],self.ttreepu.ts4[iTP],self.ttreepu.ts5[iTP],self.ttreepu.ts6[iTP],self.ttreepu.ts7[iTP])

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

                        for ts in xrange(0, weights.size): self.weightHistos[idepth][abs(ieta)][ts+1][ts2Cut].Fill(weights[ts])
                        self.corrHistos[idepth][abs(ieta)][ts2Cut].Fill(weights[0], weights[1])

            print "Processed event %d => %d..."%(iEvent,eventRange[-1])
        
        # At the very end of the event loop, write the histograms to the cache file
        self.writeHistograms(eventRange)

    # Method for writing the histograms filled during eventLoop to the cache root file
    def writeHistograms(self, eventRange):
        outfile = ROOT.TFile.Open("histoCache_%d.root"%(eventRange[0]), "RECREATE"); outfile.cd()

        # After looping over all events, write out all the histograms to the cache file
        for depth in xrange(0,7):
            for ieta in self.HBHEieta:
                for ts2Cut in self.ts2Cuts:
                    self.pulseShapesPU[depth][ieta][ts2Cut].Write(self.pulseShapesPU[depth][ieta][ts2Cut].GetName())
                    self.corrHistos[depth][ieta][ts2Cut].Write(self.corrHistos[depth][ieta][ts2Cut].GetName())

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

                if "wcorr" in keyName:
                    ieta = int(chunks[0].split("ieta")[1]); depth = int(chunks[1].split("depth")[1]); ts2Cut = int(chunks[-1].split("TS2gt")[1])
                    self.corrHistos.setdefault(depth, {}).setdefault(ieta, {}).setdefault(ts2Cut, obj)

                elif "w" in keyName:
                    ieta = int(chunks[0].split("ieta")[1]); depth = int(chunks[1].split("depth")[1]); ts2Cut = int(chunks[-1].split("TS2gt")[1]); weight = int(chunks[-2].split("w")[1])
                    self.weightHistos.setdefault(depth, {}).setdefault(ieta, {}).setdefault(weight, {}).setdefault(ts2Cut, obj)

                elif "nTPs" in keyName:
                    depth = int(chunks[0].split("depth")[1]); ts2Cut = int(chunks[-1].split("TS2gt")[1])
                    self.ietaDensity.setdefault(depth, {}).setdefault(ts2Cut, obj)

                elif "pulsePU" in keyName:
                    ieta = int(chunks[0].split("ieta")[1]); depth = int(chunks[1].split("depth")[1]); ts2Cut = int(chunks[-1].split("TS2gt")[1])
                    self.pulseShapesPU.setdefault(depth, {}).setdefault(ieta, {}).setdefault(ts2Cut, obj)

            f.Close()

    def extractWeights(self, puPulse, nopuPulse):

        # Don't try to extract weights with an empty pulse
        if numpy.count_nonzero(puPulse) == 0: 

            weights = numpy.zeros((2,1))
            weights[0] = -999.0; weights[1] = -999.0

            return weights

        ifPrint = (1 == 1)

        toPrint = ""
        if ifPrint:
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
        if   self.tpSamples == 2: soiMask[2:4] = numpy.ones((2,1))
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

        if ifPrint: toPrint += "weights: " + str(W) + "\n"

        #print "W: " + str(W)
        if ifPrint: print toPrint

        return W

    # Method for drawing average pulse for given pileup scenario
    def drawPulseShapes(self, category):

        name = "pulse" + category; histo = 0
        for depth in self.depths:
            for ieta in self.HBHEieta:
                for ts2Cut in self.ts2Cuts:

                    if ts2Cut != -1: continue
                
                    if   category == "PU":   histo = self.pulseShapesPU[depth][ieta][ts2Cut]
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
                    averagePulse.SetMarkerSize(4)
                    averagePulse.SetMarkerStyle(20)
                    averagePulse.SetMarkerColor(ROOT.kBlack)
                    averagePulse.SetLineColor(ROOT.kBlack)
                    averagePulse.Draw("SAME")
    
                    canvas.SetLogz()

                    outPath = "%s/PulseShapes/ieta%d/depth%d/TS2gt%d/%s"%(self.outPath,ieta,depth,ts2Cut,category)
                    if not os.path.exists(outPath): os.makedirs(outPath)
                    canvas.SaveAs(outPath + "/AveragePulse.pdf")

    # Method for drawing histogram of correlation between wSOI-1 and wSOI-2
    def drawWeightCorrs(self):

        for depth in self.depths:
            for ieta in self.HBHEieta:

                histo = self.corrHistos[depth][ieta][self.ts2Cut]

                # No need to print out empty plot (for ieta, depth that don't exist...)
                if histo.Integral() == 0: continue

                cname = "c_i%d_d%d_wcorr"%(ieta,depth)
                canvas = ROOT.TCanvas(cname, cname, 2400, 2400); canvas.cd()
                ROOT.gPad.SetLeftMargin(0.12)
                ROOT.gPad.SetRightMargin(0.13)

                histo.SetContour(255)
                histo.RebinX(3); histo.RebinY(3)
                theTitle = "|i#eta| = %d"%(ieta)
                if depth != 0: theTitle += ", Depth = %d"%(depth)
                histo.SetTitle(theTitle)
                histo.GetYaxis().SetTitle("w_{SOI-1}")
                histo.GetYaxis().SetRangeUser(-20,20)
                histo.GetXaxis().SetTitle("w_{SOI-2}")
                histo.GetXaxis().SetRangeUser(-20,20)

                histo.GetYaxis().SetLabelSize(0.039); histo.GetYaxis().SetTitleSize(0.051); histo.GetYaxis().SetTitleOffset(1.18)
                histo.GetXaxis().SetTitleSize(0.051); histo.GetXaxis().SetTitleOffset(0.9)
                histo.GetXaxis().SetLabelSize(0.039)
                histo.Draw("COLZ")

                canvas.SetLogz(); canvas.SetGridx(); canvas.SetGridy()

                outPath = "%s/Fits/ieta%d/depth%d"%(self.outPath,ieta,depth)
                if not os.path.exists(outPath): os.makedirs(outPath)
                canvas.SaveAs(outPath + "/WeightCorrelation.pdf")

    # Method for drawing histogram of an extracted weight with its fit
    def drawWeightHisto(self, ieta, depth, iWeight, rebin, ts2Cut, rebinHistos, rebinFits, rebinFitWeights, rebinFitStatErrors, theFitSystError, rebinMeanWeights, rebinMeanStatErrors, theMeanSystError):

        weightHisto = rebinHistos[rebin]; histoFit = rebinFits[rebin]

        fitWeight    = rebinFitWeights[rebin];    meanWeight    = rebinMeanWeights[rebin]
        fitStatError = rebinFitStatErrors[rebin]; meanStatError = rebinMeanStatErrors[rebin]
        fitSystError = theFitSystError;           meanSystError = theMeanSystError

        canvas = ROOT.TCanvas("c_i%d_d%d_w%d_r%d_TS2gt%d"%(ieta,depth,iWeight,rebin,ts2Cut), "c_i%d_d%d_w%d_r%d_TS2gt%d"%(ieta,depth,iWeight,rebin,ts2Cut), 2400, 2400); canvas.cd()
        canvas.SetGridx()
        canvas.SetGridy()
        ROOT.gPad.SetRightMargin(0.03)
        ROOT.gPad.SetLeftMargin(0.15)

        weightHisto.GetXaxis().SetRangeUser(-9,3)
        theTitle = "|i#eta| = %d"%(ieta)
        if depth != 0: theTitle += ", Depth = %d"%(depth)
        weightHisto.SetTitle(theTitle)
        weightHisto.GetXaxis().SetTitle("w_{SOI-%d}"%(3-iWeight))
        weightHisto.GetYaxis().SetTitle("A.U.")
        weightHisto.GetYaxis().SetLabelSize(0.048); weightHisto.GetYaxis().SetTitleSize(0.054); weightHisto.GetYaxis().SetTitleOffset(1.45)
        weightHisto.GetXaxis().SetLabelSize(0.048); weightHisto.GetXaxis().SetTitleSize(0.054); weightHisto.GetXaxis().SetTitleOffset(0.9)

        weightHisto.SetLineWidth(3)
        weightHisto.SetLineColor(ROOT.kBlack)

        histoFit.SetLineColor(ROOT.kRed)
        histoFit.SetLineWidth(5)
        histoFit.SetLineStyle(7)

        someText = ROOT.TPaveText(0.21, 0.62, 0.56, 0.86, "trNDC")

        someText.AddText("Peak = %3.2f_{ #pm %3.2f (stat.)}^{ #pm %3.2f (syst.)}"%(fitWeight,fitStatError,fitSystError))
        someText.AddText("Mean = %3.2f_{ #pm %3.2f (stat.)}^{ #pm %3.2f (syst.)}"%(meanWeight,meanStatError,meanSystError))
        someText.AddText("#chi^{2} / DOF = %3.2f / %d"%(histoFit.GetChisquare(), histoFit.GetNDF()))
        someText.AddText("Entries = %d"%(weightHisto.GetEntries()))
        someText.SetTextAlign(31)
        someText.SetTextSize(0.035)
        someText.SetFillColor(ROOT.kWhite);

        weightHisto.Draw("HIST")
        histoFit.Draw("SAME")
        someText.Draw("SAME")
    
        if rebin <= 4 and ts2Cut == self.ts2Cut:
            outPath = "%s/Fits/ieta%d/depth%d/SOI-%d/TS2gt%d"%(self.outPath,ieta,depth,3-iWeight,ts2Cut)
            if not os.path.exists(outPath): os.makedirs(outPath)
            canvas.SaveAs(outPath + "/WeightDistribution_rebin%d.pdf"%(rebin))

    # Method for getting weights from fit of weight distribution
    def extractFitWeights(self, save=False):

        for iWeight in self.iWeights:
            for depth in self.depths:
                for ieta in self.HBHEieta:
                    for ts2Cut in self.ts2Cuts:

                        if ts2Cut != self.ts2Cut: continue

                        histo = self.weightHistos[depth][ieta][iWeight][ts2Cut]
                        if histo.Integral() == 0:
                            self.fitWeights.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, -999)
                            self.fitStatErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, -999)
                            self.fitSystErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, -999)
                            self.meanWeights.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, -999)
                            self.meanStatErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, -999)
                            self.meanSystErrors.setdefault(depth, {}).setdefault(ieta, {}).setdefault(iWeight, {}).setdefault(ts2Cut, -999)

                            continue 

                        numEntries = float(histo.GetEntries())
                        histo.Scale(1./histo.Integral())

                        # Keys of these dictionaries correspond to rebinnings
                        rebinHistos     = {1 : 0, 2 : 0, 3 : 0, 4 : 0}
                        rebinFits       = {1 : 0, 2 : 0, 3 : 0, 4 : 0}
                        rebinWeights    = numpy.zeros((5,1))
                        rebinStatErrors = numpy.zeros((5,1)) 
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

                        if save:
                            for rebin in xrange(1,5):
                                self.drawWeightHisto(ieta, depth, iWeight, rebin, ts2Cut, rebinHistos, rebinFits, rebinFitWeights, rebinFitStatErrors, theFitSystError, rebinMeanWeights, rebinMeanStatErrors, theMeanSystError) 

    # Method for calculating the averaged-over-depth weight for each ieta and average-over-depth for HB, HE1, HE2
    def getDepthAverageWeightsAndErrors(self, weightDict, statErrorDict, systErrorDict):

        # Intialize some temporary dictionaries
        depthAverageWeights = {}; depthAverageStatErrors = {}; depthAverageSystErrors = {}
        ietaDensityDepthSum = {}
        for ieta in self.HBHEieta:
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
        for depth in self.depths:
            for ieta in self.HBHEieta:

                ietaDensityDepthSum[ieta] += self.ietaDensity[depth][self.ts2Cut].GetBinContent(ieta)
                if   ieta in self.HBieta:  subDetDensity["HB"]  += self.ietaDensity[depth][self.ts2Cut].GetBinContent(ieta) 
                elif ieta in self.HE1ieta: subDetDensity["HE1"] += self.ietaDensity[depth][self.ts2Cut].GetBinContent(ieta) 
                elif ieta in self.HE2ieta: subDetDensity["HE2"] += self.ietaDensity[depth][self.ts2Cut].GetBinContent(ieta) 

        # Now compute summed-over-depth average weight for each ieta
        for depth in self.depths:
            for ieta in self.HBHEieta:
                depthTPs = self.ietaDensity[depth][self.ts2Cut].GetBinContent(ieta)

                # Empty ietaDensity means we aren't looking at this depth...
                if depthTPs == 0: continue

                for iWeight in weightDict[depth][ieta].keys():

                    # Not very clean way of getting weight from extra dictionary or not
                    weight    = weightDict[depth][ieta][iWeight][self.ts2Cut]
                    statError = statErrorDict[depth][ieta][iWeight][self.ts2Cut]
                    systError = systErrorDict[depth][ieta][iWeight][self.ts2Cut]

                    if weight == -999: continue
                    
                    if depthAverageWeights[ieta][iWeight]        == -999: depthAverageWeights[ieta][iWeight] += 999
                    if subDetDepthAverageWeights["HB"][iWeight]  == -999: subDetDepthAverageWeights["HB"][iWeight] += 999
                    if subDetDepthAverageWeights["HE1"][iWeight] == -999: subDetDepthAverageWeights["HE1"][iWeight] += 999
                    if subDetDepthAverageWeights["HE2"][iWeight] == -999: subDetDepthAverageWeights["HE2"][iWeight] += 999

                    depthAverageWeights[ieta][iWeight] += weight * depthTPs / float(ietaDensityDepthSum[ieta])
                    if   ieta in self.HBieta:  subDetDepthAverageWeights["HB"][iWeight]  += weight * depthTPs / float(subDetDensity["HB"])
                    elif ieta in self.HE1ieta: subDetDepthAverageWeights["HE1"][iWeight] += weight * depthTPs / float(subDetDensity["HE1"]) 
                    elif ieta in self.HE2ieta: subDetDepthAverageWeights["HE2"][iWeight] += weight * depthTPs / float(subDetDensity["HE2"]) 

                    depthAverageStatErrors[ieta][iWeight] += statError * depthTPs / float(ietaDensityDepthSum[ieta])
                    if   ieta in self.HBieta:  subDetDepthAverageStatErrors["HB"][iWeight]  += statError * depthTPs / float(subDetDensity["HB"])
                    elif ieta in self.HE1ieta: subDetDepthAverageStatErrors["HE1"][iWeight] += statError * depthTPs / float(subDetDensity["HE1"]) 
                    elif ieta in self.HE2ieta: subDetDepthAverageStatErrors["HE2"][iWeight] += statError * depthTPs / float(subDetDensity["HE2"]) 

                    depthAverageSystErrors[ieta][iWeight] += systError * depthTPs / float(ietaDensityDepthSum[ieta])
                    if   ieta in self.HBieta:  subDetDepthAverageSystErrors["HB"][iWeight]  += systError * depthTPs / float(subDetDensity["HB"])
                    elif ieta in self.HE1ieta: subDetDepthAverageSystErrors["HE1"][iWeight] += systError * depthTPs / float(subDetDensity["HE1"]) 
                    elif ieta in self.HE2ieta: subDetDepthAverageSystErrors["HE2"][iWeight] += systError * depthTPs / float(subDetDensity["HE2"]) 

        return depthAverageWeights, subDetDepthAverageWeights, depthAverageStatErrors, depthAverageSystErrors, subDetDepthAverageStatErrors, subDetDepthAverageSystErrors

    # Method for writing out a text file summarizing all the extracted weights
    def getWeightSummary(self, version):

        summary = open("%s/weightSummary%s.txt"%(self.outPath,version), "w")

        weights = 0; statErrors = 0; systErrors = 0
        depthAverageWeights = 0; subdetDepthAverageWeights = 0; depthAverageStatErrors = 0
        depthAverageSystErrors = 0; subdetDepthAverageStatErrors = 0; subdetDepthAverageSystErrors = 0

        if   version == "Fit":  weights = self.fitWeights;  statErrors = self.fitStatErrors;  systErrors = self.fitSystErrors
        elif version == "Mean": weights = self.meanWeights; statErrors = self.meanStatErrors; systErrors = self.meanSystErrors
        else: return

        depthAverageWeights, subdetDepthAverageWeights, depthAverageStatErrors, \
        depthAverageSystErrors, subdetDepthAverageStatErrors, subdetDepthAverageSystErrors \
        = self.getDepthAverageWeightsAndErrors(weights, statErrors, systErrors)

        emptyStr = "              -               & "; emptyStrEnd = "              -               \\\\ "
        for iWeight in self.iWeights:
            str2Write = "\nwSOI-%d:\n"%(3-iWeight)

            for ieta in self.HBHEieta:
                ietaStr = "%d"%(ieta)
                ietaStr = ietaStr.rjust(3)

                str2Write += "%s & "%(ietaStr)
                
                if depthAverageWeights[ieta][iWeight] == -999:
                    str2Write += emptyStr
                else:
                    statError = depthAverageStatErrors[ieta][iWeight]
                    systError = depthAverageSystErrors[ieta][iWeight]
                    weightStr = "%3.2f"%(depthAverageWeights[ieta][iWeight]); weightStr = weightStr.rjust(5)
                    str2Write += "$%s_{\pm %3.2f}^{\pm %3.2f}$ & "%(weightStr,statError,systError)

                endStr = "& "
                for depth in self.depths:
                    if depth == self.depths[-1]: endStr = "\\\\"
                    
                    if weights[depth][ieta][iWeight][self.ts2Cut] == -999: 
                        if depth == self.depths[-1]: str2Write += emptyStrEnd
                        else: str2Write += emptyStr 
                    else: 
                        weightStr = "%3.2f"%(weights[depth][ieta][iWeight][self.ts2Cut]); weightStr = weightStr.rjust(5)
                        statError = statErrors[depth][ieta][iWeight][self.ts2Cut]
                        systError = systErrors[depth][ieta][iWeight][self.ts2Cut]
                        str2Write += "$%s_{\pm %3.2f}^{\pm %3.2f}$ %s"%(weightStr,statError,systError,endStr)
                str2Write += "\n"

                if ieta == 16 or ieta == 20 or ieta == 28:

                    det = ""
                    if   ieta == 16: det = "HB"
                    elif ieta == 20: det = "HE1"
                    elif ieta == 28: det = "HE2"

                    detStr = "%s"%(det)
                    detStr = detStr.rjust(3)

                    str2Write += "%s & "%(detStr)

                    if subdetDepthAverageWeights[det][iWeight] == -999:
                        str2Write += emptyStr + emptyStr + emptyStr + emptyStr + emptyStr + emptyStr + emptyStr + emptyStrEnd
                    else:
                        statError = subdetDepthAverageStatErrors[det][iWeight]
                        systError = subdetDepthAverageSystErrors[det][iWeight]
                        weightStr = "%3.2f"%(subdetDepthAverageWeights[det][iWeight]); weightStr = weightStr.rjust(5)
                        str2Write += "$%s_{\pm %3.2f}^{\pm %3.2f}$ & "%(weightStr,statError,systError)
                        str2Write += emptyStr + emptyStr + emptyStr + emptyStr + emptyStr + emptyStr + emptyStrEnd

                    str2Write += "\n"

            summary.write(str2Write)                   
        summary.close()

        # Now write the python-friendly version for importing into CMSSW
        summary = open("%s/weightSummaryPython%s.txt"%(self.outPath,version), "w")

        depthStr = ""
        if "WithDepth" in self.outPath: depthStr = "_DEPTH_AVE"

        versionStr = ""
        if version == "Mean": versionStr = "_MEAN"

        firstTag = True
        str2Write = ""
        for tag in ["", "_UP", "_DOWN"]:
            if not firstTag: str2Write += ",\n\n"
            str2Write += "\"%s%s_PER_IETA%s%s\" : cms.untracked.PSet(**dict([\n"%(self.scheme,depthStr,versionStr,tag)
            firstIeta = True
            for ieta in self.HBHEieta:
                ietaStr = "    (\"%d\","%(ieta)
                ietaStr = ietaStr.ljust(11)
                
                if not firstIeta: str2Write += ",\n"
                str2Write += "%s cms.untracked.vdouble("%(ietaStr)
                firstWeight = True
                for iWeight in self.iWeights:
                    if not firstWeight: str2Write += ", " 

                    if depthAverageWeights[ieta][iWeight] == -999:
                        continue
                    else:
                        statError = depthAverageStatErrors[ieta][iWeight]
                        systError = depthAverageSystErrors[ieta][iWeight]
                        weightStr = "%3.2f"%(depthAverageWeights[ieta][iWeight]); weightStr = weightStr.rjust(5)

                        if   "UP"   in tag: str2Write += "%s + (%3.2f**2 + %3.2f**2)**0.5"%(weightStr,statError,systError)
                        elif "DOWN" in tag: str2Write += "%s - (%3.2f**2 + %3.2f**2)**0.5"%(weightStr,statError,systError)
                        else:               str2Write += "%s"%(weightStr)

                    firstWeight = False
                
                firstIeta = False
                str2Write += "))"

            str2Write += "\n]))"
            firstTag = False

        str2Write += "\n"
        firstTag = True
        for tag in ["", "_UP", "_DOWN"]:
            if not firstTag: str2Write += ",\n\n"
            str2Write += "\"%s%s_AVE%s%s\" : cms.untracked.PSet(**dict([\n"%(self.scheme,depthStr,versionStr,tag)
            firstIeta = True
            for ieta in self.HBHEieta:
                det = "" 
                if   ieta <= 16: det = "HB" 
                elif ieta <= 20: det = "HE1"
                elif ieta <= 28: det = "HE2"

                ietaStr = "%d"%(ieta)
                ietaStr = ietaStr.rjust(2)

                if not firstIeta: str2Write += ",\n"
                str2Write += "    (\"%s\", cms.untracked.vdouble("%(ietaStr)
                firstWeight = True
                for iWeight in self.iWeights:
                    if not firstWeight: str2Write += ", "
                    if subdetDepthAverageWeights[det][iWeight] == -999: continue 
                    else:
                        statError = subdetDepthAverageStatErrors[det][iWeight]
                        systError = subdetDepthAverageSystErrors[det][iWeight]

                        weightStr = "%3.2f"%(subdetDepthAverageWeights[det][iWeight]); weightStr = weightStr.rjust(5)

                        if   "UP"   in tag: str2Write += "%s + (%3.2f**2 + %3.2f**2)**0.5"%(weightStr,statError,systError)
                        elif "DOWN" in tag: str2Write += "%s - (%3.2f**2 + %3.2f**2)**0.5"%(weightStr,statError,systError)
                        else:               str2Write += "%s"%(weightStr)

                    firstWeight = False

                firstIeta = False
                str2Write += "))"

            str2Write += "\n]))"
            firstTag = False

        summary.write(str2Write)                   
        summary.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--tag"       , dest="tag"       , help="Unique tag for output"     , type=str     , default="TAG")
    parser.add_argument("--fromCache" , dest="fromCache" , help="Read from cache file"      , default=False, action="store_true")
    parser.add_argument("--contain"   , dest="contain"   , help="With pulse containment"    , default=False, action="store_true")
    parser.add_argument("--depth"     , dest="depth"     , help="Extract with depth"        , default=False, action="store_true")
    parser.add_argument("--oot"       , dest="oot"       , help="Use OOT sample"            , default=False, action="store_true")
    parser.add_argument("--scheme"    , dest="scheme"    , help="Which pulse filter scheme" , type=str     , default="ALGO")
    parser.add_argument("--evtRange"  , dest="evtRange"  , help="Start and number"          , type=int     , nargs="+", default=[-1,1])
    
    arg = parser.parse_args()

    # Everything will work inside sandbox
    HOME = os.getenv("HOME")
    SANDBOX = HOME + "/nobackup/HCAL_Trigger_Study"
    INPUTLOC = "root://cmseos.fnal.gov//store/user/jhiltbra/HCAL_Trigger_Study/WeightExtraction"

    # Default to use OOT + IT sample: called 50PU.root
    puStr = "50PU"
    if arg.oot: puStr = "OOT"

    containStr = "NoContain"
    if arg.contain: containStr = "Contain"

    depthStr = "NoDepth"
    if arg.depth: depthStr = "Depth"

    gFromCache = arg.fromCache
    eventRange = xrange(arg.evtRange[0], arg.evtRange[0]+arg.evtRange[1]) 

    outPath = "%s/plots/Weights/%s/%s"%(SANDBOX,arg.scheme,arg.tag)
    
    PUFile   = "%s/NuGun/%s/%s/%s.root"%(INPUTLOC,containStr, depthStr, puStr)

    if not gFromCache:
        theExtractor = WeightExtractor(arg.scheme, PUFile, outPath)
        theExtractor.eventLoop(eventRange)

    else:
        theExtractor = WeightExtractor(arg.scheme, "", outPath)

        theExtractor.loadHistograms()
        theExtractor.extractFitWeights(save=True)
        theExtractor.getWeightSummary("Mean")
        theExtractor.getWeightSummary("Fit")

        theExtractor.drawPulseShapes("PU")
        theExtractor.drawWeightCorrs()
