"""
Main program and initializes window, adds controls, contains redraw loop and retrieves user-input
"""

__version__ = "Alpha (build 30-6-2018)"
__author__ = "Nard Janssens, Vinicius Silva, Robert Gowans, Ivan Antalec, Leonardo Marques - See Github PhotonFileUtils"

import os
import sys
import datetime
import time
import subprocess
import configparser

import pygame
from pygame.locals import *

from GUI import *
from PhotonFile import *
from FileDialog import *
from MessageDialog import *
from PopupDialog import *
from ProgressDialog import *

#Following tests are done for initial message to user below the disclaimer
try:
    import numpy
    numpyIsAvailable = True
except ImportError:
    numpyIsAvailable = False

try:
    import OpenGL #pyopengl
    pyopenglIsAvailable = True
    if pyopenglIsAvailable:
        from OGLEngine import *
        from Slicer import *
        from STLFile import *
except ImportError as err:
    pyopenglIsAvailable = False

#TODO LIST
#todo: in 3D display slice height
#todo: slicer has bug where outside of contour is painted
#todo: use multiprocessing to apply layerEdits
#todo: in linux circle is drawn as square
#todo: implement pcb plugin.old

#todo: continuous draw on mouse drag
#todo: calcnormals is still slow on large STLs, mainly to need to access triangles and append their normals to a list
#todo: Header LayerDef Address should be updated if importing/replacing bitmaps
#todo: check on save if layerheighs are consecutive and printer does not midprint go down
#todo: PhotonFile float_to_bytes(floatVal) does not work correct if floatVal=0.5 - now struct library used
#todo: process cursor keys for menu
#todo: hex_to_bytes(hexStr) et al. return a bytearray, should we convert this to bytes by using bytes(bytearray)?
#todo: beautify layer bar at right edge of slice image
#todo: Exe/distribution made with
#todo: drag GUI-ScrollbarH and ScrollbarV is not implementend
#todo: Numpy in Linux is slow: https://stackoverflow.com/questions/26609475/numpy-performance-differences-between-linux-and-windows


########################################################################################################################
##  Variables
########################################################################################################################

# Class which holds all data from photon file
photonfile=None
slicer=None

# Regarding image data to display
fullScreenOpenGL=False
framedScreenOpenGL=False
window=None
screen=None
dispimg_offset=[0,0]
dispimg_zoom=1
gridimg=None
defTransparent=(1,1,1)
layerimg=None
previmg=[None,None]
shadowimg=None
layerForecolor=(167,34,252)#(89,56,199) #I changed this to aproximate UV color what the machine shows X3msnake
layerBackcolor=(0,0,0)
layerLabel=None #Scroll chevrons at top left
layerNr = 0
prevNr=0
lastpos=(0,0)
editLayerMode=False

# Dimensional constants for settings
settingscolwidth=250
settingslabelwidth=160
settingslabelmargin=10
settingstextboxmargin=10
settingsrowheight=16
settingsrowspacing=28
settingstextboxwidth=settingscolwidth-settingslabelmargin-settingslabelwidth-settingstextboxmargin
settingswidth = settingscolwidth* 2  # 2 columns
settingsleft = int(1440 / 4)
windowwidth=int(1440 / 4) + settingswidth
windowheight=int(2560 / 4)+18 # height of menubar
layerRect=GRect(0,0,settingsleft,windowheight)

# GUI controls
menubar=None
frameBasic=None
frameAdvanced=None
controlsGeneral=None
controlsPreviews=None
controlsLayers=None
controlsSettings=None
frame3D=None

MODEBASIC=0
MODEADVANCED=1
MODEEDIT=2
MODEEDIT=3
frameMode=MODEBASIC
settingsMode=frameMode #disregards change to framemode MODEEDIT, used for saving preference
layercontrols = []
labelPrevNr=None

recentLoaded=[]
lastLoadDir=None
lastSaveDir=None

disableOpenGL=True # OpenGL used for stl loading and slicing, which does not work yet (experimental)

# Scroll bar to the right
sliderDrag=False
scrollLayerWidth=30
scrollLayerVMargin=30
scrollLayerRect=GRect(1440/4-scrollLayerWidth,scrollLayerVMargin,scrollLayerWidth,2560/4-scrollLayerVMargin*2)
layerCursorActive=True
layerCursorRect=GRect(1440/4-scrollLayerWidth,scrollLayerVMargin+2,scrollLayerWidth,4)

# Resin settings
resins=None
resincombo=None
resinlist=None

# Preview image in basic settings
prevImgBox=None

# Statusbar
statusbar =None

# Mode Edit vars
brushSize=1

brushDepth=1
brushDepth2Bottom=False

BSROUND=1
BSSQUARE=2
BSOPEN=0
BSFILLED=4
brushShape=BSFILLED | BSSQUARE  #round

cursorpos=(0,0)
mouseDrag=False
prevMouseDragPos=None

# Peeltime of firmware (needed to calc printing time)
peelTime = 6.5

########################################################################################################################
##  Message boxes
########################################################################################################################

def infoMessageBox(title, message):
    dialog = MessageDialog(flipFunc,screen, pos=(140, 140),
                           title=title,
                           message=message,
                           parentRedraw=redrawWindow)
    dialog.show()


def errMessageBox(errormessage):
    dialog = MessageDialog(flipFunc,screen, pos=(140, 140),
                           title="Error",
                           message=errormessage,
                           parentRedraw=redrawWindow)
    dialog.show()

def checkLoadedPhotonfile(title,message):
    if photonfile == None:
        print(title+": "+message)
        infoMessageBox(title,message)
        return False
    else:
        return True


########################################################################################################################
##  Navigation Buttons
########################################################################################################################

def prevUp():
    """ Shows next Preview Image from photonfile """
    global prevNr
    global dispimg
    if prevNr == 0: prevNr = 1
    dispimg = previmg[prevNr]
    refreshPreviewSettings()


def prevDown():
    """ Shows previous Preview Image from photonfile """
    global prevNr
    global dispimg
    if prevNr == 1: prevNr = 0
    dispimg = previmg[prevNr]
    refreshPreviewSettings()

def layerDown(delta:int=1):
    """ Go a number of layers (delta) back and display image and settings """
    global layerNr, dispimg, layerimg, photonfile
    if photonfile == None: return
    #print("layerDown")
    saveLayerSettings2PhotonFile()

    layerNr = layerNr - delta
    if layerNr < 0: layerNr = 0
    layerimg = photonfile.getBitmap(layerNr, layerForecolor, layerBackcolor)
    dispimg = layerimg
    refreshLayerSettings()
    setLayerSliderFromLayerNr()
    return


def layerUp(delta=1):
    """ Go a number of layers (delta) forward and display image and settings """
    global layerNr, dispimg, layerimg, photonfile
    if photonfile == None: return
    saveLayerSettings2PhotonFile()

    maxLayer = photonfile.nrLayers()
    layerNr = layerNr + delta
    if layerNr >= maxLayer: layerNr = maxLayer - 1
    # print("photonfile.getBitmap()")
    layerimg = photonfile.getBitmap(layerNr, layerForecolor, layerBackcolor)
    dispimg = layerimg
    # print("refreshLayerSettings()")
    refreshLayerSettings()
    setLayerSliderFromLayerNr()
    return


def readShadowLayers(nrlayers):
    """ Overlays several layers to produce a 'shadow' image of the layers below the current/active layer
    """

    global layerNr,shadowimg,layerForecolor,layerBackcolor
    if photonfile == None: return

    # First create canvas
    scale = (1, 1) # same scale as layerimg which is used in redraw()
    shadowimg = pygame.Surface((int(1440 * scale[0]), int(2560 * scale[1])),depth=32)
    shadowimg.fill((layerBackcolor))
    #shadowimg.fill((255,0,0))
    # Now blit all layers
    nrShadows=10
    stepSize=1+int(nrlayers/nrShadows)
    r = range (layerNr-nrlayers,layerNr,stepSize)
    l=len(r)
    #print ("nrLayers",nrlayers, layerNr, stepSize)
    shadowForecolor=[layerForecolor[0],layerForecolor[1],0]
    for p,lNr in enumerate(r):
       if lNr>0:
           perc=p/l
           #print (lNr,p,perc)
           shadowColor = (50 + int(perc*150 * shadowForecolor[0] / 255), 50 + int(perc*150 * shadowForecolor[1] / 255), 50 + int(perc*150 * shadowForecolor[2] / 255))
           transcol = Color (0,0,0,0)
           shadow = photonfile.getBitmap(lNr, shadowColor, transcol,scale)
           #pygame.image.save(shadow, "test"+str(p)+".png")
           shadow.set_colorkey(transcol)  # and we make black of current layer transparent
           shadowimg.blit(shadow,(0,0))

########################################################################################################################
##  Create Menu and menu handlers
########################################################################################################################

def newFile():
    """ start new file by loading empty photon file with default settings """
    global filename

    # open file and update window title to reflect a new unique (with date and time) filename
    openPhotonFile("resources/newfile.photon")
    barefilename = ("New file "+str(datetime.datetime.now().date())+" "+str(datetime.datetime.now().time())[:8])
    barefilename = barefilename.replace(":","-")
    filename = os.path.join(os.getcwd(),barefilename )
    print (filename)
    pygame.display.set_caption("Photon File Editor - " + barefilename)

def doNothing():
    """ Placeholder for menu items without functionality """
    infoMessageBox("Not yet implemented", "This feature is under development. If you want to help please visit our github page NardJ/PhotonFileUtils.")
    return

def exitFile():
    """ Exits program. """
    global running
    running=False
    print("Menu Exit was selected. Exit!")
    return

def saveFile():
    """ Asks for a filename and tells the PhotonFile object to save it . """

    global filename, lastLoadDir

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","There is no .photon file loaded to save."): return

    # Write all values on the screen to the photonfile object
    saveGeneralSettings2PhotonFile()
    savePreviewSettings2PhotonFile()
    saveLayerSettings2PhotonFile()

    # Ask user for filename and if exists to confirm overwrite resulting in okUser=True
    okUser=False
    retfilename=""
    while not okUser:
        # Get filename
        dialog = FileDialog(flipFunc,screen, (40, 40), ext=".photon",title="Save Photon File", defFilename="newfile.photon", parentRedraw=redrawWindow, startdir=lastLoadDir)
        retfilename=dialog.newFile()
        # If user canceled saveFile on FileDialog, retfilename=None and we should continue and thus set okUser to true
        if retfilename == None:
            okUser = True
        # If user selected filename, we check if filename exists (if exists okUser set to False, if not okUser is True)
        else:
            okUser = not os.path.isfile(retfilename)
        # If fileexists or user canceled saveFile on FileDialog
        if not okUser:
            dialog = MessageDialog(flipFunc,screen, pos=(140, 140), width=400,
                                   title="Please confirm",
                                   message="This file already exists. Do you want to continue?",
                                   center=True,
                                   buttonChoice=MessageDialog.OKCANCEL,
                                   parentRedraw=redrawWindow)
            ret = dialog.show()
            #if user selected ok, the users want to overwrite file so set okUser to True
            if ret=="OK": okUser=True

    # Check if user pressed Cancel
    if not retfilename==None:
        filename=retfilename
        print ("Returned: ",filename)
        try:
            # Write file and update window title to reflect new filename
            photonfile.writeFile(filename)
            barefilename = (os.path.basename(filename))
            pygame.display.set_caption("Photon File Editor - " + barefilename)
            updateRecentMenu(filename)
        except Exception as err:
            print (err)
            errMessageBox(str(err))
    else:
        print("User Canceled")
    return


class handleGLCallback:
    """Provide handles for OGLEngine to call so all file operations and such are ultimately handled by PhotonEditor.
    """

    @staticmethod
    def slice():
        global slicer
        global photonfile
        global fullScreenOpenGL
        global layerNr
        global dispimg
        global layerimg

        # Check if photonfile is loaded to prevent errors when operating on empty photonfile
        if photonfile==None:
            newFile()
        #if not checkLoadedPhotonfile("No photon file loaded!", "There is no .photon file loaded to save."): return

        # Write all values on the screen to the photonfile object
        saveGeneralSettings2PhotonFile()
        savePreviewSettings2PhotonFile()
        saveLayerSettings2PhotonFile()

        # Slice and save images
        slicer.slice()

        # Since import WILL take a while (although faster with numpy library available) show a be-patient message
        popup = ProgressDialog(flipFunc, screen, pos=(140, 140),
                               title="Please wait...",
                               message="Photon File Editor is importing your images.")
        popup.show()
        try:
            # Ask PhotonFile object to replace bitmaps
            directory=os.path.join(os.getcwd(),"slicer")
            if not photonfile.replaceBitmaps(directory, popup):
                print("User Canceled while importing.")
            # Refresh header settings which contains number of layers
            refreshHeaderSettings()
            # No preview data is changed
            #
            # Start again at layer 0 and refresh layer settings
            layerNr = 0
            refreshLayerSettings()
            # Update current layer image with new bitmap retrieved from photonfile
            layerimg = photonfile.getBitmap(layerNr, layerForecolor, layerBackcolor)
            # Exit 3D
            fullScreenOpenGL=False
            dispimg = layerimg

        except Exception as err:
            print(err)
            errMessageBox(str(err))


def loadFile(retfilename=None):
    """ Asks for a filename and tells the PhotonFile object to load it . """

    global filename, lastLoadDir

    # Set extensions, depending on OpenGL is available
    exts = [".photon"]
    if pyopenglIsAvailable and not disableOpenGL:exts.append(".stl")

    # Ask user for filename
    if retfilename==None:
        dialog = FileDialog(flipFunc,screen, (40, 40), ext=exts,title="Load Photon File", parentRedraw=redrawWindow,startdir=lastLoadDir)
        retfilename=dialog.getFile()
    else:
        filename=retfilename

    # Check if user pressed Cancel
    if not retfilename==None:
        filename = retfilename
        print ("Returned: ",filename)
        try:
            if filename.endswith(".photon"):
                # Open file and update window title to reflect new filename
                openPhotonFile(filename)
                barefilename = (os.path.basename(filename))
                pygame.display.set_caption("Photon File Editor - " + barefilename)
            elif filename.endswith(".stl"):
                global fullScreenOpenGL
                global slicer
                slicer = Slicer(gl,filename)
                fullScreenOpenGL = True
                # update window surface
                redrawWindow(None)
            updateRecentMenu(filename)

        except Exception as err:
            print (err)
            errMessageBox(str(err))
    else:
        print ("User Canceled")
    return


def undo():
    """ Undo by replacing all data with data from history. """

    global dispimg
    global layerimg
    global photonfile
    global layerNr

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","There is nothing to undo."): return

    # Insert layer
    try:
        photonfile.undo()
        if layerNr >= photonfile.nrLayers():
            layerNr = photonfile.nrLayers() - 1
            setLayerSliderFromLayerNr()
        print("Undo")
        # Refresh data from layer in sidebar (data length is possible changed)
        refreshLayerSettings()
        refreshHeaderSettings()  # number layers could have changed
        # Update current layer image with new bitmap retrieved from photonfile
        layerimg = photonfile.getBitmap(layerNr, layerForecolor, layerBackcolor)
        dispimg = layerimg
    except Exception as err: # if clipboard is empty
        print(err)
        errMessageBox(str(err))

