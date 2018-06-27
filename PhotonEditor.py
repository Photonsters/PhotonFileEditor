"""
Main program and initializes window, adds controls, contains redraw loop and retrieves user-input
"""

__version__ = "alpha"
__author__ = "Nard Janssens, Vinicius Silva, Robert Gowans, Ivan Antalec, Leonardo Marques - See Github PhotonFileUtils"

import os
import datetime
import time

import pygame
from pygame.locals import *

from GUI import *
from PhotonFile import *
from FileDialog import *
from MessageDialog import *
from PopupDialog import *

#TODO LIST
#todo: file dialog edit box not always working correctly, cursor mismatch and text overflow not handled
#todo: check on save if layerheighs are consecutive and printer does not midprint go down
#todo: replace preview images (Menu item Replace Bitmap should act on (layer/preview) images shown.)
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

# Regarding image data to display
screen=None
layerimg=None
previmg=[None,None]
layerForecolor=(89,56,199) #I changed this to aproximate UV color what the machine shows X3msnake
layerBackcolor=(0,0,0)
layerLabel=None #Scroll chevrons at top left
layerNr = 0
prevNr=0

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
    dialog = MessageDialog(screen, pos=(140, 140),
                           title=title,
                           message=message,
                           parentRedraw=redrawWindow)
    dialog.show()


