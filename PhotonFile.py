"""
Loads/Save .photon files (from the Anycubic Photon Slicer) in memory and allows editing of settings and bitmaps.
"""

__version__ = "alpha"
__author__ = "Nard Janssens, Vinicius Silva, Robert Gowans, Ivan Antalec, Leonardo Marques - See Github PhotonFileUtils"

import os
import copy
import math
import struct
from math import *

import pygame
from pygame.locals import *

try:
    import numpy
    numpyAvailable = True
    print("Numpy library available.")
except ImportError:
    numpyAvailable = False
    print ("Numpy library not found.")


########################################################################################################################
## Convert byte string to hex string
########################################################################################################################

def hexStr(bytes):
    if isinstance(bytes, bytearray):
        return ' '.join(format(h, '02X') for h in bytes)
    if isinstance(bytes, int):
        return format(bytes, '02X')
    return ("No Byte (string)")


########################################################################################################################
## Class PhotonFile
########################################################################################################################

class PhotonFile:
    isDrawing = False # Navigation can call upon retrieving bitmaps frequently. This var prevents multiple almost parallel loads
    nrLayersString = "# Layers" #String is used in multiple locations and thus can be edited here

    # Data type constants
    tpByte = 0
    tpChar = 1
    tpInt = 2
    tpFloat = 3

    # Clipboard Vars to copy/cut and paste layer settinngs/imagedata
    clipboardDef  = None
    clipboardData = None

    # This is the data structure of photon file. For each variable we need to know
    #   Title string to display user, nr bytes to read/write, type of data stored, editable
    #   Each file consists of
    #     - General info                                            ( pfStruct_Header,      Header)
    #     - Two previews which contain meta-info an raw image data  ( pfStruct_Previews,    Previews)
    #     - For each layer meta-info                                ( pfStruct_LayerDefs,   LayerDefs)
    #     - For each layer raw image data                           ( pfStruct_LayerData,   LayerData)
    pfStruct_Header = [
        ("Header",              8, tpByte,  False, ""),
        ("Bed X (mm)",          4, tpFloat, True,  "Short side of the print bed."),
        ("Bed Y (mm)",          4, tpFloat, True,  "Long side of the print bed."),
        ("Bed Z (mm)",          4, tpFloat, True,  "Maximum height the printer can print."),
        ("padding0",        3 * 4, tpByte,  False, ""), # 3 ints
        ("Layer height (mm)",   4, tpFloat, True,  "Default layer height."),
        ("Exp. time (s)",       4, tpFloat, True,  "Default exposure time."),
        ("Exp. bottom (s)",     4, tpFloat, True,  "Exposure time for bottom layers."),
        ("Off time (s)",        4, tpFloat, True,  "Time UV is turned of between layers."),
        ("# Bottom Layers",     4, tpInt,   True,  "Number of bottom layers.\n (These have different exposure time.)"),
        ("Resolution X",        4, tpInt,   True,  "X-Resolution of the screen through \n which the layer image is projected."),
        ("Resolution Y",        4, tpInt,   True,  "Y-Resolution of the screen through \n which the layer image is projected." ),
        ("Preview 0 (addr)",    4, tpInt,   False, "Address where the metadata \n of the High Res preview image can be found."),  # start of preview 0
        ("Layer Defs (addr)",   4, tpInt,   False, "Address where the metadata \n for the layer images can be found."),  # start of layerDefs
        (nrLayersString,        4, tpInt,   False, "Number of layers this file has."),
        ("Preview 1 (addr)",    4, tpInt,   False, "Address where the metadata \n of the Low Res preview image can be found."),  # start of preview 1
        ("unknown6",            4, tpInt,   False, ""),
        ("Proj.type-Cast/Mirror", 4, tpInt, False, "LightCuring/Projection type:\n 1=LCD_X_MIRROR \n 0=CAST"),   #LightCuring/Projection type // (1=LCD_X_MIRROR, 0=CAST)
        ("padding1",        6 * 4, tpByte,  False, "")  # 6 ints
    ]

    pfStruct_Previews = [
        ("Resolution X",        4, tpInt,   False, "X-Resolution of preview pictures."),
        ("Resolution Y",        4, tpInt,   False, "Y-Resolution of preview pictures."),
        ("Image Address",       4, tpInt,   False, "Address where the raw image can be found."),  # start of rawData0
        ("Data Length",         4, tpInt,   False, "Size (in bytes) of the raw image."),  # size of rawData0
        ("padding",         4 * 4, tpByte,  False, ""),  # 4 ints
        ("Image Data",         -1, tpByte,  False, "The raw image."),
    ]

    pfStruct_LayerDef = [
        ("Layer height (mm)",   4, tpFloat, True,  "Height at which this layer should be printed."),
        ("Exp. time (s)",       4, tpFloat, True,  "Exposure time for this layer."),
        ("Off time (s)",        4, tpFloat, True,  "Off time for this layer."),
        ("Image Address",       4, tpInt,   False, "Address where the raw image can be found."),#dataStartPos -> Image Address
        ("Data Length",         4, tpInt,   False, "Size (in bytes) of the raw image."),  #size of rawData+lastByte(1)
        ("padding",         4 * 4, tpByte,  False, "") # 4 ints
    ]

    # pfStruct_LayerData =
    #    rawData  - rle encoded bytes except last one
    #    lastByte - last byte of encoded bitmap data

    Header = {}
    Previews = [{},{}]
    LayerDefs = []
    LayerData = []

    History=[]
    HistoryMaxDepth = 10


    ########################################################################################################################
    ## Methods to convert bytes (strings) to python variables and back again
    ########################################################################################################################

    @staticmethod
    def bytes_to_int(bytes):
        """ Converts list or array of bytes to an int. """
        result = 0
        for b in reversed(bytes):
            result = result * 256 + int(b)
        return result

    @staticmethod
    def bytes_to_float(inbytes):
        """ Converts list or array of bytes to an float. """
        bits = PhotonFile.bytes_to_int(inbytes)
        mantissa = ((bits & 8388607) / 8388608.0)
        exponent = (bits >> 23) & 255
        sign = 1.0 if bits >> 31 == 0 else -1.0
        if exponent != 0:
            mantissa += 1.0
        elif mantissa == 0.0:
            return sign * 0.0
        return sign * pow(2.0, exponent - 127) * mantissa

    @staticmethod
    def bytes_to_hex(bytes):
        """ Converts list or array of bytes to an hex. """
        return ' '.join(format(h, '02X') for h in bytes)

    @staticmethod
    def hex_to_bytes(hexStr):
        """ Converts hex to array of bytes. """
        return bytearray.fromhex(hexStr)

    @staticmethod
    def int_to_bytes(intVal):
        """ Converts POSITIVE int to bytes. """
        return intVal.to_bytes(4, byteorder='little')

    @staticmethod
    def float_to_bytes(floatVal):
        """ Converts POSITIVE floats to bytes.
            Based heavily upon http: //www.simplymodbus.ca/ieeefloats.xls
        """
        # Error when floatVal=0.5
        return struct.pack('f',floatVal)

        if floatVal == 0: return (0).to_bytes(4, byteorder='big')

        sign = -1 if floatVal < 0 else 1
        firstBit = 0 if sign == 1 else 1
        exponent = -127 if abs(floatVal) < 1.1754943E-38 else floor(log(abs(floatVal), 10) / log(2, 10))
        exponent127 = exponent + 127
        mantissa = floatVal / pow(2, exponent) / sign
        substract = mantissa - 1
        multiply = round(substract * 8388608)
        div256_1 = multiply / 256
        divint_1 = int(div256_1)
        rem_1 = int((div256_1 - divint_1) * 256)
        div256_2 = divint_1 / 256
        divint_2 = int(div256_2)
        rem_2 = int((div256_2 - divint_2) * 256)

        bin1 = (exponent127 & 0b11111110) >> 1 | firstBit << 7
        bin2 = (exponent127 & 0b00000001) << 7 | divint_2
        bin3 = rem_2
        bin4 = rem_1
        # print ("ALT: ",bin(bin1_new), bin(bin2_new),bin(bin3_new),bin(bin4_new))
        bin1234 = bin1 | bin2 << 8 | bin3 << 16 | bin4 << 24
        return bin1234.to_bytes(4, byteorder='big')

    @staticmethod
    def convBytes(bytes, bType):
        """ Converts all photonfile types to bytes. """
        nr = None
        if bType == PhotonFile.tpInt:
            nr = PhotonFile.bytes_to_int(bytes)
        if bType == PhotonFile.tpFloat:
            nr = PhotonFile.bytes_to_float(bytes)
        if bType == PhotonFile.tpByte:
            nr = PhotonFile.bytes_to_hex(bytes)
        return nr


    ########################################################################################################################
    ## History methods
    ########################################################################################################################


    def realDeepCopy(self,dictionary):
        return #probable not needed
        """ Makes a real copy of a dictionary consisting of bytes strings
        """
        hC = copy.deepcopy(self.Header)
        for key,byteString in dictionary.items():
            dictionary[key]=(byteString+b'\x00')[:-1] # Force to make a real copy


    def saveToHistory(self, action, layerNr):
        """ Makes a copy of current /Layer Data to memory
            Since all are bytearrays no Copy.Deepcopy is needed.
        """

        # Copy LayerDefs and LayerData
        layerDef=copy.deepcopy(self.LayerDefs[layerNr])
        layerData=copy.deepcopy(self.LayerData[layerNr])
        self.realDeepCopy(layerDef)
        self.realDeepCopy(layerData)

        # Append to history stack/array
        newH = {"Action":action,"LayerNr":layerNr,"LayerDef":layerDef,"LayerData":layerData}
        print("Stored:",newH,id(layerDef),id(layerData))
        self.History.append(newH)
        if len(self.History)>self.HistoryMaxDepth:
            self.History.remove(self.History[0])


    def loadFromHistory(self):
        """ Load a copy of current Header/Preview/Layer Data to memory
            We copy by reference and remove item from history stack.
        """

        if len(self.History)==0:
            raise Exception("You have reached the maximum depth to undo.")

        # Find last item added to History
        idxLastAdded=len(self.History)-1
        lastItemAdded=self.History[idxLastAdded]
        action=lastItemAdded["Action"]
        layerNr =lastItemAdded["LayerNr"]
        layerDef = lastItemAdded["LayerDef"]
        layerData = lastItemAdded["LayerData"]
        print("Found:", self.History[idxLastAdded])

        # Reverse the actions
        if action=="insert":
            self.deleteLayer(layerNr, saveToHistory=False)
        elif action=="delete":
            self.clipboardDef=layerDef
            self.clipboardData=layerData
            self.insertLayerBefore(layerNr,fromClipboard=True, saveToHistory=False)
        elif action=="replace":
            self.clipboardDef=layerDef
            self.clipboardData=layerData
            self.deleteLayer(layerNr)
            self.insertLayerBefore(layerNr,fromClipboard=True, saveToHistory=False)

        # Remove this item
        self.History.remove(lastItemAdded)

    #Make alias for loadFromHistory
    undo = loadFromHistory

    ########################################################################################################################
    ## Class methods
    ########################################################################################################################

    def __init__(self, photonfilename):
        """ Just stores photon filename. """
        self.filename = photonfilename


    def nrLayers(self):
        """ Returns 4 bytes for number of layers as int. """
        return  PhotonFile.bytes_to_int(self.Header[self.nrLayersString])


    def readFile(self):
        """ Reads the photofile from disk to memory. """

        with open(self.filename, "rb") as binary_file:

            # Start at beginning
            binary_file.seek(0)

            # Read HEADER / General settings
            for bTitle, bNr, bType, bEditable,bHint in self.pfStruct_Header:
                self.Header[bTitle] = binary_file.read(bNr)

            # Read PREVIEWS settings and raw image data
            prevAddr=[]
            prevAddr.append(PhotonFile.bytes_to_int(self.Header["Preview 0 (addr)"]))
            prevAddr.append(PhotonFile.bytes_to_int(self.Header["Preview 1 (addr)"]))

            for previewNr in (0,1):
                binary_file.seek(prevAddr[previewNr])
                for bTitle, bNr, bType, bEditable, bHint in self.pfStruct_Previews:
                    # if rawData0 or rawData1 the number bytes to read is given bij dataSize0 and dataSize1
                    if bTitle == "Image Data": bNr = dataSize
                    self.Previews[previewNr][bTitle] = binary_file.read(bNr)
                    if bTitle == "Data Length": dataSize = PhotonFile.bytes_to_int(self.Previews[previewNr][bTitle])
	    
            layerDefAddr=PhotonFile.bytes_to_int(self.Header["Layer Defs (addr)"])
            binary_file.seek(layerDefAddr)

            # Read LAYERDEFS settings
            nLayers = PhotonFile.bytes_to_int(self.Header[self.nrLayersString])
            self.LayerDefs = [dict() for x in range(nLayers)]
            # print("nLayers:", nLayers)
            # print("  hex:", ' '.join(format(x, '02X') for x in self.Header[self.nrLayersString]))
            # print("  dec:", nLayers)
            # print("Reading layer meta-info")
            for lNr in range(0, nLayers):
                # print("  layer: ", lNr)
                for bTitle, bNr, bType, bEditable, bHint in self.pfStruct_LayerDef:
                    self.LayerDefs[lNr][bTitle] = binary_file.read(bNr)

            # Read LAYERRAWDATA image data
            # print("Reading layer image-info")
            self.LayerData = [dict() for x in range(nLayers)]
            for lNr in range(0, nLayers):
                rawDataAddr = PhotonFile.bytes_to_int(self.LayerDefs[lNr]["Image Address"])
                rawDataSize = PhotonFile.bytes_to_int(self.LayerDefs[lNr]["Data Length"])
                binary_file.seek(rawDataAddr)
                # print("  layer: ", lNr, " size: ",rawDataSize)
                self.LayerData[lNr]["Raw"] = binary_file.read(rawDataSize - 1) # b'}}}}}}}}}}
                # -1 because we don count byte for endOfLayer
                self.LayerData[lNr]["EndOfLayer"] = binary_file.read(1)

            # print (' '.join(format(x, '02X') for x in header))

            # Clear History for this new file
            self.History = []


    def writeFile(self, newfilename=None):
        """ Writes the photofile from memory to disk. """

        # Check if other filename is given to save to, otherwise use filename used to load file.
        if newfilename == None: newfilename = self.filename


        with open(newfilename, "wb") as binary_file:

            # Start at beginning
            binary_file.seek(0)

            # Write HEADER / General settings
            for bTitle, bNr, bType, bEditable,bHint in self.pfStruct_Header:
                binary_file.write(self.Header[bTitle])

            # Write PREVIEWS settings and raw image data
            for previewNr in (0, 1):
                for bTitle, bNr, bType, bEditable, bHint in self.pfStruct_Previews:
                    #print ("Save: ",bTitle)
                    binary_file.write(self.Previews[previewNr][bTitle])

            # Read LAYERDEFS settings
            nLayers = PhotonFile.bytes_to_int(self.Header[self.nrLayersString])
            for lNr in range(0, nLayers):
                #print("  layer: ", lNr)
                #print("    def: ", self.LayerDefs[lNr])
                for bTitle, bNr, bType, bEditable, bHint in self.pfStruct_LayerDef:
                    binary_file.write(self.LayerDefs[lNr][bTitle])

            # Read LAYERRAWDATA image data
            # print("Reading layer image-info")
            for lNr in range(0, nLayers):
                binary_file.write(self.LayerData[lNr]["Raw"])
                binary_file.write(self.LayerData[lNr]["EndOfLayer"])


    ########################################################################################################################
    ## Encoding
    ########################################################################################################################

    def encodedBitmap_Bytes_withnumpy(filename):
        """ Converts image data from file on disk to RLE encoded byte string.
            Uses Numpy library - Fast
            Based on https://gist.github.com/itdaniher/3f57be9f95fce8daaa5a56e44dd13de5
            Encoding scheme:
                Highest bit of each byte is color (black or white)
                Lowest 7 bits of each byte is repetition of that color, with max of 125 / 0x7D
        """

        # Load image and check if size is correct (1440 x 2560)
        imgsurf = pygame.image.load(filename)
        (width, height) = imgsurf.get_size()
        if not (width, height) == (1440, 2560):
            raise Exception("Your image dimensions are off and should be 1440x2560")

        # Convert image data to Numpy 1-dimensional array
        imgarr = pygame.surfarray.array2d(imgsurf)
        imgarr = numpy.rot90(imgarr,axes=(1,0))
        imgarr = numpy.fliplr(imgarr)  # reverse/mirror array
        x = numpy.asarray(imgarr).flatten(0)

        # Encoding magic
        where = numpy.flatnonzero
        x = numpy.asarray(x)
        n = len(x)
        if n == 0:
            return numpy.array([], dtype=numpy.int)
        starts = numpy.r_[0, where(~numpy.isclose(x[1:], x[:-1], equal_nan=True)) + 1]
        lengths = numpy.diff(numpy.r_[starts, n])
        values = x[starts]
        #ret=np.dstack((lengths, values))[0]

        # Reduce repetitions of color to max 0x7D/125 and store in bytearray
        rleData = bytearray()
        for (nr, col) in zip(lengths,values):
            color = (col>0)
            while nr > 0x7D:
                encValue = (color << 7) | 0x7D
                rleData.append(encValue)
                nr = nr - 0x7D
            encValue = (color << 7) | nr
            rleData.append(encValue)

        # Needed is an byte string, so convert
        return bytes(rleData)


    def encodedBitmap_Bytes_nonumpy(filename):
        """ Converts image data from file on disk to RLE encoded byte string.
            Processes pixels one at a time (pygame.get_at) - Slow
            Encoding scheme:
                Highest bit of each byte is color (black or white)
                Lowest 7 bits of each byte is repetition of that color, with max of 125 / 0x7D
        """

        # Load image and check if size is correct (1440 x 2560)
        imgsurf = pygame.image.load(filename)
        #bitDepth = imgsurf.get_bitsize()
        #bytePerPixel = imgsurf.get_bytesize()
        (width, height) = imgsurf.get_size()
        if not (width, height) == (1440,2560):
            raise Exception("Your image dimensions are off and should be 1440x2560")

        # Count number of pixels with same color up until 0x7D/125 repetitions
        rleData = bytearray()
        color = 0
        black = 0
        white = 1
        nrOfColor = 0
        prevColor=None
        for y in range(height):
            for x in range(width):
                # print (imgsurf.get_at((x, y)))
                (r, g, b, a) = imgsurf.get_at((x, y))
                if ((r + g + b) // 3) < 128:
                    color = black
                else:
                    color = white
                if prevColor == None: prevColor = color
                isLastPixel = (x == (width - 1) and y == (height - 1))
                if color == prevColor and nrOfColor < 0x7D and not isLastPixel:
                    nrOfColor = nrOfColor + 1
                else:
                    #print (color,nrOfColor,nrOfColor<<1)
                    encValue = (prevColor << 7) | nrOfColor # push color (B/W) to highest bit and repetitions to lowest 7 bits.
                    rleData.append(encValue)
                    prevColor = color
                    nrOfColor = 1
        return bytes(rleData)


    def encodedBitmap_Bytes(filename):
        """ Depening on availability of Numpy, calls upon correct Encoding method."""
        if numpyAvailable:
            return PhotonFile.encodedBitmap_Bytes_withnumpy(filename)
        else:
            return PhotonFile.encodedBitmap_Bytes_nonumpy(filename)


    ########################################################################################################################
    ## Decoding
    ########################################################################################################################

    def getBitmap_withnumpy(self, layerNr, forecolor=(128,255,128), backcolor=(0,0,0),scale=(0.25,0.25)):
        """ Decodes a RLE byte array from PhotonFile object to a pygame surface.
            Based on: https://gist.github.com/itdaniher/3f57be9f95fce8daaa5a56e44dd13de5
            Encoding scheme:
                Highest bit of each byte is color (black or white)
                Lowest 7 bits of each byte is repetition of that color, with max of 125 / 0x7D
        """

        # Tell PhotonFile we are drawing so GUI can prevent too many calls on getBitmap
        memory = pygame.Surface((int(1440 * scale[0]), int(2560 * scale[1])))
        if self.nrLayers()==0: return memory #could occur if loading new file
        self.isDrawing = True

        # Retrieve raw image data and add last byte to complete the byte array
        bA = self.LayerData[layerNr]["Raw"]
        # add endOfLayer Byte
        bA = bA + self.LayerData[layerNr]["EndOfLayer"]

        # Convert bytes to numpy 1 dimensional array
        bN =numpy.fromstring(bA,dtype=numpy.uint8)


        # Extract color value (highest bit) and nr of repetitions (lowest 7 bits)
        valbin = bN >> 7  # only read 1st bit
        nr = bN & ~(1 << 7)  # turn highest bit of

        # Replace 0's en 1's with correct colors
        forecolor_int = (forecolor[0] << 16) + (forecolor[1] << 8) + forecolor[2]
        backcolor_int = backcolor[0] << 16 + backcolor[1] << 8 + backcolor[2]
        val = numpy.array([{0: backcolor_int, 1: forecolor_int}[x] for x in valbin])

        # Make a 2d array like [ [3,0] [2,1], [nr_i,val_i]...] using the colorvalues (val) and repetitions(nr)
        runs = numpy.column_stack((nr, val))

        # Decoding magic
        runs_t = numpy.transpose(runs)
        lengths = runs_t[0].astype(int)
        values = runs_t[1].astype(int)
        starts = numpy.concatenate(([0], numpy.cumsum(lengths)[:-1]))
        starts, lengths, values = map(numpy.asarray, (starts, lengths, values))
        ends = starts + lengths
        n = ends[-1]
        x = numpy.full(n, 0)
        for lo, hi, val in zip(starts, ends, values):
            x[lo:hi] = val

        # Make sure we have a bitmap of the correct size and if not pad with black pixels
        if not len(x) == 3686400: print ("Warning: The file decoded with less bytes than needed. Will pad the file with zero bytes.")
        while not len(x)==3686400:
            x=numpy.append(x,(0,))

        # Convert 1-dim array to matrix
        rgb2d=x.reshape((2560,1440))                # data is stored in rows of 2560
        rgb2d = numpy.rot90(rgb2d, axes=(1, 0))     # we need 1440x2560
        rgb2d = numpy.fliplr(rgb2d)                 # however data us mirrored along x axis
        picture=pygame.surfarray.make_surface(rgb2d)# convert numpy array to pygame surface
        memory=pygame.transform.scale(picture, (int(1440*scale[0]), int(2560*scale[1]))) # rescale for display in window

        # Done drawing so next caller knows that next call can be made.
        self.isDrawing = False
        return memory


    def getBitmap_nonumpy(self, layerNr, forecolor=(128,255,128), backcolor=(0,0,0),scale=(0.25,0.25)):
        """ Decodes a RLE byte array from PhotonFile object to a pygame surface.
            Based on: https://gist.github.com/itdaniher/3f57be9f95fce8daaa5a56e44dd13de5
            Encoding scheme:
                Highest bit of each byte is color (black or white)
                Lowest 7 bits of each byte is repetition of that color, with max of 125 / 0x7D
        """

        # Tell PhotonFile we are drawing so GUI can prevent too many calls on getBitmap
        memory = pygame.Surface((int(1440 * scale[0]), int(2560 * scale[1])))
        if self.nrLayers()==0: return memory #could occur if loading new file
        self.isDrawing = True

        # Retrieve raw image data and add last byte to complete the byte array
        bA = self.LayerData[layerNr]["Raw"]
        # add endOfLayer Byte
        bA = bA + self.LayerData[layerNr]["EndOfLayer"]

        # Decode bytes to colors and draw lines of that color on the pygame surface
        x = 0
        y = 0
        for idx, b in enumerate(bA):
            # From each byte retrieve color (highest bit) and number of pixels of that color (lowest 7 bits)
            nr = b & ~(1 << 7)  # turn highest bit of
            val = b >> 7  # only read 1st bit

            # The surface to draw on is smaller (scale) than the file (1440x2560 pixels)
            x1 = int(x *scale[0])
            y1 = int(y *scale[1])
            x2 = int((x + nr) *scale[0])
            y2 = y1
            if val==0:
                col= backcolor
            else:
                col=forecolor
            # Bytes and repetions of pixels with same color can span muliple lines (y-values)
            if x2 > int(1440 *scale[0]): x2 = int(1440 *scale[1])
            pygame.draw.line(memory, col, (x1, y1), (x2, y2))
            # debug nr2=nr-(x+nr-1440) if (x+nr)>=1440 else nr
            # debug print("draw line: ", x, y, " - ", nr2)
            x = x + nr
            if x >= 1440:
                nr = x - 1440
                x = 0
                y = y + 1
                x1 = int(x *scale[0])
                y1 = int(y *scale[1])
                x2 = int((x + nr) *scale[0])
                y2 = y1
                pygame.draw.line(memory, col, (x1, y1), (x2, y2))
                # debug print ("draw line: ",x,y," - ",nr)
                x = x + nr
        #print("Screen Drawn")
        # debug print ("layer: ", layerNr)
        # debug print ("lastByte:", self.LayerData[layerNr]["EndOfLayer"])

        # Done drawing so next caller knows that next call can be made.
        self.isDrawing = False
        return memory


    def getBitmap(self, layerNr, forecolor=(128, 255, 128), backcolor=(0, 0, 0), scale=(0.25, 0.25)):
        """ Depending on availability of Numpy, calls upon correct Decoding method."""
        if numpyAvailable:
            return self.getBitmap_withnumpy(layerNr,forecolor,backcolor,scale)
        else:
            return self.getBitmap_nonumpy(layerNr,forecolor,backcolor,scale)


    def getPreviewBitmap(self, prevNr):
        """ Decodes a RLE byte array from PhotonFile object to a pygame surface.
            Based on https://github.com/Reonarudo/pcb2photon/issues/2
            Encoding scheme:
                The color (R,G,B) of a pixel spans 2 bytes (little endian) and each color component is 5 bits: RRRRR GGG GG X BBBBB
                If the X bit is set, then the next 2 bytes (little endian) masked with 0xFFF represents how many more times to repeat that pixel.
        """

        # Tell PhotonFile we are drawing so GUI can prevent too many calls on getBitmap
        self.isDrawing = True

        # Retrieve resolution of preview image and set pygame surface to that size.
        w = PhotonFile.bytes_to_int(self.Previews[prevNr]["Resolution X"])
        h = PhotonFile.bytes_to_int(self.Previews[prevNr]["Resolution Y"])
        s = PhotonFile.bytes_to_int(self.Previews[prevNr]["Data Length"])
        scale = ((1440 / 4) / w, (1440 / 4) / w)
        memory = pygame.Surface((int(w), int(h)))
        if w == 0 or h == 0: return memory # if size is (0,0) we return empty surface

        # Retrieve raw image data and add last byte to complete the byte array
        bA = self.Previews[prevNr]["Image Data"]

        # Decode bytes to colors and draw lines of that color on the pygame surface
        idx = 0
        pixelIdx = 0
        while idx < len(bA):
            # Combine 2 bytes Little Endian so we get RRRRR GGG GG X BBBBB (and advance read byte counter)
            b12 = bA[idx + 1] << 8 | bA[idx + 0]
            idx += 2
            # Retrieve colr components and make pygame color tuple
            red = math.floor(((b12 >> 11) & 0x1F) / 31 * 255)
            green = math.floor(((b12 >> 6) & 0x1F) / 31 * 255)
            blue = math.floor(((b12 >> 0) & 0x1F) / 31 * 255)
            col = (red, green, blue)

            # If the X bit is set, then the next 2 bytes (little endian) masked with 0xFFF represents how many more times to repeat that pixel.
            nr = 1
            if b12 & 0x20:
                nr12 = bA[idx + 1] << 8 | bA[idx + 0]
                idx += 2
                nr += nr12 & 0x0FFF

            # Draw (nr) many pixels of the color
            for i in range(0, nr, 1):
                x = int((pixelIdx % w))
                y = int((pixelIdx / w))
                memory.set_at((x, y), col)
                pixelIdx += 1

        # Scale the surface to the wanted resolution
        memory = pygame.transform.scale(memory, (int(w * scale[0]), int(h * scale[1])))

        # Done drawing so next caller knows that next call can be made.
        self.isDrawing = False
        return memory


    ########################################################################################################################
    ## Layer (Image) Operations
    ########################################################################################################################

    def layerHeight(self,layerNr):
        """ Return height between two layers
        """
        # We retrieve layer height from previous layer
        if layerNr>0:
            curLayerHeight = self.bytes_to_float(self.LayerDefs[layerNr]["Layer height (mm)"])
            prevLayerHeight = self.bytes_to_float(self.LayerDefs[layerNr-1]["Layer height (mm)"])
        else:
            if self.nrLayers()>1:
                curLayerHeight = self.bytes_to_float(self.LayerDefs[layerNr+1]["Layer height (mm)"])
                prevLayerHeight=0
            else:
                curLayerHeight=self.bytes_to_float(self.Header["Layer height (mm)"])
                prevLayerHeight = 0
        return curLayerHeight-prevLayerHeight
        #print ("Delta:", deltaHeight)


    def deleteLayer(self, layerNr, saveToHistory=True):
        """ Deletes layer and its image data in the PhotonFile object, but store in clipboard for paste. """

        # Store all data to history
        if saveToHistory: self.saveToHistory("delete",layerNr)

        #deltaHeight=self.bytes_to_float(self.LayerDefs[layerNr]["Layer height (mm)"])
        deltaHeight =self.layerHeight(layerNr)
        print ("deltaHeight:",deltaHeight)

        # Update start addresses of RawData of before deletion with size of one extra layerdef (36 bytes)
        for rLayerNr in range(0,layerNr):
            # Adjust image address for removal of image raw data and end byte
            curAddr=self.bytes_to_int(self.LayerDefs[rLayerNr]["Image Address"])
            newAddr=curAddr-36 # size of layerdef
            self.LayerDefs[rLayerNr]["Image Address"]= self.int_to_bytes(newAddr)

        # Update start addresses of RawData of after deletion with size of image and layerdef
        deltaLength = self.bytes_to_int(self.LayerDefs[layerNr]["Data Length"]) + 36  # +1 for len(EndOfLayer)
        nLayers=self.nrLayers()
        for rLayerNr in range(layerNr+1,nLayers):
            # Adjust image address for removal of image raw data and end byte
            curAddr=self.bytes_to_int(self.LayerDefs[rLayerNr]["Image Address"])
            newAddr=curAddr-deltaLength
            #print ("layer, cur, new: ",rLayerNr,curAddr,newAddr)
            self.LayerDefs[rLayerNr]["Image Address"]= self.int_to_bytes(newAddr)

            # Adjust layer starting height for removal of layer
            curHeight=self.bytes_to_float(self.LayerDefs[rLayerNr]["Layer height (mm)"])
            newHeight=curHeight-deltaHeight
            self.LayerDefs[rLayerNr]["Layer height (mm)"] =self.float_to_bytes(newHeight)

        # Store deleted layer in clipboard
        self.clipboardDef=self.LayerDefs[layerNr].copy()
        self.clipboardData=self.LayerData[layerNr].copy()

        # Delete layer settings and data and reduce number of layers in header
        self.LayerDefs.remove(self.LayerDefs[layerNr])
        self.LayerData.remove(self.LayerData[layerNr])
        self.Header[self.nrLayersString]=self.int_to_bytes(self.nrLayers()-1)

    def insertLayerBefore(self, layerNr, fromClipboard=False, saveToHistory=True):
        """ Inserts layer copying data of the previous layer or the clipboard. """
        if fromClipboard and self.clipboardDef==None: raise Exception("Clipboard is empty!")

        # Store all data to history
        if saveToHistory: self.saveToHistory("insert",layerNr)

        # Check if layerNr in range, could occur on undo after deleting last layer
        #   print(layerNr, "/", self.nrLayers())
        insertLast=False
        if layerNr>self.nrLayers(): layerNr=self.nrLayers()
        if layerNr == self.nrLayers():
            layerNr=layerNr-1 # temporary reduce layerNr
            insertLast=True

        # Check deltaHeight
        deltaHeight = self.layerHeight(layerNr)

        # Make duplicate of layerDef and layerData if not pasting from clipboard
        if fromClipboard == False:
            self.clipboardDef=self.LayerDefs[layerNr].copy()
            self.clipboardData=self.LayerData[layerNr].copy()

        # Set layerheight correctly
        if layerNr==0: # if first layer than the height should start at 0
            self.clipboardDef["Layer height (mm)"] = self.float_to_bytes(0)
        else:          # start at layer height of layer at which we insert
            curLayerHeight = self.bytes_to_float(self.LayerDefs[layerNr]["Layer height (mm)"])
            self.clipboardDef["Layer height (mm)"]=self.float_to_bytes(curLayerHeight)

        # Set start addresses of layer in clipboard, we add 1 layer(def) so add 36 bytes
        lA=self.bytes_to_int(self.LayerDefs[layerNr]["Image Address"])+36
        #   if lastlayer we need to add last image length
        if insertLast: lA=lA+self.bytes_to_int(self.LayerDefs[layerNr]["Data Length"])
        self.clipboardDef["Image Address"]=self.int_to_bytes(lA)

        # If we inserting last layer, we correct layerNr
        if insertLast: layerNr = layerNr + 1  # fix temporary reduced layerNr

        # Update start addresses of RawData of before insertion with size of one extra layerdef (36 bytes)
        for rLayerNr in range(0,layerNr):
            # Adjust image address for removal of image raw data and end byte
            curAddr=self.bytes_to_int(self.LayerDefs[rLayerNr]["Image Address"])
            newAddr=curAddr+36 # size of layerdef
            self.LayerDefs[rLayerNr]["Image Address"]= self.int_to_bytes(newAddr)

        # Update start addresses of RawData of after insertion with size of image and layerdef
        #   Calculate how much room we need in between. We insert an extra layerdef (36 bytes) and a extra image
        deltaLayerImgAddress = self.bytes_to_int(self.clipboardDef["Data Length"]) + 36
        nLayers=self.nrLayers()
        #   remove
        for rLayerNr in range(layerNr,nLayers):
            # Adjust image address for removal of image raw data and end byte
            curAddr=self.bytes_to_int(self.LayerDefs[rLayerNr]["Image Address"])
            newAddr=curAddr+deltaLayerImgAddress
            self.LayerDefs[rLayerNr]["Image Address"]= self.int_to_bytes(newAddr)

            # Adjust layer starting height for removal of layer
            curHeight=self.bytes_to_float(self.LayerDefs[rLayerNr]["Layer height (mm)"])
            newHeight=curHeight+deltaHeight
            self.LayerDefs[rLayerNr]["Layer height (mm)"] =self.float_to_bytes(newHeight)
            #print ("layer, cur, new: ",rLayerNr,curAddr,newAddr, "|", curHeight,newHeight ,">",self.bytes_to_float(self.LayerDefs[rLayerNr]["Layer height (mm)"]))

        # Insert layer settings and data and reduce number of layers in header
        self.LayerDefs.insert(layerNr, self.clipboardDef)
        self.LayerData.insert(layerNr, self.clipboardData)

        self.Header[self.nrLayersString]=self.int_to_bytes(self.nrLayers()+1)

        # Make new copy so second paste will not reference this inserted objects
        self.clipboardDef = self.LayerDefs[layerNr].copy()
        self.clipboardData = self.LayerData[layerNr].copy()


    def copyLayer(self,layerNr):
        # Make duplicate of layerDef and layerData
        self.clipboardDef=self.LayerDefs[layerNr].copy()
        self.clipboardData=self.LayerData[layerNr].copy()


    def replaceBitmap(self, layerNr,filePath, saveToHistory=True):
        """ Replace image data in PhotonFile object with new (encoded data of) image on disk."""

        print("  ", layerNr, "/", filePath)

        # Store all data to history
        if saveToHistory: self.saveToHistory("replace",layerNr)

        # Get/encode raw data
        rawData = PhotonFile.encodedBitmap_Bytes(filePath)

        # Last byte is stored seperately
        rawDataTrunc = rawData[:-1]
        rawDataLastByte = rawData[-1:]

        # Get change in image rawData size so we can correct starting addresses of higher layer images
        oldLength=self.bytes_to_int(self.LayerDefs[layerNr]["Data Length"]) #"Data Length" = len(rawData)+len(EndOfLayer)
        newLength=len(rawData)
        deltaLength=newLength-oldLength
        #print ("old, new, delta:",oldLength,newLength,deltaLength)

        # Update image settings and raw data of layer to be replaced
        self.LayerDefs[layerNr]["Data Length"] = self.int_to_bytes(len(rawData))
        self.LayerData[layerNr]["Raw"] = rawDataTrunc
        self.LayerData[layerNr]["EndOfLayer"] = rawDataLastByte

        # Update start addresses of RawData of all following images
        nLayers=self.nrLayers()
        for rLayerNr in range(layerNr+1,nLayers):
            curAddr=self.bytes_to_int(self.LayerDefs[rLayerNr]["Image Address"])
            newAddr=curAddr+deltaLength
            #print ("layer, cur, new: ",rLayerNr,curAddr,newAddr)
            self.LayerDefs[rLayerNr]["Image Address"]= self.int_to_bytes(newAddr)


    def replaceBitmaps(self, dirPath):
        """ Delete all images in PhotonFile object and add images in directory."""

        # Get all files, filter png-files and sort them alphabetically
        direntries = os.listdir(dirPath)
        files = []
        for entry in direntries:
            fullpath = os.path.join(dirPath, entry)
            if entry.endswith("png"):
                if not entry.startswith("_"): # on a export of images from a photon file, the preview image starts with _
                    files.append(fullpath)
        files.sort()

        print("Following files will be inserted:")
        for fullpath in files:
            print("  ", fullpath)

        # Check if there are files available and if so check first file for correct dimensions
        if len(files) == 0: raise Exception("No files of type png are found!")
        rawData = PhotonFile.encodedBitmap_Bytes(files[0])

        # Remove old data in PhotonFile object
        nLayers = len(files)
        self.Header[self.nrLayersString] = self.int_to_bytes(nLayers)
        #oldLayerDef = self.LayerDefs[0]
        self.LayerDefs = [dict() for x in range(nLayers)]
        self.LayerData = [dict() for x in range(nLayers)]

        # Depending on nr of new images, set nr of bottom layers and total layers in Header
        #   If only one image is supplied the file should be set as 0 base layers and 1 normal layer
        if nLayers == 1:
            self.Header["# Bottom Layers"] = self.int_to_bytes(0)
        #   We can't have more bottom layers than total nr of layers
        nrBottomLayers=self.bytes_to_int(self.Header["# Bottom Layers"])
        if nrBottomLayers>nLayers: nrBottomLayers=nLayers-1
        self.Header["# Bottom Layers"] = self.int_to_bytes(nrBottomLayers)
        #   Set total number of layers
        self.Header["# Layers"] = self.int_to_bytes(nLayers)

        # Calculate the start position of raw imagedata of the FIRST layer
        rawDataStartPos = 0
        for bTitle, bNr, bType, bEditable,bHint in self.pfStruct_Header:
            rawDataStartPos = rawDataStartPos + bNr
        for previewNr in (0,1):
            for bTitle, bNr, bType, bEditable, bHint in self.pfStruct_Previews:
                if bTitle == "Image Data": bNr = dataSize
                rawDataStartPos = rawDataStartPos + bNr
                if bTitle == "Data Length": dataSize = PhotonFile.bytes_to_int(self.Previews[previewNr][bTitle])
        for bTitle, bNr, bType, bEditable, bHint in self.pfStruct_LayerDef:
            rawDataStartPos = rawDataStartPos + bNr * nLayers

        # For each image file, get encoded raw image data and store in Photon File object, copying layer settings from Header/General settings.
        curLayerHeight=0.0
        deltaLayerHeight=self.bytes_to_float(self.Header["Layer height (mm)"])
        print("Processing:")
        for layerNr, file in enumerate(files):
            print("  ", layerNr,"/",nLayers, file)
            # Get encoded raw data
            rawData = PhotonFile.encodedBitmap_Bytes(file)
            rawDataTrunc = rawData[:-1]
            rawDataLastByte = rawData[-1:]

            # Update layer settings (LayerDef)
            # todo: following should be better coded
            self.LayerDefs[layerNr]["Layer height (mm)"] = self.float_to_bytes(curLayerHeight)
            if layerNr<nrBottomLayers:
                self.LayerDefs[layerNr]["Exp. time (s)"] = self.Header["Exp. bottom (s)"]
            else:
                self.LayerDefs[layerNr]["Exp. time (s)"] = self.Header["Exp. time (s)"]
            self.LayerDefs[layerNr]["Off time (s)"] = self.Header["Off time (s)"]
            self.LayerDefs[layerNr]["Image Address"] = self.int_to_bytes(rawDataStartPos)
            self.LayerDefs[layerNr]["Data Length"] = self.int_to_bytes(len(rawData))
            self.LayerDefs[layerNr]["padding"] = self.hex_to_bytes("00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00") # 4 *4bytes

            # Store raw image data (LayerData)
            self.LayerData[layerNr]["Raw"] = rawDataTrunc
            self.LayerData[layerNr]["EndOfLayer"] = rawDataLastByte

            # Keep track of address of raw imagedata and current height of 3d model to use in next layer
            print ("Layer, DataPos, DataLength ",layerNr,rawDataStartPos,len(rawData))
            rawDataStartPos = rawDataStartPos + len(rawData)
            curLayerHeight= curLayerHeight+deltaLayerHeight
            print("                New DataPos", rawDataStartPos)


    def exportBitmaps(self,dirPath,filepre):
        """ Save all images in PhotonFile object as (decoded) png files in specified directory and with file precursor"""

        # Traverse all layers
        for layerNr in range(0,self.nrLayers()):
            # Make filename
            nrStr="%04d" % layerNr
            filename=filepre+"_"+ nrStr+".png"
            #print ("filename: ",filename)
            fullfilename=os.path.join(dirPath,filename)
            # Retrieve decode pygame image surface
            imgSurf=self.getBitmap(layerNr, (255, 255, 255), (0, 0, 0), (1, 1))
            # Save layer image to disk
            pygame.image.save(imgSurf,fullfilename)

        # Also save 1st preview image
        prevSurf=self.getPreviewBitmap(0)
        #   Make filename beginning with _ so PhotonFile.importBitmaps will skip this on import layer images.
        barefilename = (os.path.basename(self.filename))
        barefilename=barefilename.split(sep=".")[0]
        filename = "_"+barefilename + "_preview.png"
        fullfilename = os.path.join(dirPath, filename)
        #   Save preview image to disk
        pygame.image.save(prevSurf, fullfilename)

        return




########################################################################################################################
## Testing
########################################################################################################################

'''
   def float_to_bytes_old(self,floatVal):
        #http: //www.simplymodbus.ca/ieeefloats.xls
        #todo: remove binary string steps
        sign     =-1 if floatVal<0  else 1
        firstBit = 0 if sign==1     else 1
        exponent=-127 if abs(floatVal)<1.1754943E-38 else floor(log(abs(floatVal),10)/log(2,10))
        print ("abs          ", abs(floatVal))
        print ("logabs       ", log(abs(floatVal),10))
        print ("log2         ", log(2,10))
        print ("logabs/log2= ", log(abs(floatVal),10)/log(2,10))
        print ("int        = ", floor(log(abs(floatVal),10)/log(2,10)))
        exponent127=exponent+127
        next8Bits=format(exponent127,'#010b')
        mantissa=floatVal/pow(2,exponent)/sign
        substract=mantissa-1
        multiply=round(substract*8388608)
        div256_1=multiply/256
        divint_1=int(div256_1)
        rem_1=int((div256_1-divint_1)*256)
        div256_2=divint_1/256
        divint_2=int(div256_2)
        rem_2=int((div256_2-divint_2)*256)

        print (sign,firstBit,exponent,exponent127)
        print (next8Bits,mantissa,substract,multiply)
        print (div256_1,divint_1,rem_1)
        print (div256_2, divint_2, rem_2)

        bin1=str(firstBit)+next8Bits[2:9]
        bin2_=format(divint_2,'#010b')[-7:]#last 7 bits
        bin2=next8Bits[-1:]+bin2_
        bin3=format(rem_2,'#010b')[-8:]
        bin4=format(rem_1,'#010b')[-8:]
        bin1234=bin4+bin3+bin2+bin1

        #print(bin4, bin3, bin2, bin1)
        return int(bin1234, 2).to_bytes(len(bin1234) // 8, byteorder='big')
'''


def testDataConversions():
    print("Testing Data Type Conversions")
    print("-----------")
    floatVal = 9999.9999563227
    print("float:", floatVal)
    bytes = (PhotonFile.float_to_bytes(floatVal))
    print("raw bytes: ", bytes, len(bytes))
    hexs = ' '.join(format(h, '02X') for h in bytes)
    print("bytes in hex:", hexs)
    f = PhotonFile.bytes_to_float(bytes)
    print("want :", floatVal)
    print("float:", f)
    if not floatVal == 0: print("diff :", 100 * (floatVal - f) / floatVal, "%")
    quit()
    print("-----------")
    intVal = 313
    print("int:", intVal)
    bytes = (PhotonFile.int_to_bytes(intVal))
    print("raw bytes: ", bytes)
    hexs = ' '.join(format(h, '02X') for h in bytes)
    print("bytes in hex:", hexs)
    i = PhotonFile.bytes_to_int(bytes)
    print("int:", i)
    print("-----------")
    hexStr = '00 A1 7D DF'
    print("hex:", hexStr)
    bytes = (PhotonFile.hex_to_bytes(hexStr))
    print("raw bytes: ", bytes)
    h = PhotonFile.bytes_to_hex(bytes)
    print("hex:", h)
    print("-----------")
    quit()


# testDataConversions()
#c=0.0000001
'''
c=0.44999998807907104 #0.4999999888241291 > 0.25
for i in range (0,20):
    bA=PhotonFile.float_to_bytes(c)
    bHA=PhotonFile.bytes_to_hex(bA)
    bB=PhotonFile.bytes_to_float(bA)
    print (i,bA,bHA, bB)
    c = c + 0.05
#quit()
'''
'''
files=("SamplePhotonFiles/Debug/debug 0.05mm (err).photon",
        "SamplePhotonFiles/Debug/debug 0.07mm (err).photon",
        "SamplePhotonFiles/Debug/debug 0.08mm (err).photon",
        "SamplePhotonFiles/Debug/debug 0.09mm (err).photon",
        "SamplePhotonFiles/Debug/debug 0.10mm.photon",
        "SamplePhotonFiles/Debug/debug 0.11mm.photon",
        "SamplePhotonFiles/Debug/debug 0.12mm.photon",
        "SamplePhotonFiles/Debug/debug 0.13mm.photon",
        "SamplePhotonFiles/Debug/debug 0.14mm.photon",
        "SamplePhotonFiles/Debug/debug 0.15mm (err).photon",
        "SamplePhotonFiles/Debug/debug 0.20mm.photon",
        "SamplePhotonFiles/Debug/debug 0.25mm.photon",
        "SamplePhotonFiles/Debug/debug 0.30mm.photon",
        "SamplePhotonFiles/Debug/debug 0.35mm.photon",
        "SamplePhotonFiles/Debug/debug 0.40mm.photon",
        "SamplePhotonFiles/Debug/debug 0.45mm.photon",
        "SamplePhotonFiles/Debug/debug 0.50mm.photon",
        "SamplePhotonFiles/Debug/debug 0.55mm (err).photon",
        "SamplePhotonFiles/Debug/debug 0.60mm.photon",
        "SamplePhotonFiles/Debug/debug 0.65mm.photon",
        "SamplePhotonFiles/Debug/debug 0.70mm.photon",
        "SamplePhotonFiles/Debug/debug 0.75mm.photon",
        "SamplePhotonFiles/Debug/debug 0.80mm.photon",
       )
'''
'''
files=("SamplePhotonFiles/Debug/debug 0.65mm test.photon",)
for file in files:
    ph=PhotonFile(file)
    ph.readFile()
    print ( file[30:34],':',
            PhotonFile.bytes_to_int(ph.Header["# Layers"]),
            PhotonFile.bytes_to_int(ph.Header["Preview 0 (addr)"]),
            PhotonFile.bytes_to_int(ph.Header["Preview 1 (addr)"]),
            PhotonFile.bytes_to_int(ph.Previews[0]["Image Address"]),
            PhotonFile.bytes_to_int(ph.Previews[0]["Data Length"]),
            PhotonFile.bytes_to_int(ph.Previews[1]["Image Address"]),
            PhotonFile.bytes_to_int(ph.Previews[1]["Data Length"]),
            PhotonFile.bytes_to_int(ph.Header["Layer Defs (addr)"]),
            )
'''

"""
("Header", 8, tpByte, False),
("Bed X (mm)", 4, tpFloat, True),
("Bed Y (mm)", 4, tpFloat, True),
("Bed Z (mm)", 4, tpFloat, True),
("padding0", 3 * 4, tpByte, False),  # 3 ints
("Layer height (mm)", 4, tpFloat, True),
("Exp. time (s)", 4, tpFloat, True),
("Exp. bottom (s)", 4, tpFloat, True),
("Off time (s)", 4, tpFloat, True),
("# Bottom Layers", 4, tpInt, True),
("Resolution X", 4, tpInt, True),
("Resolution Y", 4, tpInt, True),
("Preview 0 (addr)", 4, tpInt, False),  # start of preview 0
("Layer Defs (addr)", 4, tpInt, False),  # start of layerDefs
(nrLayersString, 4, tpInt, False),
("Preview 1 (addr)", 4, tpInt, False),  # start of preview 1
("unknown6", 4, tpInt, False),
("Proj.type-Cast/Mirror", 4, tpInt, False),  # LightCuring/Projection type // (1=LCD_X_MIRROR, 0=CAST)
("padding1", 6 * 4, tpByte, False)  # 6 ints
]

pfStruct_Previews = [
("Resolution X", 4, tpInt, False),
("Resolution Y", 4, tpInt, False),
("Image Address", 4, tpInt, False),  # start of rawData0
("Data Length", 4, tpInt, False),  # size of rawData0
("padding", 4 * 4, tpByte, False),  # 4 ints
("Image Data", -1, tpByte, False),
]

pfStruct_LayerDef = [
("Layer height (mm)", 4, tpFloat, True),
("Exp. time (s)", 4, tpFloat, True),
("Off time (s)", 4, tpFloat, True),
("Image Address", 4, tpInt, False),  # dataStartPos -> Image Address
("Data Length", 4, tpInt, False),  # size of rawData+lastByte(1)
("padding", 4 * 4, tpByte, False)  # 4 ints
"""

#quit()