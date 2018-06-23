import pygame
from pygame.locals import *
import math
from math import *
import os

try:
    import numpy
    numpyAvailable = True
except ImportError:
    numpyAvailable = False

test=True

########################################################################################################################
## PhotonFile class
## - reads file
## - draws layer
########################################################################################################################
def hexStr(bytes):
    if isinstance(bytes, bytearray):
        return ' '.join(format(h, '02X') for h in bytes)
    if isinstance(bytes, int):
        return format(bytes, '02X')
    return ("No Byte (Array)")


class PhotonFile:
    isDrawing = False

    tpByte = 0
    tpChar = 1
    tpInt = 2
    tpFloat = 3

    nrLayersString = "# Layers"

    # each item in dictionary has format "Title", nr bytes to read/write, type of data stored, editable


    pfStruct_Header = [
        ("Header", 8, tpByte, False),
        ("Bed X (mm)", 4, tpFloat, True),
        ("Bed Y (mm)", 4, tpFloat, True),
        ("Bed Z (mm)", 4, tpFloat, True),
        ("padding0", 3 * 4, tpByte, False), # 3 ints
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
        ("Proj.type-Cast/Mirror", 4, tpInt, False),   #LightCuring/Projection type // (1=LCD_X_MIRROR, 0=CAST)
        ("padding1", 6 * 4, tpByte, False)  # 6 ints
    ]

    # In specific, the prev1StartPos and prev2StartPos fields are offsets to structs describing the preview image data
    # that gets displayed on the printer.
    # The color of a pixel is 2 bytes (little endian) with each bit like this: RRRRR GGGGG X BBBBB
    # If the X bit is set, then the next 2 bytes (little endian) masked with 0xFFF represents how many more times to repeat that pixel.

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
        ("Image Address", 4, tpInt, False),#dataStartPos -> Image Address
        ("Data Length", 4, tpInt, False), #rawDataSize -> Data Length
        ("padding", 4 * 4, tpByte, False) # 4 ints
    ]

    # pfLayerDataDef =
    #    rawData  - rle encoded bytes except last one
    #    lastByte - last byte of encoded bitmap data

    Header = {}
    Previews = [{},{}]
    LayerDefs = []
    LayerData = []

    @staticmethod
    def bytes_to_int(bytes):
        result = 0
        for b in reversed(bytes):
            result = result * 256 + int(b)
        return result

    @staticmethod
    def bytes_to_float(inbytes):
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
        return ' '.join(format(h, '02X') for h in bytes)

    @staticmethod
    def hex_to_bytes(hexStr):
        return bytearray.fromhex(hexStr)

    # handles only positive ints
    @staticmethod
    def int_to_bytes(intVal):
        return intVal.to_bytes(4, byteorder='little')

    # handles only positive floats
    @staticmethod
    def float_to_bytes(floatVal):
        if floatVal == 0: return (0).to_bytes(4, byteorder='big')

        # http: //www.simplymodbus.ca/ieeefloats.xls
        # todo: remove binary string steps
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

        '''
        print (sign,firstBit,exponent,exponent127)
        print (next8Bits,mantissa,substract,multiply)
        print (div256_1,divint_1,rem_1)
        print (div256_2, divint_2, rem_2)
        print ("")
        print ("BIN1-------")
        print ("expon: ", bin(exponent127),bin((exponent127 & 0b11111110)>>1))
        print ("first: ",bin(firstBit<<7))
        print ("resul: ",bin((exponent127 & 0b11111110)>>1 | firstBit<<7))
        print ("BIN2-------")
        print ("next8: ", bin(exponent127), bin((exponent127 & 0b00000001)<<7))
        print ("divi2: ", bin(divint_2) )
        print ("resul: ", bin((exponent127 & 0b00000001)<<7 | divint_2))
        print("BIN3-------")
        print("resul: ", bin(rem_2))
        print("BIN4-------")
        print("resul: ", bin(rem_1))
        print("EIND-------")
        '''
        bin1 = (exponent127 & 0b11111110) >> 1 | firstBit << 7
        bin2 = (exponent127 & 0b00000001) << 7 | divint_2
        bin3 = rem_2
        bin4 = rem_1
        # print ("ALT: ",bin(bin1_new), bin(bin2_new),bin(bin3_new),bin(bin4_new))
        bin1234 = bin1 | bin2 << 8 | bin3 << 16 | bin4 << 24
        return bin1234.to_bytes(4, byteorder='big')

    @staticmethod
    def convBytes(bytes, bType):
        nr = None
        if bType == PhotonFile.tpInt:
            nr = PhotonFile.bytes_to_int(bytes)
        if bType == PhotonFile.tpFloat:
            nr = PhotonFile.bytes_to_float(bytes)
        if bType == PhotonFile.tpByte:
            nr = PhotonFile.bytes_to_hex(bytes)
        return nr

    def __init__(self, photonfilename):
        self.filename = photonfilename

    def nrLayers(self):
        return  PhotonFile.bytes_to_int(self.Header[self.nrLayersString])

    def readFile(self):
        with open(self.filename, "rb") as binary_file:
            # Start at beginning
            binary_file.seek(0)

            # HEADER
            for bTitle, bNr, bType, bEditable in self.pfStruct_Header:
                self.Header[bTitle] = binary_file.read(bNr)

            # PREVIEWS
            for previewNr in (0,1):
                for bTitle, bNr, bType, bEditable in self.pfStruct_Previews:
                    # if rawData0 or rawData1 the number bytes to read is given bij dataSize0 and dataSize1
                    if bTitle == "Image Data": bNr = dataSize
                    self.Previews[previewNr][bTitle] = binary_file.read(bNr)
                    if bTitle == "Data Length": dataSize = PhotonFile.bytes_to_int(self.Previews[previewNr][bTitle])

            # LAYERDEFS
            nLayers = PhotonFile.bytes_to_int(self.Header[self.nrLayersString])
            self.LayerDefs = [dict() for x in range(nLayers)]
            # print("nLayers:", nLayers)
            # print("  hex:", ' '.join(format(x, '02X') for x in self.Header[self.nrLayersString]))
            # print("  dec:", nLayers)
            # print("Reading layer meta-info")
            for lNr in range(0, nLayers):
                # print("  layer: ", lNr)
                for bTitle, bNr, bType, bEditable in self.pfStruct_LayerDef:
                    self.LayerDefs[lNr][bTitle] = binary_file.read(bNr)

            # LAYERRAWDATA
            # print("Reading layer image-info")
            self.LayerData = [dict() for x in range(nLayers)]
            for lNr in range(0, nLayers):
                rawDataSize = PhotonFile.bytes_to_int(self.LayerDefs[lNr]["Data Length"])
                # print("  layer: ", lNr, " size: ",rawDataSize)
                self.LayerData[lNr]["Raw"] = binary_file.read(rawDataSize - 1) # b'}}}}}}}}}}
                # -1 because we don count byte for endOfLayer
                self.LayerData[lNr]["EndOfLayer"] = binary_file.read(1)

            # print (' '.join(format(x, '02X') for x in header))


    def encodedBitmap_Bytes_withnumpy(filename):
        #https://gist.github.com/itdaniher/3f57be9f95fce8daaa5a56e44dd13de5
        imgsurf = pygame.image.load(filename)
        (width, height) = imgsurf.get_size()
        if not (width, height) == (1440, 2560):
            raise Exception("Your image dimensions are off and should be 1440x2560")

        imgarr = pygame.surfarray.array2d(imgsurf)
        imgarr = numpy.rot90(imgarr,axes=(1,0))
        imgarr = numpy.fliplr(imgarr)  # reverse/mirror array
        x = numpy.asarray(imgarr).flatten(0)

        where = numpy.flatnonzero
        x = numpy.asarray(x)
        n = len(x)
        if n == 0:
            return numpy.array([], dtype=numpy.int)
        starts = numpy.r_[0, where(~numpy.isclose(x[1:], x[:-1], equal_nan=True)) + 1]
        lengths = numpy.diff(numpy.r_[starts, n])
        values = x[starts]
        #ret=np.dstack((lengths, values))[0]

        rleData = bytearray()
        for (nr, col) in zip(lengths,values):
            color = (col>0)
            while nr > 0x7D:
                encValue = (color << 7) | 0x7D
                rleData.append(encValue)
                nr = nr - 0x7D
            encValue = (color << 7) | nr
            rleData.append(encValue)
        return bytes(rleData)

    def encodedBitmap_Bytes_nonumpy(filename):
        imgsurf = pygame.image.load(filename)
        #bitDepth = imgsurf.get_bitsize()
        #bytePerPixel = imgsurf.get_bytesize()
        (width, height) = imgsurf.get_size()
        if not (width, height) == (1440,2560):
            raise Exception("Your image dimensions are off and should be 1440x2560")

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
                    encValue = (prevColor << 7) | nrOfColor
                    rleData.append(encValue)
                    prevColor = color
                    nrOfColor = 1
        return bytes(rleData)

    def encodedBitmap_Bytes(filename):
        if numpyAvailable:
            return PhotonFile.encodedBitmap_Bytes_withnumpy(filename)
        else:
            return PhotonFile.encodedBitmap_Bytes_nonumpy(filename)


    def replaceBitmap(self, layerNr,filePath):
        print("  ", layerNr, "/", filePath)

        # get/encode raw data
        rawData = PhotonFile.encodedBitmap_Bytes(filePath)
        #print ("rawData Len",len(rawData))
        rawDataTrunc = rawData[:-1]
        rawDataLastByte = rawData[-1:]

        # get change in image rawData size
        oldLength=self.bytes_to_int(self.LayerDefs[layerNr]["Data Length"])
        newLength=len(rawData)
        deltaLength=newLength-oldLength
        #print ("old, new, delta:",oldLength,newLength,deltaLength)
        # update LayerDef
        self.LayerDefs[layerNr]["Data Length"] = self.int_to_bytes(len(rawData))
        # update LayerData
        self.LayerData[layerNr]["Raw"] = rawDataTrunc
        self.LayerData[layerNr]["EndOfLayer"] = rawDataLastByte

        # update startposition of RawData of all following images
        nLayers=self.nrLayers()
        for rLayerNr in range(layerNr+1,nLayers):
            curAddr=self.bytes_to_int(self.LayerDefs[rLayerNr]["Image Address"])
            newAddr=curAddr+deltaLength
            #print ("layer, cur, new: ",rLayerNr,curAddr,newAddr)
            self.LayerDefs[rLayerNr]["Image Address"]= self.int_to_bytes(newAddr)

    def replaceBitmaps(self, dirPath):
        # get all png-files and sort them alphabetically
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

        # Check if files available and if so check first file for correct dimensions
        if len(files) == 0: raise Exception("No files of type png are found!")
        rawData = PhotonFile.encodedBitmap_Bytes(files[0])

        # remove old data
        nLayers = len(files)
        self.Header[self.nrLayersString] = self.int_to_bytes(nLayers)
        #oldLayerDef = self.LayerDefs[0]
        self.LayerDefs = [dict() for x in range(nLayers)]
        self.LayerData = [dict() for x in range(nLayers)]

        #set nr of bottom layers and total layers in Header
        #   If only one image is supplied the file should be set as 0 base layers and 1 normal layer
        if nLayers == 1:
            self.Header["# Bottom Layers"] = self.int_to_bytes(0)
        #   We can't have more bottom layers than total nr of layers
        nrBottomLayers=self.bytes_to_int(self.Header["# Bottom Layers"])
        if nrBottomLayers>nLayers: nrBottomLayers=nLayers-1
        self.Header["# Bottom Layers"] = self.int_to_bytes(nrBottomLayers)
        #   set total number of layers
        self.Header["# Layers"] = self.int_to_bytes(nLayers)

        # calc start position of rawData
        rawDataStartPos = 0
        for bTitle, bNr, bType, bEditable in self.pfStruct_Header:
            rawDataStartPos = rawDataStartPos + bNr
        for previewNr in (0,1):
            for bTitle, bNr, bType, bEditable in self.pfStruct_Previews:
                if bTitle == "Image Data": bNr = dataSize
                rawDataStartPos = rawDataStartPos + bNr
                if bTitle == "Data Length": dataSize = PhotonFile.bytes_to_int(self.Previews[previewNr][bTitle])
        for bTitle, bNr, bType, bEditable in self.pfStruct_LayerDef:
            rawDataStartPos = rawDataStartPos + bNr * nLayers


        # add all files
        curLayerHeight=0.0
        deltaLayerHeight=self.bytes_to_float(self.Header["Layer height (mm)"])
        print("Processing:")
        for layerNr, file in enumerate(files):
            print("  ", layerNr,"/",nLayers, file)
            # get raw data
            rawData = PhotonFile.encodedBitmap_Bytes(file)
            rawDataTrunc = rawData[:-1]
            rawDataLastByte = rawData[-1:]

            # update LayerDef
            #todo: following should be better coded
            self.LayerDefs[layerNr]["Layer height (mm)"] = self.float_to_bytes(curLayerHeight)
            if layerNr<nrBottomLayers:
                self.LayerDefs[layerNr]["Exp. time (s)"] = self.Header["Exp. bottom (s)"]
            else:
                self.LayerDefs[layerNr]["Exp. time (s)"] = self.Header["Exp. time (s)"]
            self.LayerDefs[layerNr]["Off time (s)"] = self.Header["Off time (s)"]
            self.LayerDefs[layerNr]["Image Address"] = self.int_to_bytes(rawDataStartPos)
            self.LayerDefs[layerNr]["Data Length"] = self.int_to_bytes(len(rawData))
            self.LayerDefs[layerNr]["padding"] = self.hex_to_bytes("00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00") # 4 *4bytes
            # update LayerData
            self.LayerData[layerNr]["Raw"] = rawDataTrunc
            self.LayerData[layerNr]["EndOfLayer"] = rawDataLastByte
            # update startRawData
            print ("Layer, DataPos, DataLength ",layerNr,rawDataStartPos,len(rawData))
            rawDataStartPos = rawDataStartPos + len(rawData)
            curLayerHeight= curLayerHeight+deltaLayerHeight
            print("                New DataPos", rawDataStartPos)

    def getBitmap_withnumpy(self, layerNr, forecolor=(128,255,128), backcolor=(0,0,0),scale=(0.25,0.25)):
        """ Decodes a RLE byte array from PhotonFile object to a pygame surface

        :param layerNr:
        :param forecolor:
        :param backcolor:
        :param scale:
        :return:
        """
        #https://gist.github.com/itdaniher/3f57be9f95fce8daaa5a56e44dd13de5
        memory = pygame.Surface((int(1440 * scale[0]), int(2560 * scale[1])))
        if self.nrLayers()==0: return memory #could occur if loading new file
        self.isDrawing = True

        bA = self.LayerData[layerNr]["Raw"]
        # add endOfLayer Byte
        bA = bA + self.LayerData[layerNr]["EndOfLayer"]

        #bN = numpy.asarray(bA,dtype=numpy.uint8)
        bN =numpy.fromstring(bA,dtype=numpy.uint8)


        #extract color value (highest bit) and nr of repetitions (lowest 7 bits)
        valbin = bN >> 7  # only read 1st bit
        nr = bN & ~(1 << 7)  # turn highest bit of
        #replace 0's en 1's with correct colors
        forecolor_int = (forecolor[0] << 16) + (forecolor[1] << 8) + forecolor[2]
        backcolor_int = backcolor[0] << 16 + backcolor[1] << 8 + backcolor[2]
        val = numpy.array([{0: backcolor_int, 1: forecolor_int}[x] for x in valbin])

        #make a 2d array like [ [3,0] [2,1]...]
        runs = numpy.column_stack((nr, val))

        # make array like [(0,4), (1,5), (0,3), (1,126]
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

        #make sure we have a bitmap of the correct size
        if not len(x) == 3686400: print ("Warning: The file decoded with less bytes than needed. Will pad the file with zero bytes.")
        while not len(x)==3686400:
            x=numpy.append(x,(1,))

        rgb2d=x.reshape((2560,1440))
        #rgb2d= numpy.rot90(rgb2d)
        rgb2d = numpy.rot90(rgb2d, axes=(1, 0))
        rgb2d = numpy.fliplr(rgb2d)  # reverse/mirror array
        picture=pygame.surfarray.make_surface(rgb2d)
        memory=pygame.transform.scale(picture, (int(1440*scale[0]), int(2560*scale[1])))

        self.isDrawing = False
        return memory


    def getBitmap_nonumpy(self, layerNr, forecolor=(128,255,128), backcolor=(0,0,0),scale=(0.25,0.25)):
        # debug layerNr=PhotonFile.bytes_to_int(self.Header[self.nrLayersString])-1
        memory = pygame.Surface((int(1440 * scale[0]), int(2560 * scale[1])))
        if self.nrLayers()==0: return memory #could occur if loading new file
        self.isDrawing = True

        bA = self.LayerData[layerNr]["Raw"]
        # add endOfLayer Byte
        bA = bA + self.LayerData[layerNr]["EndOfLayer"]

        # Seek position and read N bytes
        x = 0
        y = 0
        for idx, b in enumerate(bA):
            #highest bit(7) is color, lower bits (0-6) are repeat nr
            nr = b & ~(1 << 7)  # turn highest bit of
            val = b >> 7  # only read 1st bit

            x1 = int(x *scale[0])
            y1 = int(y *scale[1])
            x2 = int((x + nr) *scale[0])
            y2 = y1
            if val==0:
                col= backcolor
            else:
                col=forecolor
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
        self.isDrawing = False
        return memory

    def getBitmap(self, layerNr, forecolor=(128, 255, 128), backcolor=(0, 0, 0), scale=(0.25, 0.25)):
        if numpyAvailable:
            return self.getBitmap_withnumpy(layerNr,forecolor,backcolor,scale)
        else:
            return self.getBitmap_nonumpy(layerNr,forecolor,backcolor,scale)


    def exportBitmaps(self,dirPath,filepre):
        for layerNr in range(0,self.nrLayers()):
            nrStr="%04d" % layerNr
            filename=filepre+"_"+ nrStr+".png"
            #print ("filename: ",filename)
            fullfilename=os.path.join(dirPath,filename)
            imgSurf=self.getBitmap(layerNr, (255, 255, 255), (0, 0, 0), (1, 1))
            pygame.image.save(imgSurf,fullfilename)

        prevSurf=self.getPreviewBitmap(0)
        filename = "_"+filepre + "_preview.png"
        # print ("filename: ",filename)
        fullfilename = os.path.join(dirPath, filename)
        pygame.image.save(prevSurf, fullfilename)

        return

    def writeFile(self, newfilename=None):
        if newfilename == None: newfilename = self.filename
        with open(newfilename, "wb") as binary_file:
            # Start at beginning
            binary_file.seek(0)

            # HEADER
            for bTitle, bNr, bType, bEditable in self.pfStruct_Header:
                binary_file.write(self.Header[bTitle])

            # PREVIEWS
            for previewNr in (0, 1):
                for bTitle, bNr, bType, bEditable in self.pfStruct_Previews:
                    #print ("Save: ",bTitle)
                    binary_file.write(self.Previews[previewNr][bTitle])

            # LAYERDEFS
            nLayers = PhotonFile.bytes_to_int(self.Header[self.nrLayersString])
            for lNr in range(0, nLayers):
                #print("  layer: ", lNr)
                #print("    def: ", self.LayerDefs[lNr])
                for bTitle, bNr, bType, bEditable in self.pfStruct_LayerDef:
                    binary_file.write(self.LayerDefs[lNr][bTitle])

            # LAYERRAWDATA
            # print("Reading layer image-info")
            for lNr in range(0, nLayers):
                binary_file.write(self.LayerData[lNr]["Raw"])
                binary_file.write(self.LayerData[lNr]["EndOfLayer"])

    def getPreviewBitmap(self, prevNr):
            #https://github.com/Reonarudo/pcb2photon/issues/2

            self.isDrawing = True
            w = PhotonFile.bytes_to_int(self.Previews[prevNr]["Resolution X"])
            h = PhotonFile.bytes_to_int(self.Previews[prevNr]["Resolution Y"])
            s = PhotonFile.bytes_to_int(self.Previews[prevNr]["Data Length"])
            scale = ((1440/4)/w, (1440/4)/w)
            memory = pygame.Surface((int(w), int(h)))
            if w==0 or h==0: return memory
            bA = self.Previews[prevNr]["Image Data"]

            # Seek position and read N bytes
            idx=0
            pixelIdx = 0
            while idx<len(bA):
                # The color of a pixel is 2 bytes (little endian) with each bit like this: RRRRR GGG GG X BBBBB
                b12 = bA[idx+1]<<8 | bA[idx+0]
                idx += 2
                red  =math.floor(((b12>>11) & 0x1F) / 31*255)
                green=math.floor(((b12>> 6) & 0x1F) / 31*255)
                blue= math.floor(((b12>> 0) & 0x1F) / 31*255)
                col = (red, green, blue)

                #red   =  b1>>3
                #green = (b1 & 0b00000111) <<2 | (b2 & 0b11000000)>>6
                #blue  =  b2 & 0b00011111

                #isRep = (b2 & 0b00100000) >> 5


                # If the X bit is set, then the next 2 bytes (little endian) masked with 0xFFF represents how many more times to repeat that pixel.
                nr=1
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

                
        
            #print("Screen Drawn")
            # debug print ("layer: ", layerNr)
            # debug print ("lastByte:", self.LayerData[layerNr]["EndOfLayer"])

            # Scale the surface to the wanted resolution
            memory = pygame.transform.scale(memory, (int(w*scale[0]), int(h*scale[1])))

            self.isDrawing = False
            return memory


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


