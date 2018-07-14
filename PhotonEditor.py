"""
Main program and initializes window, adds controls, contains redraw loop and retrieves user-input
"""

__version__ = "Alpha (build 30-6-2018)"
__author__ = "Nard Janssens, Vinicius Silva, Robert Gowans, Ivan Antalec, Leonardo Marques - See Github PhotonFileUtils"

import os
import datetime
import time
import subprocess

import pygame
from pygame.locals import *

from GUI import *
from PhotonFile import *
from FileDialog import *
from MessageDialog import *
from PopupDialog import *
from ProgressDialog import *
from OGLEngine import *
from Slicer import *
from STLFile import *

#Following tests are done for initial message to user below the disclaimer
try:
    import numpy
    numpyAvailable = True
except ImportError:
    numpyAvailable = False

try:
    import OpenGL #pyopengl
    pyopenglAvailable = True
except ImportError as err:
    pyopenglAvailable = False

#TODO LIST
#todo: make slice images editable
#       - zoom to quadrant to edit pixels of current layer,
#       - show layer underneed transparent
#       - make edit possible of current layer and all layers beneath
#todo: if change Header setting like layer height, exp. time, off time, shouldn we propagate this to the layerdefs?
#todo: OpenGL - why do we need it...
#todo: Header LayerDef Address should be updated if importing/replacing bitmaps
#todo: check on save if layerheighs are consecutive and printer does not midprint go down
#todo: button.png should be used in scrollbarv
#todo: PhotonFile float_to_bytes(floatVal) does not work correctie if floatVal=0.5 - now struct library used
#todo: process cursor keys for menu
#todo: The exposure time, off times in layerdefs are ignored by Photon printer, however layerheight not (so first two are just placeholders for future firmware.)
#todo: hex_to_bytes(hexStr) et al. return a bytearray, should we convert this to bytes by using bytes(bytearray)?
#todo: beautify layer bar at right edge of slice image
#todo: Exe/distribution made with
#todo: drag GUI-scrollbar is not implementend
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
defTransparent=(1,1,1)
layerimg=None
previmg=[None,None]
layerForecolor=(89,56,199) #I changed this to aproximate UV color what the machine shows X3msnake
layerBackcolor=(0,0,0)
layerLabel=None #Scroll chevrons at top left
layerNr = 0
prevNr=0
lastpos=(0,0)

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
windowheight=int(2560 / 4)

# GUI controls
menubar=None
controls=[]
firstHeaderTextbox=-1
firstPreviewTextbox=-1
firstLayerTextbox=-1

# Scroll bar to the right
mouseDrag=False
scrollLayerWidth=30
scrollLayerVMargin=30
scrollLayerRect=GRect(1440/4-scrollLayerWidth,scrollLayerVMargin,scrollLayerWidth,2560/4-scrollLayerVMargin*2)
layerCursorActive=True
layerCursorRect=GRect(1440/4-scrollLayerWidth,scrollLayerVMargin+2,scrollLayerWidth,4)

# Resin settings
resins=None
resincombo=None

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
    # print ("saveLayerSettings2PhotonFile()")
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

    global filename

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
        dialog = FileDialog(flipFunc,screen, (40, 40), ext=".photon",title="Save Photon File", defFilename="newfile.photon", parentRedraw=redrawWindow)
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


def loadFile():
    """ Asks for a filename and tells the PhotonFile object to load it . """

    global filename

    # Ask user for filename
    dialog = FileDialog(flipFunc,screen, (40, 40), ext=(".photon",".stl"),title="Load Photon File", parentRedraw=redrawWindow)
    retfilename=dialog.getFile()

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
    if not pyopenglAvailable:
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
    if not pyopenglAvailable:
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


def openPlugin(filename):
    # BEWARE: IT IS NORMAL THIS DOES NOT RUN IN PYCHARM!!!
    filepath="plugins/"+filename
    ifile = open(filepath, "r", encoding="Latin-1")  # Latin-1 handles special characters
    lines = ifile.read()
    exec(lines)


