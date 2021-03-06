#!/usr/bin/env python

import argparse

# An example call would be:

# python makePFAinputs.py --inputFile pfa_output.txt

# The output text file would be read into ISE

parser = argparse.ArgumentParser()
parser.add_argument("--inputFile", dest="inputFile", help="Path to input file", type=str, required=True)
args = parser.parse_args()

# Input text file from CMSSW printout...
pfa1pf  = open("pfa1p_input.txt", "w")

lin_sum_energy_text = "lin_sum_energy="
tp_calc_text        = "tp_calc_exp="
wait_6              = "#6;"
wait_30             = "#30;"
valid               = "valid_in=1;"
not_valid           = "valid_in=0;"
task                = "check_tp"

stop = 1000000

lin_sum_energy_pre = 0
lin_sum_energy_now = 0
with open(args.inputFile, "r") as f:

    line = f.readline()
    
    count = 0
    while line:

        if count == stop: break

        line = line.rstrip()

        linesplit = [x.strip() for x in line.split(',')]

        aieta = abs(int(linesplit[0]))

        if aieta < 17: continue

        weight         = int(linesplit[1])
        lin_sum_energy = int(linesplit[2])
        tp_calc_exp    = int(linesplit[3])
        tp_calc_peak   = int(linesplit[4])

        pfa1pf.write(task + "(%s, %s, %s);\n"%(str(lin_sum_energy), str(weight), str(tp_calc_exp)))

        count += 1
        line = f.readline()

pfa1pf.close()