def deleteLayer():
    """ Deletes current layer, but stores in memory/clipboard, ready for pasting  """

    global dispimg
    global layerimg
    global photonfile
    global layerNr

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","A .photon file is needed to delete layers."): return

    # Check of nrLayers at least 2, there must remain 1
    if photonfile.nrLayers()==1:
        dialog = MessageDialog(flipFunc,screen, pos=(140, 140),width=400,
                               title="No layers to delete!",
                               message="A .photon file must have at least 1 layer. \n\n You can however replace this layer with another bitmap or edit its settings.",
                               center = True,
                               parentRedraw = redrawWindow)
        dialog.show()
        return

    # Check if user is sure
    dialog = MessageDialog(flipFunc,screen, pos=(140, 140),width=400,
                           title="Please confirm",
                           message="Deleting only one layer can be undone. Are you sure?",
                           center=True,
                           buttonChoice=MessageDialog.OKCANCEL,
                           parentRedraw=redrawWindow)
    ret=dialog.show()

    # Delete if user confirmed
    if ret=="OK":
        photonfile.deleteLayer(layerNr)
        print("Layer "+str(layerNr)+ " deleted.")
        # Check if we deleted last layer and if so reduce layerNr
        if layerNr >= photonfile.nrLayers(): layerNr = layerNr - 1
        # Update layer settings with new layer
        layerimg = photonfile.getBitmap(layerNr, layerForecolor, layerBackcolor)
        dispimg = layerimg
        refreshLayerSettings()
        refreshHeaderSettings() # number layers changed
    else:
        print ("User canceled deleting a layer.")


def copyLayer():
    """ Copies layer to memory/clipboard, ready for pasting """
    global photonfile
    global layerNr

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","A .photon file is needed to duplicate layers."): return

    # Copy to memory
    photonfile.copyLayer(layerNr)


def duplicateLayer():
    """ Inserts layer before current layer (duplicate current Layer) """

    global dispimg
    global layerimg
    global photonfile
    global layerNr

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","A .photon file is needed to duplicate layers."): return

    # Insert layer
    photonfile.insertLayerBefore(layerNr,False)
    print("Layer "+str(layerNr)+ " inserted.")
    # Update layer settings with new layer
    refreshLayerSettings()
    refreshHeaderSettings()  # number layers changed
    # Update current layer image with new bitmap retrieved from photonfile
    layerimg = photonfile.getBitmap(layerNr, layerForecolor, layerBackcolor)
    dispimg = layerimg


def pasteLayer():
    """ Inserts layer before current layer (duplicate current Layer) """

    global dispimg
    global layerimg
    global photonfile
    global layerNr

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","A .photon file is needed to duplicate layers."): return

    # Insert layer
    try:
        photonfile.insertLayerBefore(layerNr,fromClipboard=True)
        print("Layer "+str(layerNr)+ " inserted.")
        # Refresh data from layer in sidebar (data length is possible changed)
        refreshLayerSettings()
        refreshHeaderSettings()  # number layers changed
        # Update current layer image with new bitmap retrieved from photonfile
        layerimg = photonfile.getBitmap(layerNr, layerForecolor, layerBackcolor)
        dispimg = layerimg
    except Exception as err: # if clipboard is empty
        print(err)
        errMessageBox(str(err))

def editLayer():
    """ Hides all controls on top of layer image and activates editing
    """
    global statusbar
    global editLayerMode
    global layercontrols
    global layerSlider_visible
    global frameMode
    global MODEEDIT

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!", "A .photon file is needed to load the bitmap in."): return

    editLayerMode=True
    frameMode=MODEEDIT

    layerSlider_visible=False

    for control in layercontrols:
        control.visible=False

    statusbar.setText(" [ESC] to exit edit mode | Use [+-/KEYPAD/Mouse] ")


def replaceBitmap():
    """ Checks which image is active, preview or layer and calls replacePreviewBitmap or replaceLayerBitmap """
    global dispimg
    global previmg
    global layerimg

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","A .photon file is needed to load the bitmap in."): return

    if dispimg == previmg[0]:
        replacePreviewBitmap()
    elif dispimg == previmg[1]:
        replacePreviewBitmap()
    elif dispimg == layerimg: replaceLayerBitmap()

def replacePreviewBitmap():
    """ Replace bitmap of current preview with new bitmap from disk selected by the user """
    """ Replace bitmap of current layer with new bitmap from disk selected by the user """

    global filename
    global dispimg
    global previmg
    global prevNr

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","A .photon file is needed to load the bitmap in."): return

    # Ask user for filename
    dialog = FileDialog(flipFunc,screen, (40, 40), ext=".png",title="Load Image File", parentRedraw=redrawWindow)
    retfilename=dialog.getFile()

    # Check if user pressed Cancel
    if not retfilename==None:
        filename = retfilename
        print ("Returned: ",filename)
        # since import can take a while (although faster with numpy library available) show a be-patient message
        popup = PopupDialog(flipFunc,screen, pos=(140, 140),
                            title="Please wait...",
                            message="Photon File Editor is importing your image.")
        popup.show()

        #photonfile.replacePreview(prevNr, filename)
        try:
            # Ask PhotonFile object to replace bitmap
            photonfile.replacePreview(prevNr,filename)
            # Refresh data from layer in sidebar (data length is possible changed)
            refreshHeaderSettings()
            refreshPreviewSettings()
            refreshLayerSettings()#data positions could be shifted to larger/smaller preview image
            # Update current layer image with new bitmap retrieved from photonfile
            previmg[prevNr] = photonfile.getPreviewBitmap(prevNr)
            dispimg = previmg[prevNr]
        except Exception as err:
            print (err)
            errMessageBox(str(err))
    else:
        print ("User Canceled")
    return

def replaceLayerBitmap():
    """ Replace bitmap of current layer with new bitmap from disk selected by the user """

    global filename
    global dispimg
    global layerimg

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","A .photon file is needed to load the bitmap in."): return

    # Ask user for filename
    dialog = FileDialog(flipFunc,screen, (40, 40), ext=".png",title="Load Image File", parentRedraw=redrawWindow)
    retfilename=dialog.getFile()

    # Check if user pressed Cancel
    if not retfilename==None:
        filename = retfilename
        print ("Returned: ",filename)
        # since import can take a while (although faster with numpy library available) show a be-patient message
        popup = PopupDialog(flipFunc,screen, pos=(140, 140),
                            title="Please wait...",
                            message="Photon File Editor is importing your image.")
        popup.show()
        try:
            # Ask PhotonFile object to replace bitmap
            photonfile.replaceBitmap(layerNr,filename)
            # Refresh data from layer in sidebar (data length is possible changed)
            refreshLayerSettings()
            # Update current layer image with new bitmap retrieved from photonfile
            layerimg = photonfile.getBitmap(layerNr, layerForecolor, layerBackcolor)
            dispimg = layerimg
        except Exception as err:
            print (err)
            errMessageBox(str(err))
    else:
        print ("User Canceled")
    return

"""
def storeLayerBitmap():
    # Stores (edited) display image to PhotonFile
    #
    global dispimg
    global layerimg
    global layerNr
    global photonfile
    # Ask PhotonFile object to replace bitmap
    photonfile.replaceBitmap(layerNr, dispimg)
    # Refresh data from layer in sidebar (data length is possible changed)
    refreshLayerSettings()
    # Show user the new bitmap (as check all is stored well)
    layerimg = photonfile.getBitmap(layerNr, layerForecolor, layerBackcolor)
    dispimg = layerimg
"""

def importBitmaps():
    """ Replace all bitmaps with all bitmap found in a directory selected by the user """
    global photonfile
    global layerNr
    global dispimg
    global layerimg

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","A .photon file is needed as template to load the bitmaps in."):return

    # Ask user for filename
    dialog = FileDialog(flipFunc,screen, (40, 40), ext=".png", title="Select directory with png files", parentRedraw=redrawWindow)
    directory = dialog.getDirectory()

    # Check if user pressed Cancel
    if not directory == None:
        print("Returned: ", directory)
        # Call redraw to remove filedialog
        redrawWindow()
        # Since import WILL take a while (although faster with numpy library available) show a be-patient message
        popup = ProgressDialog(flipFunc,screen, pos=(140, 140),
                            title="Please wait...",
                            message="Photon File Editor is importing your images.")
        popup.show()
        #debug (2 lines)
        #photonfile.replaceBitmaps(directory, popup)
        #return
        try:
            # Ask PhotonFile object to replace bitmaps
            if not photonfile.replaceBitmaps(directory, popup):
                print("User Canceled while importing.")
            # Refresh header settings which contains number of layers
            refreshHeaderSettings()
            # No preview data is changed
            #
            # Start again at layer 0 and refresh layer settings
            layerNr=0
            refreshLayerSettings()
            # Update current layer image with new bitmap retrieved from photonfile
            layerimg = photonfile.getBitmap(layerNr,layerForecolor,layerBackcolor)
            dispimg = layerimg
        except Exception as err:
            print (err)
            errMessageBox(str(err))
    else:
        print("User Canceled before importing.")
    return


def exportLayerBitmap():
    """ Exports current bitmap from a loaded photon file to a directory selected by the user """
    global filename
    global photonfile
    global layerNr

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","A .photon file is needed to export bitmaps from."):return

    # Ask user for filename
    barefilename = (os.path.basename(filename))
    barenotextfilename=os.path.splitext(barefilename)[0]
    dirname=(os.path.dirname(filename))
    newdirname=os.path.join(dirname,barenotextfilename+".bitmaps" )
    if not os.path.isdir(newdirname):
        os.mkdir(newdirname)

    # Since export can take a while (although faster with numpy library available) show a be-patient message
    popup = PopupDialog(flipFunc,screen, pos=(140, 140),
                        title="Please wait...",
                        message="Photon File Editor is exporting your image.")
    popup.show()
    try:
        # Ask PhotonFile object to replace bitmaps
        if not photonfile.exportBitmap(newdirname,"slice_",layerNr):
            print("User Canceled while exporting.")
    except Exception as err:
        print(err)
        errMessageBox(str(err))
    del popup

    #print (barefilename,filename,newdirname)


def exportPreviewBitmap():
    """ Exports current preview bitmap from a loaded photon file to a directory selected by the user """
    global filename
    global photonfile
    global prevNr

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","A .photon file is needed to export bitmaps from."):return

    # Ask user for filename
    barefilename = (os.path.basename(filename))
    barenotextfilename=os.path.splitext(barefilename)[0]
    dirname=(os.path.dirname(filename))
    newdirname=os.path.join(dirname,barenotextfilename+".bitmaps" )
    if not os.path.isdir(newdirname):
        os.mkdir(newdirname)

    # Since export can take a while (although faster with numpy library available) show a be-patient message
    popup = PopupDialog(flipFunc,screen, pos=(140, 140),
                        title="Please wait...",
                        message="Photon File Editor is exporting your (preview) image.")
    popup.show()
    try:
        # Ask PhotonFile object to replace bitmaps
        if not photonfile.exportPreviewBitmap(newdirname,prevNr):
            print("User Canceled while exporting.")
    except Exception as err:
        print(err)
        errMessageBox(str(err))
    del popup

    #print (barefilename,filename,newdirname)


def exportBitmap():
    """ Checks which image is active, preview or layer and calls exportPreviewBitmap or exportLayerBitmap """
    global dispimg
    global previmg
    global layerimg

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","A .photon file is needed to load the bitmap in."): return

    if dispimg == previmg[0]:
        exportPreviewBitmap()
    elif dispimg == previmg[1]:
        exportPreviewBitmap()
    elif dispimg == layerimg: exportLayerBitmap()


def exportBitmaps():
    """ Export all bitmaps from a loaded photon file to a directory selected by the user """
    global filename
    global photonfile

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","A .photon file is needed to export bitmaps from."):return

    # Ask user for filename
    barefilename = (os.path.basename(filename))
    barenotextfilename=os.path.splitext(barefilename)[0]
    dirname=(os.path.dirname(filename))
    newdirname=os.path.join(dirname,barenotextfilename+".bitmaps" )
    if not os.path.isdir(newdirname):
        os.mkdir(newdirname)

    # Since import WILL take a while (although faster with numpy library available) show a be-patient message
    popup = ProgressDialog(flipFunc,screen, pos=(140, 140),
                           title="Please wait...",
                           message="Photon File Editor is exporting your images.")
    popup.show()
    try:
        # Ask PhotonFile object to replace bitmaps
        if not photonfile.exportBitmaps(newdirname,"slice_",popup):
            print("User Canceled while exporting.")
    except Exception as err:
        print(err)
        errMessageBox(str(err))
    del popup

    #print (barefilename,filename,newdirname)


def about():
    """ Displays about box """
    dialog = MessageDialog(flipFunc,screen,
                           pos=(140, 140),width=400,
                           title="About Photon File Editor",
                           #message="Version Alpha \n \n Github: PhotonFileUtils \n\n o Nard Janssens (NardJ) \n o Vinicius Silva (X3msnake) \n o Robert Gowans (Rob2048) \n o Ivan Antalec (Antharon) \n o Leonardo Marques (Reonarudo) \n \n License: Free for non-commerical use.",
                           message="Version: "+ __version__ +"\n \n Github: PhotonFileUtils \n\n NardJ, X3msnake, Rob2048, \n Antharon, Reonarudo \n \n License: Free for non-commerical use.",
                           center=False,
                           parentRedraw=redrawWindow)
    dialog.show()

def showSlices():
    """ Let user switch (from preview images) to slice view """
    global dispimg
    global framedScreenOpenGL
    framedScreenOpenGL=False
    dispimg=layerimg

def showPrev0():
    """ Let user switch (from slice image view) to preview image """
    global prevNr
    global dispimg
    global framedScreenOpenGL
    framedScreenOpenGL=False
    prevNr = 0
    dispimg = previmg[prevNr ]
    refreshPreviewSettings()

def showPrev1():
    """ Let user switch (from slice image view) to preview image """
    global prevNr
    global dispimg
    global framedScreenOpenGL
    framedScreenOpenGL=False
    prevNr = 1
    dispimg = previmg[prevNr ]
    refreshPreviewSettings()

def showFramed3D():
    if not pyopenglIsAvailable:
        dialog = MessageDialog(flipFunc, screen, pos=(140, 140),
                               title="PyOpenGL not installed",
                               message="This menu item will become \n available after intalling \n pyOpenGL",
                               parentRedraw=redrawWindow)
        dialog.show()
        return
    global framedScreenOpenGL
    global dispimg
    global photonfile
    global gl
    #layerimg = photonfile.getBitmap(layerNr, (255,255,255), (0,0,0),(1,1))
    #gl.store_voxels(layerimg,2*layerNr/photonfile.nrLayers()-1)
    framedScreenOpenGL=True
    #update window surface
    #gl.store_voxels(photonfile,3)
    #redrawWindow(None)


def showFull3D():
    if not pyopenglIsAvailable:
        dialog = MessageDialog(flipFunc, screen, pos=(140, 140),
                               title="PyOpenGL not installed",
                               message="This menu item will become \n available after intalling \n pyOpenGL",
                               parentRedraw=redrawWindow)
        dialog.show()
        return
    global fullScreenOpenGL
    global slicer

    slicer = Slicer(gl)

    fullScreenOpenGL=True
    #update window surface
    redrawWindow(None)

