#! /bin/env/python
import ROOT
import numpy as np

def getShape(string):

    if   "PFA1p" in string: return 22
    elif "PFA2"  in string:
        if "uncorr" in string: return 4
        else: return 8

    return 8

def getColor(string):

    if   "PFA1p" in string:
        if   "nVtx"       not in string: return ROOT.kRed
        elif "nVtx0p0to25p0"  in string: return ROOT.TColor.GetColor("#bdd7e7") 
        elif "nVtx25p0to50p0" in string: return ROOT.TColor.GetColor("#6baed6") 
        elif "nVtxgt50p0"     in string: return ROOT.TColor.GetColor("#08519c") 
    elif "PFA2" in string:
        if   "nVtx"       not in string: return ROOT.kBlack
        elif "nVtx0p0to25p0"  in string: return ROOT.TColor.GetColor("#bae4b3") 
        elif "nVtx25p0to50p0" in string: return ROOT.TColor.GetColor("#74c476") 
        elif "nVtxgt50p0"     in string: return ROOT.TColor.GetColor("#006d2c") 
   
histograms = {}

variables = ["PFA2vsRH",    "PFA1pvsRH",    "PFA2vsRHcut", "PFA1pvsRHcut", "PFA2vsRHraw", "PFA1pvsRHraw"]
tpMins    = ["PFA2ETgt0p5", "PFA1pETgt0p5", "PFA2ETgt0p5", "PFA1pETgt0p5", "PFA2ETgt0p5", "PFA1pETgt0p5"]
rhRanges  = ["RHET0p0to10p0", "RHETgte10p0"]
nVtxs     = ["", "_nVtx0p0to25p0", "_nVtx25p0to50p0", "_nVtxgt50p0"]

for var, tpMin in zip(variables, tpMins):
    for rhRange in rhRanges:
        newRHstr = rhRange
        if "cut" in var:
            newRHstr = rhRange.replace("RH", "RHcut")
        elif "raw" in var:
            newRHstr = rhRange.replace("RH", "RHraw")

        for nVtx in nVtxs:
            histograms["h_ET_%s_%s_%s%s"%(var, newRHstr, tpMin, nVtx)] = {"mstyle" : getShape(var), "msize" : 2, "color" : getColor(var+nVtx), "draw2D" : False}

groups = {}

groups["h_ET_scale_RHET0p0to10p0"] = {"hists" : ["h_ET_PFA2vsRH_RHET0p0to10p0_PFA2ETgt0p5_nVtx0p0to25p0",  "h_ET_PFA2vsRH_RHET0p0to10p0_PFA2ETgt0p5_nVtx25p0to50p0",  "h_ET_PFA2vsRH_RHET0p0to10p0_PFA2ETgt0p5_nVtxgt50p0",
                                                "h_ET_PFA1pvsRH_RHET0p0to10p0_PFA1pETgt0p5_nVtx0p0to25p0", "h_ET_PFA1pvsRH_RHET0p0to10p0_PFA1pETgt0p5_nVtx25p0to50p0", "h_ET_PFA1pvsRH_RHET0p0to10p0_PFA1pETgt0p5_nVtxgt50p0"],
                                                "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Scale #mu(online/offline)", "min" : 0.0, "max" : 3.0}, "X" : {"title" : "i\eta", "min" :  -28.5, "max" : 28.5}
                                     }

groups["h_ET_scale_RHETgte10p0"] = {"hists" : ["h_ET_PFA2vsRH_RHETgte10p0_PFA2ETgt0p5_nVtx0p0to25p0",  "h_ET_PFA2vsRH_RHETgte10p0_PFA2ETgt0p5_nVtx25p0to50p0",  "h_ET_PFA2vsRH_RHETgte10p0_PFA2ETgt0p5_nVtxgt50p0",
                                               "h_ET_PFA1pvsRH_RHETgte10p0_PFA1pETgt0p5_nVtx0p0to25p0", "h_ET_PFA1pvsRH_RHETgte10p0_PFA1pETgt0p5_nVtx25p0to50p0", "h_ET_PFA1pvsRH_RHETgte10p0_PFA1pETgt0p5_nVtxgt50p0"],
                                               "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Scale #mu(online/offline)", "min" : 0.0, "max" : 3.0}, "X" : {"title" : "i\eta", "min" :  -28.5, "max" : 28.5}
                                   }

groups["h_ET_res_RHET0p0to10p0"] = {"hists" : ["h_ET_PFA2vsRH_RHET0p0to10p0_PFA2ETgt0p5_nVtx0p0to25p0",  "h_ET_PFA2vsRH_RHET0p0to10p0_PFA2ETgt0p5_nVtx25p0to50p0",  "h_ET_PFA2vsRH_RHET0p0to10p0_PFA2ETgt0p5_nVtxgt50p0",
                                              "h_ET_PFA1pvsRH_RHET0p0to10p0_PFA1pETgt0p5_nVtx0p0to25p0", "h_ET_PFA1pvsRH_RHET0p0to10p0_PFA1pETgt0p5_nVtx25p0to50p0", "h_ET_PFA1pvsRH_RHET0p0to10p0_PFA1pETgt0p5_nVtxgt50p0"],
                                              "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Res. #frac{#sigma}{#mu}(online/offline)", "min" : 0.0, "max" : 1.3}, "X" : {"title" : "i\eta", "min" :  -28.5, "max" : 28.5}
                                   }

