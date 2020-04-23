# First-step script directly running on HCAL ntuples files

# An example call could be:
# python studies/ratioStudyPlotter.py --inputSubPath subpath/to/scheme/ntuples

# The subpath is assumed to start inside HCAL_Trigger_Study/hcalNtuples path in the user's EOS area

import sys, os, ROOT, subprocess, argparse
from toolbox import *

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat("")
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()
ROOT.TH3.SetDefaultSumw2()
ROOT.gStyle.SetEndErrorSize(0.0)

def makeTPRH_vs_ieta(plotsDir, fNominal, fUp25, fDown25, fUp50, fDown50):

    RHETranges = ["Low", "High"]
    for RHETrange in RHETranges:

        RHETname = ""; resName = ""
        if RHETrange == "Low":
            RHETname = "RHET0.0to10.0"
            resName = "Low"
        else:
            RHETname = "RHET10.0toInf"
            resName = "High"

        hNominal = fNominal.Get("TPRH_vs_ieta_%s_TPETgt0.5_peak"%(RHETname))
        hUp25    = fUp25.   Get("TPRH_vs_ieta_%s_TPETgt0.5_peak"%(RHETname))
        hDown25  = fDown25. Get("TPRH_vs_ieta_%s_TPETgt0.5_peak"%(RHETname))
        hUp50    = fUp50.   Get("TPRH_vs_ieta_%s_TPETgt0.5_peak"%(RHETname))
        hDown50  = fDown50. Get("TPRH_vs_ieta_%s_TPETgt0.5_peak"%(RHETname))

        dummy = hNominal.Clone(); dummy.Reset()

        pNominal = hNominal.ProfileX("p_nom_%s"%(resName), 1, -1, ""); pNominal.Sumw2()
        pNominalResTemp = hNominal.ProfileX("p_nomres_%s"%(resName), 1, -1, "s"); pNominalResTemp.Sumw2()
        pNominalRes = stdDevProfile(pNominalResTemp, 29)

        pUp25 = hUp25.ProfileX("p_up25_%s"%(resName), 1, -1, ""); pUp25.Sumw2()
        pUp25ResTemp = hUp25.ProfileX("p_up25res_%s"%(resName), 1, -1, "s"); pUp25ResTemp.Sumw2()
        pUp25Res = stdDevProfile(pUp25ResTemp)

        pDown25 = hDown25.ProfileX("p_down25_%s"%(resName), 1, -1, ""); pDown25.Sumw2()
        pDown25ResTemp = hDown25.ProfileX("p_down25res_%s"%(resName), 1, -1, "s"); pDown25ResTemp.Sumw2()
        pDown25Res = stdDevProfile(pDown25ResTemp)

        pUp50 = hUp50.ProfileX("p_up50_%s"%(resName), 1, -1, ""); pUp50.Sumw2()
        pUp50ResTemp = hUp50.ProfileX("p_up50res_%s"%(resName), 1, -1, "s"); pUp50ResTemp.Sumw2()
        pUp50Res = stdDevProfile(pUp50ResTemp)

        pDown50 = hDown50.ProfileX("p_down50_%s"%(resName), 1, -1, ""); pDown50.Sumw2()
        pDown50ResTemp = hDown50.ProfileX("p_down50res_%s"%(resName), 1, -1, "s"); pDown50ResTemp.Sumw2()
        pDown50Res = stdDevProfile(pDown50ResTemp)

        set1Doptions(pNominal, lineWidth = 2, markerColor = ROOT.kBlack, lineColor = ROOT.kBlack, markerStyle = 20, markerSize = 2.7)

        band25 = makeBandGraph(pNominal, pUp25, pDown25, ROOT.kRed, 29)
        band50 = makeBandGraph(pNominal, pUp50, pDown50, ROOT.kGray+2, 29)

        band25Res = makeBandGraph(pNominalRes, pUp25Res, pDown25Res, ROOT.kRed, 29)
        band50Res = makeBandGraph(pNominalRes, pUp50Res, pDown50Res, ROOT.kGray+2, 29)

        tm = 0.026; bm = 0.15; lm = 0.11; rm = 0.12
        c = ROOT.TCanvas("c_%s"%(resName), "c_%s"%(resName), 2400, 1440)
        c.cd(); ROOT.gPad.SetLogz()
        ROOT.gPad.SetPad(0, 0.0, 1, 1.0)
        ROOT.gPad.SetTopMargin(tm)
        ROOT.gPad.SetBottomMargin(bm)
        ROOT.gPad.SetLeftMargin(lm)
        ROOT.gPad.SetRightMargin(rm)

        setAxisDims(hNominal, 0.059, 0.059, 0.059, 0.072, 0.072, 0.072, 0.95, 0.72, 1.0)
        setAxisRanges(hNominal, yMin = 0.1, yMax = 2.0, zMin = 1, zMax = 8e4)
        set2Doptions(hNominal)

        l = ROOT.TLine(-28.5, 1, 28.5, 1) 
        l.SetLineWidth(3)
        l.SetLineColor(ROOT.kBlack)
        l.SetLineStyle(2)

        hNominal.Draw("COLZ")
        band50.Draw("2SAME")
        band25.Draw("2SAME")
        pNominal.Draw("EP SAME")
        l.Draw("SAME")

        c.SaveAs("%s/TPRH_vs_ieta_%s_TPETgt0.5_peak.pdf"%(plotsDir,RHETname))

        cres = ROOT.TCanvas("cres_%s"%(resName), "cres_%s"%(resName), 2400, 1440)
        cres.cd(); cres.SetGridy(); cres.SetGridx()

        ROOT.gPad.SetPad(0, 0.0, 1, 1.0)
        ROOT.gPad.SetTopMargin(tm)
        ROOT.gPad.SetBottomMargin(bm)
        ROOT.gPad.SetLeftMargin(0.13)
        ROOT.gPad.SetRightMargin(0.03)

        setAxisDims(dummy, 0.059, 0.059, 0.059, 0.072, 0.072, 0.072, 0.85, 0.85, 1.0)
        setAxisRanges(dummy, yMin = 0.0, yMax = 0.7)
        setAxisLabels(dummy, lab = "", yLab = "#sigma#left(E_{T,TP} / E_{T,RH}#right)")

        set1Doptions(pNominalRes, lineWidth = 2, markerColor = ROOT.kBlack, lineColor = ROOT.kBlack, markerStyle = 20, markerSize = 2.7)

        dummy.Draw()
        band50Res.Draw("2SAME")
        band25Res.Draw("2SAME")
        pNominalRes.Draw("EP SAME")

        cres.SaveAs("%s/pfa_res%s.pdf"%(plotsDir,resName))

