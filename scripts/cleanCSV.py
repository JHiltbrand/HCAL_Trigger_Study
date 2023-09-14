#!/bin/env/python

f = open("event_stats_HB.txt", "r")
g = open("event_stats_HB12.txt", "w")

lines = f.readlines()

for line in lines:

    chunks = line.rstrip("\n").split(",")

    ieta = int(chunks[10])

    pfa1pET = float(chunks[2])
    pfa2ET = float(chunks[3])
    TPRH  = float(chunks[0])
    iphi = float(chunks[-1])

    #if pfa1pET >= 5.0 or pfa2ET >= 5.0:
    #    g.write(line)

    if (pfa1pET > 0.5 or pfa2ET > 0.5) and ieta == 2:
        if TPRH > 2:
            g.write(line) 
        elif iphi % 4 == 0:
            g.write(line)
