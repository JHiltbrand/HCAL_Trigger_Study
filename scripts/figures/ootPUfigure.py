import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat("")
ROOT.gStyle.SetLineWidth(4)
ROOT.gStyle.SetPaintTextFormat("3.2f")
ROOT.gStyle.SetFrameLineWidth(0)

pulses = {"TS0" : {"hist" : ROOT.TH1D("TS0", "", 8, -0.5, 7.5), "bins" : [50, 17,  5,   0,  0,  0,  0,  0], "color" : ROOT.TColor.GetColor("#984ea3")},
          "TS1" : {"hist" : ROOT.TH1D("TS1", "", 8, -0.5, 7.5), "bins" : [ 0, 40, 13,   5,  0,  0,  0,  0], "color" : ROOT.TColor.GetColor("#377eb8")},
          "TS2" : {"hist" : ROOT.TH1D("TS2", "", 8, -0.5, 7.5), "bins" : [ 0,  0, 45,  15,  5,  1,  0,  0], "color" : ROOT.TColor.GetColor("#4daf4a")},
          "TS3" : {"hist" : ROOT.TH1D("TS3", "", 8, -0.5, 7.5), "bins" : [ 0,  0,  0, 100, 30,  8,  0,  0], "color" : ROOT.TColor.GetColor("#e41a1c")},
          "TS4" : {"hist" : ROOT.TH1D("TS4", "", 8, -0.5, 7.5), "bins" : [ 0,  0,  0,   0, 41, 10,  2,  0], "color" : ROOT.TColor.GetColor("#ff7f00")},
          "TS5" : {"hist" : ROOT.TH1D("TS5", "", 8, -0.5, 7.5), "bins" : [ 0,  0,  0,   0,  0, 30,  9,  1], "color" : ROOT.TColor.GetColor("#999999")},
          "TS6" : {"hist" : ROOT.TH1D("TS6", "", 8, -0.5, 7.5), "bins" : [ 0,  0,  0,   0,  0,  0, 35,  5], "color" : ROOT.TColor.GetColor("#a65628")},
          "TS7" : {"hist" : ROOT.TH1D("TS7", "", 8, -0.5, 7.5), "bins" : [ 0,  0,  0,   0,  0,  0,  0, 33], "color" : ROOT.TColor.GetColor("#f781bf")}
}

perfect = {"TS0" : {"hist" : ROOT.TH1D("TS0_perfect", "", 8, -0.5, 7.5), "bins" : [72,  0,  0,   0,  0,  0,  0,  0], "color" : ROOT.TColor.GetColor("#984ea3")},
           "TS1" : {"hist" : ROOT.TH1D("TS1_perfect", "", 8, -0.5, 7.5), "bins" : [ 0, 58,  0,   0,  0,  0,  0,  0], "color" : ROOT.TColor.GetColor("#377eb8")},
           "TS2" : {"hist" : ROOT.TH1D("TS2_perfect", "", 8, -0.5, 7.5), "bins" : [ 0,  0, 65,   0,  0,  0,  0,  0], "color" : ROOT.TColor.GetColor("#4daf4a")},
           "TS3" : {"hist" : ROOT.TH1D("TS3_perfect", "", 8, -0.5, 7.5), "bins" : [ 0,  0,  0, 138,  0,  0,  0,  0], "color" : ROOT.TColor.GetColor("#e41a1c")},
           "TS4" : {"hist" : ROOT.TH1D("TS4_perfect", "", 8, -0.5, 7.5), "bins" : [ 0,  0,  0,   0, 53,  0,  0,  0], "color" : ROOT.TColor.GetColor("#ff7f00")},
           "TS5" : {"hist" : ROOT.TH1D("TS5_perfect", "", 8, -0.5, 7.5), "bins" : [ 0,  0,  0,   0,  0, 40,  0,  0], "color" : ROOT.TColor.GetColor("#999999")},
           "TS6" : {"hist" : ROOT.TH1D("TS6_perfect", "", 8, -0.5, 7.5), "bins" : [ 0,  0,  0,   0,  0,  0, 40,  0], "color" : ROOT.TColor.GetColor("#a65628")},
           "TS7" : {"hist" : ROOT.TH1D("TS7_perfect", "", 8, -0.5, 7.5), "bins" : [ 0,  0,  0,   0,  0,  0,  0, 33], "color" : ROOT.TColor.GetColor("#f781bf")}
}