def calcTime():
    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    global photonfile, peelTime
    if not checkLoadedPhotonfile("No photon file loaded!", "A .photon file is needed to calculate the print time."): return

    # Calculate time
    offTime=expBottom=PhotonFile.bytes_to_float(photonfile.Header["Off time (s)"])
    # minimum offtime is 6.5 seconds by default and use adjustable by editing peelTime
    # in settings.ini. PeelTime is the time the printer needs to rise the build plate and dip back into the resin.
    offTime=max(offTime,peelTime)
    nrBottom=PhotonFile.bytes_to_int(photonfile.Header["# Bottom Layers"])
    expBottom=PhotonFile.bytes_to_float(photonfile.Header["Exp. bottom (s)"])
    expNormal = PhotonFile.bytes_to_float(photonfile.Header["Exp. time (s)"])
    nrNormal=photonfile.nrLayers()-nrBottom
    time=nrBottom*(offTime+expBottom)+nrNormal*(offTime+expNormal)
    hr=int(time//3600)
    min=int((time % 3600) // 60)
    sec=int(time % 60)

    # Display time
    message = "Your model takes \n" + str(hr) + " hours, " + str(min) +" minutes, "+str(sec)+" seconds."
    infoMessageBox("Printing time", message)

def calcVolume():
    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    global photonfile
    if not checkLoadedPhotonfile("No photon file loaded!", "A .photon file is needed to calculate the volume."): return

    # Since calculation can take a while (although faster with numpy library available) show a be-patient message
    popup = ProgressDialog(flipFunc,screen, pos=(140, 140),
                           title="Please wait...",
                           message="Calculating volume.")
    popup.show()
    try:
        volume = photonfile.volume(popup)
        volmm=str(math.ceil(volume))+" mm3"
        volml=str(math.ceil(volume/1000))+" ml"
        message="The volume of your model is \n"+volmm+" / "+volml+ "\n\n Add 10% margin to be sure!"
        infoMessageBox("Volume of model", message)
    except Exception as err:
        print(err)
        errMessageBox(str(err))
    del popup


def validateLayerHeight():
    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    global photonfile
    if not checkLoadedPhotonfile("No photon file loaded!", "A .photon file is needed to calculate the volume."): return

    # Get current layer Height
    lHeight=PhotonFile.bytes_to_float(photonfile.Header["Layer height (mm)"])
    lHmicro=1000*lHeight

    # Hardware resolution 10µ (0.01mm)
    # Due to how python works round (0.031,2) but also 0.03 will be stored as 0.029999999
    # If we multiply 0.02999999 x 1000 python calcs this as 30.0
    # To be safe we calc proposed layerheight in µm and round
    nHmicro=10*round(100*lHeight,0)
    print (lHeight,lHmicro,nHmicro)

    # Check deviation of General Layer Height from optimum
    msg1=""
    deviation=lHmicro % 10
    if deviation> 1: # This deviation is not due to rounding errors of Anycubic Photon Slicer, but user caused
        msg1="You selected an incompatible layer height!\n"

    # Check cumulative layerheights in Layer Defs against optimal layerheight
    msg2=""
    for lNr in range(0,photonfile.nrLayers()):
        cumHeight = PhotonFile.bytes_to_float(photonfile.LayerDefs[lNr]["Layer height (mm)"])
        cumHmicro = cumHeight * 1000
        calcHmicro=lNr*nHmicro
        deviation=cumHmicro-calcHmicro
        if deviation>1: # Due to storage error (think 0.02999999) this added up to large deviation in this layer
            msg2="Your General Layerheight was propogated with rounding errors in the print!\n"

    # Ask user wat to do
    msg12=msg1+msg2
    if len(msg12)==0:
        msg = "Results of height validation: \n\n No errors found!\n"
        dialog = MessageDialog(flipFunc, screen, pos=(140, 140), width=400,
                               title="No errors found!",
                               message=msg,
                               center=True,
                               buttonChoice=MessageDialog.OK,
                               parentRedraw=redrawWindow)
        ret = dialog.show()
    else:
        msg="Results of height validation: \n\n"+msg12+"\nDo you want to correct this?"
        dialog = MessageDialog(flipFunc, screen, pos=(140, 140), width=400,
                               title="Please confirm!",
                               message=msg,
                               center=True,
                               buttonChoice=MessageDialog.OKCANCEL,
                               parentRedraw=redrawWindow)
        ret = dialog.show()
        # if user selected ok, the users want to overwrite file so set okUser to True
        if ret == "OK":
            if len(msg1)>0:
                photonfile.Header["Layer height (mm)"]=PhotonFile.float_to_bytes(nHmicro/1000)
            if len(msg2)>0:
                for lNr in range(0, photonfile.nrLayers()):
                    calcHmicro = lNr * nHmicro
                    photonfile.LayerDefs[lNr]["Layer height (mm)"]=PhotonFile.float_to_bytes(calcHmicro/1000)
        refreshHeaderSettings()
        refreshLayerSettings()

def readPlugins():
    """ Returns content plugin directory. """
    # Read directory
    direntries=os.listdir("plugins/")
    # Extract files and apply filter
    files = []
    for entry in direntries:
        #if entry.endswith(".plugin"): files.append(entry)
        if entry.endswith(".py"): files.append(entry)
        files.sort(key=str.lower)
    return files


def openPlugin(pluginfilename):
    # BEWARE: IT IS NORMAL THIS DOES NOT RUN IN PYCHARM!!!
    filepath="plugins/"+pluginfilename
    ifile = open(filepath, "r", encoding="Latin-1")  # Latin-1 handles special characters
    lines = ifile.read()
    exec(lines)

def setFrameMode(fMode):
    global settingsMode
    global frameBasic
    global frameAdvanced
    global frameMode
    global MODEBASIC
    global MODEADVANCED
    global settingswidth
    global windowwidth
    global windowheight
    global gl
    global window
    frameMode=fMode
    if frameMode == MODEBASIC or frameMode == MODEADVANCED: settingsMode = fMode
    print ("fMode",fMode)
    return
    if frameMode == MODEBASIC:
        settingswidth = settingscolwidth  # 1 columns
        settingsMode=MODEBASIC
        #frameBasic.visible=True
        #frameAdvanced.visible = False
    elif frameMode == MODEADVANCED:
        settingswidth = settingscolwidth * 2  # 2 columns
        settingsMode=MODEADVANCED
        #frameBasic.visible = False
        #frameAdvanced.visible = True
    windowwidth = settingsleft + settingswidth

    if not pyopenglIsAvailable or disableOpenGL:
        window = pygame.display.set_mode((windowwidth, windowheight))
        global menubar
    else:
        gl = GL((windowwidth, windowheight), handleGLCallback)

def loadRecent(fileName):
    print ("loadRecent", fileName)
    loadFile(fileName)


def updateRecentMenu(filenamepath=None):
    """ Adds filename to recents if not yet present, stores last directory and updates menu"""
    global recentLoaded, lastLoadDir, menubar

    # Store last dir and update recents list
    if not filenamepath==None:
        # store last dir
        lastLoadDir = os.path.dirname(filenamepath)

        # update recents list
        fnd = False
        for recent in recentLoaded:
            if recent == filenamepath: fnd = True
        if not fnd: recentLoaded.append(filenamepath)

        # check if recent list < 7
        while len(recentLoaded)>7:
            recentLoaded.pop(0)

    # Update Menu
    menubar.clearSubItems("File", "Open Recent")
    for recent in recentLoaded:
        recentshort=os.path.basename(recent)
        menubar.addSubItem("File", "Open Recent", recentshort, loadRecent, recent)

def setOpenGL(enable):
    global disableOpenGL,running
    disableOpenGL= not enable
    dialog = MessageDialog(flipFunc, screen, pos=(140, 140), width=400,
                           title="Please restart PhotonFileEditor.",
                           message="PhotonFileEditor will close now. \n Your changes will NOT be saved!\n Continue?",
                           center=True,
                           buttonChoice=MessageDialog.OKCANCEL,
                           parentRedraw=redrawWindow)
    ret = dialog.show()

    if ret=="OK":
        running=False

def createMenu():
    global menubar
    global screen
    global MODEBASIC
    global MODEADVANCED
    global disableOpenGL

    # Create the menu
    menubar=MenuBar(screen)
    menubar.addMenu("File","F")
    menubar.addItem("File", "New", newFile)
    menubar.addItem("File", "Load",loadFile)
    menubar.addSubMenu("File", "Open Recent")
    #menubar.addSubItem("File", "Open Recent", "Photon.photon",loadRecent,"Photon.photon")
    #menubar.addSubItem("File", "Open Recent", "Test.photon",loadRecent,"Test.photon")
    updateRecentMenu()
    menubar.addItem("File", "Save As", saveFile)
    menubar.addItem("File", "Exit", exitFile)
    menubar.addMenu("Edit", "E")
    menubar.addItem("Edit", "Undo", undo)
    menubar.addItem("Edit", "----")
    menubar.addItem("Edit", "Cut Layer", deleteLayer)
    menubar.addItem("Edit", "Copy Layer", copyLayer)
    menubar.addItem("Edit", "Paste Layer", pasteLayer)
    menubar.addItem("Edit", "Duplicate Layer", duplicateLayer)
    menubar.addItem("Edit", "----")
    menubar.addItem("Edit", "Export Bitmap", exportBitmap)
    menubar.addItem("Edit", "Replace Bitmap", replaceBitmap)
    menubar.addItem("Edit", "----")
    menubar.addItem("Edit", "Import Bitmaps", importBitmaps)
    menubar.addItem("Edit", "Export Bitmaps", exportBitmaps)
    menubar.addMenu("View", "V")
    menubar.addItem("View", "Slices", showSlices)
    menubar.addItem("View", "Preview 0", showPrev0)
    menubar.addItem("View", "Preview 1",showPrev1)
    menubar.addItem("View", "----")
    if pyopenglIsAvailable:
        if disableOpenGL:
            menubar.addItem("View", "Enable OGL", setOpenGL, True)
        else:
            menubar.addItem("View", "Disable OGL", setOpenGL, False)
            menubar.addItem("View", "3D", showFramed3D)
            menubar.addItem("View", "Full 3D", showFull3D)
        menubar.addItem("View", "----")
    menubar.addItem("View", "Basic settings",setFrameMode,MODEBASIC)
    menubar.addItem("View", "Advanced settings",setFrameMode,MODEADVANCED)
    menubar.addMenu("Tools","T")
    menubar.addItem("Tools", "Layer Height", validateLayerHeight)
    menubar.addItem("Tools", "Volume", calcVolume)
    menubar.addItem("Tools", "Print Time", calcTime)

    menubar.addMenu("Plugins ", "P")
    for plugin in readPlugins():
        name=plugin.split(".py")[0]
        menubar.addItem("Plugins ", name,openPlugin,plugin)
    menubar.addMenu("Help", "H")
    menubar.addItem("Help", "About",about)


def createLayerOperations():
    """ Create the layer modification buttons pointing to Edit menu layer options """
    global layercontrols
    global menubar
    viewport_yoffset = 8
    iconsize=(46,59)
    icondist=iconsize[0]+16
    layercontrols.append(ImgBox(screen, filename="resources/cut.png", filename_hover="resources/cut-hover.png",
                           rect=GRect(20+0*icondist,2560/4-iconsize[1]-viewport_yoffset,-1,-1),
                           borderhovercolor=(0,0,0),toolTip="Cut (and store in clipboard)",
                           func_on_click=deleteLayer))
    layercontrols.append(ImgBox(screen, filename="resources/copy.png", filename_hover="resources/copy-hover.png",
                           rect=GRect(20+1*icondist, 2560 / 4 - iconsize[1] - viewport_yoffset,-1,-1),
                           borderhovercolor=(0, 0, 0),toolTip="Copy (to clipboard)",
                           func_on_click=copyLayer))
    layercontrols.append(ImgBox(screen, filename="resources/paste.png", filename_hover="resources/paste-hover.png",
                           rect=GRect(20+2*icondist, 2560 / 4 - iconsize[1] - viewport_yoffset,-1,-1),
                           borderhovercolor=(0, 0, 0), toolTip="Paste (from clipboard)",
                           func_on_click=pasteLayer))
    layercontrols.append(ImgBox(screen, filename="resources/duplicate.png", filename_hover="resources/duplicate-hover.png",
                           rect=GRect(20+3*icondist, 2560 / 4 - iconsize[1] - viewport_yoffset,-1,-1),
                           borderhovercolor=(0, 0, 0), toolTip="Duplicate (current layer)",
                           func_on_click=duplicateLayer))
    layercontrols.append(ImgBox(screen, filename="resources/edit.png", filename_hover="resources/edit-hover.png",
                           rect=GRect(20+4.2*icondist, 2560 / 4 - iconsize[1] - viewport_yoffset,-1,-1),
                           borderhovercolor=(0, 0, 0), toolTip="Edit mode",
                           func_on_click=editLayer))

def createLayernavigation():
    """ Create the layer navigation buttons (Up/Down) """
    global layerLabel
    global menubar
    global layercontrols
    global layerNr

    # Add two imageboxes to control as layer nav buttons
    viewport_yoffset=menubar.getHeight()
    layercontrols.append(ImgBox(screen, filename="resources/arrow-up.png", filename_hover="resources/arrow-up-hover.png", rect=GRect(20,20+viewport_yoffset,-1,-1), borderhovercolor=(0,0,0),func_on_click=layerDown))
    layercontrols.append(ImgBox(screen, filename="resources/arrow-down.png", filename_hover="resources/arrow-down-hover.png", rect=GRect(20,80+viewport_yoffset,-1,-1), borderhovercolor=(0,0,0),func_on_click=layerUp))
    layerLabel=Label(screen,GRect(26,80,52,40),textcolor=(255,255,255),fontsize=24,text="",istransparent=True,center=True)
    layerLabel.font.set_bold(True)
    layercontrols.append(layerLabel)

    layerNr=0
    setLayerSliderFromLayerNr()


def createStatusBar():
    """ Create status bar. """
    global statusbar
    global controls
    statusbar = Label(screen, text=" Status ready!",rect=GRect(settingsleft , windowheight-28,windowwidth-settingsleft+1, 28),drawBorder=True)
    statusbar.font.set_bold(True)


def createSidebarSettings():
    """ Create all labels and input boxes to edit the general, preview and current layer settings of the photonfile. """
    global menubar
    global screen
    global controls
    global frameBasic
    global frameAdvanced
    global controlsGeneral
    global controlsPreviews
    global controlsLayers
    global controlsSettings

    global settingscolwidth
    global settingslabelwidth
    global settingslabelmargin
    global settingstextboxmargin
    global settingsrowheight
    global settingsrowspacing
    global settingstextboxwidth
    global settingswidth
    global settingsleft

    global labelPrevNr
    global labelLayerNr

    global resins
    global resincombo
    global resinlist
    global prevImgBox

    global statusbar

    # The controls are placed below the menubar
    viewport_yoffset=menubar.getHeight()

    # Setup Frames for settings
    # We have 2 frames: Basic and Advanced
    # Basic is 1 column and consist of two rows: General and Layer
    # Advanced is 2 columns, first column consist of General, second column consists of Preview and Layer
    margin=GRect(2,2,0,0)
    settingsrowheight=26

    debugFrames=False # for debugging we want to see each frame with a different color

    frameResinsAdv = Frame(screen,
                       rect=GRect(0, 0, settingscolwidth, 32 + 6 * settingsrowspacing),
                       text="", drawbackground=debugFrames, backcolor=(0, 0, 255), drawborder=debugFrames,
                       margin=margin, topoffset=0,
                       layout=Frame.TOPDOWN, spacing=4, gridsize=28)
    frameResinsBasic = Frame(screen,
                       rect=GRect(0, 0, settingscolwidth, 32 + 6 * settingsrowspacing),
                       text="", drawbackground=debugFrames, backcolor=(0, 0, 255), drawborder=debugFrames,
                       margin=margin, topoffset=0,
                       layout=Frame.TOPDOWN, spacing=4, gridsize=28)

    frameBasic = Frame(screen,
                          rect=GRect(settingsleft, viewport_yoffset, 2 * settingscolwidth,
                                     windowheight - viewport_yoffset),
                          text="", topoffset=0,
                          drawbackground=debugFrames, backcolor=(255, 0, 0),
                          drawborder=debugFrames, margin=margin,
                          layout=Frame.LEFTRIGHT, spacing=0, gridsize=settingscolwidth,
                          )
    frameBasicLeft = Frame(screen,
                          rect=GRect(0, 0, settingscolwidth,windowheight - viewport_yoffset),
                          text="", drawbackground=False, drawborder=False, margin=margin,topoffset=0,
                          layout=Frame.TOPDOWN, spacing=14, gridsize=-1,
                          )
    frameBasicRight = Frame(screen,
                          rect=GRect(0, 0, settingscolwidth,windowheight - viewport_yoffset),
                          text="", drawbackground=False, drawborder=False, margin=margin,topoffset=0,
                          layout=Frame.TOPDOWN, spacing=14, gridsize=-1,
                          )
    frameGenBasic=Frame(screen,
                     rect=GRect(0, 0, settingscolwidth, 32 + 10 * settingsrowspacing),
                     text="General",drawbackground=debugFrames,backcolor=(255,255,0),drawborder=debugFrames,margin=margin,topoffset=0,
                     layout=Frame.TOPDOWN,spacing=4,gridsize=28)
    framePrevBasic=Frame(screen,
                     rect=GRect(0, 0, settingslabelwidth+ settingstextboxwidth, settingsrowheight+settingslabelwidth+settingstextboxwidth),
                     text="Preview",drawbackground=debugFrames,backcolor=(255,0,255),drawborder=debugFrames,margin=margin,topoffset=0,
                     layout=Frame.TOPDOWN,spacing=4,gridsize=-1)
    frameLayerBasic=Frame(screen,
                     rect=GRect(0,0, settingscolwidth, 32 + 1 * settingsrowspacing),
                     text="",drawbackground=debugFrames,backcolor=(0,255,255),drawborder=debugFrames,margin=margin,topoffset=0,
                     layout=Frame.TOPDOWN,spacing=4,gridsize=28)

    frameBasic.append(frameBasicLeft)
    frameBasic.append(frameBasicRight)
    frameBasicLeft.append(frameGenBasic)
    frameBasicLeft.append(frameLayerBasic)
    frameBasicRight.append(framePrevBasic)
    frameBasicRight.append(frameResinsBasic)

    frameAdvanced=Frame(screen,
                     rect=GRect(settingsleft, viewport_yoffset, 2* settingscolwidth,windowheight - viewport_yoffset),
                     text="",topoffset=0,
                     drawbackground=debugFrames,backcolor=(255,0,0),
                     drawborder=debugFrames,margin=margin,
                     layout=Frame.LEFTRIGHT,spacing=0,gridsize=settingscolwidth,
                     )
    frameAdvancedLeft = Frame(screen,
                          rect=GRect(0, 0, settingscolwidth,windowheight - viewport_yoffset),
                          text="", drawbackground=False, drawborder=False, margin=margin,topoffset=0,
                          layout=Frame.TOPDOWN, spacing=14, gridsize=-1,
                          )
    frameAdvancedRight = Frame(screen,
                          rect=GRect(0, 0, settingscolwidth,windowheight - viewport_yoffset),
                          text="", drawbackground=False, drawborder=False, margin=margin,topoffset=0,
                          layout=Frame.TOPDOWN, spacing=14, gridsize=-1,
                          )
    frameGenAdvanced=Frame(screen,
                     rect=GRect(0, 0, settingscolwidth, 32 + 19 * settingsrowspacing),
                     text="General",drawbackground=debugFrames,backcolor=(255,0,0),drawborder=debugFrames,margin=margin,topoffset=0,
                     layout=Frame.TOPDOWN,spacing=4,gridsize=28)
    framePrevAdvanced=Frame(screen,
                     rect=GRect(0, 0, settingscolwidth, 32 + 6 * settingsrowspacing),
                     text="",drawbackground=debugFrames,backcolor=(0,255,0),drawborder=debugFrames,margin=margin,topoffset=0,
                     layout=Frame.TOPDOWN,spacing=4,gridsize=28)
    frameLayerAdvanced=Frame(screen,
                     rect=GRect(0,0, settingscolwidth, 32 + 6 * settingsrowspacing),
                     text="",drawbackground=debugFrames,backcolor=(0,0,255),drawborder=debugFrames,margin=margin,topoffset=0,
                     layout=Frame.TOPDOWN,spacing=4,gridsize=28)
    frameAdvanced.append(frameAdvancedLeft)
    frameAdvanced.append(frameAdvancedRight)
    frameAdvancedLeft.append(frameGenAdvanced)
    frameAdvancedRight.append(framePrevAdvanced)
    frameAdvancedRight.append(frameLayerAdvanced)
    frameAdvancedRight.append(frameResinsAdv)

    controlsSettings=[] # will contain all controls of General/Previews/Layers
    controlsGeneral=[]
    controlsPreviews = []
    controlsLayers = []


    # We need to translate the datatype of the photon settings to the datatypes an inputbox recognizes and enforces from the user
    transTypes={PhotonFile.tpByte: TextBox.HEX,PhotonFile.tpInt: TextBox.INT,PhotonFile.tpFloat: TextBox.FLOAT,PhotonFile.tpChar: TextBox.HEX}

    # Add General data fields
    for row, (bTitle, bNr, bType, bEditable,bHint) in enumerate(PhotonFile.pfStruct_Header,1):#enum start at 1
        tbType = transTypes[bType]
        bcolor=(255,255,255) if bEditable else (128,128,128)
        label=Label(screen, text=bTitle, rect=GRect(0,0,settingslabelwidth,settingsrowheight))
        textbox=TextBox(screen, text="", \
                        rect=GRect(0,0, settingstextboxwidth, settingsrowheight),\
                        editable=bEditable, \
                        backcolor=bcolor, \
                        textcolor=(0,0,0),\
                        inputType=tbType, \
                        toolTip=bHint, \
                        onEnter=updateTextBox2PhotonFile, \
                        onLostFocus=updateTextBox2PhotonFile, \
                        linkedData={"VarGroup":"Header","Title":bTitle,"NrBytes":bNr,"Type":bType} \
                        )
        frow = Frame(
                    screen,rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                    text="",drawborder=False,drawbackground=False,margin=GRect(0, 0, 0, 0),topoffset=0,
                    layout=Frame.LEFTRIGHT,spacing=settingstextboxmargin,gridsize=settingslabelwidth)
        frow.append(label)
        frow.append(textbox)
        if bEditable: frameGenBasic.append(frow)
        frameGenAdvanced.append(frow)
        controlsGeneral.append(textbox)

    # Add Preview data fields
    # First we need navigation buttons for previewNr which replaces title of frame
    frow = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=settingstextboxmargin, gridsize=settingslabelwidth)
    frowsub = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=2, gridsize=-1)
    labelPrevNr=Label(screen, text=(str(prevNr)+"/2"),rect=GRect(0,0,30, 26))
    h=labelPrevNr.rect.height

    buttonLeft = ImgBox(screen,rect=GRect(0,0,18,h),filename="resources/buttonarrow.png",rotate=90,
                        drawBorder=True,func_on_click=prevDown)
    buttonRight = ImgBox(screen,rect=GRect(0,0,18,h),filename="resources/buttonarrow.png",rotate=-90,
                        drawBorder=True, func_on_click=prevUp)

    label = Label(screen, text="Preview", rect=GRect(0, 0, settingstextboxwidth - 40, 20))
    label.font.set_bold(True)
    frow.append(label)
    frow.append(frowsub)
    frowsub.append(buttonLeft)
    frowsub.append(labelPrevNr)
    frowsub.append(buttonRight)
    framePrevAdvanced.append(frow)

    prevImgBox = ImgBox(screen,rect=GRect(0,0,settingslabelwidth+settingstextboxwidth,settingslabelwidth+settingstextboxwidth),drawBorder=True)
    #framePrevBasic.append(label)
    framePrevBasic.append(prevImgBox)

    # Now add the settings
    for row, (bTitle, bNr, bType,bEditable, bHint) in enumerate(PhotonFile.pfStruct_Previews, 1):
        tbType = transTypes[bType]
        bcolor = (255, 255, 255) if bEditable else (128, 128, 128)
        label=Label(screen, text=bTitle, rect=GRect(0,0,settingslabelwidth,settingsrowheight))
        textbox = TextBox(screen, text="", \
                    rect=GRect(0,0, settingstextboxwidth, settingsrowheight),\
                    editable=bEditable, \
                    backcolor=bcolor, \
                    textcolor=(0, 0, 0), \
                    inputType=tbType, \
                    toolTip=bHint, \
                    onEnter=updateTextBox2PhotonFile, \
                    onLostFocus=updateTextBox2PhotonFile, \
                    linkedData={"VarGroup": "Preview", "Title": bTitle, "NrBytes": bNr, "Type": bType} \
                    )
        frow = Frame(screen,rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                    text="",drawborder=False,drawbackground=False,margin=GRect(0, 0, 0, 0),topoffset=0,
                    layout=Frame.LEFTRIGHT,spacing=settingstextboxmargin,gridsize=settingslabelwidth)
        frow.append(label)
        frow.append(textbox)
        if bEditable: framePrevBasic.append(frow)
        framePrevAdvanced.append(frow)
        controlsPreviews.append(textbox)

    # Add Current Layer meta fields
    # First we need navigation buttons for previewNr which replaces title of frame
    frow = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingslabelwidth)
    #frowsub = Frame(screen,
    #             rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
    #             text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
    #             layout=Frame.LEFTRIGHT, spacing=2, gridsize=-1)
    #buttonLeft=Button(screen, rect=GRect(0,0, 18, 20), text="<", func_on_click=layerDown)
    #buttonRight = Button(screen, rect=GRect(0, 0, 18, 20), text=">", func_on_click=layerUp)
    labelLayerNr=Label(screen, text="000/000",rect=GRect(0,0,80, 20))

    label = Label(screen, text="Layer", rect=GRect(0, 0, settingslabelwidth+settingstextboxwidth-120, 20))
    label.font.set_bold(True)
    frow.append(label)
    #frow.append(frowsub)
    frow.append(labelLayerNr)
    #frowsub.append(buttonLeft)
    #frowsub.append(labelLayerNr)
    #frowsub.append(buttonRight)

    frameLayerBasic.append(frow)
    frameLayerAdvanced.append(frow)

    # Now add the settings
    for row, (bTitle, bNr, bType,bEditable, bHint) in enumerate(PhotonFile.pfStruct_LayerDef, 9):
        tbType = transTypes[bType]
        bcolor = (255, 255, 255) if bEditable else (128, 128, 128)
        label=Label(screen, text=bTitle, rect=GRect(0,0,settingslabelwidth,settingsrowheight))
        textbox=TextBox(screen, text="", \
                                rect=GRect(0,0, settingstextboxwidth, settingsrowheight),\
                                editable=bEditable, \
                                backcolor=bcolor, \
                                textcolor=(0, 0, 0), \
                                inputType=tbType,\
                                toolTip=bHint, \
                                onEnter=updateTextBox2PhotonFile, \
                                onLostFocus=updateTextBox2PhotonFile, \
                                linkedData={"VarGroup": "LayerDef", "Title": bTitle, "NrBytes": bNr, "Type": bType} \
                                )

        frow = Frame(screen,rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                    text="",drawborder=False,drawbackground=False,margin=GRect(0, 0, 0, 0),topoffset=0,
                    layout=Frame.LEFTRIGHT,spacing=settingstextboxmargin,gridsize=settingslabelwidth)
        frow.append(label)
        frow.append(textbox)
        if bEditable: frameLayerBasic.append(frow)
        frameLayerAdvanced.append(frow)
        controlsLayers.append(textbox)

    # Add Resin Presets Chooser
    # First read settings from file
    # columns are Brand,Type,Layer,NormalExpTime,OffTime,BottomExp,BottomLayers
    ifile = open("resources/resins.csv", "r",encoding="Latin-1") #Latin-1 handles special characters
    lines = ifile.readlines()
    resins = [tuple(line.strip().split(";")) for line in lines]
    resinnames=[]
    for resin in resins:
        resinnames.append(resin[0]+ "-"+resin[1]+"-"+resin[2])

    # Make combobox (add last, so always on top)
    resincombo=Combobox(screen,
                             rect=GRect(0,0, settingslabelwidth+settingstextboxwidth, settingsrowheight),
                             expandHeight=110,
                             items=resinnames,
                             defitemnr=0
                             )

    resinlist = ListBox(screen,
                          rect=GRect(0, 0, settingslabelwidth + settingstextboxwidth, settingsrowheight*10),
                          items=resinnames,
                          func_on_click=None)

    # Add apply button
    resinbutton=Button(screen,
                            rect=GRect(0,0, settingstextboxwidth,settingsrowheight),
                            text="Apply", func_on_click=applyResinSettings
                             )

    frow = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingslabelwidth)
    label = Label(screen, text="Resin settings", rect=GRect(0, 0, settingslabelwidth+settingstextboxwidth-120, 20))
    label.font.set_bold(True)
    frow.append(label)
    frow.append(resinbutton)

    # Add combobox to controls
    frameResinsAdv.append(frow)
    frameResinsAdv.append(resincombo)

    # Add combobox to controls
    frameResinsBasic.append(frow)
    frameResinsBasic.append(resinlist)

    # Make one list of all controls
    controlsSettings = controlsLayers+controlsGeneral


