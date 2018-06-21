import pygame
from pygame.locals import *
from GUI import *
from PhotonFile import *
from FileDialog import *
from MessageDialog import *
from PopupDialog import *

#todo: importing is very slow....
#todo: beautify layer bar at right edge of slice image
#todo: Exe/distribution made with
#todo: after click on menuitem, the menulist should close
#todo: mousescroll in listbox does not move scrollbar
#todo: drag GUI-scrollbar is not implementend
#todo: drag in layer Scroll Area is not implemented


#           cmd.com - prompt, type...
#           pyinstaller --onefile --windowed PhotonViewer.py

########################################################################################################################
##  Setup screen and load Photon file
########################################################################################################################
screen=None
layerimg=None
previmg=[None,None]
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
controls=[]
layerNr = 0
prevNr=0
photonfile=None
menubar=None
firstHeaderTextbox=-1
firstPreviewTextbox=-1
firstLayerTextbox=-1
layerForecolor=(89,56,199) #I changed this to aproximate UV color what the machine shows X3msnake
layerBackcolor=(0,0,0)

#Scroll button at top left
layerLabel=None

#Scroll bar to the right
scrollLayerWidth=30
scrollLayerVMargin=30
scrollLayerRect=GRect(1440/4-scrollLayerWidth,scrollLayerVMargin,scrollLayerWidth,2560/4-scrollLayerVMargin*2)
layerCursorActive=True
layerCursorRect=GRect(1440/4-scrollLayerWidth,scrollLayerVMargin+2,scrollLayerWidth,4)


# Prev Nav Buttons call back methods
def prevUp():
    global prevNr
    global dispimg
    if prevNr == 0: prevNr = 1
    dispimg = previmg[prevNr]
    refreshPreviewControls()


def prevDown():
    global prevNr
    global dispimg
    if prevNr == 1: prevNr = 0
    dispimg = previmg[prevNr]
    refreshPreviewControls()


# Add Up/Down Layer Buttons
def layerDown():
    global layerNr, dispimg, layerimg, photonfile
    if photonfile == None: return
    saveLayer2PhotonFile()

    layerNr = layerNr - 1
    if layerNr < 0: layerNr = 0
    layerimg = photonfile.getBitmap(layerNr, layerForecolor, layerBackcolor)
    dispimg = layerimg
    refreshLayerControls()
    return


def layerUp():
    global layerNr, dispimg, layerimg, photonfile
    if photonfile == None: return
    # print ("saveLayer2PhotonFile()")
    saveLayer2PhotonFile()

    maxLayer = photonfile.nrLayers()
    layerNr = layerNr + 1
    if layerNr == maxLayer: layerNr = maxLayer - 1
    # print("photonfile.getBitmap()")
    layerimg = photonfile.getBitmap(layerNr, layerForecolor, layerBackcolor)
    dispimg = layerimg
    # print("refreshLayerControls()")
    refreshLayerControls()
    return


