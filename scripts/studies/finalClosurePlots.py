# The finalClosurePlots script extracts the raw 2D histograms made by the closureStudyPlotter script
# and puts them into final presentable form. An example call would be:
# python studies/finalClosurePlots.py --tag someTag --pfaY subpath/to/nominal --pfaX1 subpath/to/new

import sys, os, ROOT, argparse, math
from toolbox import *

ROOT.TH1.SetDefaultSumw2()
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat("")
ROOT.gStyle.SetPaintTextFormat("3.2f")
ROOT.gStyle.SetFrameLineWidth(2)
#ROOT.gStyle.SetErrorX(0)

def fillMap(pfaKey, inRootDir):

    if "NULL" in inRootDir: return

    MAPPFAHISTOS[pfaKey] = {}

    for histoFile in os.listdir(inRootDir):

       if ".root" not in histoFile: continue
       histoFile = ROOT.TFile.Open(inRootDir + "/" + histoFile, "READ")
       for hkey in histoFile.GetListOfKeys():
           if "TH" not in hkey.GetClassName(): continue

           name = hkey.GetName()
           histo = hkey.ReadObj()
           histo.SetDirectory(0)

           histo.Sumw2()
           
           if name in MAPPFAHISTOS[pfaKey].keys(): MAPPFAHISTOS[pfaKey][name].Add(histo)
           else: MAPPFAHISTOS[pfaKey][name] = histo

