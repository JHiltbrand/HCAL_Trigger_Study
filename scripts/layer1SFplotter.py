#! /usr/bin/env python

import ROOT, random, os, argparse, string, numpy, array, json
ROOT.PyConfig.IgnoreCommandLineOptions = True

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat("")
ROOT.gStyle.SetPaintTextFormat("3.2f")
ROOT.gStyle.SetFrameLineWidth(2)
ROOT.gStyle.SetEndErrorSize(0)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

class Layer1SFplotter:

    def __init__(self, approved, wip, outpath, inputFile):

        self.inputFile   = inputFile
        self.outpath     = outpath
        
        if not os.path.exists(self.outpath):
            os.makedirs(self.outpath)

        self.approved     = approved
        self.wip          = wip

        # Customized numbers that are scaled
        # to work with or without a ratio plot
        self.TopMargin    = 0.06
        self.BottomMargin = 0.12
        self.RightMargin  = 0.12
        self.LeftMargin   = 0.12

    # Create a canvas and determine if it should be split for a ratio plot
    # Margins are scaled on-the-fly so that distances are the same in either
    # scenario.
    def makeCanvas(self, doLogX = False, doLogY = False, doLogZ = False):

        randStr = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
       
        canvas = ROOT.TCanvas(randStr, randStr, 900, 900)

        ROOT.gPad.SetTopMargin(self.TopMargin)
        ROOT.gPad.SetBottomMargin(self.BottomMargin)
        ROOT.gPad.SetLeftMargin(self.LeftMargin)
        ROOT.gPad.SetRightMargin(self.RightMargin)
        if doLogX:
            ROOT.gPad.SetLogx()
        if doLogY:
            ROOT.gPad.SetLogy()
        if doLogZ:
            ROOT.gPad.SetLogz()

        return canvas

    def addCMSlogo(self, canvas):

        canvas.cd()

        mark = ROOT.TLatex()
        mark.SetNDC(True)

        mark.SetTextAlign(11)
        mark.SetTextSize(0.065)
        mark.SetTextFont(61)
        mark.DrawLatex(self.LeftMargin, 1 - (self.TopMargin - 0.012), "CMS")

        mark.SetTextFont(52)
        mark.SetTextSize(0.035)

        if self.approved:
            mark.DrawLatex(self.LeftMargin + 0.14, 1 - (self.TopMargin - 0.012), "Supplementary")
        elif self.wip:
            mark.DrawLatex(self.LeftMargin + 0.14, 1 - (self.TopMargin - 0.012), "Work in Progress")
        else:
            mark.DrawLatex(self.LeftMargin + 0.14, 1 - (self.TopMargin - 0.012), "Preliminary")

        mark.SetTextFont(42)
        mark.SetTextAlign(31)
        mark.DrawLatex(1 - self.RightMargin, 1 - (self.TopMargin - 0.012), "Run 3 (13 TeV)")

    def output4CMSSW(self, SFs):
        
        f = open("%s/Layer1_SF.py"%(self.outpath), "w")

        etBins = ", ".join([str(s) for s in numpy.arange(1, 11, 1)])
        etBins += ", 128"

        f.write("layer1HCalScaleETBins  = cms.vint32([%s]),\n"%(etBins))
        f.write("layer1HCalScaleFactors = cms.vdouble([\n")

        for et in numpy.arange(0.0, 11.0, 1.0):
            sfList = []
            for aieta in range(1, 29):
                sfList.append(str(SFs[aieta][str(et)]))

            sfStr = ", ".join(sfList)
            f.write("        " + sfStr + ",\n")

        f.write("]),")

    # Main function to compose the full stack plot with or without a ratio panel
    def makePlots(self):

        sfMap = {}

        f = ROOT.TFile.Open(self.inputFile, "READ")

        sfHisto = None
        textAngle = 89
        yedges = array.array('d', [0.25] + list(numpy.arange(0.75, 10.75, 1.0)) + [10.25])
        sfHisto = ROOT.TH2F("sfHisto", "sfHisto", 28, 0.5, 28.5, len(yedges)-1, yedges)

        sfHisto.SetContour(255)
        sfHisto.SetTitle("")
        sfHisto.SetMarkerSize(0.6)
        sfHisto.GetXaxis().SetTitle("|i\eta|")
        sfHisto.GetYaxis().SetTitle("TP E_{T} (PFA2) [GeV]")

        sfHisto.GetXaxis().SetTitleSize(0.050); sfHisto.GetYaxis().SetTitleSize(0.050)
        sfHisto.GetXaxis().SetLabelSize(0.039); sfHisto.GetYaxis().SetLabelSize(0.039)
        sfHisto.GetXaxis().SetTitleOffset(1.1); sfHisto.GetYaxis().SetTitleOffset(1.1) 

        ETs = numpy.arange(0.0, 11.0, 1.0)
        for iET in range(0, len(ETs)):
            
            etStr = ""
            etKey = ""
            etVal = -1.0
            if iET == len(ETs) - 1:
                etStr = "gte10p0"
                etVal = 10.0
            else:
                lowET  = ETs[iET]
                highET = ETs[iET+1]
                etStr = "%sto%s"%(str(lowET).replace(".", "p"), str(highET).replace(".", "p"))
                etVal = lowET
                if lowET == 0.0:
                    etVal = 0.5

            htemp = f.Get("h_SF_PFA2ET%s_PFA1pETgt0p0"%(etStr))

            profile = htemp.QuantilesX(0.5, "h_SF_PFA2ET%s_profileX"%(etStr))
            profile.Sumw2()

            for xBin in range(1, profile.GetNbinsX()+1):
                aieta = int(profile.GetBinCenter(xBin))

                SF    = profile.GetBinContent(xBin)
                SFerr = profile.GetBinError(xBin)

                if aieta not in sfMap:
                    sfMap[aieta] = {}

                if   etVal == 0.5:
                    sfMap[aieta]["0.0"] = SF
                    sfMap[aieta]["0.5"] = SF
                elif etVal == 10.0:
                    sfMap[aieta]["10.0"] = SF
                else:
                    sfMap[aieta]["%.1f"%(etVal)] = SF
                    sfMap[aieta]["%.1f"%(etVal+0.5)] = SF

                sfBin = sfHisto.Fill(aieta, etVal, SF)
                sfHisto.SetBinError(sfBin, SFerr)

        canvas = self.makeCanvas()
        canvas.cd()

        sfHisto.Draw("COLZ TEXT%d E"%(textAngle))

        self.addCMSlogo(canvas)
        saveName = "%s/Layer1_SF"%(self.outpath)
        canvas.SaveAs(saveName+".pdf")

        f = open("%s/Layer1_SF.json"%(self.outpath), "w")
        json.dump(sfMap, f)
        f.close()

        self.output4CMSSW(sfMap)

if __name__ == "__main__":

    usage = "usage: %layer1SFplotter [options]"
    parser = argparse.ArgumentParser(usage)
    parser.add_argument("--approved",     dest="approved",     help="Plot is approved",         default=False,  action="store_true") 
    parser.add_argument("--wip",          dest="wip",          help="Plot is work in progress", default=False,  action="store_true") 
    parser.add_argument("--inputFile",    dest="inputFile",    help="Path to root file",        default="NULL", required=True)
    parser.add_argument("--outpath",      dest="outpath",      help="Where to put plots",       default="NULL", required=True)
    args = parser.parse_args()

    plotter = Layer1SFplotter(args.approved, args.wip, args.outpath, args.inputFile)
    plotter.makePlots()