def init_pygame_surface():
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

    pygame.init()
    pygame.display.set_caption("Photon File Editor")
    # load and set the logo
    logo = pygame.image.load("PhotonEditor32x32.png")
    pygame.display.set_icon(logo)
    pygame.font.init()

    # create a surface on screen width room for settings
    screen = pygame.display.set_mode((windowwidth, windowheight))
    scale = (0.25, 0.25)
    dispimg = pygame.Surface((int(1440 * scale[0]), int(2560 * scale[1])))
    dispimg.fill((0,0,0))
    previmg[0]=dispimg
    previmg[1] = dispimg
    layerimg = dispimg

    # create menu
    def infoMessageBox(title,message):
        dialog = MessageDialog(screen, pos=(140, 140),
                               title=title,
                               message=message,
                               parentRedraw=redrawMainWindow)
        dialog.show()
    def errMessageBox(errormessage):
        dialog = MessageDialog(screen, pos=(140, 140),
                               title="Error",
                               message=errormessage,
                               parentRedraw=redrawMainWindow)
        dialog.show()

    def doNothing():
        return
    def saveFile():
        global filename
        if photonfile==None:
            print ("No photon file loaded!!")
            infoMessageBox("No photon file loaded!","There is no .photon file loaded to save.")
            return
        saveHeader2PhotonFile()
        savePreview2PhotonFile()
        saveLayer2PhotonFile()
        dialog = FileDialog(screen, (40, 40), ext=".photon",title="Save Photon File", defFilename="newfile.photon", parentRedraw=redrawMainWindow)
        retfilename=dialog.newFile()
        if not retfilename==None:
            filename=retfilename
            photonfile.writeFile(filename)
            barefilename = (os.path.basename(filename))
            pygame.display.set_caption("Photon File Editor - " + barefilename)
            '''
            print ("Returned: ",filename)
            try:
                photonfile.writeFile(filename)
            except Exception as err:
                errMessageBox(str(err))
            '''
        else:
            print("User Canceled")
        return

    def loadFile():
        global filename
        dialog = FileDialog(screen, (40, 40), ext=".photon",title="Load Photon File", parentRedraw=redrawMainWindow)
        retfilename=dialog.getFile()
        if not retfilename==None:
            filename = retfilename
            print ("Returned: ",filename)
            openPhotonFile(filename)
            barefilename = (os.path.basename(filename))
            pygame.display.set_caption("Photon File Editor - "+barefilename)
            '''
            try:
                openPhotonFile(filename)
            except Exception as err:
                errMessageBox(str(err))
            '''
        else:
            print ("User Canceled")
        return

    def newFile():
        openPhotonFile("resources/newfile.photon")
        barefilename = ("New file")
        pygame.display.set_caption("Photon File Editor - " + barefilename)

    def replaceBitmap():
        global filename
        global dispimg
        global layerimg
        dialog = FileDialog(screen, (40, 40), ext=".png",title="Load Image File", parentRedraw=redrawMainWindow)
        retfilename=dialog.getFile()
        if not retfilename==None:
            filename = retfilename
            print ("Returned: ",filename)
            popup = PopupDialog(screen, pos=(140, 140),
                                title="Please wait...",
                                message="Photon File Editor is importing your images.")
            popup.show()
            photonfile.replaceBitmap(layerNr,filename)
            refreshLayerControls()
            layerimg = photonfile.getBitmap(layerNr, layerForecolor, layerBackcolor)
            dispimg = layerimg
            '''
            try:
                openPhotonFile(filename)
            except Exception as err:
                errMessageBox(str(err))
            '''
        else:
            print ("User Canceled")
        return

    def importBitmaps():
        global photonfile
        global layerNr
        global dispimg
        global layerimg
        if photonfile==None:
            print ("No template loaded!!")
            infoMessageBox("No photon file loaded!","A .photon file is needed as template to load the bitmaps in.")
            return
        dialog = FileDialog(screen, (40, 40), ext=".png", title="Select directory with png files", parentRedraw=redrawMainWindow)
        directory = dialog.getDirectory()
        if not directory == None:
            print("Returned: ", directory)
            #try:
            popup = PopupDialog(screen, pos=(140, 140),
                                title="Please wait...",
                                message="Photon File Editor is importing your images.")
            popup.show()
            photonfile.replaceBitmaps(directory)

            layerNr=0
            refreshLayerControls()
            layerimg = photonfile.getBitmap(layerNr,layerForecolor,layerBackcolor)
            dispimg = layerimg
            #except Exception as err:
            #    errMessageBox(str(err))
        else:
            print("User Canceled")
        return

    def exportBitmaps():
        global filename
        global photonfile

        barefilename = (os.path.basename(filename))
        barenotextfilename=os.path.splitext(barefilename)[0]
        dirname=(os.path.dirname(filename))
        newdirname=os.path.join(dirname,barenotextfilename+".bitmaps" )
        if not os.path.isdir(newdirname):
            os.mkdir(newdirname)

        popup=PopupDialog(screen, pos=(140, 140),
                               title="Please wait...",
                               message="Photon File Editor is exporting your images.")
        popup.show()
        photonfile.exportBitmaps(newdirname,"slice_")
        del popup

        #print (barefilename,filename,newdirname)

    def about():
        dialog = MessageDialog(screen, pos=(140, 140),
                               title="About PhotonEditor",
                               message="Version Alpha \n Author: Nard Janssens \n License: Free for non-commerical use.",
                               parentRedraw=redrawMainWindow)
        dialog.show()
    def showSlices():
        global dispimg
        dispimg=layerimg
    def showPrev0():
        global dispimg
        dispimg = previmg[0]
    def showPrev1():
        global dispimg
        dispimg = previmg[1]

    menubar=MenuBar(screen)
    menubar.addMenu("File","F")
    menubar.addItem("File", "New", newFile)
    menubar.addItem("File","Load",loadFile)
    menubar.addItem("File","Save As",saveFile)
    menubar.addMenu("Edit", "E")
    menubar.addItem("Edit", "Import Bitmaps",importBitmaps)
    menubar.addItem("Edit", "Replace Bitmap", replaceBitmap)
    menubar.addItem("Edit", "Export Bitmaps", exportBitmaps)
    menubar.addMenu("View", "V")
    menubar.addItem("View", "Slices", showSlices)
    menubar.addItem("View", "Preview 0", showPrev0)
    menubar.addItem("View", "Preview 1",showPrev1)
    menubar.addItem("View", "3D", doNothing)
    menubar.addMenu("Help", "H")
    menubar.addItem("Help", "About",about)
    viewport_yoffset=menubar.height+8



    #layer nav buttons
    controls.append(ImgBox(screen, filename="resources/arrow-up.png", filename_hover="resources/arrow-up-hover.png", pos=(20,20+viewport_yoffset), borderhovercolor=(0,0,0),func_on_click=layerUp))
    controls.append(ImgBox(screen, filename="resources/arrow-down.png", filename_hover="resources/arrow-down-hover.png", pos=(20,80+viewport_yoffset), borderhovercolor=(0,0,0),func_on_click=layerDown))
    layerLabel=Label(screen,GRect(26,80,52,40),textcolor=(255,255,255),fontsize=24,text="",istransparent=True,center=True)
    layerLabel.font.set_bold(True)
    controls.append(layerLabel)

    transTypes={PhotonFile.tpByte: TextBox.HEX,PhotonFile.tpInt: TextBox.INT,PhotonFile.tpFloat: TextBox.FLOAT,PhotonFile.tpChar: TextBox.HEX}
    # Add Header data fields
    row=0
    titlebox=Label(screen,text="General", rect=GRect(settingsleft + settingslabelmargin, 10 + row * 24 + viewport_yoffset, settingscolwidth, 16),drawBorder=False)
    titlebox.font.set_bold(True)
    controls.append(titlebox)
    for row, (bTitle, bNr, bType, bEditable) in enumerate(PhotonFile.pfStruct_Header,1):#enum start at 1
        controls.append(Label(screen, text=bTitle, rect=GRect(settingsleft+settingslabelmargin,10+row*settingsrowspacing+viewport_yoffset,settingslabelwidth,settingsrowheight)))
    firstHeaderTextbox=len(controls)
    for row,  (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Header,1):#enum start at 1
        tbType = transTypes[bType]
        bcolor=(255,255,255) if bEditable else (128,128,128)
        controls.append(TextBox(screen, text="", \
                                rect=GRect(settingsleft+settingslabelwidth+settingstextboxmargin, 10 + row * settingsrowspacing+viewport_yoffset, settingstextboxwidth, settingsrowheight),\
                                editable=bEditable, \
                                backcolor=bcolor, \
                                textcolor=(0,0,0),\
                                inputType=tbType, \
                                onEnter=updateTextBox2PhotonFile, \
                                linkedData={"VarGroup":"Header","Title":bTitle,"NrBytes":bNr,"Type":bType} \
                                ))

    # Add Preview data fields
    row=0
    settingsleft = settingsleft+settingscolwidth
    titlebox = Label(screen, text="Preview", rect=GRect(settingsleft+settingslabelmargin,10+row*settingsrowspacing+viewport_yoffset,settingscolwidth,settingsrowheight))
    titlebox.font.set_bold(True)
    controls.append(titlebox)
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Previews, 1):
        controls.append(Label(screen, text=bTitle, rect=GRect(settingsleft+settingslabelmargin,10+row*settingsrowspacing+viewport_yoffset,settingslabelwidth,settingsrowheight)))

    row = 0
    #nav buttons for previewNr
    controls.append(Button(screen, rect=GRect(settingsleft + settingslabelwidth + settingstextboxmargin + settingstextboxwidth - 40,10 + row * settingsrowspacing + viewport_yoffset, 18, 20), text="<",func_on_click=prevDown))
    controls.append(Button(screen,rect=GRect(settingsleft+settingslabelwidth+settingstextboxmargin+settingstextboxwidth-18,10+row*settingsrowspacing+viewport_yoffset,18,20),text=">",func_on_click=prevUp))
    #PrevNr and Prev TextBoxes
    firstPreviewTextbox = len(controls)
    controls.append(Label(screen, text=str(prevNr),rect=GRect(settingsleft+settingslabelwidth+settingstextboxmargin, 10 + row * settingsrowspacing + viewport_yoffset, settingstextboxwidth-40, settingsrowheight)))
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Previews, 1):
        tbType = transTypes[bType]
        bcolor = (255, 255, 255) if bEditable else (128, 128, 128)
        controls.append(TextBox(screen, text="", \
                                rect=GRect(settingsleft+settingslabelwidth+settingstextboxmargin, 10 + row * settingsrowspacing+viewport_yoffset, settingstextboxwidth, settingsrowheight),\
                                editable=bEditable, \
                                backcolor=bcolor, \
                                textcolor=(0, 0, 0), \
                                inputType=tbType, \
                                onEnter=updateTextBox2PhotonFile, \
                                linkedData={"VarGroup": "Preview", "Title": bTitle, "NrBytes": bNr, "Type": bType} \
                                ))

    # Add Current Layer meta fields
    row=8
    titlebox = Label(screen, text="Layer", rect=GRect(settingsleft+settingslabelmargin,10+row*settingsrowspacing+viewport_yoffset,settingscolwidth,settingsrowheight))
    titlebox.font.set_bold(True)
    controls.append(titlebox)
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_LayerDef,9):
        controls.append(Label(screen, text=bTitle, rect=GRect(settingsleft+settingslabelmargin,10+row*settingsrowspacing+viewport_yoffset,120,16)))
    row=8
    firstLayerTextbox = len(controls)
    controls.append(Label(screen, text=str(layerNr), rect=GRect(settingsleft + settingslabelwidth+settingstextboxmargin, 10 + row * settingsrowspacing+viewport_yoffset, settingstextboxwidth, settingsrowheight)))
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_LayerDef, 9):
        tbType = transTypes[bType]
        bcolor = (255, 255, 255) if bEditable else (128, 128, 128)
        controls.append(TextBox(screen, text="", \
                                rect=GRect(settingsleft + settingslabelwidth+settingstextboxmargin, 10 + row * settingsrowspacing+viewport_yoffset, settingstextboxwidth, settingsrowheight),\
                                editable=bEditable, \
                                backcolor=bcolor, \
                                textcolor=(0, 0, 0), \
                                inputType=tbType,\
                                onEnter=updateTextBox2PhotonFile, \
                                linkedData={"VarGroup": "LayerDef", "Title": bTitle, "NrBytes": bNr, "Type": bType} \
                                ))
    #controls[firstHeaderTextbox].backcolor=(255,0,0)
    #controls[firstPreviewTextbox].backcolor = (255, 0, 0)
    #controls[firstLayerTextbox].backcolor = (255, 0, 0)