def createMenu():
    global menubar
    global screen

    # Create the menu
    menubar=MenuBar(screen)
    menubar.addMenu("File","F")
    menubar.addItem("File", "New", newFile)
    menubar.addItem("File","Load",loadFile)
    menubar.addItem("File","Save As",saveFile)
    menubar.addItem("File","Exit",exitFile)
    menubar.addMenu("Edit", "E")
    menubar.addItem("Edit", "Undo", undo)
    menubar.addItem("Edit", "----", None)
    menubar.addItem("Edit", "Cut Layer", deleteLayer)
    menubar.addItem("Edit", "Copy Layer", copyLayer)
    menubar.addItem("Edit", "Paste Layer", pasteLayer)
    menubar.addItem("Edit", "Duplicate Layer", duplicateLayer)
    menubar.addItem("Edit", "----", None)
    menubar.addItem("Edit", "Export Bitmap", exportBitmap)
    menubar.addItem("Edit", "Replace Bitmap", replaceBitmap)
    menubar.addItem("Edit", "----", None)
    menubar.addItem("Edit", "Import Bitmaps", importBitmaps)
    menubar.addItem("Edit", "Export Bitmaps", exportBitmaps)
    menubar.addMenu("View", "V")
    menubar.addItem("View", "Slices", showSlices)
    menubar.addItem("View", "Preview 0", showPrev0)
    menubar.addItem("View", "Preview 1",showPrev1)
    menubar.addItem("View", "3D", showFramed3D)
    menubar.addItem("View", "Full 3D", showFull3D)
    menubar.addItem("View", "Volume", calcVolume)

    menubar.addMenu("Plugins ", "P")
    for plugin in readPlugins():
        name=plugin.split(".py")[0]
        menubar.addItem("Plugins ", name,openPlugin,plugin)
    menubar.addMenu("Help", "H")
    menubar.addItem("Help", "About",about)


def createLayerOperations():
    """ Create the layer modification buttons pointing to Edit menu layer options """
    global controls
    global menubar
    viewport_yoffset = 8
    iconsize=(46,59)
    icondist=iconsize[0]+16
    controls.append(ImgBox(screen, filename="resources/cut.png", filename_hover="resources/cut-hover.png",
                           pos=(20+0*icondist,2560/4-iconsize[1]-viewport_yoffset),
                           borderhovercolor=(0,0,0),toolTip="Cut (and store in clipboard)",
                           func_on_click=deleteLayer))
    controls.append(ImgBox(screen, filename="resources/copy.png", filename_hover="resources/copy-hover.png",
                           pos=(20+1*icondist, 2560 / 4 - iconsize[1] - viewport_yoffset),
                           borderhovercolor=(0, 0, 0),toolTip="Copy (to clipboard)",
                           func_on_click=copyLayer))
    controls.append(ImgBox(screen, filename="resources/paste.png", filename_hover="resources/paste-hover.png",
                           pos=(20+2*icondist, 2560 / 4 - iconsize[1] - viewport_yoffset),
                           borderhovercolor=(0, 0, 0), toolTip="Paste (from clipboard)",
                           func_on_click=pasteLayer))
    controls.append(ImgBox(screen, filename="resources/duplicate.png", filename_hover="resources/duplicate-hover.png",
                           pos=(20+3*icondist, 2560 / 4 - iconsize[1] - viewport_yoffset),
                           borderhovercolor=(0, 0, 0), toolTip="Duplicate (current layer)",
                           func_on_click=duplicateLayer))


def createLayernavigation():
    """ Create the layer navigation buttons (Up/Down) """
    global layerLabel
    global menubar
    global controls
    global layerNr

    # Add two imageboxes to control as layer nav buttons
    viewport_yoffset=menubar.height+8
    controls.append(ImgBox(screen, filename="resources/arrow-up.png", filename_hover="resources/arrow-up-hover.png", pos=(20,20+viewport_yoffset), borderhovercolor=(0,0,0),func_on_click=layerDown))
    controls.append(ImgBox(screen, filename="resources/arrow-down.png", filename_hover="resources/arrow-down-hover.png", pos=(20,80+viewport_yoffset), borderhovercolor=(0,0,0),func_on_click=layerUp))
    layerLabel=Label(screen,GRect(26,80,52,40),textcolor=(255,255,255),fontsize=24,text="",istransparent=True,center=True)
    layerLabel.font.set_bold(True)
    controls.append(layerLabel)

    layerNr=0
    setLayerSliderFromLayerNr()