def errMessageBox(errormessage):
    dialog = MessageDialog(screen, pos=(140, 140),
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
        dialog = FileDialog(screen, (40, 40), ext=".photon",title="Save Photon File", defFilename="newfile.photon", parentRedraw=redrawWindow)
        retfilename=dialog.newFile()
        # If user canceled saveFile on FileDialog, retfilename=None and we should continue and thus set okUser to true
        if retfilename == None:
            okUser = True
        # If user selected filename, we check if filename exists (if exists okUser set to False, if not okUser is True)
        else:
            okUser = not os.path.isfile(retfilename)
        # If fileexists or user canceled saveFile on FileDialog
        if not okUser:
            dialog = MessageDialog(screen, pos=(140, 140), width=400,
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


def loadFile():
    """ Asks for a filename and tells the PhotonFile object to load it . """

    global filename

    # Ask user for filename
    dialog = FileDialog(screen, (40, 40), ext=".photon",title="Load Photon File", parentRedraw=redrawWindow)
    retfilename=dialog.getFile()

    # Check if user pressed Cancel
    if not retfilename==None:
        filename = retfilename
        print ("Returned: ",filename)
        try:
            # Open file and update window title to reflect new filename
            openPhotonFile(filename)
            barefilename = (os.path.basename(filename))
            pygame.display.set_caption("Photon File Editor - " + barefilename)
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
        dialog = MessageDialog(screen, pos=(140, 140),width=400,
                               title="No layers to delete!",
                               message="A .photon file must have at least 1 layer. \n\n You can however replace this layer with another bitmap or edit its settings.",
                               center = True,
                               parentRedraw = redrawWindow)
        dialog.show()
        return

    # Check if user is sure
    dialog = MessageDialog(screen, pos=(140, 140),width=400,
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
    """ Replace bitmap of current layer with new bitmap from disk selected by the user """

    global filename
    global dispimg
    global layerimg

    # Check if photonfile is loaded to prevent errors when operating on empty photonfile
    if not checkLoadedPhotonfile("No photon file loaded!","A .photon file is needed to load the bitmap in."): return

    # Ask user for filename
    dialog = FileDialog(screen, (40, 40), ext=".png",title="Load Image File", parentRedraw=redrawWindow)
    retfilename=dialog.getFile()

    # Check if user pressed Cancel
    if not retfilename==None:
        filename = retfilename
        print ("Returned: ",filename)
        # since import can take a while (although faster with numpy library available) show a be-patient message
        popup = PopupDialog(screen, pos=(140, 140),
                            title="Please wait...",
                            message="Photon File Editor is importing your images.")
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
    dialog = FileDialog(screen, (40, 40), ext=".png", title="Select directory with png files", parentRedraw=redrawWindow)
    directory = dialog.getDirectory()

    # Check if user pressed Cancel
    if not directory == None:
        print("Returned: ", directory)
        # Since import WILL take a while (although faster with numpy library available) show a be-patient message
        popup = PopupDialog(screen, pos=(140, 140),
                            title="Please wait...",
                            message="Photon File Editor is importing your images.")
        popup.show()
        try:
            # Ask PhotonFile object to replace bitmaps
            photonfile.replaceBitmaps(directory)
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
        print("User Canceled")
    return

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
    popup=PopupDialog(screen, pos=(140, 140),
                           title="Please wait...",
                           message="Photon File Editor is exporting your images.")
    popup.show()
    try:
        # Ask PhotonFile object to replace bitmaps
        photonfile.exportBitmaps(newdirname,"slice_")
    except Exception as err:
        print(err)
        errMessageBox(str(err))
    del popup

    #print (barefilename,filename,newdirname)


def about():
    """ Displays about box """
    dialog = MessageDialog(screen, pos=(140, 140),width=400,
                           title="About Photon File Editor",
                           #message="Version Alpha \n \n Github: PhotonFileUtils \n\n o Nard Janssens (NardJ) \n o Vinicius Silva (X3msnake) \n o Robert Gowans (Rob2048) \n o Ivan Antalec (Antharon) \n o Leonardo Marques (Reonarudo) \n \n License: Free for non-commerical use.",
                           message="Version Alpha \n \n Github: PhotonFileUtils \n\n NardJ, X3msnake, Rob2048, \n Antharon, Reonarudo \n \n License: Free for non-commerical use.",
                           center=False,
                           parentRedraw=redrawWindow)
    dialog.show()

def showSlices():
    """ Let user switch (from preview images) to slice view """
    global dispimg
    dispimg=layerimg

def showPrev0():
    """ Let user switch (from slice image view) to preview image """
    global dispimg
    dispimg = previmg[0]

def showPrev1():
    """ Let user switch (from slice image view) to preview image """
    global dispimg
    dispimg = previmg[1]



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
    menubar.addItem("Edit", "______________", None)
    menubar.addItem("Edit", "Cut Layer", deleteLayer)
    menubar.addItem("Edit", "Copy Layer", copyLayer)
    menubar.addItem("Edit", "Paste Layer", pasteLayer)
    menubar.addItem("Edit", "Duplicate Layer", duplicateLayer)
    menubar.addItem("Edit", "______________", None)
    menubar.addItem("Edit", "Replace Bitmap", replaceBitmap)
    menubar.addItem("Edit", "______________", None)
    menubar.addItem("Edit", "Import Bitmaps", importBitmaps)
    menubar.addItem("Edit", "Export Bitmaps", exportBitmaps)
    menubar.addMenu("View", "V")
    menubar.addItem("View", "Slices", showSlices)
    menubar.addItem("View", "Preview 0", showPrev0)
    menubar.addItem("View", "Preview 1",showPrev1)
    menubar.addItem("View", "..3D", doNothing)
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
    ifile = open("resources/resins.txt", "r")
    lines = ifile.readlines()
    resins = [tuple(line.strip().split(",")) for line in lines]
    resinnames=[]
    for resin in resins:
        resinnames.append(resin[0])

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
                            text="Apply", func_on_click=ApplyResinSettings
                             ))

    # Add combobox to controls
    controls.append(resincombo)


def ApplyResinSettings():
    """ Applies the selected resin settings.
    """
    global resins
    global resincombo
    global photonfile

    # Check if photonfile is loaded
    if photonfile==None: return

    # Check if user didn't select title (first item)
    resinname=resincombo.text
    if resinname=="Brand": return

    # columns are Brand,Type,Layer Height,NormalExpTime,OffTime,BottomExp,BottomLayers
    for (sBrand,sType,sLayerHeight,sNormalExpTime,sOffTime,sBottomExp,sBottomLayers)  in resins:
        if sBrand == resinname:
            # Convert all strings to floats/int
            rLayerHeight=float(sLayerHeight)
            rNormalExpTime = float(sNormalExpTime)
            rOffTime=float(sOffTime)
            rBottomExp=float(sBottomExp)
            rBottomLayers=int(sBottomLayers)
            #print (sBrand, rLayerHeight,rNormalExpTime, rOffTime, rBottomExp, rBottomLayers)

            # Set Header/General settings
            photonfile.Header["Layer height (mm)"]=PhotonFile.float_to_bytes(rLayerHeight)
            photonfile.Header["Exp. time (s)"] = PhotonFile.float_to_bytes(rNormalExpTime)
            photonfile.Header["Off time (s)"] = PhotonFile.float_to_bytes(rOffTime)
            photonfile.Header["Exp. bottom (s)"] = PhotonFile.float_to_bytes(rBottomExp)
            photonfile.Header["# Bottom Layers"] = PhotonFile.int_to_bytes(rBottomLayers)

            # Set settings of each layer
            cLayerHeight=0
            for layerNr, layerDef in enumerate(photonfile.LayerDefs):
                layerDef["Layer height (mm)"]=PhotonFile.float_to_bytes(cLayerHeight)
                cLayerHeight=cLayerHeight+rLayerHeight
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

    # For debugging we display current script-path and last modified date, so we know which version we are testing/editing
    scriptPath=os.path.join(os.getcwd(), "PhotonEditor.py")
    scriptDateTime=time.ctime(os.path.getmtime(scriptPath))
    print ("Script Info:")
    print ("  "+ scriptPath)
    print("  " + str(scriptDateTime))

    # Init pygame, fonts and set window frame properties
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption("Photon File Editor")
    logo = pygame.image.load("PhotonEditor32x32.png")
    pygame.display.set_icon(logo)

    # Create a window surface we can draw the menubar, controls and layer/preview  bitmaps on
    screen = pygame.display.set_mode((windowwidth, windowheight))
    scale = (0.25, 0.25)

    # Initialize the surfaces for layer/preview images we want to fill from photonfile and draw on screen
    dispimg = pygame.Surface((int(1440 * scale[0]), int(2560 * scale[1])))
    dispimg.fill((0,0,0))
    previmg[0]=dispimg
    previmg[1] = dispimg
    layerimg = dispimg

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



########################################################################################################################
##  Drawing/Event-Polling Loop
########################################################################################################################

def redrawWindow():
    """ Redraws the menubar, settings and displayed layer/preview image """

    # Clear window surface
    screen.fill(defFormBackground)

    # Draw layer/preview images
    w, h = dispimg.get_size()
    dw = (1440 / 4 - w) / 2
    dh = (2560 / 4 - h) / 2
    if not photonfile==None:
        if not photonfile.isDrawing:
            screen.blit(dispimg, (dw, dh))
    else:#also if we have no photonfile we still need to draw to cover up menu/filedialog etc
        screen.blit(dispimg, (dw, dh))

    # Redraw all side bar
    for ctrl in controls:
        ctrl.redraw()

    # Redraw Menubar
    menubar.redraw()

    # Redraw (cursor of) layer slider
    if layerCursorActive and not photonfile==None and dispimg==layerimg:
        pygame.draw.rect(screen, (0, 0, 150), scrollLayerRect.tuple(), 1)
        pygame.draw.rect(screen, (0,0,255), layerCursorRect.tuple(), 0)


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

def main():
    """ Entrypoint and controls the rest """

    global controls
    global menubar
    global mouseDrag
    global running
    global photonfile
    lastpos=(0,0) # stores last position for tooltip

    # Initialize the pygame module and create the window
    createWindow()

    # Main loop
    while running:
        # Redraw the window (in background) and tell pygame to show it (bring to foreground)
        redrawWindow()
        # Check for tooltips to draw
        for ctrl in controls:
            hasToolTip = getattr(ctrl, "handleToolTips", False)
            if hasToolTip:
                ret = ctrl.handleToolTips(lastpos)
                if not ret==None :
                    ret.redraw()

        pygame.display.flip()


        # Event handling, gets all event from the eventqueue
        for event in pygame.event.get():

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
                if event.key == pygame.K_TAB:
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

    pygame.quit()

main()