def updateTextBox2PhotonFile(textbox, val,linkedData):
    global photonfile
    if photonfile==None: return
    #print ("updateTextBox2PhotonFile")
    #print ("data: ",val, linkedData)
    for control in controls:
        if control==textbox:
            pVarGroup=linkedData["VarGroup"]
            pTitle= linkedData["Title"]
            pBNr = linkedData["NrBytes"]
            pType = linkedData["Type"]
            pLayerNr = None
            if "LayerNr" in linkedData:linkedData["LayerNr"]
            bytes=None
            #do some check if val is of correct type and length
            if pType == PhotonFile.tpChar:bytes=PhotonFile.hex_to_bytes(val)
            if pType == PhotonFile.tpByte:bytes = PhotonFile.hex_to_bytes(val)
            if pType == PhotonFile.tpInt: bytes = PhotonFile.int_to_bytes(int(val))
            if pType == PhotonFile.tpFloat: bytes = PhotonFile.float_to_bytes(float(val))
            if not len(bytes)==pBNr:
                print ("Error: Data size ("+str(len(bytes))+") not expected ("+str(pBNr)+")in PhotonViewer.updateTextBox2PhotonFile!")
                print ("  Metadata: ", linkedData)
                print ("  Value: ", val)
                print ("  Bytes: ", bytes)
                return
            if pVarGroup=="Header":photonfile.Header[pTitle]=bytes
            if pVarGroup=="Preview":photonfile.Previews[prevNr][pTitle]=bytes
            if pVarGroup=="LayerDef": photonfile.LayerDefs[layerNr][pTitle] = bytes
            #print ("Found. New Val: ",val,linkedData)

    return

