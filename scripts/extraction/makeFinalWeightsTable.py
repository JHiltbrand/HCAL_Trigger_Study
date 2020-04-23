#!/usr/bin/env python

import argparse
from collections import defaultdict

def writeHeader(outfile):

    outfile.write("\\rotatebox{90}{\n")
    outfile.write("\def\\arraystretch{1.8}\n")
    outfile.write("     \\begin{tabular}{|c|c|c|}\n")
    outfile.write("         \hline\n")
    outfile.write("         \\textbf{\\aieta} & \\textbf{\\PFAonep} & \\textbf{\\PFAtwop}\\\\\\hline\n")

def writeFooter(outfile):

    outfile.write("     \end{tabular}\n")
    outfile.write("\n")
    outfile.write("}\n")

def write2Latex(outfile, m, det):

    ietaLow = -1; ietaHigh = -1
    if   det == "HB":  ietaLow = 1;  ietaHigh = 16
    elif det == "HE1": ietaLow = 17; ietaHigh = 20
    elif det == "HE2": ietaLow = 21; ietaHigh = 28
    else: return 

    for ieta in xrange(1, 29):
        if ieta >= ietaLow and ieta <= ietaHigh:

            PFA1p_theWeight    = float(m["PFA1p_TTbar50"][str(ieta)]["0"]["Weight"])
            PFA1p_theStat     = float(m["PFA1p_TTbar50"][str(ieta)]["0"]["Stat"])

            PFA1p_ttbar25  = float(m["PFA1p_TTbar25"][str(ieta)]["0"]["Weight"])
            PFA1p_ttbar75  = float(m["PFA1p_TTbar75"][str(ieta)]["0"]["Weight"])
            PFA1p_ttbar100 = float(m["PFA1p_TTbar100"][str(ieta)]["0"]["Weight"])

            PFA1p_nugun25  = float(m["PFA1p_NuGun25"][str(ieta)]["0"]["Weight"])
            PFA1p_nugun50  = float(m["PFA1p_NuGun25"][str(ieta)]["0"]["Weight"])
            PFA1p_nugun75  = float(m["PFA1p_NuGun75"][str(ieta)]["0"]["Weight"])
            PFA1p_nugun100 = float(m["PFA1p_NuGun100"][str(ieta)]["0"]["Weight"])

            PFA1p_processSyst = abs(PFA1p_theWeight - PFA1p_nugun50)
            PFA1p_puSyst = abs(max([PFA1p_ttbar25, PFA1p_theWeight, PFA1p_ttbar75, PFA1p_ttbar100])-min([PFA1p_ttbar25, PFA1p_theWeight, PFA1p_ttbar75, PFA1p_ttbar100]))

            PFA2p_theWeight     = float(m["PFA2p_TTbar50"][str(ieta)]["0"]["Weight"])
            PFA2p_theStat     = float(m["PFA2p_TTbar50"][str(ieta)]["0"]["Stat"])

            PFA2p_ttbar25  = float(m["PFA2p_TTbar25"][str(ieta)]["0"]["Weight"])
            PFA2p_ttbar75  = float(m["PFA2p_TTbar75"][str(ieta)]["0"]["Weight"])
            PFA2p_ttbar100 = float(m["PFA2p_TTbar100"][str(ieta)]["0"]["Weight"])

            PFA2p_nugun25  = float(m["PFA2p_NuGun25"][str(ieta)]["0"]["Weight"])
            PFA2p_nugun50  = float(m["PFA2p_NuGun25"][str(ieta)]["0"]["Weight"])
            PFA2p_nugun75  = float(m["PFA2p_NuGun75"][str(ieta)]["0"]["Weight"])
            PFA2p_nugun100 = float(m["PFA2p_NuGun100"][str(ieta)]["0"]["Weight"])

            PFA2p_processSyst = abs(PFA2p_theWeight - PFA2p_nugun50)
            PFA2p_puSyst = abs(max([PFA2p_ttbar25, PFA2p_theWeight, PFA2p_ttbar75, PFA2p_ttbar100])-min([PFA2p_ttbar25, PFA2p_theWeight, PFA2p_ttbar75, PFA2p_ttbar100]))

            outfile.write("         \\textbf{{{:d}}}   & ${:3.2f} \pm {:3.2f}\;\\text{{(stat.)}} \pm {:3.2f}\;\\text{{(syst.)}} \pm {:3.2f}\;\\text{{(syst.)}}$ & ${:3.2f} \pm {:3.2f}\;\\text{{(stat.)}} \pm {:3.2f}\;\\text{{(syst.)}} \pm {:3.2f}\;\\text{{(syst.)}}$ \\\\\\hline".format(ieta, PFA1p_theWeight, PFA1p_theStat, PFA1p_processSyst, PFA1p_puSyst, PFA2p_theWeight, PFA2p_theStat, PFA2p_processSyst, PFA2p_puSyst))

            if ieta == ietaHigh: outfile.write("\\rowcolor{lightgray}\n")
            else:                outfile.write("\n")

    PFA1p_theWeight     = float(m["PFA1p_TTbar50"][det]["0"]["Weight"])
    PFA1p_theStat     = float(m["PFA1p_TTbar50"][str(ieta)]["0"]["Stat"])

    PFA1p_ttbar25  = float(m["PFA1p_TTbar25"][det]["0"]["Weight"]) 
    PFA1p_ttbar75  = float(m["PFA1p_TTbar75"][det]["0"]["Weight"])
    PFA1p_ttbar100 = float(m["PFA1p_TTbar100"][det]["0"]["Weight"])

    PFA1p_nugun25  = float(m["PFA1p_NuGun25"][det]["0"]["Weight"])
    PFA1p_nugun50  = float(m["PFA1p_NuGun25"][det]["0"]["Weight"])
    PFA1p_nugun75  = float(m["PFA1p_NuGun75"][det]["0"]["Weight"])
    PFA1p_nugun100 = float(m["PFA1p_NuGun100"][det]["0"]["Weight"])

    PFA2p_theWeight = float(m["PFA2p_TTbar50"][det]["0"]["Weight"])
    PFA2p_theStat   = float(m["PFA2p_TTbar50"][str(ieta)]["0"]["Stat"])

    PFA2p_ttbar25  = float(m["PFA2p_TTbar25"][det]["0"]["Weight"])
    PFA2p_ttbar75  = float(m["PFA2p_TTbar75"][det]["0"]["Weight"])
    PFA2p_ttbar100 = float(m["PFA2p_TTbar100"][det]["0"]["Weight"])

    PFA2p_nugun25  = float(m["PFA2p_NuGun25"][det]["0"]["Weight"])
    PFA2p_nugun50  = float(m["PFA2p_NuGun25"][det]["0"]["Weight"])
    PFA2p_nugun75  = float(m["PFA2p_NuGun75"][det]["0"]["Weight"])
    PFA2p_nugun100 = float(m["PFA2p_NuGun100"][det]["0"]["Weight"])

    outfile.write("         \\textbf{{{:s}}} & \\textbf{{${:3.2f} \pm {:3.2f}\;\\text{{(stat.)}} \pm {:3.2f}\;\\text{{(syst.)}} \pm {:3.2f}\;\\text{{(syst.)}}$}} & \\textbf{{${:3.2f} \pm {:3.2f}\;\\text{{(stat.)}} \pm {:3.2f}\;\\text{{(syst.)}} \pm {:3.2f}\;\\text{{(syst.)}}$}} \\\\\\hline\n".format(det, PFA1p_theWeight, PFA1p_theStat, PFA1p_processSyst, PFA1p_puSyst, PFA2p_theWeight, PFA2p_theStat, PFA2p_processSyst, PFA2p_puSyst))