def createSidebar3D():
    """ Create all labels and input boxes to slice an STL """
    global screen
    global frame3D
    global settingscolwidth
    global settingslabelwidth
    global settingslabelmargin
    global settingstextboxmargin
    global settingsrowheight
    global settingsrowspacing
    global settingstextboxwidth
    global settingswidth
    global settingsleft

    # The controls are placed below the menubar
    viewport_yoffset=menubar.getHeight()

    # Setup Frames for settings
    # We have 2 frames: Basic and Advanced
    # Basic is 1 column and consist of two rows: General and Layer
    # Advanced is 2 columns, first column consist of General, second column consists of Preview and Layer
    margin=GRect(2,2,0,0)
    settingsrowheight=26

    debugFrames=False # for debugging we want to see each frame with a different color

    # Make Layer Edit sidebar
    frame3D=Frame(screen,
                     rect=GRect(settingsleft+settingscolwidth/2, viewport_yoffset, settingscolwidth/2,windowheight - viewport_yoffset),
                     text="Slice Settings",topoffset=0,
                     drawbackground=debugFrames,backcolor=(255,0,0),
                     drawborder=debugFrames,margin=GRect(settingslabelmargin,settingslabelmargin,0,0),
                     layout=Frame.TOPDOWN,spacing=14,gridsize=-1,
                     )

    # Number of transparent layer below current to show
    frow = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingslabelwidth)
    frow.append(Label(screen, text="Slice height", rect=GRect(0, 0, settingslabelwidth + settingstextboxwidth - 120, 20)))
    frow.append(ScrollBarH(screen,GRect(0,0,settingstextboxwidth*2,settingsrowheight),minScroll=1, maxScroll=100, curScroll=1,func_on_click=readShadowLayers))
    frameEdit.append(frow)

    # Brush shape (square/round/filled/open/text)
    frow = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingslabelwidth)
    frow.append(Label(screen, text="Brush shape", rect=GRect(0, 0, settingslabelwidth + settingstextboxwidth - 120, 20)))

    frowsub = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingsrowheight*2)
    group=[]
    # Full circle
    img = pygame.Surface((settingsrowheight, settingsrowheight))
    pygame.draw.circle(img, (0, 0, 0), (settingsrowheight//2, settingsrowheight//2), settingsrowheight//2-2, 0)
    frowsub.append(Checkbox(screen, GRect(0, 0, settingsrowheight, settingsrowheight),
                         type=Checkbox.image,borderwidth=0,selectborderwidth=3, img=img,func_on_click=setBrushShapeRoundFilled,group=group))
    # Full Square
    img = pygame.Surface((settingsrowheight, settingsrowheight))
    pygame.draw.rect(img, (0, 0, 0), (2,2,settingsrowheight-4, settingsrowheight-4), 0)
    frowsub.append(Checkbox(screen, GRect(0, 0, settingsrowheight, settingsrowheight),
                            type=Checkbox.image, borderwidth=0,selectborderwidth=3, img=img, func_on_click=setBrushShapeSquareFilled,group=group))
    # Open circle
    #img = pygame.Surface((settingsrowheight, settingsrowheight))
    #pygame.draw.circle(img, (0, 0, 0), (settingsrowheight//2, settingsrowheight//2), settingsrowheight//2-2, 2)
    #frowsub.append(Checkbox(screen, GRect(0, 0, settingsrowheight, settingsrowheight),
    #                     type=Checkbox.image,borderwidth=0,selectborderwidth=3, img=img,func_on_click=setBrushShapeRoundOpen,group=group))
    # Open Square
    #img = pygame.Surface((settingsrowheight, settingsrowheight))
    #pygame.draw.rect(img, (0, 0, 0), (2, 2, settingsrowheight - 4, settingsrowheight - 4), 2)
    #frowsub.append(Checkbox(screen, GRect(0, 0, settingsrowheight, settingsrowheight),
    #                        type=Checkbox.image, borderwidth=0,selectborderwidth=3, img=img, func_on_click=setBrushShapeSquareOpen,group=group))

    # ABC
    img = pygame.Surface((settingsrowheight, settingsrowheight))
    font = pygame.font.SysFont(defFontName, defFontSize)
    font.set_bold(True)
    font.set_underline(True)
    textsurface = font.render("Abc", True, (0,0,0))
    img.blit(textsurface, (0,0),(0, 0, img.get_width(), img.get_height() ))
    #frowsub.append(Checkbox(screen, GRect(0, 0, settingsrowheight, settingsrowheight),
    #                        type=Checkbox.image, borderwidth=0,selectborderwidth=3, img=img, func_on_click=None,group=group))

    frow.append(frowsub)
    frameEdit.append(frow)

    # Brush size
    frow = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingslabelwidth)
    frow.append(Label(screen, text="Brush size", rect=GRect(0, 0, settingslabelwidth + settingstextboxwidth - 120, 20)))
    frow.append(ScrollBarH(screen,GRect(0,0,settingstextboxwidth*2,settingsrowheight),minScroll=1, maxScroll=50, curScroll=1,func_on_click=setBrushSize))
    frameEdit.append(frow)

    # Brush depth
    frow = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingslabelwidth)
    frow.append(Label(screen, text="Brush depth", rect=GRect(0, 0, settingslabelwidth + settingstextboxwidth - 120, 20)))
    frow.append(ScrollBarH(screen, GRect(0, 0, settingstextboxwidth * 2, settingsrowheight), minScroll=1, maxScroll=10,curScroll=1, func_on_click=setBrushDepth))
    frameEdit.append(frow)

    # Brush depth until bottom reached?
    frow = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingslabelwidth)
    frow.append(Label(screen, text="", rect=GRect(0, 0, settingslabelwidth + settingstextboxwidth - 120, 20)))
    frowsub = Frame(screen,
                    rect=GRect(0, 0, settingstextboxmargin + settingstextboxwidth,settingsrowheight),
                    text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                    layout=Frame.LEFTRIGHT, spacing=4, gridsize=-1)
    frowsub.append(Label(screen, text="To bottom", rect=GRect(0, 0, settingslabelwidth + settingstextboxwidth - 120, 20)))
    frowsub.append(Checkbox(screen,GRect(0,0,settingsrowheight,settingsrowheight),type=Checkbox.checkbox,func_on_click=setBrushDepth2Bottom))
    frow.append(frowsub)
    frameEdit.append(frow)