def saveHeader2PhotonFile():
    #print ("saveHeader2PhotonFile")
    global photonfile
    global firstHeaderTextbox

    if photonfile==None:return
    # Header data fields
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Header,firstHeaderTextbox):#enum start at 22
        if bEditable:
            textBox=controls[row]
            #print (row,bTitle,textBox.text)
            updateTextBox2PhotonFile(textBox,textBox.text,{"VarGroup": "Header", "Title": bTitle, "NrBytes": bNr, "Type": bType})

def savePreview2PhotonFile():
    #print("savePreview2PhotonFile")
    global photonfile
    global prevNr
    global firstPreviewTextbox

    if photonfile==None:return
    # Preview data fields
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Previews, firstPreviewTextbox+1):
        if bEditable:
            textBox=controls[row]
            print (row,bTitle,textBox.text)
            updateTextBox2PhotonFile(textBox,textBox.text,{"VarGroup": "Preview", "Title": bTitle, "NrBytes": bNr, "Type": bType})

def saveLayer2PhotonFile():
    #print ("saveLayer2PhotonFile")
    global photonfile
    global layerNr
    global firstLayerTextbox
    if photonfile == None: return
    # Current Layer meta fields
    for row, (bTitle, bNr, bType, bEditable) in enumerate(PhotonFile.pfStruct_LayerDef, firstLayerTextbox+1):
        if bEditable:
            textBox=controls[row]
            #print (row,bTitle,textBox.text)
            updateTextBox2PhotonFile(textBox,textBox.text,{"VarGroup": "LayerDef", "Title": bTitle, "NrBytes": bNr, "Type": bType})