def createSidebar():
    """ Create all labels and input boxes to edit the general, preview and current layer settings of the photonfile. """
    global menubar
    global screen
    global controls

    global settingscolwidth
    global settingslabelwidth
    global settingslabelmargin
    global settingstextboxmargin
    global settingsrowheight
    global settingsrowspacing
    global settingstextboxwidth
    global settingswidth
    global settingsleft

    global firstHeaderTextbox
    global firstPreviewTextbox
    global firstLayerTextbox

    global resins
    global resincombo

    # The controls are placed below the menubar
    viewport_yoffset=menubar.height+8

    # We need to translate the datatype of the photon settings to the datatypes an inputbox recognizes and enforces from the user
    transTypes={PhotonFile.tpByte: TextBox.HEX,PhotonFile.tpInt: TextBox.INT,PhotonFile.tpFloat: TextBox.FLOAT,PhotonFile.tpChar: TextBox.HEX}

    # Add General data fields
    # Start with the title of this settingsgroup
    row=0
    titlebox=Label(screen,text="General", rect=GRect(settingsleft + settingslabelmargin, 10 + row * 24 + viewport_yoffset, settingscolwidth, 16),drawBorder=False)
    titlebox.font.set_bold(True)
    controls.append(titlebox)
    # Add all labels for the settings we want to add
    for row, (bTitle, bNr, bType, bEditable,bHint) in enumerate(PhotonFile.pfStruct_Header,1):#enum start at 1
        controls.append(Label(screen, text=bTitle, rect=GRect(settingsleft+settingslabelmargin,10+row*settingsrowspacing+viewport_yoffset,settingslabelwidth,settingsrowheight)))
    # Add all input boxes for the settings we want to add
    firstHeaderTextbox=len(controls)
    for row,  (bTitle, bNr, bType,bEditable,bHint) in enumerate(PhotonFile.pfStruct_Header,1):#enum start at 1
        tbType = transTypes[bType]
        bcolor=(255,255,255) if bEditable else (128,128,128)
        controls.append(TextBox(screen, text="", \
                                rect=GRect(settingsleft+settingslabelwidth+settingstextboxmargin, 10 + row * settingsrowspacing+viewport_yoffset, settingstextboxwidth, settingsrowheight),\
                                editable=bEditable, \
                                backcolor=bcolor, \
                                textcolor=(0,0,0),\
                                inputType=tbType, \
                                toolTip=bHint, \
                                onEnter=updateTextBox2PhotonFile, \
                                linkedData={"VarGroup":"Header","Title":bTitle,"NrBytes":bNr,"Type":bType} \
                                ))

    # Add Preview data fields
    # Start with the title of this settingsgroup
    row=0
    settingsleft = settingsleft+settingscolwidth
    titlebox = Label(screen, text="Preview", rect=GRect(settingsleft+settingslabelmargin,10+row*settingsrowspacing+viewport_yoffset,settingscolwidth,settingsrowheight))
    titlebox.font.set_bold(True)
    controls.append(titlebox)
    # Add all labels for the settings we want to add
    for row, (bTitle, bNr, bType,bEditable, bHint) in enumerate(PhotonFile.pfStruct_Previews, 1):
        controls.append(Label(screen, text=bTitle, rect=GRect(settingsleft+settingslabelmargin,10+row*settingsrowspacing+viewport_yoffset,settingslabelwidth,settingsrowheight)))
    # We also need navigation buttons for previewNr
    row = 0
    controls.append(Button(screen, rect=GRect(settingsleft + settingslabelwidth + settingstextboxmargin + settingstextboxwidth - 40,10 + row * settingsrowspacing + viewport_yoffset, 18, 20), text="<",func_on_click=prevDown))
    controls.append(Button(screen,rect=GRect(settingsleft+settingslabelwidth+settingstextboxmargin+settingstextboxwidth-18,10+row*settingsrowspacing+viewport_yoffset,18,20),text=">",func_on_click=prevUp))
    firstPreviewTextbox = len(controls)
    controls.append(Label(screen, text=str(prevNr),rect=GRect(settingsleft+settingslabelwidth+settingstextboxmargin, 10 + row * settingsrowspacing + viewport_yoffset, settingstextboxwidth-40, settingsrowheight)))
    # Add all input boxes for the settings we want to add
    for row, (bTitle, bNr, bType,bEditable, bHint) in enumerate(PhotonFile.pfStruct_Previews, 1):
        tbType = transTypes[bType]
        bcolor = (255, 255, 255) if bEditable else (128, 128, 128)
        controls.append(TextBox(screen, text="", \
                                rect=GRect(settingsleft+settingslabelwidth+settingstextboxmargin, 10 + row * settingsrowspacing+viewport_yoffset, settingstextboxwidth, settingsrowheight),\
                                editable=bEditable, \
                                backcolor=bcolor, \
                                textcolor=(0, 0, 0), \
                                inputType=tbType, \
                                toolTip=bHint, \
                                onEnter=updateTextBox2PhotonFile, \
                                linkedData={"VarGroup": "Preview", "Title": bTitle, "NrBytes": bNr, "Type": bType} \
                                ))

    # Add Current Layer meta fields
    # Start with the title of this settingsgroup
    row=8
    titlebox = Label(screen, text="Layer", rect=GRect(settingsleft+settingslabelmargin,10+row*settingsrowspacing+viewport_yoffset,settingscolwidth,settingsrowheight))
    titlebox.font.set_bold(True)
    controls.append(titlebox)
    # Add all labels for the settings we want to add
    for row, (bTitle, bNr, bType,bEditable, bHint) in enumerate(PhotonFile.pfStruct_LayerDef,9):
        controls.append(Label(screen, text=bTitle, rect=GRect(settingsleft+settingslabelmargin,10+row*settingsrowspacing+viewport_yoffset,120,16)))
    row=8
    # Add all input boxes for the settings we want to add
    firstLayerTextbox = len(controls)
    controls.append(Label(screen, text=str(layerNr), rect=GRect(settingsleft + settingslabelwidth+settingstextboxmargin, 10 + row * settingsrowspacing+viewport_yoffset, settingstextboxwidth, settingsrowheight)))
    for row, (bTitle, bNr, bType,bEditable, bHint) in enumerate(PhotonFile.pfStruct_LayerDef, 9):
        tbType = transTypes[bType]
        bcolor = (255, 255, 255) if bEditable else (128, 128, 128)
        controls.append(TextBox(screen, text="", \
                                rect=GRect(settingsleft + settingslabelwidth+settingstextboxmargin, 10 + row * settingsrowspacing+viewport_yoffset, settingstextboxwidth, settingsrowheight),\
                                editable=bEditable, \
                                backcolor=bcolor, \
                                textcolor=(0, 0, 0), \
                                inputType=tbType,\
                                toolTip=bHint, \
                                onEnter=updateTextBox2PhotonFile, \
                                linkedData={"VarGroup": "LayerDef", "Title": bTitle, "NrBytes": bNr, "Type": bType} \
                                ))

    # Add Resin Presets Chooser
    # First read settings from file
    # columns are Brand,Type,Layer,NormalExpTime,OffTime,BottomExp,BottomLayers
    ifile = open("resources/resins.csv", "r",encoding="Latin-1") #Latin-1 handles special characters
    lines = ifile.readlines()
    resins = [tuple(line.strip().split(";")) for line in lines]
    resinnames=[]
    for resin in resins:
        resinnames.append(resin[0]+ "-"+resin[1]+"-"+resin[2])

    # Start with the title of this settingsgroup
    row=16
    titlebox = Label(screen, text="Resin Presets", rect=GRect(settingsleft+settingslabelmargin,10+row*settingsrowspacing+viewport_yoffset,settingscolwidth,settingsrowheight))
    titlebox.font.set_bold(True)
    controls.append(titlebox)

    # Make combobox (add last, so always on top)
    row=row+1
    resincombo=Combobox(screen,
                             rect=GRect(settingsleft + settingslabelmargin, 10 + row * settingsrowspacing+viewport_yoffset, settingstextboxwidth+settingslabelwidth, settingsrowheight),\
                             items=resinnames,
                             defitemnr=0,
                             )

    # Add apply button
    row=row+1+0.4 # combo is larger than normal
    controls.append( Button(screen,
                            rect=GRect(settingsleft + settingslabelwidth + settingstextboxmargin, 10 + row * settingsrowspacing + viewport_yoffset, settingstextboxwidth,settingsrowheight*1.6), \
                            text="Apply", func_on_click=applyResinSettings
                             ))

    # Add combobox to controls
    controls.append(resincombo)


