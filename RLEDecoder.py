import pygame
from pygame.locals import *
import struct

def bytes_to_int(bytes):
    result = 0
    for b in reversed(bytes):
        result = result * 256 + int(b)
    return result

class PhotonFile:

    def __init__(self,photonfilename, pyscreen):
        self.filename = photonfilename
        self.pyscreen=pyscreen


    def readFile(self):
        with open(self.filename, "rb") as binary_file:
            binary_file.seek(0)  # Go to beginning
            #HEADER
            self.unknown0        =binary_file.read(8)
            self.sizeX           =binary_file.read(4)
            self.sizeY           =binary_file.read(4)
            self.sizeZ           =binary_file.read(4)
            self.padding0        =binary_file.read(3*4)
            self.layerThickness  = binary_file.read(4)
            self.normalExposure= binary_file.read(4)
            self.bottomExposure= binary_file.read(4)
            self.offTime= binary_file.read(4)
            self.nBottomLayers= binary_file.read(4)
            self.resolutionX= binary_file.read(4)
            self.resolutionY= binary_file.read(4)
            self.unknown3= binary_file.read(4)
            self.unknown4= binary_file.read(4)
            self.nLayers= binary_file.read(4)
            self.unknown5= binary_file.read(4)
            self.unknown6= binary_file.read(4)
            self.unknown7= binary_file.read(4)
            self.padding1= binary_file.read(6*4)

            #REST
            self.unknown8 = binary_file.read(4)
            self.unknown9 = binary_file.read(4)
            self.dataStartPos0= binary_file.read(4)
            self.dataSize0= binary_file.read(4)
            self.padding0= binary_file.read(4*4)
            dataSize0 = bytes_to_int(self.dataSize0)
            print("dataSize0:")
            print("  hex:",' '.join(format(x, '02X') for x in self.dataSize0))
            print("  dec:", dataSize0)
            self.c0= binary_file.read(dataSize0)
            self.unknown14 = binary_file.read(4)
            self.unknown15 = binary_file.read(4)
            self.dataStartPos1 = binary_file.read(4)
            self.dataSize1 = binary_file.read(4)
            self.padding1 = binary_file.read(4 * 4)
            dataSize1=bytes_to_int(self.dataSize1)
            print("dataSize1:")
            print("  hex:",' '.join(format(x, '02X') for x in self.dataSize1))
            print("  dec:", dataSize1)
            self.c1 = binary_file.read(dataSize1)

            #LAYERDEFS
            nLayers=bytes_to_int(self.nLayers)
            print("nLayers:")
            print("  hex:",' '.join(format(x, '02X') for x in self.nLayers))
            print("  dec:", nLayers)

            self.layerHeight=[None]*nLayers
            self.bottomExposureTime=[None]*nLayers
            self.offTime = [None]*nLayers
            self.dataStartPos = [None]*nLayers
            self.rawDataSize =[None]*nLayers
            self.padding = [None]*nLayers
            print ("Reading layer meta-info")
            for lNr in range (0,nLayers):
                print ("  layer: ", lNr)
                self.layerHeight[lNr]= binary_file.read(4)
                self.bottomExposureTime[lNr]= binary_file.read(4)
                self.offTime[lNr]= binary_file.read(4)
                self.dataStartPos[lNr]= binary_file.read(4)
                self.rawDataSize[lNr]= binary_file.read(4)
                self.padding[lNr]= binary_file.read(4*4)

            #LAYERRAWDATA
            self.layerDataBlock = [None] * nLayers
            self.endOfLayer = [None] * nLayers
            print("Reading layer image-info")
            for lNr in range(0,nLayers):
                print ("  layer: ", lNr)
                rawDataSize=bytes_to_int(self.rawDataSize[lNr])
                self.layerDataBlock[lNr]=binary_file.read(rawDataSize-1)
                # -1 because we don count byte for endOfLayer
                self.endOfLayer[lNr]=binary_file.read(1)


            #print (' '.join(format(x, '02X') for x in header))

            self.drawLayer(0)


    def drawLayer(self,layerNr):
        bA = self.layerDataBlock[layerNr]

        # Seek position and read N bytes
        x=0
        y=0
        debStr="0  "
        for idx,b in enumerate(bA):
            nr = b & ~(1 << 7) # turn highest bit of
            val = b >> 7       # only read 1st bit
            '''
            if x > 0:
                debStr = debStr + format(b, '02X') + " "
            if x == 0:
                print(debStr)
                debStr = str(y) + "  "
            '''
            for i in range(0,nr):
                self.pyscreen.set_at((int(x/4),int(y/4)),(255*val,255*val,255))
                x = x + 1
                if x>=1440:
                    x=0
                    y=y+1
                    #print (x,y,b,val)
            if y > 2560: break
        print("Screen Drawn")
        return




# initialize the pygame module
pygame.init()
# load and set the logo
#logo = pygame.image.load("logo32x32.png")
#pygame.display.set_icon(logo)
pygame.display.set_caption("Photon Encoder/Decoder")

# create a surface on screen that has the size of 240 x 180
screen = pygame.display.set_mode((int(1440/4),int(2560/4)))

 #read file
photonfile = PhotonFile ("SamplePhotonFiles/Smilie.photon",screen)
photonfile.readFile()


# define a variable to control the main loop
running = True

# main loop
drawn=False
while running:
    if not drawn:
        draw()
        pygame.display.flip()
        drawn=True

    # event handling, gets all event from the eventqueue
    for event in pygame.event.get():
        # only do something if the event is of type QUIT
        if event.type == pygame.QUIT:
            # change the value to False, to exit the main loop
            running = False





