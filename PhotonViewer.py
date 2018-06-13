import pygame
from pygame.locals import *



########################################################################################################################
## PhotonFile class
## - reads file
## - draws layer
########################################################################################################################

class PhotonFile:
    isDrawing=False

    tpByte = 0
    tpChar = 1
    tpInt = 2
    tpFloat = 3

    pfStruct_Header = [
        ("unknown0", 8,tpByte),
        ("sizeX", 4,tpFloat),
        ("sizeY", 4,tpFloat),
        ("sizeZ", 4,tpFloat),
        ("padding0", 3 * 4,tpInt),
        ("layerThickness", 4,tpFloat),
        ("normalExposure", 4,tpFloat),
        ("bottomExposure", 4,tpFloat),
        ("offTime", 4,tpFloat),
        ("nBottomLayers", 4,tpInt),
        ("resolutionX", 4,tpInt),
        ("resolutionY", 4,tpInt),
        ("unknown3", 4,tpInt),
        ("unknown4", 4,tpInt),
        ("nLayers", 4,tpInt),
        ("unknown5", 4,tpInt),
        ("unknown6", 4,tpInt),
        ("unknown7", 4,tpInt),
        ("padding1", 6 * 4,tpInt)
    ]

    pfStruct_Common = [
        ("unknown8", 4,tpInt),
        ("unknown9", 4,tpInt),
        ("dataStartPos0", 4,tpInt),
        ("dataSize0", 4,tpInt),
        ("padding0", 4 * 4,tpInt),
        ("c0", -1,tpByte),
        ("unknown14", 4,tpInt),
        ("unknown15", 4,tpInt),
        ("dataStartPos1", 4,tpInt),
        ("dataSize1", 4,tpInt),
        ("padding1", 4 * 4,tpInt),
        ("c1", -1,tpByte),
    ]

    pfStruct_LayerDef = [
        ("layerHeight", 4,tpFloat),
        ("bottomExposureTime", 4,tpFloat),
        ("offTime", 4,tpFloat),
        ("dataStartPos", 4,tpInt),
        ("rawDataSize", 4,tpInt),
        ("padding", 4 * 4,tpInt)
    ]

    Header = {}
    Common = {}
    LayerDefs = []
    LayerData = []

    def bytes_to_int(self,bytes):
        result = 0
        for b in reversed(bytes):
            result = result * 256 + int(b)
        return result

    def bytes_to_float(self,inbytes):
        bits = self.bytes_to_int(inbytes)
        mantissa = ((bits & 8388607) / 8388608.0)
        exponent = (bits >> 23) & 255
        sign = 1.0 if bits >> 31 == 0 else -1.0
        if exponent != 0:
            mantissa += 1.0
        elif mantissa == 0.0:
            return sign * 0.0
        return sign * pow(2.0, exponent - 127) * mantissa

    def bytes_to_hex(self,bytes):
        return ' '.join(format(h, '02X') for h in bytes)

    def convBytes(self,bytes,bType):
        nr=None
        if bType==self.tpInt:
            nr=self.bytes_to_int(bytes)
        if bType == self.tpFloat:
            nr = self.bytes_to_float(bytes)
        if bType == self.tpByte:
            nr = self.bytes_to_hex(bytes)
        return nr


    def __init__(self, photonfilename, pyscreen):
        self.filename = photonfilename
        self.pyscreen = pyscreen

    def readFile(self):
        with open(self.filename, "rb") as binary_file:
            # Start at beginning
            binary_file.seek(0)

            # HEADER
            for bTitle, bNr, bType in self.pfStruct_Header:
                self.Header[bTitle] = binary_file.read(bNr)

            # COMMON
            for bTitle, bNr,bType in self.pfStruct_Common:
                # if C0 or C1 the number bytes to read is given bij dataSize0 and dataSize1
                if bTitle == "c0":bNr = dataSize0
                if bTitle == "c1": bNr = dataSize1
                self.Common[bTitle] = binary_file.read(bNr)
                if bTitle == "dataSize0":dataSize0 = self.bytes_to_int(self.Common[bTitle])
                if bTitle == "dataSize1": dataSize1 = self.bytes_to_int(self.Common[bTitle])

            # LAYERDEFS
            nLayers = self.bytes_to_int(self.Header["nLayers"])
            self.LayerDefs =[dict() for x in range(nLayers)]
            print("nLayers:", nLayers)
            #print("  hex:", ' '.join(format(x, '02X') for x in self.Header["nLayers"]))
            #print("  dec:", nLayers)
            print("Reading layer meta-info")
            for lNr in range(0, nLayers):
                print("  layer: ", lNr)
                for bTitle, bNr,bType in self.pfStruct_LayerDef:
                    self.LayerDefs[lNr][bTitle] = binary_file.read(bNr)

            # LAYERRAWDATA
            print("Reading layer image-info")
            self.LayerData = [dict() for x in range(nLayers)]
            for lNr in range(0, nLayers):
                rawDataSize = self.bytes_to_int(self.LayerDefs[lNr]["rawDataSize"])
                print("  layer: ", lNr, " size: ",rawDataSize)
                self.LayerData[lNr]["Raw"] = binary_file.read(rawDataSize - 1)
                # -1 because we don count byte for endOfLayer
                self.LayerData[lNr]["EndOfLayer"] = binary_file.read(1)

            # print (' '.join(format(x, '02X') for x in header))

            self.drawLayer(0)

    def drawLayer(self, layerNr):
        self.isDrawing=True
        pygame.draw.rect(self.pyscreen, (0,0,0), (0,0,int(1440/4), int(2560/4)))
        self.font = pygame.font.SysFont("Consolas", 32)
        textsurface = self.font.render("Please wait...", False, (255,255,255))
        self.pyscreen.blit(textsurface, ((100,100)))

        pygame.display.flip()

        bA = self.LayerData[layerNr]["Raw"]

        # Seek position and read N bytes
        x = 0
        y = 0
        for idx, b in enumerate(bA):
            nr = b & ~(1 << 7)  # turn highest bit of
            val = b >> 7  # only read 1st bit

            x1 = int(x / 4)
            y1 = int(y / 4)
            x2 = int((x+nr)/4)
            y2 = y1
            col=(55*val,255*val,255)
            if x2>int(1440/4): x2=int(1440/4)
            pygame.draw.line(self.pyscreen,col,(x1,y1),(x2,y2))
            x=x+nr
            if x>=1440:
                nr=x-1440
                x=0
                y=y+1
                x1 = int(x / 4)
                y1 = int(y / 4)
                x2 = int((x + nr) / 4)
                y2 = y1
                pygame.draw.line(self.pyscreen, col, (x1, y1), (x2, y2))
                x=x+nr
        print("Screen Drawn")
        pygame.display.flip()
        self.isDrawing = False
        #break
        return