binLabels = ["-3", "-2", "-1", "0", "+1", "+2", "+3", "+4"]
bxs = ["TS0", "TS1", "TS2", "TS4", "TS5", "TS6", "TS7", "TS3"]

def setHistoOptions(histo):
    histo.SetMinimum(0)
    histo.GetYaxis().SetTickLength(0)
    histo.GetXaxis().SetTickLength(0)
    histo.GetYaxis().SetLabelSize(0)
    histo.GetXaxis().SetLabelSize(0.08)
    histo.GetYaxis().SetTitle("A.U.")
    histo.GetXaxis().SetTitle("BX")
    histo.GetYaxis().SetTitleSize(0.06)
    histo.GetXaxis().SetTitleSize(0.07)
    histo.GetXaxis().SetTitleOffset(0.9)
    histo.GetYaxis().SetTitleOffset(0.3)
    histo.SetTitle("")

fullPulse = ROOT.TH1F("FullPulse", "", 8, -0.5, 7.5)
fullPulsePerfect = ROOT.TH1F("FullPulsePerfect", "", 8, -0.5, 7.5)

fullPulseStack = ROOT.THStack("FullPulseStack", "")
fullPerfectStack = ROOT.THStack("FullPerfectStack", "")

for ts in xrange(0,8):
    fullPulse.GetXaxis().SetBinLabel(ts+1,binLabels[ts])
    fullPulsePerfect.GetXaxis().SetBinLabel(ts+1,binLabels[ts])

for bx in bxs:
    for ts in xrange(0,8):
        pulses[bx]["hist"].SetBinContent(ts+1, pulses[bx]["bins"][ts])
        pulses[bx]["hist"].GetXaxis().SetBinLabel(ts+1, binLabels[ts])

    setHistoOptions(pulses[bx]["hist"])
    pulses[bx]["hist"].SetFillColorAlpha(pulses[bx]["color"],1.0)
    pulses[bx]["hist"].SetLineWidth(0)

    fullPulseStack.Add(pulses[bx]["hist"].Clone(bx+"Clone"))

for bx in bxs:
    for ts in xrange(0,8):
        perfect[bx]["hist"].SetBinContent(ts+1, perfect[bx]["bins"][ts])
        perfect[bx]["hist"].GetXaxis().SetBinLabel(ts+1, binLabels[ts])

    setHistoOptions(perfect[bx]["hist"])
    perfect[bx]["hist"].SetFillColorAlpha(perfect[bx]["color"],1.0)
    perfect[bx]["hist"].SetLineWidth(0)

    fullPerfectStack.Add(perfect[bx]["hist"].Clone(bx+"ClonePerfect"))

for pulse, pulseDict in pulses.iteritems():
    fullPulse.Add(pulseDict["hist"])

for pulse, pulseDict in perfect.iteritems():
    fullPulsePerfect.Add(pulseDict["hist"])

signal = pulses["TS3"]["hist"].Clone("signal")
perfectSignal = perfect["TS3"]["hist"].Clone("perfectSignal")

signal.SetLineWidth(6); signal.SetLineStyle(7); signal.SetLineColor(ROOT.kBlack)
perfectSignal.SetLineWidth(6); perfectSignal.SetLineStyle(7); perfectSignal.SetLineColor(ROOT.kBlack)

histoMax = 140

# Draw realstic pulses and total pulse
canvas = ROOT.TCanvas("canvas", "canvas", 2400, 1800); canvas.cd()

