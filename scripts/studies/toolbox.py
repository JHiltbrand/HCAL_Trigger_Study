import ROOT, random, string

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat("")
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()
ROOT.TH3.SetDefaultSumw2()

def randomString():
    randStr = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
    return randStr

# In ROOT's infinite wisdom, when a ProfileY is taken
# things are mapped back to the x axis
# So to make sense of this, remap things back to y axis (emulate)
def remapProfile(profile):

    outprof = ROOT.TGraphErrors(profile.GetNbinsX())
    for bin in xrange(1, profile.GetNbinsX()):
       
        # This is actually the profile in the x direction
        binx = profile.GetBinCenter(bin)

        # This is actually the y value for the profile
        binc = profile.GetBinContent(bin)

        # This is actually error in the x direction
        bine = profile.GetBinError(bin)

        outprof.SetPoint(bin, binc, binx)
        outprof.SetPointError(bin, bine, 0)
     
    return outprof

# From a profile type object, get the error on each bin
# And use that to construct a new profile of the std devs
def stdDevProfile(profile, skip = -1):

    stddevProf = ROOT.TGraphErrors(profile);
    ROOT.SetOwnership(stddevProf, False)

    xerr = profile.GetBinWidth(1)
    for xbin in xrange(1, profile.GetNbinsX()+1):
        if xbin != skip:
            stddevProf.SetPoint(xbin, profile.GetBinCenter(xbin), profile.GetBinError(xbin))
            stddevProf.SetPointError(xbin, xerr/2.0, 0)

    return stddevProf

# The makeBandGraph method takes three TH1s where histoUp and histoDown
# would make an envelope around histoNominal. An optional color for the 
# band is passable
def makeBandGraph(histoNominal, histoUp, histoDown, color, skip = -1):
    
    graphBand = 0; npoints = 0
    if "TH1" in histoUp.ClassName() or "TProf" in histoUp.ClassName(): npoints = histoUp.GetNbinsX()
    elif "Error" in histoUp.ClassName():                               npoints = histoUp.GetN()

    graphBand = ROOT.TGraphAsymmErrors(npoints)

    for iPoint in xrange(0, npoints):

        x = ROOT.Double(0); yUp = ROOT.Double(0); yNom = ROOT.Double(0); yDown = ROOT.Double(0)
        xtemp = ROOT.Double(0); xtemp2 = ROOT.Double(0); ytemp = ROOT.Double(0)

        # Depending on what object was passed, we get the relevant info differently
        # If python hads and we could overload the function...
        if "TH1" in histoUp.ClassName() or "TProf" in histoUp.ClassName():

            x = histoUp.GetBinCenter(iPoint+1); yUp = histoUp.GetBinContent(iPoint+1)
            yNom = histoNominal.GetBinContent(iPoint+1); yDown = histoDown.GetBinContent(iPoint+1)
            xwidth2 = histoNominal.GetBinWidth(1)/2.0

        elif "Error" in histoUp.ClassName():

            histoUp.GetPoint(iPoint, x, yUp); histoUp.GetPoint(2, xtemp, ytemp); histoUp.GetPoint(1, xtemp2, ytemp)
            xwidth2 = (xtemp - xtemp2)/2.0
            histoNominal.GetPoint(iPoint, x, yNom); histoDown.GetPoint(iPoint, x, yDown)

        upErr = yUp - yNom
        downErr = yNom - yDown
        if downErr < 0. and upErr > 0. or downErr > 0. and upErr < 0.:
            if abs(downErr) >= abs(upErr): upErr = 0.
            else: downErr = 0.

        if iPoint != skip:
            graphBand.SetPoint(iPoint, x, yNom)
            graphBand.SetPointError(iPoint, xwidth2, xwidth2, downErr, upErr)

    graphBand.SetFillColorAlpha(color, 1.0)

    ROOT.SetOwnership(graphBand, False)
        
    return graphBand