groups["h_ET_res_RHETgte10p0"] = {"hists" : ["h_ET_PFA2vsRH_RHETgte10p0_PFA2ETgt0p5_nVtx0p0to25p0",  "h_ET_PFA2vsRH_RHETgte10p0_PFA2ETgt0p5_nVtx25p0to50p0",  "h_ET_PFA2vsRH_RHETgte10p0_PFA2ETgt0p5_nVtxgt50p0",
                                            "h_ET_PFA1pvsRH_RHETgte10p0_PFA1pETgt0p5_nVtx0p0to25p0", "h_ET_PFA1pvsRH_RHETgte10p0_PFA1pETgt0p5_nVtx25p0to50p0", "h_ET_PFA1pvsRH_RHETgte10p0_PFA1pETgt0p5_nVtxgt50p0"],
                                            "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Res. #frac{#sigma}{#mu}(online/offline)", "min" : 0.0, "max" : 0.3}, "X" : {"title" : "i\eta", "min" :  -28.5, "max" : 28.5}
                                 }

groups["h_ET_scale_RHcutET0p0to10p0"] = {"hists" : ["h_ET_PFA2vsRHcut_RHcutET0p0to10p0_PFA2ETgt0p5_nVtx0p0to25p0",  "h_ET_PFA2vsRHcut_RHcutET0p0to10p0_PFA2ETgt0p5_nVtx25p0to50p0",  "h_ET_PFA2vsRHcut_RHcutET0p0to10p0_PFA2ETgt0p5_nVtxgt50p0",
                                                "h_ET_PFA1pvsRHcut_RHcutET0p0to10p0_PFA1pETgt0p5_nVtx0p0to25p0", "h_ET_PFA1pvsRHcut_RHcutET0p0to10p0_PFA1pETgt0p5_nVtx25p0to50p0", "h_ET_PFA1pvsRHcut_RHcutET0p0to10p0_PFA1pETgt0p5_nVtxgt50p0"],
                                                "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Scale #mu(online/offline)", "min" : 0.0, "max" : 3.0}, "X" : {"title" : "i\eta", "min" :  -28.5, "max" : 28.5}
                                     }

groups["h_ET_scale_RHcutETgte10p0"] = {"hists" : ["h_ET_PFA2vsRHcut_RHcutETgte10p0_PFA2ETgt0p5_nVtx0p0to25p0",  "h_ET_PFA2vsRHcut_RHcutETgte10p0_PFA2ETgt0p5_nVtx25p0to50p0",  "h_ET_PFA2vsRHcut_RHcutETgte10p0_PFA2ETgt0p5_nVtxgt50p0",
                                               "h_ET_PFA1pvsRHcut_RHcutETgte10p0_PFA1pETgt0p5_nVtx0p0to25p0", "h_ET_PFA1pvsRHcut_RHcutETgte10p0_PFA1pETgt0p5_nVtx25p0to50p0", "h_ET_PFA1pvsRHcut_RHcutETgte10p0_PFA1pETgt0p5_nVtxgt50p0"],
                                               "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Scale #mu(online/offline)", "min" : 0.0, "max" : 3.0}, "X" : {"title" : "i\eta", "min" :  -28.5, "max" : 28.5}
                                   }

groups["h_ET_res_RHcutET0p0to10p0"] = {"hists" : ["h_ET_PFA2vsRHcut_RHcutET0p0to10p0_PFA2ETgt0p5_nVtx0p0to25p0",  "h_ET_PFA2vsRHcut_RHcutET0p0to10p0_PFA2ETgt0p5_nVtx25p0to50p0",  "h_ET_PFA2vsRHcut_RHcutET0p0to10p0_PFA2ETgt0p5_nVtxgt50p0",
                                              "h_ET_PFA1pvsRHcut_RHcutET0p0to10p0_PFA1pETgt0p5_nVtx0p0to25p0", "h_ET_PFA1pvsRHcut_RHcutET0p0to10p0_PFA1pETgt0p5_nVtx25p0to50p0", "h_ET_PFA1pvsRHcut_RHcutET0p0to10p0_PFA1pETgt0p5_nVtxgt50p0"],
                                              "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Res. #frac{#sigma}{#mu}(online/offline)", "min" : 0.0, "max" : 1.3}, "X" : {"title" : "i\eta", "min" :  -28.5, "max" : 28.5}
                                   }

