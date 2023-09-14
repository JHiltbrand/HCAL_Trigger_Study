import subprocess

# If the site name contains any of these strings
# then the corresponding file/dataset is on tape
ONTAPE = ["MSS", "Export", "Buffer", "Tape"]

# Add the redirector to the files in the list
def addRedirectors(files, redirector):

    returnFiles = []
    for file in files: 
        if "root://" not in file:
            returnFiles.append(file.replace("/store/", "%s//store/"%(redirector)))
        else:
            returnFiles.append(file)

    return returnFiles 

def addRedirector(file, redirector):

    if "root://" in file:
        return file
    else:
        returnFile = file.replace("/store/", "%s//store/"%(redirector))
        return returnFile 

# From list of numbers make 2-tuple lists for continuous ranges
def rangesFromList(alist):

    tempList = []
    for i in alist: tempList.append(int(i))

    tempList.sort()

    firstRange = 0; lastRange = 0; returnList = []
    for ilumi in xrange(len(tempList)):
        
        if ilumi == 0: firstRange = tempList[ilumi]
            
        elif tempList[ilumi] - tempList[ilumi-1] > 1:
            lastRange = tempList[ilumi-1]
            returnList.append([firstRange, lastRange])
            firstRange = tempList[ilumi]

            if ilumi == len(tempList) - 1: returnList.append([firstRange, firstRange])

        elif ilumi == len(tempList) - 1: returnList.append([firstRange, tempList[ilumi]])
            
    return returnList

def files4Dataset(dataset):

    # Construct dasgoclient call and make it, reading back the standard out to get the list of files
    proc = subprocess.Popen(['dasgoclient', '--query=file dataset=%s'%(dataset)], stdout=subprocess.PIPE)
    files = proc.stdout.readlines();  files = [file.rstrip() for file in files]

    # Prep the files for insertion into cmsRun config by adding the global redirector
    returnFiles = []
    for file in files:
        if not fileOnlyOnTape(file):
            returnFiles.append(file.replace("/store/", "root://cms-xrd-global.cern.ch///store/"))

    return returnFiles

def getParents4File(file):

    # Find the parent files (more than one!) for each file in the dataset
    proc = subprocess.Popen(['dasgoclient', '--query=parent file=%s'%("/"+file.split("///")[-1])], stdout=subprocess.PIPE)
    parents = proc.stdout.readlines();  parents = [parent.rstrip() for parent in parents]

    return parents

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

    returnList = rangesFromList(lumiList)

    return returnList

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
  
    onlyOnTape = True 
    for site in sites:
        siteIsTape = any(keyword in site for keyword in ONTAPE)
        onlyOnTape &= siteIsTape

    return onlyOnTape 