def createSidebarEdit():
    """ Create all labels and input boxes to edit the layer image. """
    global screen
    global frameEdit
    global settingscolwidth
    global settingslabelwidth
    global settingslabelmargin
    global settingstextboxmargin
    global settingsrowheight
    global settingsrowspacing
    global settingstextboxwidth
    global settingswidth
    global settingsleft

    # The controls are placed below the menubar
    viewport_yoffset=menubar.getHeight()

    # Setup Frames for settings
    # We have 2 frames: Basic and Advanced
    # Basic is 1 column and consist of two rows: General and Layer
    # Advanced is 2 columns, first column consist of General, second column consists of Preview and Layer
    margin=GRect(2,2,0,0)
    settingsrowheight=26

    debugFrames=False # for debugging we want to see each frame with a different color

    # Make Layer Edit sidebar
    frameEdit=Frame(screen,
                     rect=GRect(settingsleft, viewport_yoffset, settingscolwidth,windowheight - viewport_yoffset),
                     text="Layer Edit Settings",topoffset=0,
                     drawbackground=debugFrames,backcolor=(255,0,0),
                     drawborder=debugFrames,margin=GRect(settingslabelmargin,settingslabelmargin,0,0),
                     layout=Frame.TOPDOWN,spacing=14,gridsize=-1,
                     )

    # Number of transparent layer below current to show
    frow = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingslabelwidth)
    frow.append(Label(screen, text="Shadow Layers", rect=GRect(0, 0, settingslabelwidth + settingstextboxwidth - 120, 20)))
    frow.append(ScrollBarH(screen,GRect(0,0,settingstextboxwidth*2,settingsrowheight),minScroll=1, maxScroll=100, curScroll=1,func_on_click=readShadowLayers))
    frameEdit.append(frow)

    # Brush shape (square/round/filled/open/text)
    frow = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingslabelwidth)
    frow.append(Label(screen, text="Brush shape", rect=GRect(0, 0, settingslabelwidth + settingstextboxwidth - 120, 20)))

    frowsub = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingsrowheight*2)
    group=[]
    # Full circle
    img = pygame.Surface((settingsrowheight, settingsrowheight))
    pygame.draw.circle(img, (0, 0, 0), (settingsrowheight//2, settingsrowheight//2), settingsrowheight//2-2, 0)
    frowsub.append(Checkbox(screen, GRect(0, 0, settingsrowheight, settingsrowheight),
                         type=Checkbox.image,borderwidth=0,selectborderwidth=3, img=img,func_on_click=setBrushShapeRoundFilled,group=group))
    # Full Square
    img = pygame.Surface((settingsrowheight, settingsrowheight))
    pygame.draw.rect(img, (0, 0, 0), (2,2,settingsrowheight-4, settingsrowheight-4), 0)
    frowsub.append(Checkbox(screen, GRect(0, 0, settingsrowheight, settingsrowheight),
                            type=Checkbox.image, borderwidth=0,selectborderwidth=3, img=img, func_on_click=setBrushShapeSquareFilled,group=group))
    # Open circle
    #img = pygame.Surface((settingsrowheight, settingsrowheight))
    #pygame.draw.circle(img, (0, 0, 0), (settingsrowheight//2, settingsrowheight//2), settingsrowheight//2-2, 2)
    #frowsub.append(Checkbox(screen, GRect(0, 0, settingsrowheight, settingsrowheight),
    #                     type=Checkbox.image,borderwidth=0,selectborderwidth=3, img=img,func_on_click=setBrushShapeRoundOpen,group=group))
    # Open Square
    #img = pygame.Surface((settingsrowheight, settingsrowheight))
    #pygame.draw.rect(img, (0, 0, 0), (2, 2, settingsrowheight - 4, settingsrowheight - 4), 2)
    #frowsub.append(Checkbox(screen, GRect(0, 0, settingsrowheight, settingsrowheight),
    #                        type=Checkbox.image, borderwidth=0,selectborderwidth=3, img=img, func_on_click=setBrushShapeSquareOpen,group=group))

    # ABC
    img = pygame.Surface((settingsrowheight, settingsrowheight))
    font = pygame.font.SysFont(defFontName, defFontSize)
    font.set_bold(True)
    font.set_underline(True)
    textsurface = font.render("Abc", True, (0,0,0))
    img.blit(textsurface, (0,0),(0, 0, img.get_width(), img.get_height() ))
    #frowsub.append(Checkbox(screen, GRect(0, 0, settingsrowheight, settingsrowheight),
    #                        type=Checkbox.image, borderwidth=0,selectborderwidth=3, img=img, func_on_click=None,group=group))

    frow.append(frowsub)
    frameEdit.append(frow)

    # Brush size
    frow = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingslabelwidth)
    frow.append(Label(screen, text="Brush size", rect=GRect(0, 0, settingslabelwidth + settingstextboxwidth - 120, 20)))
    frow.append(ScrollBarH(screen,GRect(0,0,settingstextboxwidth*2,settingsrowheight),minScroll=1, maxScroll=50, curScroll=1,func_on_click=setBrushSize))
    frameEdit.append(frow)

    # Brush depth
    frow = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingslabelwidth)
    frow.append(Label(screen, text="Brush depth", rect=GRect(0, 0, settingslabelwidth + settingstextboxwidth - 120, 20)))
    frow.append(ScrollBarH(screen, GRect(0, 0, settingstextboxwidth * 2, settingsrowheight), minScroll=1, maxScroll=10,curScroll=1, func_on_click=setBrushDepth))
    frameEdit.append(frow)

    # Brush depth until bottom reached?
    frow = Frame(screen,
                 rect=GRect(0, 0, settingslabelwidth + settingstextboxmargin + settingstextboxwidth, settingsrowheight),
                 text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                 layout=Frame.LEFTRIGHT, spacing=4, gridsize=settingslabelwidth)
    frow.append(Label(screen, text="", rect=GRect(0, 0, settingslabelwidth + settingstextboxwidth - 120, 20)))
    frowsub = Frame(screen,
                    rect=GRect(0, 0, settingstextboxmargin + settingstextboxwidth,settingsrowheight),
                    text="", drawborder=False, drawbackground=False, margin=GRect(0, 0, 0, 0), topoffset=0,
                    layout=Frame.LEFTRIGHT, spacing=4, gridsize=-1)
    frowsub.append(Label(screen, text="To bottom", rect=GRect(0, 0, settingslabelwidth + settingstextboxwidth - 120, 20)))
    frowsub.append(Checkbox(screen,GRect(0,0,settingsrowheight,settingsrowheight),type=Checkbox.checkbox,func_on_click=setBrushDepth2Bottom))
    frow.append(frowsub)
    frameEdit.append(frow)

    # Multiple brushes, e.q. cylinder to bottom, small to large diameter towards bottom, draw angled to bottom
    # Undo


# Some call backs from EditFrame
def setBrushDepth(depth):
    global brushDepth
    brushDepth=depth
def setBrushDepth2Bottom(checked):
    global brushDepth2Bottom
    brushDepth2Bottom = checked
def setBrushSize(size):
    global brushSize
    brushSize=size
def setBrushShapeSquareOpen(checked):
    global brushShape
    if checked: brushShape=BSSQUARE | BSOPEN
def setBrushShapeSquareFilled(checked):
    global brushShape
    if checked: brushShape=BSSQUARE | BSFILLED
def setBrushShapeRoundOpen(checked):
    global brushShape
    if checked: brushShape=BSROUND | BSOPEN
def setBrushShapeRoundFilled(checked):
    global brushShape
    if checked: brushShape = BSROUND | BSFILLED


def applyResinSettings():
    """ Applies the selected resin settings.
    """
    global resins
    global resincombo
    global resinlist
    global photonfile
    global frameMode

    # Check if photonfile is loaded
    if photonfile==None: return

    # Check if user didn't select title (first item)
    if frameMode==MODEADVANCED:
        resinname=resincombo.text
        resinidx=resincombo.index
    elif frameMode==MODEBASIC:
        resinname = resinlist.activeText()
        resinidx = resinlist.activeIndex()
    else:return
    if resinname.startswith("Brand"): return

    # columns are Brand,Type,Layer Height,NormalExpTime,OffTime,BottomExp,BottomLayers
    (sBrand,sType,sLayerHeight,sNormalExpTime,sOffTime,sBottomExp,sBottomLayers,sAuthor,sTemp,sComment1,sComment2)=resins[resinidx]
    print ("Apply resinSettings: ",sBrand,sType,sLayerHeight)
    # Convert all strings to floats/int
    rLayerHeight=float(sLayerHeight.replace(",","."))
    rNormalExpTime = float(sNormalExpTime.replace(",","."))
    rOffTime=float(sOffTime.replace(",","."))
    rBottomExp=float(sBottomExp.replace(",","."))
    rBottomLayers=int(sBottomLayers)
    #print (sBrand, rLayerHeight,rNormalExpTime, rOffTime, rBottomExp, rBottomLayers)

    # Check if we apply settings with same layer height
    fileHeight=PhotonFile.bytes_to_float(photonfile.Header["Layer height (mm)"])
    fileHeight=(int(100*fileHeight))/100
    if not fileHeight==rLayerHeight:
        dialog = MessageDialog(flipFunc,screen, pos=(140, 140), width=450,
                               title="Please confirm",
                               message="The settings are meant for Layer Height "+str(rLayerHeight)+" mm.\n"+\
                                       "Your file is sliced at a Layer Height of "+str(fileHeight)+" mm.",
                               center=True,
                               buttonChoice=MessageDialog.OKCANCEL,
                               parentRedraw=redrawWindow)
        print ("window",window)
        ret = dialog.show()
        # if user selected ok, the users want to overwrite file so set okUser to True
        if not ret == "OK": return

    # Set Header/General settings
    #photonfile.Header["Layer height (mm)"]=PhotonFile.float_to_bytes(rLayerHeight)
    photonfile.Header["Exp. time (s)"] = PhotonFile.float_to_bytes(rNormalExpTime)
    photonfile.Header["Off time (s)"] = PhotonFile.float_to_bytes(rOffTime)
    photonfile.Header["Exp. bottom (s)"] = PhotonFile.float_to_bytes(rBottomExp)
    photonfile.Header["# Bottom Layers"] = PhotonFile.int_to_bytes(rBottomLayers)

    # Set settings of each layer
    cLayerHeight=0
    for layerNr, layerDef in enumerate(photonfile.LayerDefs):
        #layerDef["Layer height (mm)"]=PhotonFile.float_to_bytes(cLayerHeight)
        #cLayerHeight=cLayerHeight+rLayerHeight
        if layerNr<rBottomLayers:
            layerDef["Exp. time (s)"]=PhotonFile.float_to_bytes(rBottomExp)
        else:
            layerDef["Exp. time (s)"] = PhotonFile.float_to_bytes(rNormalExpTime)
        layerDef["Off time (s)"] = PhotonFile.float_to_bytes(rOffTime)
    refreshHeaderSettings()
    refreshLayerSettings()


