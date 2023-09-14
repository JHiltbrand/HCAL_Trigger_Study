#! /bin/env/python
histograms = {}

varStrs  = ["PFA2RHvsNvtx",                       "PFA1pRHvsNvtx",                       "PFA2RHcutvsNvtx",                           "PFA1pRHcutvsNvtx"]
varSels  = ["TP_energy_PFA2/RH_energy_MAHI:nVtx", "TP_energy_PFA1p/RH_energy_MAHI:nVtx", "TP_energy_PFA2/RH_energy_MAHI_cutoff:nVtx", "TP_energy_PFA1p/RH_energy_MAHI_cutoff:nVtx"]

nVtxStrs = ["", "_nVtx0p0to25p0",         "_nVtx25p0to50p0",         "_nVtxgt50p0"]
nVtxSels = ["", "&&nVtx>0.0&&nVtx<=25.0", "&&nVtx>25.0&&nVtx<=50.0", "&&nVtx>50.0"]

rhStrs   = ["RHET0p0to10p0",                           "RHETgte10p0",          "RHcutET0p0to10p0",                                      "RHcutETgte10p0"]
rhSels   = ["RH_energy_MAHI>0.0&&RH_energy_MAHI<10.0", "RH_energy_MAHI>=10.0", "RH_energy_MAHI_cutoff>0.0&&RH_energy_MAHI_cutoff<10.0", "RH_energy_MAHI_cutoff>=10.0"]

tpStrs  = ["PFA2ETgt0p5",        "PFA1pETgt0p5",        "PFA2ETgt0p5",        "PFA1pETgt0p5"]
tpSels  = ["TP_energy_PFA2>0.5", "TP_energy_PFA1p>0.5", "TP_energy_PFA2>0.5", "TP_energy_PFA1p>0.5"]

# Make 2D histograms of RH chi2 vs energy
aietas = range(1, 29)
for aieta in aietas:

    for nVtxStr, nVtxSel in zip(nVtxStrs, nVtxSels):

        histograms["h_RH_chi2_sum_vs_energy%s_ieta%d"%(nVtxStr, aieta)]   = {"weight" : "1.0", "selection" : "abs(ieta)==%d&&RH_exist_MAHI==1%s"%(aieta, nVtxSel), "variable" : "RH_energy_MAHI:RH_chi2_sum",   "xbins" : 100, "xmin" : 0,   "xmax" : 100,  "ybins" : 100, "ymin" : 0, "ymax" : 10}
        histograms["h_RH_chi2_worst_vs_energy%s_ieta%d"%(nVtxStr, aieta)] = {"weight" : "1.0", "selection" : "abs(ieta)==%d&&RH_exist_MAHI==1%s"%(aieta, nVtxSel), "variable" : "RH_energy_MAHI:RH_chi2_worst", "xbins" : 100, "xmin" : 0,   "xmax" : 100,  "ybins" : 100, "ymin" : 0, "ymax" : 10}

        histograms["h_ET_ProftoPFA1pRH%s_ieta%d"%(nVtxStr, aieta)] = {"weight" : "1.0", "selection" : "abs(ieta)==%d%s"%(aieta, nVtxSel), "variable" : "TP_energy_PFA1p/RH_energy_MAHI:RH_depth_profile", "ybins" : 500, "ymin" : -0.005, "ymax" : 49.995, "xbins" : 717, "xmin" : 0.5, "xmax" : 717.5}
        histograms["h_ET_ProftoPFA2RH%s_ieta%d"%(nVtxStr, aieta)]  = {"weight" : "1.0", "selection" : "abs(ieta)==%d%s"%(aieta, nVtxSel), "variable" : "TP_energy_PFA2/RH_energy_MAHI:RH_depth_profile",  "ybins" : 500, "ymin" : -0.005, "ymax" : 49.995, "xbins" : 717, "xmin" : 0.5, "xmax" : 717.5}

    if aieta == 28:
        for varStr, varSel, tpStr, tpSel in zip(varStrs, varSels, tpStrs, tpSels):
            for rhStr, rhSel in zip(rhStrs, rhSels):
                if ("cut" not in varStr and "cut" in rhStr) or ("cut" in varStr and "cut" not in rhStr):
                    continue

                histograms["h_%s_%s_%s_ieta%d"%(varStr, rhStr, tpStr, aieta)] = {"weight" : "1.0", "selection" : "abs(ieta)==%d&&%s&&%s"%(aieta, rhSel, tpSel), "variable" : varSel, "ybins" : 500, "ymin" : -0.005, "ymax" : 49.995, "xbins" : 101, "xmin" : -0.5, "xmax" : 100.5}

# Make 2D histograms of TP/RH ET vs ieta
varStrs  = ["PFA2vsRH",                           "PFA1pvsRH",                           "PFA2vsRHcut",                               "PFA1pvsRHcut",                               "PFA2vsRHraw",                       "PFA1pvsRHraw"]
varSels  = ["TP_energy_PFA2/RH_energy_MAHI:ieta", "TP_energy_PFA1p/RH_energy_MAHI:ieta", "TP_energy_PFA2/RH_energy_MAHI_cutoff:ieta", "TP_energy_PFA1p/RH_energy_MAHI_cutoff:ieta", "TP_energy_PFA2/RH_energy_raw:ieta", "TP_energy_PFA1p/RH_energy_raw:ieta"]

rhStrs   = ["RHET0p0to10p0",                           "RHETgte10p0",          "RHcutET0p0to10p0",                                      "RHcutETgte10p0",              "RHrawET0p0to10p0",                      "RHrawETgte10p0"]
rhSels   = ["RH_energy_MAHI>0.0&&RH_energy_MAHI<10.0", "RH_energy_MAHI>=10.0", "RH_energy_MAHI_cutoff>0.0&&RH_energy_MAHI_cutoff<10.0", "RH_energy_MAHI_cutoff>=10.0", "RH_energy_raw>0.0&&RH_energy_raw<10.0", "RH_energy_raw>=10.0"]

tpStrs  = ["PFA2ETgt0p5",        "PFA1pETgt0p5",        "PFA2ETgt0p5",        "PFA1pETgt0p5",        "PFA2ETgt0p5",        "PFA1pETgt0p5"]
tpSels  = ["TP_energy_PFA2>0.5", "TP_energy_PFA1p>0.5", "TP_energy_PFA2>0.5", "TP_energy_PFA1p>0.5", "TP_energy_PFA2>0.5", "TP_energy_PFA1p>0.5"]

for varStr, varSel, tpStr, tpSel in zip(varStrs, varSels, tpStrs, tpSels):
    for rhStr, rhSel in zip(rhStrs, rhSels):
        if ("cut" not in varStr and "cut" in rhStr) or ("cut" in varStr and "cut" not in rhStr):
            continue

        for nVtxStr, nVtxSel in zip(nVtxStrs, nVtxSels):
    
            hname = "h_ET_%s_%s_%s%s"%(varStr, rhStr, tpStr, nVtxStr)
            hsel  = "%s&&%s%s"%(tpSel, rhSel, nVtxSel)

            histograms[hname] = {"weight" : "1.0", "selection" : hsel, "variable" : varSel, "xbins" : 57, "xmin" : -28.5, "xmax" : 28.5,  "ybins" : 5000, "ymin" : -0.005, "ymax" : 49.995}
