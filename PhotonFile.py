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

    def hex_to_bytes(self,hex):
        return
    def int_to_bytes(self,int):
        return
    def float_to_bytes(self,float):
        return

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
            #print("nLayers:", nLayers)
            #print("  hex:", ' '.join(format(x, '02X') for x in self.Header["nLayers"]))
            #print("  dec:", nLayers)
            #print("Reading layer meta-info")
            for lNr in range(0, nLayers):
                #print("  layer: ", lNr)
                for bTitle, bNr,bType in self.pfStruct_LayerDef:
                    self.LayerDefs[lNr][bTitle] = binary_file.read(bNr)

            # LAYERRAWDATA
            #print("Reading layer image-info")
            self.LayerData = [dict() for x in range(nLayers)]
            for lNr in range(0, nLayers):
                rawDataSize = self.bytes_to_int(self.LayerDefs[lNr]["rawDataSize"])
                #print("  layer: ", lNr, " size: ",rawDataSize)
                self.LayerData[lNr]["Raw"] = binary_file.read(rawDataSize - 1)
                # -1 because we don count byte for endOfLayer
                self.LayerData[lNr]["EndOfLayer"] = binary_file.read(1)

            # print (' '.join(format(x, '02X') for x in header))


    def getBitmap(self, layerNr):
        scale=(0.25,0.25)
        memory = pygame.Surface((int(1440*scale[0]), int(2560*scale[1])))
        self.isDrawing=True

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
            pygame.draw.line(memory, col, (x1, y1), (x2, y2))
            x=x+nr
            if x>=1440:
                nr=x-1440
                x=0
                y=y+1
                x1 = int(x / 4)
                y1 = int(y / 4)
                x2 = int((x + nr) / 4)
                y2 = y1
                pygame.draw.line(memory, col, (x1, y1), (x2, y2))
                x=x+nr
        #print("Screen Drawn")
        self.isDrawing = False
        return memory

    def writeFile(self, newfilename=None):
        if newfilename==None: newfilename=self.filename
        with open(newfilename, "wb") as binary_file:
            # Start at beginning
            binary_file.seek(0)

            # HEADER
            for bTitle, bNr, bType in self.pfStruct_Header:
                binary_file.write(self.Header[bTitle])

            # COMMON
            for bTitle, bNr,bType in self.pfStruct_Common:
                binary_file.write(self.Common[bTitle])

            # LAYERDEFS
            nLayers = self.bytes_to_int(self.Header["nLayers"])
            for lNr in range(0, nLayers):
                print("  layer: ", lNr)
                print("    def: ", self.LayerDefs[lNr])
                for bTitle, bNr,bType in self.pfStruct_LayerDef:
                    binary_file.write(self.LayerDefs[lNr][bTitle])

            # LAYERRAWDATA
            #print("Reading layer image-info")
            for lNr in range(0, nLayers):
                binary_file.write(self.LayerData[lNr]["Raw"])
                binary_file.write(self.LayerData[lNr]["EndOfLayer"])