def draw2DHistoAndProfile(canvas, iamLegend, keyName, histoName, zMax, color, markerStyle, markerSize, line, drewRatio):

    canvas.cd()

    theHisto = MAPPFAHISTOS[keyName][histoName]
    dummy = ROOT.TH2F("dummy", "", theHisto.GetNbinsX(), theHisto.GetXaxis().GetBinLowEdge(1), theHisto.GetXaxis().GetBinUpEdge(theHisto.GetNbinsX()), 720, -10, 10); dummy.SetDirectory(0); ROOT.SetOwnership(dummy, False)
    graph = 0

    # Very careful now, take the profile before cutting off the y range!
    profile = theHisto.ProfileX("p_%s_%s"%(theHisto.GetName(),keyName), 1, -1, ""); ROOT.SetOwnership(profile, False); profile.Sumw2()
    set1Doptions(profile, markerColor = color, lineWidth = 2, lineColor = color, markerSize = markerSize, markerStyle = markerStyle)

    if   keyName == "PFAUNCORR": iamLegend.AddEntry(profile, "Total Bias from OOT PU", "EP")
    elif keyName == "PFAMODE":   iamLegend.AddEntry(profile, "Residual Bias (w/ Mode Weights)", "EP")
    elif keyName == "PFAMEAN":   iamLegend.AddEntry(profile, "Residual Bias (w/ Mean Weights)", "EP")


    if   "ETCorr"  in histoName: setAxisDims(dummy, 0.050, 0.050, 0.050, 0.055, 0.055, 0.055, 1.00, 1.20, 1.0)
    elif "ETRatio" in histoName: setAxisDims(dummy, 0.050, 0.050, 0.050, 0.050, 0.035, 0.050, 1.00, 2.0, 1.0)

    # Set some visual options for the actual 2D TP/RH
    dummy.SetContour(255)

    if "ETCorr" in histoName:
        dummy.GetXaxis().SetRangeUser(-0.25,20.25)
        dummy.GetYaxis().SetRangeUser(-0.25,20.25)

        dummy.GetXaxis().SetTitle("TP E_{T} [GeV] (t#bar{t}+0PU)")
        dummy.GetYaxis().SetTitle("TP E_{T} [GeV] (t#bar{t}+PU)")
    else: 
        
        graph = ROOT.TGraphErrors(profile.GetNbinsX()); ROOT.SetOwnership(graph, False)
        for xbin in xrange(1, profile.GetNbinsX()):
            error = profile.GetBinError(xbin); content = profile.GetBinContent(xbin); entries = profile.GetBinEntries(xbin)
            x = profile.GetBinCenter(xbin); y = content; width = profile.GetBinWidth(1)
            graph.SetPoint(xbin-1, x, content-1.0); graph.SetPointError(xbin-1, width/2.3, error)

        set1Doptions(graph, markerColor = color, lineWidth = 2, lineColor = color, markerSize = markerSize, markerStyle = markerStyle)

        dummy.GetYaxis().SetRangeUser(-0.75,2.0)
        dummy.GetXaxis().SetTitle("TP E_{T} [GeV] (t#bar{t}+0PU)")
        dummy.GetXaxis().SetRangeUser(0.25,20.25)
        dummy.GetYaxis().SetTitle("#mu#left(#frac{E_{T,OOTPU} - E_{T,0PU}}{E_{T,0PU}}#right)")

    dummy.GetZaxis().SetRangeUser(1,zMax)
    if not drewRatio:
        dummy.Draw("COLZ")
        if "ETCorr" in histoName:  theHisto.Draw("COLZ SAME")
        drewRatio = True
    
    # Sneak the line in so the profile is draw on top
    #line.Draw("SAME")
    try: graph.Draw("EP SAME")
    except: profile.Draw("EP SAME")

    return drewRatio

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--tag"      , dest="tag"      , type=str, default=""    , help="Unique tag for output")
    parser.add_argument("--pfaUncorr"    , dest="pfaUncorr"    , type=str, default="NULL", help="Path to PFAuncorr dir") 
    parser.add_argument("--pfaMean"    , dest="pfaMean"    , type=str, default="NULL", help="Path to PFAmean dir") 
    parser.add_argument("--pfaMode"    , dest="pfaMode"    , type=str, default="NULL", help="Path to PFAmode dir") 

    args = parser.parse_args()
    
    MAPPFAHISTOS = {}

    # Figure out the stub to use for the output directory
    # If neither pfaX1 or pfaX2 have been specified then quit!
    # The subtlety here is that pfaX1 takes precedence for the output directory
    stub = ""
    if args.pfaUncorr != "NULL": stub = args.pfaUncorr.split("Closure/")[0].split("/")[0]
    else: quit()

    tag = args.tag

    HOME = os.getenv("HOME")
    OUTBASE = "%s/nobackup/HCAL_Trigger_Study/plots/Closure"%(HOME)
    INPUTLOC = "%s/nobackup/HCAL_Trigger_Study/input/Closure"%(HOME)

    # Save the input directories provided and fill the map of histos
    fillMap("PFAUNCORR", INPUTLOC + "/" + args.pfaUncorr)
    fillMap("PFAMEAN", INPUTLOC + "/" + args.pfaMean)
    fillMap("PFAMODE", INPUTLOC + "/" + args.pfaMode)

    # Set up the output directory and make it if it does not exist
    outpath = "%s/%s/%s"%(OUTBASE,stub,tag)
    if not os.path.exists(outpath): os.makedirs(outpath)

    # Save the final histograms
    for name in MAPPFAHISTOS.values()[0].keys():

        className = MAPPFAHISTOS.values()[0][name].ClassName()

        if "TH2" in className:
            zMax = 2e3 
            
            c1 = 0; line = 0
            if "ETCorr" in name:

                c1 = ROOT.TCanvas("%s"%(name), "%s"%(name), 1600, 1440); c1.cd(); c1.SetLogz()

                ROOT.gPad.SetTopMargin(0.026)
                ROOT.gPad.SetBottomMargin(0.14)
                ROOT.gPad.SetLeftMargin(0.13)
                ROOT.gPad.SetRightMargin(0.14)

                ROOT.gPad.SetGridx()
                ROOT.gPad.SetGridy()

                line = ROOT.TLine(-0.25, -0.25, 20.65, 20.65) 

            elif "ETRatio" in name:

                c1 = ROOT.TCanvas("%s"%(name), "%s"%(name), 1600, 1440); c1.cd(); c1.SetLogz()

                ROOT.gPad.SetTopMargin(0.026)
                ROOT.gPad.SetBottomMargin(0.12)
                ROOT.gPad.SetLeftMargin(0.16)
                ROOT.gPad.SetRightMargin(0.03)
                ROOT.gPad.SetGridx()
                ROOT.gPad.SetGridy()

                line = ROOT.TLine(0.25, 0, 20.25, 0) 

            line.SetLineWidth(4)
            line.SetLineColor(ROOT.kBlack)
            line.SetLineStyle(7)

            drewRatio = False; iamLegend = ROOT.TLegend(0.55, 0.75, 0.95, 0.95)
            drewRatio = draw2DHistoAndProfile(c1, iamLegend, "PFAUNCORR" , name, zMax, ROOT.kBlack, 24, 1.7, line, drewRatio)
            drewRatio = draw2DHistoAndProfile(c1, iamLegend, "PFAMODE" , name, zMax, ROOT.kBlack  , 20, 2.0, line, drewRatio)
            drewRatio = draw2DHistoAndProfile(c1, iamLegend, "PFAMEAN" , name, zMax, ROOT.kRed , 20, 2.0, line, drewRatio)
            iamLegend.SetTextFont(63); iamLegend.SetMargin(0.12)
            c1.cd()
            iamLegend.Draw("SAME")
            line.Draw("SAME")

            ietaList = name.split("ieta")[-1].split("to")
            ietaStr = ""
            if len(ietaList) > 1: ietaStr = "%s to %s"%(ietaList[0],ietaList[1])
            else:                 ietaStr = "%s"%(ietaList[0])

            ietaText = ROOT.TPaveText(0.20, 0.86, 0.40, 0.95, "trNDC")
            ietaText.SetFillColor(ROOT.kWhite); ietaText.SetTextAlign(11); ietaText.SetTextFont(63); ietaText.SetTextSize(90)
            ietaText.AddText("|i#eta| = %s"%(ietaStr))

            ietaText.Draw("SAME")

            c1.SaveAs("%s/%s.pdf"%(outpath,name))