def refreshHeaderControls():
    global photonfile
    global firstHeaderTextbox
    if photonfile==None:return
    # Header data fields
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Header,firstHeaderTextbox ):
        nr=PhotonFile.convBytes(photonfile.Header[bTitle],bType)
        if bType==PhotonFile.tpFloat:nr=round(nr,4) #round floats to 4 decimals
        controls[row].setText(str(nr))

def refreshPreviewControls():
    global photonfile
    global prevNr
    global firstPreviewTextbox
    if photonfile == None: return
    # Preview data fields
    row = firstPreviewTextbox
    controls[row].setText(str(prevNr)+"/2")
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Previews, firstPreviewTextbox+1):
        nr=PhotonFile.convBytes(photonfile.Previews[prevNr][bTitle],bType)
        if bType == PhotonFile.tpFloat: nr = round(nr, 4) #round floats to 4 decimals
        controls[row].setText(str(nr))

def refreshLayerControls():
    global photonfile
    global layerNr
    global layerLabel
    if photonfile==None:return
    if photonfile.nrLayers() == 0: return  # could occur if loading new file
    # Current Layer meta fields
    row=firstLayerTextbox
    controls[row].setText(str(layerNr)+ " / "+str(photonfile.nrLayers()))
    #print (layerNr)
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_LayerDef,firstLayerTextbox+1):
        nr=PhotonFile.convBytes(photonfile.LayerDefs[layerNr][bTitle],bType)
        #print("reading: ", bTitle,"=",nr)
        if bType == PhotonFile.tpFloat: nr = round(nr, 4) #round floats to 4 decimals
        controls[row].setText(str(nr))

    #finally we update layerLabel in between the up and down ^ on the top left of the screen
        layerLabel.setText(str(layerNr))