def fillMap(infile, m, topKey):

    line = infile.readline()
    
    while line:

        line = line.rstrip()

        if "ieta" not in line:
            line = infile.readline()
            continue

        ieta   = "NULL"
        depth  = "NULL"
        weight = "NULL"
        stat   = "NULL"
        syst   = "NULL"
        rms    = "NULL"

        linesplit = [x.strip() for x in line.split(',')]

        for chunk in linesplit:
            if   "ieta"   in chunk: ieta = chunk.split("ieta")[-1]
            elif "depth"  in chunk: depth = chunk.split("depth")[-1]
            elif "weight" in chunk: weight = chunk.split("weight")[-1]
            elif "stat"   in chunk: stat = chunk.split("stat")[-1]
            elif "syst"   in chunk: syst = chunk.split("syst")[-1]
            elif "rms"    in chunk: rms = chunk.split("rms")[-1]

        m.setdefault(topKey, {}).setdefault(str(ieta), {}).setdefault(str(depth), {}).setdefault("Weight", weight)
        m.setdefault(topKey, {}).setdefault(str(ieta), {}).setdefault(str(depth), {}).setdefault("Stat", stat)

        line = infile.readline()

parser = argparse.ArgumentParser()
args = parser.parse_args()

mapEverything = {}

pfa1p_25PU_ttbar  = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA1p/NoDepth_TTbar_25PU_OOT/weightSummaryMean.txt"
pfa1p_50PU_ttbar  = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA1p/NoDepth_TTbar_50PU_OOT/weightSummaryMean.txt"
pfa1p_75PU_ttbar  = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA1p/NoDepth_TTbar_75PU_OOT/weightSummaryMean.txt"
pfa1p_100PU_ttbar = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA1p/NoDepth_TTbar_100PU_OOT/weightSummaryMean.txt"