def applyResinSettings():
    """ Applies the selected resin settings.
    """
    global resins
    global resincombo
    global photonfile

    # Check if photonfile is loaded
    if photonfile==None: return

    # Check if user didn't select title (first item)
    resinname=resincombo.text
    resinidx=resincombo.index
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
##  Setup windows, pygame, menu and controls
########################################################################################################################

def createWindow():
    """ Create all labels and input boxes to edit the general, preview and current layer settings of the photonfile. """
    global window
    global screen
    global dispimg
    global layerimg
    global previmg
    global windowwidth
    global windowheight
    global settingsleft
    global settingswidth
    global controls
    global layerNr
    global menubar
    global firstHeaderTextbox
    global firstPreviewTextbox
    global firstLayerTextbox
    global layerLabel
    global filename
    global pyopenglAvailable

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
    logo = pygame.image.load("PhotonEditor32x32.png")
    pygame.display.set_icon(logo)
    if not pyopenglAvailable:
        # Create a window surface we can draw the menubar, controls and layer/preview  bitmaps on
        window = pygame.display.set_mode((windowwidth, windowheight))

    scale = (0.25, 0.25)

    # Creat a surface
    if not pyopenglAvailable:
        screen = pygame.Surface((windowwidth,windowheight))
    else:
        screen = pygame.Surface((1024, 1024))
        screen.set_colorkey(defTransparent)

    print ("Window Size:", windowwidth,windowheight)


    # Initialize the surfaces for layer/preview images we want to fill from photonfile and draw on screen
    dispimg = pygame.Surface((int(1440 * scale[0]), int(2560 * scale[1])))
    dispimg.fill(defTransparent) # first we fill with transparent
    previmg[0]=dispimg
    previmg[1] = dispimg
    layerimg = dispimg

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
    if not numpyAvailable or not pyopenglAvailable:
        libraryString = "_______________________________\n\n"
    if not numpyAvailable :
        libraryString = libraryString + \
       "> PhotonFileEditor works faster if you \n" \
       "   install numpy!\n\n"
    if not pyopenglAvailable :
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

    # Create sidebar to display the settings of the photonfile
    createSidebar()

    # Create layer controls to navigate (up and down) the layers (and display another layer)
    createLayernavigation()

    # Create toolbar to do layer operations from edit menu
    createLayerOperations()


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
        if pVarGroup=="Header":photonfile.Header[pTitle]=bytes
        if pVarGroup=="Preview":photonfile.Previews[prevNr][pTitle]=bytes
        if pVarGroup=="LayerDef": photonfile.LayerDefs[layerNr][pTitle] = bytes
    #print ("Found. New Val: ",val,linkedData)