########################################################################################################################
## UI/Datafield classes
########################################################################################################################

class Rect():
    x = 0
    y = 0
    width = 0
    height = 0

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def tuple(self):
        return (self.x, self.y, self.width, self.height)

class ImgBox():
    rect=None
    img=None
    hoverimg=None
    hoverActive=False
    action=None

    def __init__(self, pyscreen, filename,filename_hover=None, pos=(0,0),borderhovercolor=(0,0,255),func_on_click=None):
        self.pyscreen = pyscreen
        self.img=pygame.image.load(filename)
        if not filename_hover==None:
            self.hoverimg = pygame.image.load(filename_hover)
        self.rect=self.img.get_rect()
        self.rect[0]=pos[0]
        self.rect[1] = pos[1]
        self.borderhovercolor=borderhovercolor
        self.func_on_click=func_on_click
        if func_on_click==None: print ("None")

    def redraw(self):
        self.pyscreen.blit(self.img,self.rect)
        if self.hoverActive and not self.hoverimg==None:
            self.pyscreen.blit(self.hoverimg, self.rect)
        else:
            self.pyscreen.blit(self.img, self.rect)

    def handleMouseMove(self, pos):
        if pos[0] > self.rect[0] and pos[0] < (self.rect[0] + self.rect[2]) and \
            pos[1] > self.rect[1] and pos[1] < (self.rect[1] + self.rect[3]):
            self.hoverActive=True
        else:
            self.hoverActive=False

    def handleMouseUp(self, pos):
        if pos[0] > self.rect[0] and pos[0] < (self.rect[0] + self.rect[2]) and \
                pos[1] > self.rect[1] and pos[1] < (self.rect[1] + self.rect[3]):
            if not self.func_on_click==None:
                self.func_on_click()

    def handleKeyDown(self,key,unicode):
        return