pfa1p_25PU_nugun  = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA1p/NoDepth_NuGun_25PU_OOT/weightSummaryMean.txt"
pfa1p_50PU_nugun  = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA1p/NoDepth_NuGun_50PU_OOT/weightSummaryMean.txt"
pfa1p_75PU_nugun  = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA1p/NoDepth_NuGun_75PU_OOT/weightSummaryMean.txt"
pfa1p_100PU_nugun = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA1p/NoDepth_NuGun_100PU_OOT/weightSummaryMean.txt"

pfa2p_25PU_ttbar  = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA2p/NoDepth_TTbar_25PU_OOT/weightSummaryMean.txt"
pfa2p_50PU_ttbar  = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA2p/NoDepth_TTbar_50PU_OOT/weightSummaryMean.txt"
pfa2p_75PU_ttbar  = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA2p/NoDepth_TTbar_75PU_OOT/weightSummaryMean.txt"
pfa2p_100PU_ttbar = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA2p/NoDepth_TTbar_100PU_OOT/weightSummaryMean.txt"

pfa2p_25PU_nugun  = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA2p/NoDepth_NuGun_25PU_OOT/weightSummaryMean.txt"
pfa2p_50PU_nugun  = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA2p/NoDepth_NuGun_50PU_OOT/weightSummaryMean.txt"
pfa2p_75PU_nugun  = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA2p/NoDepth_NuGun_75PU_OOT/weightSummaryMean.txt"
pfa2p_100PU_nugun = "/uscms/home/jhiltb/nobackup/HCAL_Trigger_Study/plots/Weights/PFA2p/NoDepth_NuGun_100PU_OOT/weightSummaryMean.txt"

pfa1p_tt25  = open(pfa1p_25PU_ttbar, "r")
pfa1p_tt50  = open(pfa1p_50PU_ttbar, "r")
pfa1p_tt75  = open(pfa1p_75PU_ttbar, "r")
pfa1p_tt100 = open(pfa1p_100PU_ttbar, "r")

pfa1p_nu25  = open(pfa1p_25PU_nugun, "r")
pfa1p_nu50  = open(pfa1p_50PU_nugun, "r")
pfa1p_nu75  = open(pfa1p_75PU_nugun, "r")
pfa1p_nu100 = open(pfa1p_100PU_nugun, "r")

pfa2p_tt25  = open(pfa2p_25PU_ttbar, "r")
pfa2p_tt50  = open(pfa2p_50PU_ttbar, "r")
pfa2p_tt75  = open(pfa2p_75PU_ttbar, "r")
pfa2p_tt100 = open(pfa2p_100PU_ttbar, "r")

pfa2p_nu25  = open(pfa2p_25PU_nugun, "r")
pfa2p_nu50  = open(pfa2p_50PU_nugun, "r")
pfa2p_nu75  = open(pfa2p_75PU_nugun, "r")
pfa2p_nu100 = open(pfa2p_100PU_nugun, "r")

fillMap(pfa1p_tt25,  mapEverything, "PFA1p_TTbar25")
fillMap(pfa1p_tt50,  mapEverything, "PFA1p_TTbar50")
fillMap(pfa1p_tt75,  mapEverything, "PFA1p_TTbar75")
fillMap(pfa1p_tt100, mapEverything, "PFA1p_TTbar100")

fillMap(pfa1p_nu25,  mapEverything, "PFA1p_NuGun25")
fillMap(pfa1p_nu50,  mapEverything, "PFA1p_NuGun50")
fillMap(pfa1p_nu75,  mapEverything, "PFA1p_NuGun75")
fillMap(pfa1p_nu100, mapEverything, "PFA1p_NuGun100")

fillMap(pfa2p_tt25,  mapEverything, "PFA2p_TTbar25")
fillMap(pfa2p_tt50,  mapEverything, "PFA2p_TTbar50")
fillMap(pfa2p_tt75,  mapEverything, "PFA2p_TTbar75")
fillMap(pfa2p_tt100, mapEverything, "PFA2p_TTbar100")

fillMap(pfa2p_nu25,  mapEverything, "PFA2p_NuGun25")
fillMap(pfa2p_nu50,  mapEverything, "PFA2p_NuGun50")
fillMap(pfa2p_nu75,  mapEverything, "PFA2p_NuGun75")
fillMap(pfa2p_nu100, mapEverything, "PFA2p_NuGun100")

outfileHB = open("FinalWeightsHB.tex", "w")
outfileHE = open("FinalWeightsHE.tex", "w")

writeHeader(outfileHB); writeHeader(outfileHE)
write2Latex(outfileHB, mapEverything, "HB")
write2Latex(outfileHE, mapEverything, "HE1")
write2Latex(outfileHE, mapEverything, "HE2")
writeFooter(outfileHB); writeFooter(outfileHE)
