import subprocess

# If the site name contains any of these strings
# then the corresponding file/dataset is on tape
ONTAPE = ["MSS", "Export", "Buffer"]

# Given a dataset and a run of interest, get a list
# of blocks that compose that run
def blocks4Run(run, dataset):

    proc = subprocess.Popen(['dasgoclient', '--query=block dataset=%s run=%s'%(dataset,run)], stdout=subprocess.PIPE)
    blocks = proc.stdout.readlines()
    blocks = [block.rstrip() for block in blocks]
    return blocks

# Given a single block, get the list of files that
# make up that block
def files4Block(block):

    proc = subprocess.Popen(['dasgoclient', '--query=file block=%s'%(block)], stdout=subprocess.PIPE)
    files = proc.stdout.readlines()
    files = [afile.rstrip() for afile in files]
    return files

# Given a dataset and a run of interest, get
# the list of files that contain the events 
# for the run
def files4Run(dataset,run):

    proc = subprocess.Popen(['dasgoclient', '--query=file dataset=%s run=%s'%(dataset,run)], stdout=subprocess.PIPE)
    files = proc.stdout.readlines()
    files = [afile.rstrip() for afile in files]
    return files

# Given a file (full path) return a list of lumis
# present in that file
def lumis4File(afile):

    lumiList = []
    proc = subprocess.Popen(['dasgoclient', '--query=lumi file=%s'%(afile)], stdout=subprocess.PIPE)
    lumis = proc.stdout.readlines()
    for lumi in lumis:
        lumiList += lumi.rstrip().strip('[').strip(']').split(',')
    lumiList = [int(lumi) for lumi in lumiList]
    return lumiList

# For a given block, determine if it is on tape or not
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

# For a given file, determine if it is on tape or not
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