# Using the nominal histogram and its up and down variation, create an error band
def getUncertaintyBand(histo, histoUp, histoDown, fillColor):

    gPFAXBand = 0
    if histoUp != 0 and histoDown != 0:

        pPFAX     = histo.ProfileX("p_%s_%d_ub"%(histo.GetName(),histo.GetUniqueID()), 1, -1, "");             pPFAX.Sumw2()
        pPFAXUp   = histoUp.ProfileX("p_%s_%d_ub"%(histoUp.GetName(),histoUp.GetUniqueID()), 1, -1, "");       pPFAXUp.Sumw2()
        pPFAXDown = histoDown.ProfileX("p_%s_%d_ub"%(histoDown.GetName(),histoDown.GetUniqueID()), 1, -1, ""); pPFAXDown.Sumw2()

        gPFAXBand = makeBandGraph(pPFAXUp, pPFAXDown, pPFAX, fillColor)

        set1Doptions(gPFAXBand, lineWidth = 3, lineColor = fillColor, markerColor = fillColor, markerSize = 0)
           
        if gPFAXBand: ROOT.SetOwnership(gPFAXBand, False)

    return gPFAXBand

def setAxisRebins(histo, xReb = 1, yReb = 1, zReb = 1):

    if xReb != 1: histo.Rebin(xReb)
    if yReb != 1: histo.RebinY(yReb)
    if zReb != 1: histo.RebinZ(zReb)

# A helper function to set all three axis ranges
def setAxisLabels(histo, lab = "NULL", xLab = "NULL", yLab = "NULL", zLab = "NULL"):

    if lab  != "NULL": histo.SetTitle(lab)
    if xLab != "NULL": histo.GetXaxis().SetTitle(xLab)
    if yLab != "NULL": histo.GetYaxis().SetTitle(yLab)
    if zLab != "NULL": histo.GetZaxis().SetTitle(zLab)

# A little helper function to set axis label, title sizes and offsets
def setAxisDims(histo, xLabelSize, yLabelSize, zLabelSize, xTitleSize, yTitleSize, zTitleSize, xOffset, yOffset, zOffset):

    histo.GetXaxis().SetLabelSize(xLabelSize); histo.GetXaxis().SetTitleSize(xTitleSize); histo.GetXaxis().SetTitleOffset(xOffset)
    histo.GetYaxis().SetLabelSize(yLabelSize); histo.GetYaxis().SetTitleSize(yTitleSize); histo.GetYaxis().SetTitleOffset(yOffset)
    
    try:
        histo.GetZaxis().SetLabelSize(zLabelSize); histo.GetZaxis().SetTitleSize(zTitleSize); histo.GetZaxis().SetTitleOffset(zOffset)
    except:
        return

# A helper function to set all three axis ranges
def setAxisRanges(histo, xMin = -1, xMax = -1, yMin = -1, yMax = -1, zMin = -1, zMax = -1):

    if xMin != xMax: histo.GetXaxis().SetRangeUser(xMin, xMax)
    if yMin != yMax: histo.GetYaxis().SetRangeUser(yMin, yMax)
    if zMin != zMax: histo.GetZaxis().SetRangeUser(zMin, zMax)

# A function to set some TH1 options
def set1Doptions(histo, fillColor = -1, lineColor = ROOT.kBlack, markerColor = ROOT.kBlack, lineStyle = 1, markerStyle = 20, lineWidth = 2, markerSize = 2.7, normalize = False):

    histo.SetLineColor(lineColor)
    histo.SetLineStyle(lineStyle)
    histo.SetLineWidth(lineWidth)

    histo.SetMarkerColor(markerColor)
    histo.SetMarkerStyle(markerStyle)
    histo.SetMarkerSize(markerSize)

    if fillColor != -1: histo.SetFillColor(fillColor)

    if normalize:
        try:    histo.Scale(1.0/histo.Integral())
        except: print "Could not normalize histogram named: %s"%(histo.GetName())

# A function to set some TH2 options
def set2Doptions(histo, contour = 255):

    if "TH2" not in histo.ClassName(): return

    histo.SetContour(255)

