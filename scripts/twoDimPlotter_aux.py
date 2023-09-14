#! /bin/env/python

histograms = {}

rhStrs = ["RHET0p0to0p05", "RHET0p05to0p1", "RHET0p1to0p5", "RHETgt0p5"]

aietas = range(1, 29)
for aieta in aietas:
    histograms["h_RH_chi2_sum_vs_energy_ieta%d"%(aieta)]   = {"option" : "COLZ", "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "Rec Hit Energy (MAHI) [GeV]", "min" : 0.0, "max" : 10.0}, "X" : {"title" : "MAHI Fit \chi^{2} (tower sum)",      "min" :  0.0, "max" : 100.0}}
    histograms["h_RH_chi2_worst_vs_energy_ieta%d"%(aieta)] = {"option" : "COLZ", "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "Rec Hit Energy (MAHI) [GeV]", "min" : 0.0, "max" : 10.0}, "X" : {"title" : "MAHI Fit \chi^{2} (worst in tower)", "min" :  0.0, "max" : 100.0}}

    histograms["h_ET_ProftoPFA2RH_ieta%d"%(aieta)]  = {"option" : "COLZ", "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Ratio (online/offline)", "min" : -0.005, "max" : 49.995}, "X" : {"title" : "RH (MAHI) Profile", "min" :  0.5, "max" : 717.5}}
    histograms["h_ET_ProftoPFA1pRH_ieta%d"%(aieta)]  = {"option" : "COLZ", "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Ratio (online/offline)", "min" : -0.005, "max" : 49.995}, "X" : {"title" : "RH (MAHI) Profile", "min" :  0.5, "max" : 717.5}}

# Make 2D histograms of TP/RH ET vs ieta
varStrs = ["PFA2vsRH",      "PFA1pvsRH",    "PFA2vsRHcut",      "PFA1pvsRHcut"]
rhStrs  = ["RHET0p0to10p0", "RHETgte10p0",  "RHcutET0p0to10p0", "RHcutETgte10p0"]
tpStrs  = ["PFA2ETgt0p5",   "PFA1pETgt0p5", "PFA2ETgt0p5",      "PFA1pETgt0p5"]
nVtxStrs = ["", "_nVtx0p0to25p0",         "_nVtx25p0to50p0",         "_nVtxgt50p0"]

for varStr, tpStr in zip(varStrs, tpStrs):
    for rhStr in rhStrs:
        if ("cut" not in varStr and "cut" in rhStr) or ("cut" in varStr and "cut" not in rhStr):
            continue

        for nVtxStr in nVtxStrs:
    
            hname = "h_ET_%s_%s_%s%s"%(varStr, rhStr, tpStr, nVtxStr)
            histograms[hname] = {"option" : "COLZ", "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Ratio (online/offline)", "min" : 0.0, "max" : 49.0}, "X" : {"title" : "i\eta", "min" :  -28.5, "max" : 28.5}}