########################################################################################################################
##  Save user preferences
########################################################################################################################

def loadUserPrefs():
    """ Loads user settings from settings.ini to global variables
        e.g. last path opened, settings adv/basic
    """
    global frameMode
    global settingsMode
    global lastLoadDir
    global recentLoaded
    global disableOpenGL
    global peelTime
    global pyopenglIsAvailable

    # If we are not in Win32 we load locally, else we save in Documents
    dir=os.getcwd()
    if sys.platform == "win32": dir=os.path.expanduser("~\\Documents\PhotonFileEditor\\")
    path=os.path.join(dir,"settings.ini")

    # Set default lastLoadDir
    lastLoadDir=os.getcwd()

    # Settings.ini could be absent or wrongly edited by user
    try:
        parser = configparser.ConfigParser()
        parser.read(path)
        if parser.has_option("General","UserMode"): frameMode=parser.getint("General","UserMode")
        settingsMode = frameMode
        if parser.has_option("General", "DisableOpenGL"):disableOpenGL=parser.getboolean("General","DisableOpenGL")
        if parser.has_option("General", "PeelTime"):peelTime=parser.getfloat("General","peelTime")
        if parser.has_option("General", "LastLoadDir"):lastLoadDir= parser.get("General","LastLoadDir")
        for recIdx in range(0,9):
            recStr="Recent"+str(recIdx)
            if parser.has_option("General", recStr):
                recentFile = parser.get("General",recStr)
                recentLoaded.append(recentFile.strip())
    except Exception as err:
        print(err)

    if disableOpenGL:
        if pyopenglIsAvailable: print ("OpenGL is available, but is disabled by user.")


def saveUserPrefs():
    """ Save user settings to settings.ini from global variables
        e.g. last path opened, settings adv/basic
    """
    global settingsMode
    global disableOpenGL
    global peelTime
    global lastLoadDir

    parser = configparser.ConfigParser()
    parser.add_section("General")
    parser.set("General", "UserMode", str(settingsMode))
    parser.set("General", "DisableOpenGL", str(disableOpenGL))
    parser.set("General", "PeelTime", str(peelTime))
    parser.set("General", "LastLoadDir", lastLoadDir)
    for idx,recent in enumerate(recentLoaded):
        recStr="Recent"+str(idx)
        parser.set("General", recStr, recent)

    # If we are not in Win32 we save locally, else we save in Documents
    dir=os.getcwd()
    if sys.platform == "win32":
        dir = os.path.expanduser("~\\Documents\PhotonFileEditor\\")
        if not os.path.isdir(dir):
            try:
                os.mkdir(dir)
            except Exception as err:
                print (err)
    path=os.path.join(dir,"settings.ini")
    file=open(path,'w')
    parser.write(file)
    file.close()

########################################################################################################################
##  Setup windows, pygame, menu and controls
########################################################################################################################

def createWindow():
    """ Create all labels and input boxes to edit the general, preview and current layer settings of the photonfile. """
    global window
    global screen
    global dispimg
    global layerimg
    global previmg
    global gridimg
    global windowwidth
    global windowheight
    global settingsleft
    global settingswidth
    global controls
    global layerNr
    global menubar
    global layerLabel
    global filename
    global numpyAvailable
    global pyopenglIsAvailable
    global layerRect
    global gl

    # For debugging we display current script-path and last modified date, so we know which version we are testing/editing
    scriptPath=os.path.join(os.getcwd(), "PhotonEditor.py")
    scriptDateTime=time.ctime(os.path.getmtime(scriptPath))
    print ("Script Info:")
    print ("  "+ scriptPath)
    print("  " + str(scriptDateTime))

    # Init pygame, fonts
    pygame.init()
    pygame.font.init()
    # Set window frame properties
    pygame.display.set_caption("Photon File Editor")
    logo = pygame.image.load("PhotonEditor.png")
    pygame.display.set_icon(logo)

    # Create window
    if not pyopenglIsAvailable or disableOpenGL:
        # Create a window surface we can draw the menubar, controls and layer/preview  bitmaps on
        #window = pygame.display.set_mode((windowwidth, windowheight))
        if frameMode == MODEBASIC:
            settingswidth = settingscolwidth * 2 # 1 columns
        elif frameMode == MODEADVANCED:
            settingswidth = settingscolwidth * 2  # 2 columns
        windowwidth = settingsleft + settingswidth
        window = pygame.display.set_mode((windowwidth, windowheight))

    # Create a surface
    if not pyopenglIsAvailable or disableOpenGL:
        screen = pygame.Surface((windowwidth,windowheight))
    else:
        screen = pygame.Surface((1024, 1024))
        screen.set_colorkey(defTransparent)
        gl = GL((windowwidth, windowheight), handleGLCallback)

    print ("Window Size:", windowwidth,windowheight)


    # Initialize the surfaces for layer/preview images we want to fill from photonfile and draw on screen
    scale = (0.25, 0.25)
    dispimg = pygame.Surface((int(1440 * scale[0]), int(2560 * scale[1])))
    dispimg.fill(defTransparent) # first we fill with transparent
    previmg[0]=dispimg
    previmg[1] = dispimg
    layerimg = dispimg

    # Make grid for edit with large zoom
    gridimg = pygame.Surface((int(1440 * scale[0]), int(2560 * scale[1])))
    gridcol = Color(100,100,100)
    transcol= Color(0,0,0,0)
    gridimg.fill(transcol)
    gridimg.set_colorkey(transcol)
    for row in range (0, int(2560 * scale[1]), 4):
        pygame.draw.line(gridimg, gridcol, (0,row), (1440 * scale[0], row))
    for col in range (0, int(1440 * scale[1]), 4):
        pygame.draw.line(gridimg, gridcol, (col,0), (col,2560 * scale[0]))

    #display Nag screen on image
    disclaimerString= "" \
    "Disclaimer:\n" \
    "_______________________________\n" \
    "\n" \
    "Use this at your own risk!\n" \
    "\n" \
    "Backup your photon files before using \n" \
    "them in the software! Verify and dry \n" \
    "test your files before doing a produc-\n" \
    "tion run! \n" \
    "\n" \
    "By using this software you accept the \n" \
    "licence available in the Github reposi- \n" \
    "tory of this project. This means you \n"\
    "accept all risks and you can hold no-\n" \
    "one liable for any damage! \n\n\n"

    #display warnings about numpy
    libraryString=""
    if not numpyIsAvailable or not pyopenglIsAvailable:
        libraryString = "_______________________________\n\n"
    print ("numpyIsAvailable ",numpyIsAvailable )
    if not numpyIsAvailable :
        libraryString = libraryString + \
        "> PhotonFileEditor works faster if you \n" \
        "   install numpy!\n\n"
    if not pyopenglIsAvailable:
        libraryString = libraryString + \
        "> If you install pyOpenGl the built-in\n" \
        "   slicer and voxel viewer will become\n"\
        "   available in the future!"

    fontDisclaimer = pygame.font.SysFont(defFontName, defFontSize-2)
    for nr,line in enumerate(disclaimerString.split("\n")):
        if nr==0:
            fontDisclaimer.set_bold(True)
        if nr==1:
            fontDisclaimer.set_bold(False)
        textsurface = fontDisclaimer.render(line, True, (255,255,255))
        dispimg.blit(textsurface, (18,180+nr*defFontSize))

    for nr,line in enumerate(libraryString.split("\n")):
        textsurface = fontDisclaimer.render(line, True, (255,255,255))
        dispimg.blit(textsurface, (18,420+nr*defFontSize))


    # Create the menu and setup the menu methods which handle the users actions
    createMenu()
    global layerRect
    layerRect.y=menubar.getHeight()
    layerRect.height=windowheight-layerRect.y
    #print ("layerRect: ",layerRect)

    # Create sidebar to display the settings of the photonfile
    createSidebarSettings()
    createSidebarEdit()

    # Create layer controls to navigate (up and down) the layers (and display another layer)
    createLayernavigation()

    # Create toolbar to do layer operations from edit menu
    createLayerOperations()

    # Create statusbar below sidebar
    createStatusBar()

def updateTextBox2PhotonFile(control, val,linkedData):
    """ Saves value in current textbox to the correct setting in the PhotonFile object. """

    global photonfile
    # If no photonfile nothing to save, so exit
    if photonfile==None: return

    # Meta-info of current the PhotonFile setting in 'control' was stored in each textbox and retrieved
    pVarGroup=linkedData["VarGroup"]
    pTitle= linkedData["Title"]
    pBNr = linkedData["NrBytes"]
    pType = linkedData["Type"]

    # Check if user input 'val' is of correct type and length
    bytes = None  # if pType not recognized we return bytes=None
    if pType == PhotonFile.tpChar: bytes=PhotonFile.hex_to_bytes(val)
    if pType == PhotonFile.tpByte: bytes = PhotonFile.hex_to_bytes(val)
    if pType == PhotonFile.tpInt: bytes = PhotonFile.int_to_bytes(int(val))
    if pType == PhotonFile.tpFloat: bytes = PhotonFile.float_to_bytes(float(val))
    if not len(bytes)==pBNr:
        print ("Error: Data size ("+str(len(bytes))+") not expected ("+str(pBNr)+")in PhotonViewer.updateTextBox2PhotonFile!")
        print ("  Metadata: ", linkedData)
        print ("  Value: ", val)
        print ("  Bytes: ", bytes)
        return

    # Save setting to photonfile
    if not bytes==None:
        if pVarGroup=="Header":
            propHeader2LayerDefs(pTitle, bytes)
            photonfile.Header[pTitle]=bytes
        if pVarGroup=="Preview":photonfile.Previews[prevNr][pTitle]=bytes
        if pVarGroup=="LayerDef": photonfile.LayerDefs[layerNr][pTitle] = bytes
    #print ("Found. New Val: ",val,linkedData)


def propHeader2LayerDefs(pTitle,newbytes):
    """ Updates layerdef settings if exp. (bottom) time, off time or layer height is adjusted in General settings.
    """
    oldbytes=photonfile.Header[pTitle]
    if oldbytes==newbytes: return

    # Save exposure time and off time to layerdefs (should always be equal, and ignored in layerdefs by photon printer
    nrBottomLayers =  PhotonFile.bytes_to_int(photonfile.Header["# Bottom Layers"])
    if pTitle == "Layer height (mm)":
        newHeight=PhotonFile.bytes_to_float(newbytes)

    # First traverse the bottom layers
    currHeight=0
    for lNr in range(0,nrBottomLayers):
        if pTitle == "Exp. bottom (s)":photonfile.LayerDefs[lNr]["Exp. time (s)"] = newbytes
        if pTitle == "Off time (s)": photonfile.LayerDefs[lNr]["Off time (s)"]=newbytes
        if pTitle == "Layer height (mm)":
            photonfile.LayerDefs[lNr]["Layer height (mm)"]=PhotonFile.float_to_bytes(currHeight)
            currHeight=lNr*newHeight

    # Next traverse the normal layers
    for lNr in range(nrBottomLayers,photonfile.nrLayers()):
        if pTitle == "Exp. time (s)": photonfile.LayerDefs[lNr]["Exp. time (s)"] = newbytes
        if pTitle == "Off time (s)": photonfile.LayerDefs[lNr]["Off time (s)"] = newbytes
        if pTitle == "Layer height (mm)":
            photonfile.LayerDefs[lNr]["Layer height (mm)"]=PhotonFile.float_to_bytes(currHeight)
            currHeight=lNr*newHeight

    #We need to upate data in displayer layer setting
    if pTitle == "Exp. bottom (s)" or \
            pTitle == "Exp. time (s)" or \
            pTitle == "Off time (s)" or \
            pTitle == "Layer height (mm)":
        refreshLayerSettings()

def saveGeneralSettings2PhotonFile():
    """ Saves all textboxes in the general settingsgroup """

    #print ("saveGeneralSettings2PhotonFile")
    global photonfile
    global controlsGeneral

    # If no photonfile nothing to save, so exit
    if photonfile==None:return

    # Check for each general setting in PhotonFile if it is editable, control index in controls and update setting
    for row, (bTitle, bNr, bType,bEditable,bHint) in enumerate(PhotonFile.pfStruct_Header):#enum start at 22
        if bEditable:
            textBox=controlsGeneral[row]
            #print (row,bTitle,textBox.text)
            updateTextBox2PhotonFile(textBox,textBox.text,{"VarGroup": "Header", "Title": bTitle, "NrBytes": bNr, "Type": bType})


def savePreviewSettings2PhotonFile():
    """ Saves all textboxes in the preview settingsgroup """

    #print("savePreviewSettings2PhotonFile")
    global photonfile
    global prevNr
    global controlsPreviews

    # If no photonfile nothing to save, so exit
    if photonfile==None:return

    # Check for each preview setting in PhotonFile if it is editable, control index in controls and update setting
    for row, (bTitle, bNr, bType,bEditable, bHint) in enumerate(PhotonFile.pfStruct_Previews):
        if bEditable:
            textBox=controlsPreviews[row]
            print (row,bTitle,textBox.text)
            updateTextBox2PhotonFile(textBox,textBox.text,{"VarGroup": "Preview", "Title": bTitle, "NrBytes": bNr, "Type": bType})


def saveLayerSettings2PhotonFile():
    """ Saves all textboxes in the layer settingsgroup """

    #print ("saveLayerSettings2PhotonFile")
    global photonfile
    global layerNr
    global controlsLayers

    # If no photonfile nothing to save, so exit
    if photonfile == None: return

    # Check for each layer setting in PhotonFile if it is editable, control index in controls and update setting
    for row, (bTitle, bNr, bType, bEditable, bHint) in enumerate(PhotonFile.pfStruct_LayerDef):
        if bEditable:
            textBox=controlsLayers[row]
            #print (row,bTitle,textBox.text)
            updateTextBox2PhotonFile(textBox,textBox.text,{"VarGroup": "LayerDef", "Title": bTitle, "NrBytes": bNr, "Type": bType})