ROOT.gPad.SetTopMargin(0.02)
ROOT.gPad.SetBottomMargin(0.14)
ROOT.gPad.SetLeftMargin(0.06)
ROOT.gPad.SetRightMargin(0.02)

fullPulse.SetLineWidth(6)
fullPulse.SetLineStyle(7)
fullPulse.SetLineColor(ROOT.kBlack)

setHistoOptions(fullPulse)

pulses["TS7"]["hist"].GetYaxis().SetRangeUser(0,histoMax)

#pulses["TS7"]["hist"].Draw("HIST SAME")
#pulses["TS6"]["hist"].Draw("HIST SAME")
#pulses["TS5"]["hist"].Draw("HIST SAME")
#pulses["TS4"]["hist"].Draw("HIST SAME")
#pulses["TS3"]["hist"].Draw("HIST SAME")
#pulses["TS2"]["hist"].Draw("HIST SAME")
#pulses["TS1"]["hist"].Draw("HIST SAME")
#pulses["TS0"]["hist"].Draw("HIST SAME")

fullPulseStack.Draw()
setHistoOptions(fullPulseStack)
fullPulseStack.Draw()
fullPulse.Draw("HIST SAME")

canvas.SaveAs("ootPUpulse_total.pdf")

# Draw realistic (no oot pu) pulse
canvas2 = ROOT.TCanvas("canvas2", "canvas2", 2400, 1800); canvas2.cd()

ROOT.gPad.SetTopMargin(0.02)
ROOT.gPad.SetBottomMargin(0.14)
ROOT.gPad.SetLeftMargin(0.06)
ROOT.gPad.SetRightMargin(0.02)

pulses["TS3"]["hist"].GetYaxis().SetRangeUser(0,histoMax)
pulses["TS3"]["hist"].Draw("HIST")
signal.Draw("SAME HIST")

canvas2.SaveAs("ootPUpulse_signal.pdf")

# Draw ideal pulses
canvas3 = ROOT.TCanvas("canvas3", "canvas3", 2400, 1800); canvas3.cd()

ROOT.gPad.SetTopMargin(0.02)
ROOT.gPad.SetBottomMargin(0.14)
ROOT.gPad.SetLeftMargin(0.06)
ROOT.gPad.SetRightMargin(0.02)

fullPulsePerfect.SetLineWidth(6)
fullPulsePerfect.SetLineStyle(7)
fullPulsePerfect.SetLineColor(ROOT.kBlack)

setHistoOptions(fullPulsePerfect)

perfect["TS7"]["hist"].GetYaxis().SetRangeUser(0,histoMax)

#perfect["TS7"]["hist"].Draw("HIST SAME")
#perfect["TS6"]["hist"].Draw("HIST SAME")
#perfect["TS5"]["hist"].Draw("HIST SAME")
#perfect["TS4"]["hist"].Draw("HIST SAME")
#perfect["TS3"]["hist"].Draw("HIST SAME")
#perfect["TS2"]["hist"].Draw("HIST SAME")
#perfect["TS1"]["hist"].Draw("HIST SAME")
#perfect["TS0"]["hist"].Draw("HIST SAME")

fullPerfectStack.Draw()
setHistoOptions(fullPerfectStack)
fullPerfectStack.Draw()
fullPulsePerfect.Draw("HIST SAME")

canvas3.SaveAs("ootPUpulse_total_perfect.pdf")

# Draw realistic (no oot pu) pulse
canvas4 = ROOT.TCanvas("canvas4", "canvas4", 2400, 1800); canvas4.cd()

ROOT.gPad.SetTopMargin(0.02)
ROOT.gPad.SetBottomMargin(0.14)
ROOT.gPad.SetLeftMargin(0.06)
ROOT.gPad.SetRightMargin(0.02)

perfect["TS3"]["hist"].GetYaxis().SetRangeUser(0,histoMax)
perfect["TS3"]["hist"].Draw("HIST")

perfectSignal.Draw("SAME HIST")
canvas4.SaveAs("ootPUpulse_signal_perfect.pdf")