class TextBox():
    rect=Rect(0,0,80,32)
    margin = Rect(4, 4, 4, 4)
    bordercolor = (0, 0, 255)
    backcolor = (50, 50, 50)
    textcolor = (255, 255, 255)
    borderwidth = 1
    text = "text"
    maxlength=10
    font=None
    fontname = "Consolas"
    fontsize = 24
    editable=True
    cursorActive=False
    cursorChar=0


    def __init__(self, pyscreen,rect=Rect(0, 0, 80, 32),margin=Rect(4,4,4,4),
                 bordercolor=(0,0,255),backcolor=(50,50,50),textcolor=(255,255,255),
                 borderwidth=1,
                 text="text",maxlength=10,fontname="Consolas",fontsize=24,editable=True):
        self.pyscreen = pyscreen
        self.rect = rect
        self.margin=margin
        self.bordercolor=bordercolor
        self.backcolor=backcolor
        self.textcolor=textcolor
        self.borderwidth=borderwidth
        self.text = text
        self.maxlength = maxlength
        self.font = pygame.font.SysFont(fontname, fontsize)
        self.editable=editable

        # We want to make sure the text fully fits in the TextBox
        text_width, text_height = self.font.size("M[].j")
        if len(self.text)>self.maxlength: self.text=self.text[0:self.maxlength]
        #And that the textbox has enough height to show each letter
        if self.rect.height<(text_height+2*self.margin.y): self.rect.height=text_height+2*self.margin.y

    def redraw(self):
        color = (200, 000, 000)
        textsurface = self.font.render(self.text, False, self.textcolor)
        pygame.draw.rect(self.pyscreen, self.backcolor, self.rect.tuple(), 0)
        pygame.draw.rect(self.pyscreen, self.bordercolor, self.rect.tuple(), self.borderwidth)
        self.pyscreen.blit(textsurface, (self.rect.x + self.margin.x, self.rect.y + self.margin.y),(0,0,self.rect.width-2*self.margin.x,self.rect.height-2*self.margin.y))
        if self.cursorActive:
            text_width, text_height = self.font.size(self.text[0:self.cursorChar])
            if self.rect.x+self.margin.x+text_width<self.rect.x+self.rect.width: # we don't want to put cursor outside box
                pygame.draw.rect(self.pyscreen,
                                 self.textcolor,
                                 (self.rect.x+self.margin.x+text_width,self.rect.y+self.margin.y,2,self.rect.height-2*self.margin.y-1),
                                 0)

    def handleMouseMove(self,pos):
        return

    def handleMouseUp(self,pos):
        if not self.editable: return
        if pos[0]>self.rect.x and pos[0]<(self.rect.x+self.rect.width) and \
            pos[1] > self.rect.y and pos[1] < (self.rect.y + self.rect.height):
            self.cursorActive=True

            relx=pos[0]-self.rect.x
            rely = pos[1] - self.rect.y
            self.cursorChar=0
            for i in range(0,len(self.text)):
                text_width, text_height = self.font.size(self.text[0:i])
                if relx>(text_width+self.margin.x):
                    self.cursorChar=self.cursorChar+1
        else:
            self.cursorActive = False


    def handleKeyDown(self,key,unicode):
        if not self.editable: return
        if self.cursorActive:
            if key in range(K_0,K_9) or key==K_PERIOD:
                if len(self.text)<self.maxLength:
                    self.text=self.text[0:self.cursorChar]+unicode+self.text[self.cursorChar:]
                    self.cursorChar=self.cursorChar+1
            if key==K_BACKSPACE:
                self.text = self.text[0:self.cursorChar-1] + self.text[self.cursorChar:]
                self.cursorChar = self.cursorChar - 1
                if self.cursorChar<0: self.cursorChar=0
            if key == K_DELETE:
                self.text = self.text[0:self.cursorChar ]+ self.text[self.cursorChar+1:]
            if key == K_LEFT:
                self.cursorChar = self.cursorChar - 1
                if self.cursorChar < 0: self.cursorChar = 0
            if key == K_RIGHT:
                self.cursorChar = self.cursorChar + 1
                if self.cursorChar > len(self.text): self.cursorChar = len(self.text)

            print(key,K_DELETE,unicode, self.text)


########################################################################################################################
##  Setup screen and load Photon file
########################################################################################################################

# initialize the pygame module
pygame.init()
pygame.font.init()

# load and set the logo
# logo = pygame.image.load("logo32x32.png")
# pygame.display.set_icon(logo)
pygame.display.set_caption("Photon Encoder/Decoder")

# create a surface on screen width room for settings
settingswidth = 200*2 # 2 columns
settingsleft = int(1440 / 4)
screen = pygame.display.set_mode((int(1440 / 4) + settingswidth, int(2560 / 4)))