# From the events TChain, do a TTree draw to make an ND histo
# Variables, labels, and cut are specified by the user
def makeNDhisto(evtsTree, variables, ranges, labels, cut):

    h = 0; hName = "h_%s_%s"%(evtsTree.GetTitle(), randomString())
    if len(variables) == 3:
        h = ROOT.TH3F(hName, ";%s;%s;%s"%(labels[0], labels[1], labels[2]), ranges[0], ranges[1], ranges[2], ranges[3], ranges[4], ranges[5], ranges[6], ranges[7], ranges[8])
        evtsTree.Draw("%s:%s:%s>>%s"%(variables[2],variables[1],variables[0],hName), cut, "", ROOT.TTree.kMaxEntries, 0)
        h = ROOT.gDirectory.Get(hName)
    elif len(variables) == 2:
        h = ROOT.TH2F(hName, ";%s;%s"%(labels[0], labels[1]), ranges[0], ranges[1], ranges[2], ranges[3], ranges[4], ranges[5])
        evtsTree.Draw("%s:%s>>%s"%(variables[1],variables[0],hName), cut)
        h = ROOT.gDirectory.Get(hName)
    elif len(variables) == 1:
        h = ROOT.TH1F(hName, ";%s"%(labels[0]), ranges[0], ranges[1], ranges[2])
        evtsTree.Draw("%s>>%s"%(variables[0],hName), cut)
        h = ROOT.gDirectory.Get(hName)

    return h

    h.SetTitle("")
    h.GetXaxis().SetTitle(title)
    h.GetYaxis().SetTitle("A.U.")

def make1Dhisto(histo, axisRange, varNames, tag, write = True):

    h = 0
    # Two separate ranges must have been specified
    if len(axisRange) > 3:
        htempp = histo.Clone(histo.GetName()+"_pos_%s"%(randomString())); htempn = histo.Clone(histo.GetName()+"_neg_%s"%(randomString()))
        if   axisRange[0] == "Y":
            hp = htempp.ProjectionX(htempp.GetName()+"_%s%0.1fto%0.1f_projX_%s"%(axisRange[0],axisRange[1],axisRange[2],randomString()),htempp.GetYaxis().FindBin(axisRange[1]),htempp.GetYaxis().FindBin(axisRange[2]))
            hn = htempn.ProjectionX(htempn.GetName()+"_%s%0.1fto%0.1f_projX_%s"%(axisRange[0],axisRange[1],axisRange[2],randomString()),htempn.GetYaxis().FindBin(axisRange[3]),htempn.GetYaxis().FindBin(axisRange[4]))
        elif axisRange[0] == "X":
            hp = htempp.ProjectionY(htempp.GetName()+"_%s%0.1fto%0.1f_projY_%s"%(axisRange[0],axisRange[1],axisRange[2],randomString()),htempp.GetXaxis().FindBin(axisRange[1]),htempp.GetXaxis().FindBin(axisRange[2]))
            hn = htempn.ProjectionY(htempn.GetName()+"_%s%0.1fto%0.1f_projY_%s"%(axisRange[0],axisRange[1],axisRange[2],randomString()),htempn.GetXaxis().FindBin(axisRange[3]),htempn.GetXaxis().FindBin(axisRange[4]))

        h = hn; hn.Add(hp)

    # Just one range of the variable to project out
    else:
        htemp = histo.Clone(histo.GetName()+"_clone")
        if   axisRange[0] == "Y": h = htemp.ProjectionX(htemp.GetName()+"_projX_%s"%(randomString()), htemp.GetYaxis().FindBin(axisRange[1]),htemp.GetYaxis().FindBin(axisRange[2]))
        elif axisRange[0] == "X": h = htemp.ProjectionY(htemp.GetName()+"_projY_%s"%(randomString()), htemp.GetXaxis().FindBin(axisRange[1]),htemp.GetXaxis().FindBin(axisRange[2]))

    name = "%s_%s"%(varNames[1], varNames[0])
    h.SetName("%s%0.1fto%0.1f%s"%(name, axisRange[1], axisRange[2], tag))
    h.SetTitle("")

    return h

