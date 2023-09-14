#! /usr/bin/env python

import ROOT, random, os, argparse, string, copy, math, re
ROOT.PyConfig.IgnoreCommandLineOptions = True

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat("")
ROOT.gStyle.SetPaintTextFormat("3.3f")
ROOT.gStyle.SetFrameLineWidth(2)
ROOT.gStyle.SetEndErrorSize(0)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

# This class owns a histogram and can take a ROOT TH1 or
# a path to extract the histogram from
#    histo      : ROOT TH1 object to hold onto
#    rootFile   : input path to ROOT file containing histos
#    histoName  : name of histo to be extracted from file
#    hinfo      : dictionary of params for customizing histo
#    pinfo      : additional params for customizing histo
#    aux        : auxiliary multiplier for offsetting y-axis label
class Histogram:

    def __init__(self, histo=None, rootFile=None, histoName=None, hinfo=None, ginfo=None, aux = 1.0):

        self.xDim = {}
        self.yDim = {}

        self.info = hinfo

        for key, value in ginfo.items():
            if key == "hists": continue
            self.info[key] = value

        self.histoName = histoName
        self.filePath  = rootFile

        # Custom tuned values for these dimensions/sizes
        # Are scaled accordingly if margins change
        self.xDim["title"]  = 0.055; self.yDim["title"]  = 0.055
        self.xDim["label"]  = 0.045; self.yDim["label"]  = 0.045
        self.xDim["offset"] = 1.0;   self.yDim["offset"] = 0.65

        self.histogram = histo

        self.profile    = -1
        self.profileErr = -1

        self.setupHisto(aux)

    def IsGood(self):
        return self.histogram != -1

    def Draw(self, canvas, drawProfileError=False):

        if self.histogram != -1 and self.info["draw2D"]:
            self.histogram.Draw("COLZ SAME")

        if drawProfileError and self.profileErr != -1:
            self.profileErr.Draw("P SAME")
        elif not drawProfileError and self.profile != -1:
            self.profile.Draw("P SAME")
            
    # Simply get the raw histogram from the input ROOT file
    def getHisto(self):

        if self.histogram != None:
            return 0

        f = None
        try:
            f = ROOT.TFile.Open(self.filePath, "READ")
        except Exception as e:
            print("WARNING: Could not open file \"%s\" !"%(self.filePath), e)
            return -1
        
        if f == None:
            print("WARNING: Skipping file \"%s\" for histo \"%s\" !"%(self.filePath, self.histoName))
            return -1

        histo = f.Get(self.histoName)

        if histo == None:
            print("WARNING: Skipping histo \"%s\" from \"%s\""%(self.histoName, self.filePath))
            return -1

        histo.SetDirectory(0)

        f.Close()

        self.histogram = histo
        return 0

    def makeProfileError(self):

        nbins = self.profile.GetNbinsX()
        width = self.profile.GetBinWidth(1)
        low   = self.profile.GetBinLowEdge(1)
        high  = self.profile.GetBinLowEdge(nbins) + width
        self.profileErr = ROOT.TH1F("%s_error"%(self.profile.GetName()), "%s_error"%(self.profile.GetName()), nbins, low, high)
        self.profileErr.SetDirectory(0)
        for iBin in range(1, self.profile.GetNbinsX()+1):
            error = self.profile.GetBinError(iBin)
            content = self.profile.GetBinContent(iBin)

            if content != 0.0:
                if "PFA2" in self.profile.GetName() and "cut" not in self.profile.GetName() and "0p0to10p0" in self.profile.GetName():
                    print(self.profile.GetName(), iBin, error, content)
                self.profileErr.SetBinContent(iBin, error / content)
                self.profileErr.SetBinError(iBin, 0.0)

    def setupHisto(self, aux):

        code = self.getHisto()

        if code != -1:

            # rebin first
            if "rebin" in self.info["X"]:
                self.histogram.RebinX(self.info["X"]["rebin"])
            if "rebin" in self.info["Y"]:
                self.histogram.RebinY(self.info["Y"]["rebin"])

            self.profile = self.histogram.ProfileX("%s_%d"%(self.histogram.GetName(),self.histogram.GetUniqueID()), 1, -1, "s"); self.profile.Sumw2()

            self.makeProfileError()

            def setOptions(histo):
                histo.GetXaxis().SetTitleSize(self.xDim["title"]);    histo.GetYaxis().SetTitleSize(self.yDim["title"])
                histo.GetXaxis().SetLabelSize(self.xDim["label"]);    histo.GetYaxis().SetLabelSize(self.yDim["label"])
                histo.GetXaxis().SetTitleOffset(self.xDim["offset"]); histo.GetYaxis().SetTitleOffset(self.yDim["offset"] * aux)
                histo.GetXaxis().SetTitle(self.info["X"]["title"]);   histo.GetYaxis().SetTitle(self.info["Y"]["title"])

                if "min" in self.info["X"] and "max" in self.info["X"]:
                    histo.GetXaxis().SetRangeUser(self.info["X"]["min"], self.info["X"]["max"])
                if "min" in self.info["Y"] and "max" in self.info["Y"]:
                    histo.GetYaxis().SetRangeUser(self.info["Y"]["min"], self.info["Y"]["max"])

                histo.SetMarkerSize(self.info["msize"])
                histo.SetLineColor(self.info["color"])
                histo.SetLineWidth(0)
                histo.SetMarkerColor(self.info["color"])
                histo.SetMarkerStyle(self.info["mstyle"])

                histo.SetTitle("")

            setOptions(self.profile)
            setOptions(self.profileErr)

        else:
            self.profile    = -1
            self.profileErr = -1
            self.histogram  = -1