def openPhotonFile(filename):
    global photonfile
    global dispimg
    global layerimg
    global previmg
    global layerNr
    # read file
    photonfile = PhotonFile(filename)
    photonfile.readFile()

    layerNr = 0  # reset this to 0 so we prevent crash if previous photonfile was navigated to layer above the last layer of new photonfile
    layerimg=photonfile.getBitmap(layerNr,layerForecolor,layerBackcolor)
    previmg[0]=photonfile.getPreviewBitmap(0)
    previmg[1] = photonfile.getPreviewBitmap(1)
    dispimg=layerimg
    refreshHeaderControls()
    refreshPreviewControls()
    refreshLayerControls()


# initialize the pygame module
init_pygame_surface()

########################################################################################################################
##  Drawing/Event-Polling Loop
########################################################################################################################

# define a variable to control the main loop
running = True

def redrawMainWindow():
    w,h=dispimg.get_size()
    dw=(1440/4-w)/2
    dh=(2560/4-h)/2
    screen.fill(defFormBackground)
    if not photonfile==None:
        if not photonfile.isDrawing:
            screen.blit(dispimg, (dw, dh))
    else:#also if we have no photonfile we still need to draw to cover up menu/filedialog etc
        screen.blit(dispimg, (dw, dh))

    for ctrl in controls:
        ctrl.redraw()

    menubar.redraw()

    if layerCursorActive and not photonfile==None and dispimg==layerimg:
        pygame.draw.rect(screen, (0, 0, 150), scrollLayerRect.tuple(), 1)
        pygame.draw.rect(screen, (0,0,255), layerCursorRect.tuple(), 0)



# main loop
while running:
    # redraw photonfile

    redrawMainWindow()
    pygame.display.flip()
    #pygame.time.Clock().tick(60)

    # event handling, gets all event from the eventqueue
    for event in pygame.event.get():
        pos = pygame.mouse.get_pos()
        # only do something if the event is of type QUIT
        if event.type == pygame.QUIT:
            # change the value to False, to exit the main loop
            running = False
        if event.type == pygame.MOUSEBUTTONUP:
            menubar.handleMouseUp(pos,event.button)
            for ctrl in controls:
                ctrl.handleMouseUp(pos,event.button)

        if event.type == pygame.MOUSEBUTTONDOWN:
            menubar.handleMouseDown(pos,event.button)
            for ctrl in controls:
                ctrl.handleMouseDown(pos,event.button)

            #Calc position of layerCursor
            if not photonfile==None:
                mousePoint=GPoint.fromTuple(pos)
                if mousePoint.inGRect(scrollLayerRect):
                    relY=(mousePoint.y-scrollLayerVMargin)/(2560/4-scrollLayerVMargin*2)
                    layerNr=int((photonfile.nrLayers()-1)*relY)
                    layerCursorRect=scrollLayerRect.copy()
                    layerCursorRect.y=mousePoint.y-2
                    layerCursorRect.height=4
                    print("layercursor:", layerCursorRect, layerNr,"/",photonfile.nrLayers())
                    #layerCursorActive=True
                    layerimg = photonfile.getBitmap(layerNr,layerForecolor,layerBackcolor)
                    dispimg = layerimg
                    refreshLayerControls()
                else:
                    None
                    #layerCursorActive=False
                #print (event.button)


        if event.type == pygame.MOUSEMOTION:
            menubar.handleMouseMove(pos)
            for ctrl in controls:
                ctrl.handleMouseMove(pos)

        if event.type == pygame.KEYDOWN :
            if event.key == pygame.K_UP: layerUp()
            if event.key == pygame.K_DOWN: layerDown()
            if event.key == pygame.K_ESCAPE :
              print ("Escape key pressed down.")
              running = False
            else:
                for ctrl in controls:
                    ctrl.handleKeyDown(event.key,event.unicode)

        #elif event.type == pygame.KEYUP :

pygame.quit()


