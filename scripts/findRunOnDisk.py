import argparse
from multiprocessing import Pool
from dasgoHelpers import *

# Function that gets called in parallel from main
# when searching multiple runs to see which are on
# tape
def analysis(run):

    # First get the blocks for the run
    blocks = blocks4Run(run, dataset)

    # If any block is only on tape, then run is useless...
    for block in blocks:

        if blockOnlyOnTape(block):
            print "Run %s is partially on tape..."%(run)
            return 
            
    # Although a block may not be _only_ on tape,
    # some of its files may be, so check each one
    files = files4Run(dataset, run)

    # If a single file is only on tape, then consider
    # the run useless...
    for aFile in files:

        if fileOnlyOnTape(aFile): return 

    print "Run \"%s\" is entirely on disk!"%(run)

# A function to print each file for a run
# along with the lumis contained in the file
def lumiAnalysis(run):

    files = files4Run(dataset, run)

    for aFile in files:

        # Always skip tape-only stuff...
        if fileOnlyOnTape(aFile): continue

        lumis = lumis4File(aFile)

        for lumi in lumis:
            print "File '%s' contains lumis "%(aFile)
            print lumis
            break

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--run"          , dest="run"          , help="Which run to analyze"     , type=str, default="1")
    parser.add_argument("--dataset"      , dest="dataset"      , help="Which dataset to analyze" , type=str, default="NULL")
    parser.add_argument("--findRunOnDisk", dest="findRunOnDisk", help="Mode for finding runs"    , default=False, action="store_true")
    args = parser.parse_args()

    run           = args.run
    dataset       = args.dataset
    findRunOnDisk = args.findRunOnDisk

    if dataset == "NULL":
        print "No dataset has been provided! Exiting..."
        quit()

    if findRunOnDisk:

        proc = subprocess.Popen(['dasgoclient', '--query=run dataset=%s'%(dataset)], stdout=subprocess.PIPE)
        runs = proc.stdout.readlines()
        runs = [run.rstrip() for run in runs]

        p = Pool(24) 

        p.map(analysis, runs)

    else:
        lumiAnalysis(run)