def refreshHeaderSettings():
    """ Updates all textboxes in the general settingsgroup with data from photonfile"""
    global photonfile

    # If no photonfile nothing to save, so exit
    if photonfile==None:return

    # Travers all general settings and update values in textboxes
    for row, (bTitle, bNr, bType,bEditable,bHint) in enumerate(PhotonFile.pfStruct_Header):
        nr=PhotonFile.convBytes(photonfile.Header[bTitle],bType)
        if bType==PhotonFile.tpFloat:
            nr=round(nr,3) #round floats to 3 decimals
            snr=str(nr)
            nrDec=len(snr)-snr.index('.')-1
            if nrDec>3:snr=snr[:len(snr)-(nrDec-3)]
        else:
            snr = str(nr)
        controlsGeneral[row].setText(snr)


def refreshPreviewSettings():
    """ Updates all textboxes in the preview settingsgroup with data from photonfile"""
    global photonfile
    global prevNr
    global labelPrevNr
    global prevImgBox

    # If no photonfile nothing to save, so exit
    if photonfile == None: return

    print ("prevNr: ",prevNr)
    # Travers all preview settings and update values in textboxes
    labelPrevNr.setText(str(prevNr)+"/2") # Update preview counter
    for row, (bTitle, bNr, bType,bEditable, bHint) in enumerate(PhotonFile.pfStruct_Previews):
        nr=PhotonFile.convBytes(photonfile.Previews[prevNr][bTitle],bType)
        if bType == PhotonFile.tpFloat: nr = round(nr, 4) #round floats to 4 decimals
        controlsPreviews[row].setText(str(nr))

    # put it in imgbox, however image box will stretch img to fit
    prevImg=photonfile.getPreviewBitmap(0,(settingslabelwidth+settingstextboxwidth))
    w,h=prevImg.get_size()
    dy=(prevImgBox.rect.height-h)/2
    prevImgBox.img.fill(defFormBackground)
    prevImgBox.img.blit(prevImg,dest=(0, dy))
    prevImgBox.drawBorder=True
    #alternative implementation
    #canvas=pygame.Surface((prevImgBox.rect.width, prevImgBox.rect.height))
    #canvas.fill(defFormBackground)
    #canvas.blit(prevImg,dest=(0, 0))
    #prevImgBox.img=canvas

def refreshLayerSettings():
    """ Updates all textboxes in the layer settingsgroup with data from photonfile"""
    global photonfile
    global layerNr
    global layerLabel
    global labelLayerNr

    # If we have no photonfile loaded of there are no layers in the file there is nothing to save, so exit
    if photonfile==None:return
    if photonfile.nrLayers() == 0: return  # could occur if loading new file

    # Travers all layer settings and update values in textboxes
    labelLayerNr.setText(str(layerNr)+ " / "+str(photonfile.nrLayers())) # Update layer counter
    for row, (bTitle, bNr, bType,bEditable, bHint) in enumerate(PhotonFile.pfStruct_LayerDef):
        nr=PhotonFile.convBytes(photonfile.LayerDefs[layerNr][bTitle],bType)
        #print("reading: ", bTitle,"=",nr)
        if bType==PhotonFile.tpFloat:
            nr=round(nr,3) #round floats to 3 decimals
            snr=str(nr)
            nrDec=len(snr)-snr.index('.')-1
            if nrDec>3:snr=snr[:len(snr)-(nrDec-3)]
        else:
            snr = str(nr)
        controlsLayers[row].setText(snr)

    #finally we update layerLabel in between the up and down ^ on the top left of the screen
    layerLabel.setText(str(layerNr))


def openPhotonFile(filename):
    """ Reads a photonfile from disk and updates all settings and first layer/preview images. """
    global photonfile
    global dispimg
    global layerimg
    global previmg
    global layerNr
    global framedScreenOpenGL

    # Ask PhotonFile to read the file
    photonfile = PhotonFile(filename)
    photonfile.readFile()

    # Updates all settings and first layer/preview images.
    layerNr = 0  # reset this to 0 so we prevent crash if previous photonfile was navigated to layer above the last layer of new photonfile
    layerimg=photonfile.getBitmap(layerNr,layerForecolor,layerBackcolor)
    previmg[0]=photonfile.getPreviewBitmap(0)
    previmg[1] = photonfile.getPreviewBitmap(1)
    dispimg=layerimg
    refreshHeaderSettings()
    refreshPreviewSettings()
    refreshLayerSettings()
    setLayerSliderFromLayerNr()
    framedScreenOpenGL = False


########################################################################################################################
##  Drawing/Event-Polling Loop
########################################################################################################################
fontFullScreen=None