def saveGeneralSettings2PhotonFile():
    """ Saves all textboxes in the general settingsgroup """

    #print ("saveGeneralSettings2PhotonFile")
    global photonfile
    global firstHeaderTextbox

    # If no photonfile nothing to save, so exit
    if photonfile==None:return

    # Check for each general setting in PhotonFile if it is editable, control index in controls and update setting
    for row, (bTitle, bNr, bType,bEditable,bHint) in enumerate(PhotonFile.pfStruct_Header,firstHeaderTextbox):#enum start at 22
        if bEditable:
            textBox=controls[row]
            #print (row,bTitle,textBox.text)
            updateTextBox2PhotonFile(textBox,textBox.text,{"VarGroup": "Header", "Title": bTitle, "NrBytes": bNr, "Type": bType})


def savePreviewSettings2PhotonFile():
    """ Saves all textboxes in the preview settingsgroup """

    #print("savePreviewSettings2PhotonFile")
    global photonfile
    global prevNr
    global firstPreviewTextbox

    # If no photonfile nothing to save, so exit
    if photonfile==None:return

    # Check for each preview setting in PhotonFile if it is editable, control index in controls and update setting
    for row, (bTitle, bNr, bType,bEditable, bHint) in enumerate(PhotonFile.pfStruct_Previews, firstPreviewTextbox+1):
        if bEditable:
            textBox=controls[row]
            print (row,bTitle,textBox.text)
            updateTextBox2PhotonFile(textBox,textBox.text,{"VarGroup": "Preview", "Title": bTitle, "NrBytes": bNr, "Type": bType})