groups["h_ET_res_RHcutETgte10p0"] = {"hists" : ["h_ET_PFA2vsRHcut_RHcutETgte10p0_PFA2ETgt0p5_nVtx0p0to25p0",  "h_ET_PFA2vsRHcut_RHcutETgte10p0_PFA2ETgt0p5_nVtx25p0to50p0",  "h_ET_PFA2vsRHcut_RHcutETgte10p0_PFA2ETgt0p5_nVtxgt50p0",
                                            "h_ET_PFA1pvsRHcut_RHcutETgte10p0_PFA1pETgt0p5_nVtx0p0to25p0", "h_ET_PFA1pvsRHcut_RHcutETgte10p0_PFA1pETgt0p5_nVtx25p0to50p0", "h_ET_PFA1pvsRHcut_RHcutETgte10p0_PFA1pETgt0p5_nVtxgt50p0"],
                                            "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Res. #frac{#sigma}{#mu}(online/offline)", "min" : 0.0, "max" : 0.3}, "X" : {"title" : "i\eta", "min" :  -28.5, "max" : 28.5}
                                 }

groups["h_ET_scale_RHrawET0p0to10p0"] = {"hists" : ["h_ET_PFA2vsRHraw_RHrawET0p0to10p0_PFA2ETgt0p5_nVtx0p0to25p0",  "h_ET_PFA2vsRHraw_RHrawET0p0to10p0_PFA2ETgt0p5_nVtx25p0to50p0",  "h_ET_PFA2vsRHraw_RHrawET0p0to10p0_PFA2ETgt0p5_nVtxgt50p0",
                                                "h_ET_PFA1pvsRHraw_RHrawET0p0to10p0_PFA1pETgt0p5_nVtx0p0to25p0", "h_ET_PFA1pvsRHraw_RHrawET0p0to10p0_PFA1pETgt0p5_nVtx25p0to50p0", "h_ET_PFA1pvsRHraw_RHrawET0p0to10p0_PFA1pETgt0p5_nVtxgt50p0"],
                                                "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Scale #mu(online/offline)", "min" : 0.0, "max" : 3.0}, "X" : {"title" : "i\eta", "min" :  -28.5, "max" : 28.5}
                                     }

groups["h_ET_scale_RHrawETgte10p0"] = {"hists" : ["h_ET_PFA2vsRHraw_RHrawETgte10p0_PFA2ETgt0p5_nVtx0p0to25p0",  "h_ET_PFA2vsRHraw_RHrawETgte10p0_PFA2ETgt0p5_nVtx25p0to50p0",  "h_ET_PFA2vsRHraw_RHrawETgte10p0_PFA2ETgt0p5_nVtxgt50p0",
                                               "h_ET_PFA1pvsRHraw_RHrawETgte10p0_PFA1pETgt0p5_nVtx0p0to25p0", "h_ET_PFA1pvsRHraw_RHrawETgte10p0_PFA1pETgt0p5_nVtx25p0to50p0", "h_ET_PFA1pvsRHraw_RHrawETgte10p0_PFA1pETgt0p5_nVtxgt50p0"],
                                               "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Scale #mu(online/offline)", "min" : 0.0, "max" : 3.0}, "X" : {"title" : "i\eta", "min" :  -28.5, "max" : 28.5}
                                   }

groups["h_ET_res_RHrawET0p0to10p0"] = {"hists" : ["h_ET_PFA2vsRHraw_RHrawET0p0to10p0_PFA2ETgt0p5_nVtx0p0to25p0",  "h_ET_PFA2vsRHraw_RHrawET0p0to10p0_PFA2ETgt0p5_nVtx25p0to50p0",  "h_ET_PFA2vsRHraw_RHrawET0p0to10p0_PFA2ETgt0p5_nVtxgt50p0",
                                              "h_ET_PFA1pvsRHraw_RHrawET0p0to10p0_PFA1pETgt0p5_nVtx0p0to25p0", "h_ET_PFA1pvsRHraw_RHrawET0p0to10p0_PFA1pETgt0p5_nVtx25p0to50p0", "h_ET_PFA1pvsRHraw_RHrawET0p0to10p0_PFA1pETgt0p5_nVtxgt50p0"],
                                              "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Res. #frac{#sigma}{#mu}(online/offline)", "min" : 0.0, "max" : 1.3}, "X" : {"title" : "i\eta", "min" :  -28.5, "max" : 28.5}
                                   }

groups["h_ET_res_RHrawETgte10p0"] = {"hists" : ["h_ET_PFA2vsRHraw_RHrawETgte10p0_PFA2ETgt0p5_nVtx0p0to25p0",  "h_ET_PFA2vsRHraw_RHrawETgte10p0_PFA2ETgt0p5_nVtx25p0to50p0",  "h_ET_PFA2vsRHraw_RHrawETgte10p0_PFA2ETgt0p5_nVtxgt50p0",
                                            "h_ET_PFA1pvsRHraw_RHrawETgte10p0_PFA1pETgt0p5_nVtx0p0to25p0", "h_ET_PFA1pvsRHraw_RHrawETgte10p0_PFA1pETgt0p5_nVtx25p0to50p0", "h_ET_PFA1pvsRHraw_RHrawETgte10p0_PFA1pETgt0p5_nVtxgt50p0"],
                                            "logX" : False, "logY" : False, "logZ" : True, "Y" : {"title" : "E_{T} Res. #frac{#sigma}{#mu}(online/offline)", "min" : 0.0, "max" : 0.3}, "X" : {"title" : "i\eta", "min" :  -28.5, "max" : 28.5}
                                 }