def redrawWindow(tooltip=None):
    """ Redraws the menubar, settings and displayed layer/preview image """
    global pyopenglIsAvailable
    global screen
    global dispimg
    global gridimg
    global windowwidth
    global windowheight
    global fontFullScreen
    global dispimg_offset
    global frameMode

    # Clear window surface
    if not fullScreenOpenGL:
        screen.fill(defFormBackground)
    else:
        screen.fill(defTransparent)
        # Draw user guide
        if fontFullScreen==None:
            fontFullScreen =pygame.font.SysFont(defFontName, defFontSize - 2)

        pygame.draw.rect(screen,defFormBackground,(0,windowheight-24,windowwidth,24),0)
        arrowlr="[img]resources/KeyLeft.png[/img][img]resources/KeyRight.png[/img]"
        arrowud="[img]resources/KeyUp.png[/img][img]resources/KeyDown.png[/img]"
        mouse="[img]resources/Mouse.png[/img]"
        mouseLeft= "[img]resources/MouseL.png[/img]"
        mouseRight= "[img]resources/MouseR.png[/img]"
        mouseScroll= "[img]resources/MouseS.png[/img]"
        #text = "[b]Move[b]:\u2190\u2191\u2193\u2192, [mouse][left]  [b]|[b]  [b]Rotate[b]: [shift]\u2190\u2191\u2193\u2192, [mouse][right]  [b]|[b]  [b]Zoom[b]: [ctrl]\u2191\u2193, [mouse][scroll]  [b]|[b]  [b]Reset[b]: [Q]  [b]|[b]  [b]Slice[b]: [F5]"
        text = "[b]Move[b]:"+arrowud+arrowlr+", "+mouseLeft+\
               " [b]|[b] "+\
               "[b]Rotate[b]: [shift]"+arrowud+arrowlr+", "+mouseRight+\
               " [b]|[b] "+\
               "[b]Zoom[b]: [ctrl]"+arrowud+", "+mouseScroll+\
               " [b]|[b] "+\
               "[b]Reset[b]: [Q]"+\
               " [b]|[b] "+\
               "[b]Model[b]: [Alt]"+\
               " [b]|[b] "+\
               "[b]Slice[b]: [F5]"+\
               " [b]|[b] "+\
               "[b]Layer height[b]: [+,-]"
        drawTextMarkdown(text,fontFullScreen,defFormForeground,screen,(8,windowheight-20))
        return

    # Draw layer/preview images
    w, h = dispimg.get_size()
    #dw = (1440 / 4 - w) / 2
    #dh = (2560 / 4 - h) / 2
    if not photonfile==None:
        if not photonfile.isDrawing:
            #if we display layer image we need to apply zoom
            global layerimg
            global shadowimg
            global menubar
            if  dispimg==layerimg:
                # display current layer and scale back
                global dispimg_offset
                global dispimg_zoom
                scimg=pygame.transform.scale(dispimg,(int(dispimg_zoom/4*1440),int(dispimg_zoom/4*2560)))
                # if we are in edit mode, we display shadow images
                if not shadowimg==None and frameMode==MODEEDIT:
                    shadowimg = pygame.transform.scale(shadowimg,
                                                   (int(dispimg_zoom / 4 * 1440), int(dispimg_zoom / 4 * 2560)))
                    screen.blit(shadowimg, dest=(0, menubar.getHeight()),
                                   area=Rect(dispimg_offset[0] * dispimg_zoom / 4, dispimg_offset[1] * dispimg_zoom / 4,1440 / 4, 2560 / 4)
                                   )  # dest is pos to blit to, area is rect of source/dispimg to blit from
                    scimg.set_colorkey((0,0,0)) # and we make black of current layer transparent
                # blit the current layer
                screen.blit(scimg,
                            dest=(0, menubar.getHeight()),
                            area=Rect(dispimg_offset[0]*dispimg_zoom/4,dispimg_offset[1]*dispimg_zoom/4,1440/4,2560/4)
                            ) #dest is pos to blit to, area is rect of source/dispimg to blit from
                # if we are in edit mode, we display cursor
                if frameMode == MODEEDIT:
                    global brushSize, brushShape, brushDepth, brushDepth2Bottom, cursorpos, layerRect
                    gpos = GPoint.fromTuple(cursorpos)
                    if gpos.inGRect(layerRect):
                        displace = (-2-brushSize, -2-brushSize)
                        cursorimg = pygame.Surface((brushSize, brushSize))
                        transcol = Color(0, 0, 0, 0)
                        cursorimg.fill(transcol)
                        cursorimg.set_colorkey(transcol)
                        if brushShape & BSROUND:pygame.draw.circle(cursorimg, (255, 0, 0), (brushSize // 2, brushSize // 2),brushSize // 2 , not brushShape & BSFILLED)
                        if brushShape & BSSQUARE:pygame.draw.rect(cursorimg, (255, 0, 0), (0, 0, brushSize, brushSize), not brushShape & BSFILLED)
                        pixCoord = [cursorpos[0] + displace[0],cursorpos[1] + displace[1] ]
                        # If we zoomed to pixelsize>1, we need to scale up (and pixelate) the cursor as well as snap it to the grid
                        if dispimg_zoom>4:
                            # Scale up (and pixelate) the cursor
                            nBrushSize=int(brushSize*dispimg_zoom / 4)
                            cursorimg = pygame.transform.scale(cursorimg,(nBrushSize ,nBrushSize))
                            # We need to snap pixCoord to grid
                            x=pixCoord[0]
                            y=pixCoord[1]
                            y=y-menubar.getHeight() # remove height from menubar since it can have a height not a multiple of gridsize
                            x = x - x % (dispimg_zoom / 4)
                            y = y - y % (dispimg_zoom / 4)
                            y=y+menubar.getHeight()
                            pixCoord=[x,y]
                        screen.blit(cursorimg,dest=pixCoord)
                    if dispimg_zoom>4: screen.blit(gridimg,(0,menubar.getHeight()))
            else:
                screen.blit(dispimg,
                            dest=(0, menubar.getHeight()+(2560/4-menubar.getHeight()-dispimg.get_height())/2),
                            )  # dest is pos to blit to, area is rect of source/dispimg to blit from
    else:#also if we have no photonfile we still need to draw to cover up menu/filedialog etc
        screen.blit(dispimg, dest=(0, menubar.getHeight()))

    if framedScreenOpenGL:
        scale = (0.25, 0.25)
        dispimg = pygame.Surface((int(1440 * scale[0]), int(2560 * scale[1])))
        dispimg.fill((defTransparent))
        pygame.draw.rect(screen,defTransparent,(0,0,int(1440 * scale[0]), int(2560 * scale[1])),0)

    # Redraw Sidebar
    frameActive().redraw()

    # Redraw other controls
    for ctrl in layercontrols:
      ctrl.redraw()

    # Redraw Statusbar
    statusbar.redraw()

    # Redraw Menubar
    menubar.redraw()

    # Redraw (cursor of) layer slider
    global layerSlider_visible
    if layerSlider_visible:
        if layerCursorActive and not photonfile==None and dispimg==layerimg:
            pygame.draw.rect(screen, (0, 0, 150), scrollLayerRect.tuple(), 1)
            pygame.draw.rect(screen, (0,0,255), layerCursorRect.tuple(), 0)

    # Redraw tooltip
    if not tooltip==None:
        tooltip.redraw()
        print (screen.get_size() ,tooltip.rect)


def setLayerSliderFromLayerNr():
    """ Calculates correct position of layerscroll indicator from layerNr.
        (Used after layer navigation buttons are used.
    """
    global photonfile
    global scrollLayerRect
    global layerCursorRect
    global layerNr

    if not photonfile==None:
        if photonfile.nrLayers()>1:
            relY = layerNr / int(photonfile.nrLayers() - 1)
        else: relY=0
    else: relY=0
    scrnY=relY * (2560 / 4 - scrollLayerVMargin * 2)+scrollLayerVMargin
    layerCursorRect = scrollLayerRect.copy()
    layerCursorRect.y = scrnY - 2
    layerCursorRect.height = 4


imgPrevLoadTime=0 # keeps time since last img load and used to prevent to many image load
layerSlider_visible=True
def handleLayerSlider(checkRect=True):
    """ Checks if layerslider is used (dragged by mouse) and updates layer image and settings"""
    global layerSlider_visible
    if not layerSlider_visible: return

    global photonfile
    global dispimg
    global layerimg
    global layerBackcolor
    global layerForecolor
    global layerNr
    global scrollLayerRect
    global scrollLayerVMargin
    global scrollLayerWidth
    global layerCursorRect
    global imgPrevLoadTime


    # Check if mouse is in area of layerSlider (only needed on mousedown) of check is not needed (checkOk==Truel; if mouse dragged)
    checkOk=True
    pos = pygame.mouse.get_pos()
    mousePoint = GPoint.fromTuple(pos)
    if checkRect: checkOk=mousePoint.inGRect(scrollLayerRect)

    # If no photonfile we have nothing to do
    if not photonfile == None:
        if checkOk:
            # Calc position of layerCursor based on Y of mouse cursor and from this the selected layer number
            relY = (mousePoint.y - scrollLayerVMargin) / (2560 / 4 - scrollLayerVMargin * 2)
            if relY<0: relY=0
            if relY>1: relY=1
            layerNr = round((photonfile.nrLayers() - 1) * relY)
            layerCursorRect = scrollLayerRect.copy()
            layerCursorRect.y = (relY*(2560 / 4 - scrollLayerVMargin * 2)+scrollLayerVMargin) - 2
            layerCursorRect.height = 4
            # Get image of new layer, display and update layer settings
            secSincePrevLoad = time.time()-imgPrevLoadTime
            if secSincePrevLoad>0.1: # to not overload the pc, we have a minimal interval between images (in sec)
                waitForImg=True
                layerimg = photonfile.getBitmap(layerNr, layerForecolor, layerBackcolor)
                dispimg = layerimg
                refreshLayerSettings()
                imgPrevLoadTime = time.time()
            return True
        else:
            return False
            # layerCursorActive=False
        # print (event.button)


def activeControlIdx():
    global controlsSettings
    """ Returns first textbox in controls where cursorActive is True. """
    for idx, control in enumerate(controlsSettings):
        if type(control) == TextBox:
            if control.cursorActive == True: return idx
    return None

# Define a variable to control the main loop
running = True
gl=None

def init():
    global gl,flipFunc, pyopenglIsAvailable, disableOpenGL

    # Load user preferences
    loadUserPrefs()

    # Link to correct display flip function
    if pyopenglIsAvailable and not disableOpenGL:
        flipFunc = flipOGL
    else:
        flipFunc = flipSDL

    # Initialize the pygame module and create the window
    createWindow()
    # Init lastpos mouse hovered
    lastpos=(0,0) # stores last position for tooltip
    loop()
    # load user preferences
    saveUserPrefs()

def loop():
    # Main loop
    while running:
        poll()
        flipFunc()
    pygame.quit()

def frameActive():
    global frameMode
    global MODEBASIC
    global MODEADVANCED
    global MODEEDIT
    global frameBasic
    global frameAdvanced
    global frameEdit
    if frameMode == MODEBASIC:return frameBasic
    elif frameMode == MODEADVANCED:return frameAdvanced
    elif frameMode == MODEEDIT:return frameEdit

dragDistance=None
def checkMouseDrag(pos,event):
    global mouseDrag,prevMouseDragPos,dragDistance, layerRect
    gpos=GPoint.fromTuple(pos)
    #if event.type == pygame.MOUSEBUTTONDOWN and gpos.inGRect(layerRect): mouseInitDrag=True#mouseDrag=True
    if event.type == pygame.MOUSEBUTTONUP:mouseDrag = False
    if event.type == pygame.MOUSEMOTION and not gpos.inGRect(layerRect):mouseDrag=False

    # extra check
    if event.type == pygame.MOUSEMOTION:
        if not (pygame.mouse.get_pressed()[0] or
                pygame.mouse.get_pressed()[1] or
                pygame.mouse.get_pressed()[2]): mouseDrag = False
        else:
            mouseDrag=True
    # store previous pos
    if not prevMouseDragPos==None:
        dragDistance=(pos[0]-prevMouseDragPos[0],pos[1]-prevMouseDragPos[1])
    else:
        dragDistance=(0,0)
    if mouseDrag:
        prevMouseDragPos=pos
    else:
        prevMouseDragPos=None

drawQueue=[]
def storeDrawQueue():
    global drawQueue
    global layerNr

    # Since store can take a while show a be-patient message
    popup = ProgressDialog(flipFunc, screen, pos=(140, 140),
                           title="Please wait...",
                           message="Photon File Editor is storing your edits.")
    popup.show()

    # Now traverse all layers and check for each drawcmd if it affects the layer
    for lNr in range(0,layerNr+1):
        # Check all drawcmds against this layer
        layerQueue=[]
        for drawCmd in drawQueue:
            (brushShape, brushSize, brushDepth, brushDepth2Bottom, pcolor, pixRect, pixCenter, pixRadius)=drawCmd
            lowestLayer = -1
            if not brushDepth2Bottom: lowestLayer = layerNr - ( brushDepth - 1 )
            if lNr>=lowestLayer and lNr<=layerNr:
                layerQueue.append(drawCmd)

        # Edit layer if cmds found
        if len(layerQueue)>0:
            editLayer = photonfile.getBitmap(lNr, layerForecolor, layerBackcolor, (1, 1))
            for (brushShape, brushSize, brushDepth, brushDepth2Bottom, pcolor, pixRect, pixCenter, pixRadius) in layerQueue:
                if brushShape & BSROUND:pygame.draw.circle(editLayer, pcolor, pixCenter,pixRadius, (not brushShape & BSFILLED)*2)
                if brushShape & BSSQUARE:pygame.draw.rect(editLayer, pcolor, pixRect, (not brushShape & BSFILLED)*6)
                # Ask PhotonFile object to replace bitmap
            photonfile.replaceBitmap(lNr, editLayer, False)

    # Clear queue
    drawQueue.clear()

def poll(event=None):
    """ Entrypoint and controls the rest """
    global layercontrols
    global controlsSettings
    global frameMode
    global frameBasic
    global frameAdvanced
    global settingsMode
    global menubar
    global sliderDrag
    global mouseDrag
    global running
    global photonfile
    global window
    global screen
    global lastpos
    global fullScreenOpenGL
    global framedScreenOpenGL
    global dispimg_zoom
    global dispimg_offset
    global layerimg
    global dispimg
    global layerForecolor
    global layerBackcolor
    global editLayerMode
    global layercontrols
    global layerSlider_visible

    tooltip=None
    for event in pygame.event.get():
    #event = pygame.event.wait()

        #Check if fullscreen OpenGL
        if fullScreenOpenGL:
            if event.type == pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    fullScreenOpenGL = False
                    return
            gl.poll(True, event)
            return

        # Event handling, gets all event from the eventqueue
        #for event in pygame.event.get():
        #if not hasOpenGL: event = pygame.event.wait()

        if pyopenglIsAvailable and not disableOpenGL:
            gl.poll(framedScreenOpenGL,event)

        pos = pygame.mouse.get_pos()
        lastpos=pos
        isNumlockOn = (pygame.key.get_mods() & pygame.KMOD_NUM) == 4096

        # Check if window was closed
        if event.type == pygame.QUIT:
            print("Window was closed. Exit!")
            saveUserPrefs()
            running = False  # change the value to False, to exit the main loop

        if not editLayerMode:
            if event.type == pygame.MOUSEBUTTONUP:
                sliderDrag=False
                if not menubar.handleMouseUp(pos,event.button):
                    frameActive().handleMouseUp(pos,event.button)
                    for ctrl in layercontrols:
                        ctrl.handleMouseUp(pos,event.button)

            if event.type == pygame.MOUSEBUTTONDOWN:
                sliderDrag=handleLayerSlider()
                if not menubar.handleMouseDown(pos,event.button):
                    frameActive().handleMouseDown(pos,event.button)
                    for ctrl in layercontrols:
                        ctrl.handleMouseDown(pos,event.button)

            if event.type == pygame.MOUSEMOTION:
                if sliderDrag: handleLayerSlider(False)
                if not menubar.handleMouseMove(pos):
                    frameActive().handleMouseMove(pos)
                    for ctrl in layercontrols:
                        ctrl.handleMouseMove(pos)


            if event.type == pygame.KEYDOWN :
                #If numlock on then we use it to navigate layers
                if not photonfile==None:
                    if not isNumlockOn:
                        maxLayer = photonfile.nrLayers()
                        page=int(maxLayer/10)
                        if event.key == pygame.K_KP8: layerDown()
                        if event.key == pygame.K_KP9: layerDown(page)
                        if event.key == pygame.K_KP2: layerUp()
                        if event.key == pygame.K_KP3: layerUp(page)
                    if event.key == pygame.K_UP: layerDown()
                    if event.key == pygame.K_DOWN: layerUp()

                #We use tab to navigate the textboxes in controls
                if event.key in (pygame.K_TAB,pygame.K_RETURN,pygame.K_KP_ENTER):
                    # Check shift state, without we move to next, with to previous control
                    isLShift = (pygame.key.get_mods() & pygame.KMOD_LSHIFT)
                    dir=1 if not isLShift else -1
                    # Get control with active cursor
                    prevActive=activeControlIdx()
                    # Check because maybe there is none active
                    if not prevActive==None:
                        # Remove cursor from found control
                        #controls[prevActive].cursorActive=False
                        controlsSettings[prevActive].setFocus(False)
                        # Make first editable textbox we find in direction of dir
                        fnd=False
                        idx=prevActive+dir
                        while not fnd:
                            if type(controlsSettings[idx]) == TextBox and controlsSettings[idx].editable and not fnd:
                                #controls[idx].cursorActive = True
                                controlsSettings[idx].setFocus(True)
                                fnd=True
                            idx=idx+dir
                            if idx>=len(controlsSettings): idx=0
                            if idx<0: idx= len(controlsSettings) - 1

                if event.key == pygame.K_ESCAPE :
                    print ("Escape key pressed down. Exit!")
                    running = False
                else:
                    if not menubar.handleKeyDown(event.key,event.unicode):
                        frameActive().handleKeyDown(event.key,event.unicode)
                        for ctrl in layercontrols:
                            ctrl.handleKeyDown(event.key,event.unicode)

        if editLayerMode:
            global dragDistance, wasDragged
            wasDragged=mouseDrag
            checkMouseDrag(pos,event)
            # Handle control mouse events
            if event.type == pygame.MOUSEBUTTONDOWN:
                frameActive().handleMouseDown(pos, event.button)
            if event.type == pygame.MOUSEBUTTONUP:
                frameActive().handleMouseUp(pos, event.button)
            if event.type == pygame.MOUSEMOTION:
                frameActive().handleMouseMove(pos)

            # Handle close and store edit mode
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    print ("Exit edit mode.")
                    # Draw Queue to all layers
                    storeDrawQueue()
                    # Store bitmap
                    # storeLayerBitmap()
                    # Reset pan and zoom
                    dispimg_offset=[0,0]
                    dispimg_zoom=1
                    # Change GUI elements for normal mode
                    editLayerMode=False
                    frameMode=settingsMode
                    layerSlider_visible = True
                    for control in layercontrols:
                        control.visible = True
                    statusbar.setText("")

            # Handle zoom / pan of layer image
            # Zoom
            scrollUp=False
            scrollDown=False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_KP_PLUS:
                    scrollUp = True
                if event.key == pygame.K_KP_MINUS:
                    scrollDown = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 5:
                    scrollUp = True
                if event.button == 4:
                    scrollDown = True
            if (scrollUp and dispimg_zoom<4) or (scrollDown and dispimg_zoom<=4):
                dzm = 0.5
            else:
                dzm = 12
            if scrollUp:
                    if dispimg_zoom < 16:
                        cx=dispimg_offset[0]+1440/2/dispimg_zoom
                        cy=dispimg_offset[1]+2560/2/dispimg_zoom
                        dispimg_zoom+=dzm
                        dispimg_offset[0] = cx - (1440 / 2) / dispimg_zoom
                        dispimg_offset[1] = cy - (2560 / 2) / dispimg_zoom
                        print ("zoom: ",dispimg_zoom)
            if scrollDown:
                    if dispimg_zoom > 1:
                        cx=dispimg_offset[0]+1440/2/dispimg_zoom
                        cy=dispimg_offset[1]+2560/2/dispimg_zoom
                        dispimg_zoom-=dzm
                        dispimg_offset[0] = cx - (1440 / 2) / dispimg_zoom
                        dispimg_offset[1] = cy - (2560 / 2) / dispimg_zoom
                        print("zoom: ", dispimg_zoom)

            # Pan
            x = dispimg_offset[0]
            y = dispimg_offset[1]
            dx=0
            dy=0
            if mouseDrag:
                dx = dragDistance[0] * 4 / dispimg_zoom
                dy = dragDistance[1] * 4 / dispimg_zoom
                x -= dx
                y -= dy
            if event.type == pygame.KEYDOWN:
                dx = 1440 / dispimg_zoom
                dy = 2560 / dispimg_zoom
                if (not isNumlockOn and event.key == pygame.K_KP8) or event.key==pygame.K_UP :y-=dy
                if (not isNumlockOn and event.key == pygame.K_KP2) or event.key==pygame.K_DOWN:y+=dy
                if (not isNumlockOn and event.key == pygame.K_KP4) or event.key==pygame.K_LEFT:x-=dx
                if (not isNumlockOn and event.key == pygame.K_KP6) or event.key==pygame.K_RIGHT:x+=dx
            #Check for boundaries
            if not dx==0 or not dy==0:
                if x<0: x=0
                if y<0: y=0
                if x > 1440 * (1 - 1 / dispimg_zoom): x = 1440 * (1 - 1 / dispimg_zoom)
                if y > 2560 * (1 - 1 / dispimg_zoom): y = 2560 * (1 - 1 / dispimg_zoom)
                x = int(x)
                y = int(y)
                dispimg_offset = [x , y]

            # Store mouse position to draw
            if event.type == pygame.MOUSEMOTION:
                global cursorpos
                cursorpos = pos

            # Handle editing of layer image
            if event.type == pygame.MOUSEBUTTONUP and not wasDragged:
                if event.button==1 or event.button==3:
                    if dispimg == layerimg:
                        gpos = GPoint.fromTuple(pos)
                        displace=(-2-brushSize,-2-brushSize)
                        layerRectEditArea=layerRect.copy()
                        #layerRectEditArea.shrink(editMargin)

                        if gpos.inGRect(layerRectEditArea):
                            if dispimg_zoom > 4:
                                d = 0.5 # magic needed for circle, had no time to find out the cause
                                # Scale up (and pixelate) the cursor
                                pixCoord = [dispimg_offset[0] + (pos[0] + displace[0]) * 4 / dispimg_zoom,
                                            dispimg_offset[1] + (pos[1] + displace[1] - menubar.getHeight()) * 4 / dispimg_zoom]
                                pixRect = (pixCoord[0], pixCoord[1], brushSize , brushSize )
                                pixCenter = (int(pixCoord[0] + brushSize / 2-d),
                                             int(pixCoord[1] + brushSize / 2-d))
                                pixRadius = int(brushSize / 2-d)
                                if pixRadius <1: pixRadius=1
                            else:
                                d = 4 - dispimg_zoom  # magic needed for circle, had no time to find out the cause
                                pixCoord = [dispimg_offset[0] + (pos[0]+displace[0]) * 4 / dispimg_zoom,
                                            dispimg_offset[1] + (pos[1]+displace[1] - menubar.getHeight()) * 4 / dispimg_zoom]
                                pixRect = (pixCoord[0], pixCoord[1], brushSize * 4 / dispimg_zoom, brushSize * 4 / dispimg_zoom)
                                pixCenter=(int(pixCoord[0] + brushSize * 2 / dispimg_zoom-d),
                                           int(pixCoord[1]+brushSize * 2 / dispimg_zoom-d))
                                pixRadius=int(brushSize * 2 / dispimg_zoom-d)
                                if pixRadius < 1: pixRadius=1
                            if event.button == 1:pcolor=layerForecolor
                            elif event.button == 3:pcolor=layerBackcolor
                            #def draw2Layer(layernr,color,shape):
                            #now queue draw command (for exit edit) and show
                            global drawQueue
                            drawCmd=(brushShape,brushSize, brushDepth, brushDepth2Bottom, pcolor,pixRect,pixCenter,pixRadius)
                            drawQueue.append(drawCmd)
                            if brushShape & BSROUND: pygame.draw.circle(layerimg, pcolor, pixCenter, pixRadius,(not brushShape & BSFILLED) * 2)
                            if brushShape & BSSQUARE: pygame.draw.rect(layerimg, pcolor, pixRect,(not brushShape & BSFILLED) * 6)

                        dispimg = layerimg

    # Check for tooltips to draw
    global windowwidth
    tooltip=None
    ret = frameActive().handleToolTips(lastpos,windowwidth)
    if not ret == None: tooltip = ret
    for ctrl in layercontrols:
        hasToolTip = getattr(ctrl, "handleToolTips", False)
        if hasToolTip:
            ret = ctrl.handleToolTips(lastpos)
            if not ret==None: tooltip=ret


    # Redraw the window (in background) and tell pygame to show it (bring to foreground)
    redrawWindow(tooltip)

def flipSDL():
    window.blit(screen, (0, 0))
    pygame.display.flip()

def flipOGL():
    gl.redraw(screen, framedScreenOpenGL or fullScreenOpenGL)
    pygame.display.flip()

#################################################################################
# MAIN
#################################################################################

flipFunc=None

init()
#from PIL import Image, ImageDraw
#im=Image.open("slicer/slice__0001.png")
#draw = ImageDraw.Draw(im)
#ImageDraw.floodfill(im,(720, 1280), (255,0,0))
#draw.line((0, im.size[1], im.size[0], 0), fill=128)
#del draw

# write to stdout
#im.save("slicer/slice__0001b.png", "PNG")