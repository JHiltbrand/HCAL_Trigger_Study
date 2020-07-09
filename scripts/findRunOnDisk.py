import sys, os, subprocess
from multiprocessing import Pool

ONTAPE = ["MSS", "Export", "Buffer"]

def blocks4Run(run, dataset):

    proc = subprocess.Popen(['dasgoclient', '--query=block dataset=%s run=%s'%(dataset,run)], stdout=subprocess.PIPE)
    blocks = proc.stdout.readlines()
    blocks = [block.rstrip() for block in blocks]
    return blocks

def files4Block(block):

    proc = subprocess.Popen(['dasgoclient', '--query=file block=%s'%(block)], stdout=subprocess.PIPE)
    files = proc.stdout.readlines()
    files = [afile.rstrip() for afile in files]
    return files

def files4Run(dataset,run):

    proc = subprocess.Popen(['dasgoclient', '--query=file dataset=%s run=%s'%(dataset,run)], stdout=subprocess.PIPE)
    files = proc.stdout.readlines()
    files = [afile.rstrip() for afile in files]
    return files

def lumis4File(afile):

    lumiList = []
    proc = subprocess.Popen(['dasgoclient', '--query=lumi file=%s'%(afile)], stdout=subprocess.PIPE)
    lumis = proc.stdout.readlines()
    for lumi in lumis:
        lumiList += lumi.rstrip().strip('[').strip(']').split(',')
    lumiList = [int(lumi) for lumi in lumiList]
    return lumiList

def blockOnlyOnTape(block):

    proc = subprocess.Popen(['dasgoclient', '--query=site block=%s'%(block)], stdout=subprocess.PIPE)
    sites = proc.stdout.readlines()
    sites = [site.rstrip() for site in sites]

    onTape = True 
    for site in sites:
        siteIsTape = False
        for keyword in ONTAPE:
            siteIsTape |= (keyword in site)
        onTape &= siteIsTape

    return onTape 

def fileOnlyOnTape(aFile):

    proc = subprocess.Popen(['dasgoclient', '--query=site file=%s'%(aFile)], stdout=subprocess.PIPE)
    sites = proc.stdout.readlines()
    sites = [site.rstrip() for site in sites]
  
    onTape = True 
    for site in sites:
        siteIsTape = False
        for keyword in ONTAPE:
            siteIsTape |= (keyword in site)
        onTape &= siteIsTape

    return onTape 

def analysis(run):

    blocks = blocks4Run(run, dataset)

    for block in blocks:

        if blockOnlyOnTape(block):
            print "Run %s is partially on tape..."%(run)
            return 
            
    files = files4Run(dataset, run)

    for aFile in files:

        if fileOnlyOnTape(aFile):
            return 

    print "\n\n"
    print "Run \"%s\" is entirely on disk!\n\n"%(run)

def lumiAnalysis(run):

    files = files4Run(dataset, run)

    for aFile in files:

        if fileOnlyOnTape(aFile): continue

        lumis = lumis4File(aFile)

        for lumi in lumis:
            if lumi >= 501 and lumi <= 819:
                print "File '%s' contains lumis "%(aFile)
                print lumis
                break

if __name__ == "__main__":

    dataset = str(sys.argv[1])

    lumiAnalysis(324021)

    #proc = subprocess.Popen(['dasgoclient', '--query=run dataset=%s'%(dataset)], stdout=subprocess.PIPE)
    #runs = proc.stdout.readlines()
    #runs = [run.rstrip() for run in runs]

    #p = Pool(24) 

    #p.map(analysis, runs)