class ProfilePlotter:

    def __init__(self, approved, wip, outpath, inputFile, histograms, groups):

        self.histograms  = histograms
        self.groups      = groups
    
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
        self.RightMargin  = 0.02
        self.LeftMargin   = 0.08

    # Create a canvas and determine if it should be split for a ratio plot
    # Margins are scaled on-the-fly so that distances are the same in either
    # scenario.
    def makeCanvas(self, doLogX, doLogY, doLogZ):

        randStr = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
       
        canvas = ROOT.TCanvas(randStr, randStr, 1600, 900)

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
        mark.SetTextSize(0.070)
        mark.SetTextFont(61)
        mark.DrawLatex(self.LeftMargin + 0.02, 1 - 2.0 * self.TopMargin, "CMS")

        mark.SetTextFont(52)
        mark.SetTextSize(0.040)

        if self.approved:
            mark.DrawLatex(self.LeftMargin + 0.105, 1 - 2.0 * self.TopMargin, "Supplementary")
        elif self.wip:
            mark.DrawLatex(self.LeftMargin + 0.105, 1 - 2.0 * self.TopMargin, "Work in Progress")
        else:
            mark.DrawLatex(self.LeftMargin + 0.105, 1 - 2.0 * self.TopMargin, "Preliminary")

        mark.SetTextFont(42)
        mark.SetTextAlign(31)
        mark.SetTextSize(0.040)
        mark.DrawLatex(1 - self.RightMargin, 1 - (self.TopMargin - 0.015), "Run 3 (13 TeV)")

    def addExtraInfo(self, histoName, canvas):

        nameChunks = histoName.split("_")

        stringChunks = []

        for chunk in nameChunks:
    
            if not bool(re.search(r"\d", chunk)): continue

            varStr = ""
            if "ET" in chunk:
                parts = chunk.split("ET")

                if "RH" in parts[0]:
                    varStr = "RH (MAHI) E_{T}"
                elif "PFA2" in parts[0]:
                    varStr = "TP (PFA2) E_{T}"
                elif "PFA1p" in parts[0]:
                    varStr = "TP (PFA1p) E_{T}"

                if "gte" in parts[1]:
                    cut = parts[1].split("gte")[-1].replace("p", ".")
                    stringChunks.append("%s #geq %s GeV"%(varStr, cut)) 
                elif "gt" in parts[1]:
                    cut = parts[1].split("gt")[-1].replace("p", ".")
                    stringChunks.append("%s > %s GeV"%(varStr, cut)) 
                elif "lte" in parts[1]:
                    cut = parts[1].split("lte")[-1].replace("p", ".")
                    stringChunks.append("%s #leq %s GeV"%(varStr, cut)) 
                elif "lt" in parts[1]:
                    cut = parts[1].split("lt")[-1].replace("p", ".")
                    stringChunks.append("%s < %s GeV"%(varStr, cut)) 
                elif "to" in parts[1]:
                    arange = [s.replace("p", ".") for s in parts[1].split("to")]
                    op = "<"
                    if "PFA2" in parts[0]:
                        op = "#leq"
                    stringChunks.append("%s < %s %s %s GeV"%(arange[0], varStr, op, arange[1]))
                else:
                    cut = parts[1].replace("p", ".")
                    stringChunks.append("%s = %s GeV"%(varStr, cut))

            elif "nVtx" in chunk:
                parts = chunk.split("nVtx")

                varStr = "N_{vtx}"

                if "gte" in parts[1]:
                    cut = parts[1].split("gte")[-1].split("p")[0]
                    stringChunks.append("%s #geq %s"%(varStr, cut)) 
                elif "gt" in parts[1]:
                    cut = parts[1].split("gt")[-1].split("p")[0]
                    stringChunks.append("%s > %s"%(varStr, cut)) 
                elif "lte" in parts[1]:
                    cut = parts[1].split("lte")[-1].split("p")[0]
                    stringChunks.append("%s #leq %s"%(varStr, cut)) 
                elif "lt" in parts[1]:
                    cut = parts[1].split("lt")[-1].split("p")[0]
                    stringChunks.append("%s < %s"%(varStr, cut)) 
                elif "to" in parts[1]:
                    arange = [s.split("p")[0] for s in parts[1].split("to")]
                    stringChunks.append("%s < %s #leq %s"%(arange[0], varStr, arange[1]))
                else:
                    cut = parts[1].split("p")[0]
                    stringChunks.append("%s = %s"%(varStr, cut))

        canvas.cd()

        mark = ROOT.TLatex()
        mark.SetNDC(True)

        mark.SetTextAlign(13)
        mark.SetTextSize(0.040)
        mark.SetTextFont(42)

        spacing = 0.06
        nChunk  = 0
        for chunk in stringChunks:
            mark.DrawLatex(self.LeftMargin + 0.03, 1 - self.TopMargin - 0.04 - self.TopMargin - nChunk * spacing, chunk)
            nChunk += 1

    # Main function to compose the full stack plot with or without a ratio panel
    def makePlots(self):

        for gname, ginfo in self.groups.items():

            hnames = ginfo["hists"]

            # Top loop begins going over each histo-to-be-plotted
            nEntry = 0
            spacing = 0.06
            legends = []
            Hobjs   = []
            for hname in hnames:

                hinfo = self.histograms[hname]

                if hname == hnames[0]:
                    canvas = self.makeCanvas(ginfo["logX"], ginfo["logY"], ginfo["logZ"])
                    canvas.cd()

                Hobjs.append(Histogram(None, self.inputFile, hname, hinfo, ginfo))

                if "_res_" in gname:
                    Hobjs[-1].Draw(canvas, drawProfileError = True)
                else:
                    Hobjs[-1].Draw(canvas)

                legName = ""
                if "_PFA2_" in hname or "PFA2vs" in hname or "PFA2uncorr" in hname:
                    if "uncorr" in hname and "close" in hname:
                        legName = "PFA2 (raw)"
                    elif "close" in hname:
                        legName = "PFA2 (scaled)"    
                    else:
                        legName = "PFA2"
                elif "_PFA1p_" in hname or "PFA1pvs" in hname:
                    legName = "PFA1p"

                if "nVtx0p0to25p0" in hname and "nVtx0p0to25p0" not in gname:
                    legName += " (0 < N_{vtx} #leq 25)"
                elif "nVtx25p0to50p0" in hname and "nVtx25p0to50p0" not in gname:
                    legName += " (25 < N_{vtx} #leq 50)"
                elif "nVtxgt50p0" in hname and "nVtxgt50p0" not in gname:
                    legName += " (N_{vtx} > 50)"

                legends.append(ROOT.TLegend(0.65, 1.0 - self.TopMargin - 0.02 - (nEntry + 1) * spacing, 1.0 - self.RightMargin - 0.02, 1.0 - self.TopMargin - 0.02 - nEntry * spacing, "", "trNDC"))
                legends[-1].SetFillStyle(0)
                legends[-1].SetTextSize(0.040)
                legends[-1].SetLineWidth(0)
                legends[-1].AddEntry(Hobjs[-1].profile, legName, "P")

                legends[-1].Draw("SAME")
                nEntry += 1

            self.addCMSlogo(canvas)
            self.addExtraInfo(gname, canvas)
   
            saveName = "%s/%s"%(self.outpath, gname)
            canvas.SaveAs(saveName+".pdf")

if __name__ == "__main__":

    usage = "usage: %twoDimPlotter [options]"
    parser = argparse.ArgumentParser(usage)
    parser.add_argument("--approved",     dest="approved",     help="Plot is approved",         default=False,  action="store_true") 
    parser.add_argument("--wip",          dest="wip",          help="Plot is work in progress", default=False,  action="store_true") 
    parser.add_argument("--inputFile",    dest="inputFile",    help="Path to root file",        default="NULL", required=True)
    parser.add_argument("--outpath",      dest="outpath",      help="Where to put plots",       default="NULL", required=True)
    parser.add_argument("--options",      dest="options",      help="options file",             default="twoDimPlotter_aux", type=str)
    args = parser.parse_args()

    # The auxiliary file contains many "hardcoded" items
    # describing which histograms to get and how to draw
    # them. These things are changed often by the user
    # and thus are kept in separate sidecar file.
    importedGoods = __import__(args.options)

    # Names of histograms, rebinning, titles, ranges, etc.
    histograms  = importedGoods.histograms

    # Get a mapping of which profiles (histograms) to draw together
    groups      = importedGoods.groups

    plotter = ProfilePlotter(args.approved, args.wip, args.outpath, args.inputFile, histograms, groups)
    plotter.makePlots()