# Assumes an input of a 3D histo and projects a portion of the specified axis.
# If four numbers are specified in axisRange it is assumed to be two isolated ranges
# to be projected out and added together 
def make2Dhisto(histo, axisRange, varNames, write = True):

    h = 0
    # Two separate ranges must have been specified
    if len(axisRange) > 3:
        htempp = histo.Clone(histo.GetName()+"%s%0.1fto%0.1f_pos_%s"%(axisRange[0],axisRange[1],axisRange[2],randomString())); htempn = histo.Clone(histo.GetName()+"%s%0.1fto0.1%f_neg_%s"%(axisRange[0],axisRange[1],axisRange[2],randomString()))
        if   axisRange[0] == "X":
            htempp.GetXaxis().SetRange(htempp.Getxaxis().FindBin(axisRange[1]),htempp.GetXaxis().FindBin(axisRange[2]))
            htempn.GetXaxis().SetRange(htempn.Getxaxis().FindBin(axisRange[3]),htempn.GetXaxis().FindBin(axisRange[4]))
            htempn.GetXaxis().SetBit(ROOT.TAxis.kAxisRange); htempp.GetXaxis().SetBit(ROOT.TAxis.kAxisRange)
            hn = htempn.Project3D("zx"); hp = htempp.Project3D("zx")
        elif axisRange[0] == "Y":
            htempp.GetYaxis().SetRange(htempp.Getxaxis().FindBin(axisRange[1]),htempp.GetYaxis().FindBin(axisRange[2]))
            htempn.GetYaxis().SetRange(htempn.Getxaxis().FindBin(axisRange[3]),htempn.GetYaxis().FindBin(axisRange[4]))
            htempp.GetYaxis().SetBit(ROOT.TAxis.kAxisRange); htempn.GetYaxis().SetBit(ROOT.TAxis.kAxisRange)
            hn = htempn.Project3D("zy"); hp = htempp.Project3D("zy")
        elif axisRange[0] == "Z":
            htempp.GetZaxis().SetRange(htempp.Getxaxis().FindBin(axisRange[1]),htempp.GetZaxis().FindBin(axisRange[2]))
            htempn.GetZaxis().SetRange(htempn.Getxaxis().FindBin(axisRange[3]),htempn.GetZaxis().FindBin(axisRange[4]))
            htempp.GetZaxis().SetBit(ROOT.TAxis.kAxisRange); htempn.GetZaxis().SetBit(ROOT.TAxis.kAxisRange)
            hn = htempn.Project3D("yx"); hp = htempp.Project3D("yx")

        h = hn; hn.Add(hp)

    # Just one range of the variable to project out
    else:
        htemp = histo.Clone(histo.GetName()+"%s%fto%f_clone_%s"%(axisRange[0],axisRange[1],axisRange[2],randomString()))
        if   axisRange[0] == "X":
            htemp.GetXaxis().SetRange(htemp.GetXaxis().FindBin(axisRange[1]),htemp.GetXaxis().FindBin(axisRange[2]))
            htemp.GetXaxis().SetBit(ROOT.TAxis.kAxisRange)
            h = htemp.Project3D("zx")
        elif axisRange[0] == "Y":
            htemp.GetYaxis().SetRange(htemp.GetYaxis().FindBin(axisRange[1]),htemp.GetYaxis().FindBin(axisRange[2]))
            htemp.GetYaxis().SetBit(ROOT.TAxis.kAxisRange)
            h = htemp.Project3D("zy")
        elif axisRange[0] == "Z":
            htemp.GetZaxis().SetRange(htemp.GetZaxis().FindBin(axisRange[1]),htemp.GetZaxis().FindBin(axisRange[2]))
            htemp.GetZaxis().SetBit(ROOT.TAxis.kAxisRange)
            h = htemp.Project3D("yx")

    name = "%s_vs_%s_%s"%(varNames[1], varNames[0], varNames[2])
    h.SetName("%s%0.1fto%0.1f"%(name, axisRange[1], axisRange[2]))
    h.SetTitle("")
    
    return h