def analysis(PFANominal, PFAUp25, PFADown25, PFAUp50, PFADown50, plotsDir):

    if not os.path.exists(plotsDir): os.makedirs(plotsDir)

    fNominal = ROOT.TFile.Open(PFANominal + "/ratios.root") 
    fUp25    = ROOT.TFile.Open(PFAUp25 + "/ratios.root") 
    fUp50    = ROOT.TFile.Open(PFAUp50 + "/ratios.root") 
    fDown25  = ROOT.TFile.Open(PFADown25 + "/ratios.root") 
    fDown50  = ROOT.TFile.Open(PFADown50 + "/ratios.root") 

    makeTPRH_vs_ieta(plotsDir, fNominal, fUp25, fDown25, fUp50, fDown50)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--pfaNominal", dest="pfaNominal", help="Subpath to nominal PFA files"        , type=str , required=True)
    parser.add_argument("--pfa25"     , dest="pfa25"     , help="Subpath to 25% biased Up PFA files"  , type=str , required=True)
    parser.add_argument("--pfa50"     , dest="pfa50"     , help="Subpath to 50% biased Down PFA files", type=str , required=True)
    parser.add_argument("--tag"       , dest="tag"       , help="Unique tag for separating"           , type=str , default="")
    args = parser.parse_args()

    HOME = os.getenv("HOME"); USER = os.getenv("USER")
    INPUTLOC = "%s/nobackup/HCAL_Trigger_Study/input/Ratios"%(HOME)
    PLOTSLOC = "%s/nobackup/HCAL_Trigger_Study/plots/Ratios"%(HOME)

    # Let the output folder structure mirror the input folder structure
    fileStubNominal = args.pfaNominal
    fileStubUp25    = args.pfa25 + "_UP"
    fileStubUp50    = args.pfa50 + "_UP"
    fileStubDown25  = args.pfa25 + "_DOWN"
    fileStubDown50  = args.pfa50 + "_DOWN"

    tag      = args.tag

    analysis(INPUTLOC + "/" + fileStubNominal, INPUTLOC + "/" + fileStubUp25, INPUTLOC + "/" + fileStubDown25, INPUTLOC + "/" + fileStubUp50, INPUTLOC + "/" + fileStubDown50, PLOTSLOC + "/" + fileStubNominal + "/" + tag)