def saveLayerSettings2PhotonFile():
    """ Saves all textboxes in the layer settingsgroup """

    #print ("saveLayerSettings2PhotonFile")
    global photonfile
    global layerNr
    global firstLayerTextbox

    # If no photonfile nothing to save, so exit
    if photonfile == None: return

    # Check for each layer setting in PhotonFile if it is editable, control index in controls and update setting
    for row, (bTitle, bNr, bType, bEditable, bHint) in enumerate(PhotonFile.pfStruct_LayerDef, firstLayerTextbox+1):
        if bEditable:
            textBox=controls[row]
            #print (row,bTitle,textBox.text)
            updateTextBox2PhotonFile(textBox,textBox.text,{"VarGroup": "LayerDef", "Title": bTitle, "NrBytes": bNr, "Type": bType})


def refreshHeaderSettings():
    """ Updates all textboxes in the general settingsgroup with data from photonfile"""
    global photonfile
    global firstHeaderTextbox

    # If no photonfile nothing to save, so exit
    if photonfile==None:return

    # Travers all general settings and update values in textboxes
    for row, (bTitle, bNr, bType,bEditable,bHint) in enumerate(PhotonFile.pfStruct_Header,firstHeaderTextbox ):
        nr=PhotonFile.convBytes(photonfile.Header[bTitle],bType)
        if bType==PhotonFile.tpFloat:nr=round(nr,4) #round floats to 4 decimals
        controls[row].setText(str(nr))


def refreshPreviewSettings():
    """ Updates all textboxes in the preview settingsgroup with data from photonfile"""
    global photonfile
    global prevNr
    global firstPreviewTextbox

    # If no photonfile nothing to save, so exit
    if photonfile == None: return

    print ("prevNr: ",prevNr)
    # Travers all preview settings and update values in textboxes
    row = firstPreviewTextbox
    controls[row].setText(str(prevNr)+"/2") # Update preview counter
    for row, (bTitle, bNr, bType,bEditable, bHint) in enumerate(PhotonFile.pfStruct_Previews, firstPreviewTextbox+1):
        nr=PhotonFile.convBytes(photonfile.Previews[prevNr][bTitle],bType)
        if bType == PhotonFile.tpFloat: nr = round(nr, 4) #round floats to 4 decimals
        controls[row].setText(str(nr))


def refreshLayerSettings():
    """ Updates all textboxes in the layer settingsgroup with data from photonfile"""
    global photonfile
    global layerNr
    global layerLabel

    # If we have no photonfile loaded of there are no layers in the file there is nothing to save, so exit
    if photonfile==None:return
    if photonfile.nrLayers() == 0: return  # could occur if loading new file

    # Travers all layer settings and update values in textboxes
    row=firstLayerTextbox
    controls[row].setText(str(layerNr)+ " / "+str(photonfile.nrLayers())) # Update layer counter
    #print (layerNr)
    for row, (bTitle, bNr, bType,bEditable, bHint) in enumerate(PhotonFile.pfStruct_LayerDef,firstLayerTextbox+1):
        nr=PhotonFile.convBytes(photonfile.LayerDefs[layerNr][bTitle],bType)
        #print("reading: ", bTitle,"=",nr)
        if bType == PhotonFile.tpFloat: nr = round(nr, 4) #round floats to 4 decimals
        controls[row].setText(str(nr))

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
    global pyopenglAvailable
    global screen
    global dispimg
    global windowwidth
    global windowheight
    global fontFullScreen

    # Clear window surface
    if not fullScreenOpenGL:
        screen.fill(defFormBackground)
    else:
        screen.fill(defTransparent)
        # Draw user guide
        if fontFullScreen==None:
            fontFullScreen =pygame.font.SysFont(defFontName, defFontSize - 2)

        pygame.draw.rect(screen,defFormBackground,(0,windowheight-24,windowwidth,24),0)
        text = "[b]Move[b]:\u2190\u2191\u2193\u2192, [mouse][left]  [b]|[b]  [b]Rotate[b]: [shift]\u2190\u2191\u2193\u2192, [mouse][right]  [b]|[b]  [b]Zoom[b]: [ctrl]\u2191\u2193, [mouse][scroll]  [b]|[b]  [b]Reset[b]: [Q]  [b]|[b]  [b]Slice[b]: [F5]"
        drawTextMarkdown(text,fontFullScreen,defFormForeground,screen,(8,windowheight-20))
        return

    # Draw layer/preview images
    w, h = dispimg.get_size()
    dw = (1440 / 4 - w) / 2
    dh = (2560 / 4 - h) / 2
    if not photonfile==None:
        if not photonfile.isDrawing:
            screen.blit(dispimg, (dw, dh))
    else:#also if we have no photonfile we still need to draw to cover up menu/filedialog etc
        screen.blit(dispimg, (dw, dh))

    if framedScreenOpenGL:
        scale = (0.25, 0.25)
        dispimg = pygame.Surface((int(1440 * scale[0]), int(2560 * scale[1])))
        dispimg.fill((defTransparent))
        pygame.draw.rect(screen,defTransparent,(0,0,int(1440 * scale[0]), int(2560 * scale[1])),0)

    # Redraw all side bar
    for ctrl in controls:
        ctrl.redraw()

    # Redraw Menubar
    menubar.redraw()

    # Redraw (cursor of) layer slider
    if layerCursorActive and not photonfile==None and dispimg==layerimg:
        pygame.draw.rect(screen, (0, 0, 150), scrollLayerRect.tuple(), 1)
        pygame.draw.rect(screen, (0,0,255), layerCursorRect.tuple(), 0)

    # Redraw tooltip
    if not tooltip==None: tooltip.redraw()


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
def handleLayerSlider(checkRect=True):
    """ Checks if layerslider is used (dragged by mouse) and updates layer image and settings"""

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
    """ Returns first textbox in controls where cursorActive is True. """
    for idx, control in enumerate(controls):
        if type(control) == TextBox:
            if control.cursorActive == True: return idx
    return None