# read file
photonfile = PhotonFile("SamplePhotonFiles/Smilie.photon", screen)
photonfile.readFile()

# Add all UI elements
controls=[]

# Add Up/Down Layer Buttons
layerNr=0
def layerDown():
    global layerNr
    layerNr=layerNr-1
    if layerNr<0: layerNr=0
    photonfile.drawLayer(layerNr)
    redrawLayerControls()
    return

def layerUp():
    global layerNr
    maxLayer=photonfile.convBytes(photonfile.Header["nLayers"],photonfile.tpInt)
    layerNr=layerNr+1
    if layerNr==maxLayer: layerNr=maxLayer-1
    photonfile.drawLayer(layerNr)
    redrawLayerControls()
    return

controls.append(ImgBox(screen, filename="resources/arrow-up.png", filename_hover="resources/arrow-up-hover.png", pos=(20,20), borderhovercolor=(0,0,0),func_on_click=layerUp))
controls.append(ImgBox(screen, filename="resources/arrow-down.png", filename_hover="resources/arrow-down-hover.png", pos=(20,80), borderhovercolor=(0,0,0),func_on_click=layerDown))

# Add Header data fields
idx=0
controls.append(TextBox(screen, text="HEADER", rect=Rect(settingsleft+10,10+idx*24,180,16),editable=False,bordercolor=(0,0,0)))
idx=idx+1
for bTitle, bNr, bType in photonfile.pfStruct_Header:
    controls.append(TextBox(screen, text=bTitle, rect=Rect(settingsleft+10,10+idx*24,80,16),editable=False))
    nr=photonfile.convBytes(photonfile.Header[bTitle],bType)
    controls.append(TextBox(screen, text=str(nr), rect=Rect(settingsleft + 10+90, 10 + idx * 24, 80, 16),editable=True))
    idx=idx+1

# Add Common data fields
idx=0
settingsleft = settingsleft+200
controls.append(TextBox(screen, text="COMMON", rect=Rect(settingsleft+10,10+idx*24,180,16),editable=False,bordercolor=(0,0,0)))
idx=idx+1
for bTitle, bNr, bType in photonfile.pfStruct_Common:
    controls.append(TextBox(screen, text=bTitle, rect=Rect(settingsleft+10,10+idx*24,80,16),editable=False))
    nr=photonfile.convBytes(photonfile.Common[bTitle],bType)
    controls.append(TextBox(screen, text=str(nr), rect=Rect(settingsleft + 10+90, 10 + idx * 24, 80, 16),editable=True))
    idx=idx+1

def redrawLayerControls():
# Add Current Layer meta fields
    idx=14
    controls.append(TextBox(screen, text="LAYER: "+str(layerNr), rect=Rect(settingsleft+10,10+idx*24,180,16),editable=False,bordercolor=(0,0,0)))
    idx=idx+1

    for bTitle, bNr, bType in photonfile.pfStruct_LayerDef:
        controls.append(TextBox(screen, text=bTitle, rect=Rect(settingsleft+10,10+idx*24,80,16),editable=False))
        nr=photonfile.convBytes(photonfile.LayerDefs[layerNr][bTitle],bType)
        controls.append(TextBox(screen, text=str(nr), rect=Rect(settingsleft + 10+90, 10 + idx * 24, 80, 16),editable=True))
        idx=idx+1

redrawLayerControls()

########################################################################################################################
##  Drawing/Event-Polling Loop
########################################################################################################################

# define a variable to control the main loop
running = True

# main loop
while running:
    # if not drawn:
    while photonfile.isDrawing:
        None

    for ctrl in controls:
        ctrl.redraw()

    pygame.display.flip()
    #    drawn=True

    # event handling, gets all event from the eventqueue
    for event in pygame.event.get():
        # only do something if the event is of type QUIT
        if event.type == pygame.QUIT:
            # change the value to False, to exit the main loop
            running = False
        if event.type == pygame.MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()
            for ctrl in controls:
                ctrl.handleMouseUp(pos)

        if event.type == pygame.MOUSEMOTION:
            pos = pygame.mouse.get_pos()
            for ctrl in controls:
                ctrl.handleMouseMove(pos)

        if event.type == pygame.KEYDOWN :

            if event.key == pygame.K_ESCAPE :
              print ("Escape key pressed down.")
              running = False
            else:
                for ctrl in controls:
                    ctrl.handleKeyDown(event.key,event.unicode)

        #elif event.type == pygame.KEYUP :