# Define a variable to control the main loop
running = True
gl=None

def init():
    global gl
    # Initialize the pygame module and create the window
    createWindow()
    # Init lastpos mouse hovered
    lastpos=(0,0) # stores last position for tooltip
    if not pyopenglAvailable:
        loop()
        quit()
    else:
        gl=GL((windowwidth,windowheight),handleGLCallback)
        loop()
        #gl.userLoop(screen, poll)


#import test.py


def loop():
    # Main loop
    while running:
        poll()
        flipFunc()
    pygame.quit()


def poll(event=None):
    """ Entrypoint and controls the rest """
    global controls
    global menubar
    global mouseDrag
    global running
    global photonfile
    global window
    global screen
    global lastpos
    global fullScreenOpenGL
    global framedScreenOpenGL

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

        if pyopenglAvailable:
            gl.poll(framedScreenOpenGL,event)

        pos = pygame.mouse.get_pos()
        lastpos=pos
        if event.type == pygame.QUIT:
            print("Window was closed. Exit!")
            running = False  # change the value to False, to exit the main loop

        if event.type == pygame.MOUSEBUTTONUP:
            mouseDrag=False
            if not menubar.handleMouseUp(pos,event.button):
                for ctrl in controls:
                    ctrl.handleMouseUp(pos,event.button)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouseDrag=handleLayerSlider()
            if not menubar.handleMouseDown(pos,event.button):
                for ctrl in controls:
                    ctrl.handleMouseDown(pos,event.button)

        if event.type == pygame.MOUSEMOTION:
            if mouseDrag: handleLayerSlider(False)
            if not menubar.handleMouseMove(pos):
                for ctrl in controls:
                    ctrl.handleMouseMove(pos)


        if event.type == pygame.KEYDOWN :
            #If numlock on then we use it to navigate layers
            if not photonfile==None:
                isNumlockOn = (pygame.key.get_mods() & pygame.KMOD_NUM) == 4096
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
                    controls[prevActive].cursorActive=False
                    # Make first editable textbox we find in direction of dir
                    fnd=False
                    idx=prevActive+dir
                    while not fnd:
                        if type(controls[idx]) == TextBox and controls[idx].editable and not fnd:
                            controls[idx].cursorActive = True
                            fnd=True
                        idx=idx+dir
                        if idx>=len(controls): idx=0
                        if idx<0: idx=len(controls)-1

            if event.key == pygame.K_ESCAPE :
                print ("Escape key pressed down. Exit!")
                running = False
            else:
                if not menubar.handleKeyDown(event.key,event.unicode):
                    for ctrl in controls:
                        ctrl.handleKeyDown(event.key,event.unicode)

    # Check for tooltips to draw
    tooltip=None
    for ctrl in controls:
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
if pyopenglAvailable:
    flipFunc=flipOGL
else:
    flipFunc=flipSDL
init()
