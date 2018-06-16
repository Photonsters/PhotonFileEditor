import pygame
from pygame.locals import *
import math
from math import *

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

    #each item in dictionary has format "Title", nr bytes to read/write, type of data stored, editable

    pfStruct_Header = [
        ("unknown0", 8,tpByte,False),
        ("sizeX", 4,tpFloat,True),
        ("sizeY", 4,tpFloat,True),
        ("sizeZ", 4,tpFloat,True),
        ("padding0", 3 * 4,tpInt,False),
        ("layerThickness", 4,tpFloat,True),
        ("normalExposure", 4,tpFloat,True),
        ("bottomExposure", 4,tpFloat,True),
        ("offTime", 4,tpFloat,True),
        ("nBottomLayers", 4,tpInt,True),
        ("resolutionX", 4,tpInt,True),
        ("resolutionY", 4,tpInt,True),
        ("unknown3", 4,tpInt,False),
        ("unknown4", 4,tpInt,False),
        ("nLayers", 4,tpInt,True),
        ("unknown5", 4,tpInt,False),
        ("unknown6", 4,tpInt,False),
        ("unknown7", 4,tpInt,False),
        ("padding1", 6 * 4,tpInt,False)
    ]

    pfStruct_Common = [
        ("unknown8", 4,tpInt,False),
        ("unknown9", 4,tpInt,False),
        ("dataStartPos0", 4,tpInt,False),
        ("dataSize0", 4,tpInt,False),
        ("padding0", 4 * 4,tpInt,False),
        ("c0", -1,tpByte,False),
        ("unknown14", 4,tpInt,False),
        ("unknown15", 4,tpInt,False),
        ("dataStartPos1", 4,tpInt,False),
        ("dataSize1", 4,tpInt,False),
        ("padding1", 4 * 4,tpInt,False),
        ("c1", -1,tpByte,False),
    ]

    pfStruct_LayerDef = [
        ("layerHeight", 4,tpFloat,True),
        ("bottomExposureTime", 4,tpFloat,True),
        ("offTime", 4,tpFloat,True),
        ("dataStartPos", 4,tpInt,False),
        ("rawDataSize", 4,tpInt,False),
        ("padding", 4 * 4,tpInt,False)
    ]

    Header = {}
    Common = {}
    LayerDefs = []
    LayerData = []

    def bytes_to_int(bytes):
        result = 0
        for b in reversed(bytes):
            result = result * 256 + int(b)
        return result

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

    def bytes_to_hex(bytes):
        return ' '.join(format(h, '02X') for h in bytes)

    def hex_to_bytes(hexStr):
        return  bytearray.fromhex(hexStr)

    #handles only positive ints
    def int_to_bytes(intVal):
        return intVal.to_bytes(4, byteorder='little')

    # handles only positive floats
    def float_to_bytes(floatVal):
        if floatVal==0: return (0).to_bytes(4, byteorder='big')

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
        bin1=(exponent127 & 0b11111110)>>1 | firstBit<<7
        bin2=(exponent127 & 0b00000001)<<7 | divint_2
        bin3=rem_2
        bin4=rem_1
        #print ("ALT: ",bin(bin1_new), bin(bin2_new),bin(bin3_new),bin(bin4_new))
        bin1234=bin1 | bin2<<8 | bin3<<16 | bin4<<24
        return bin1234.to_bytes(4, byteorder='big')

    def convBytes(bytes,bType):
        nr=None
        if bType==PhotonFile.tpInt:
            nr=PhotonFile.bytes_to_int(bytes)
        if bType == PhotonFile.tpFloat:
            nr = PhotonFile.bytes_to_float(bytes)
        if bType == PhotonFile.tpByte:
            nr = PhotonFile.bytes_to_hex(bytes)
        return nr


    def __init__(self, photonfilename, pyscreen):
        self.filename = photonfilename
        self.pyscreen = pyscreen

    def readFile(self):
        with open(self.filename, "rb") as binary_file:
            # Start at beginning
            binary_file.seek(0)

            # HEADER
            for bTitle, bNr, bType,bEditable in self.pfStruct_Header:
                self.Header[bTitle] = binary_file.read(bNr)

            # COMMON
            for bTitle, bNr,bType,bEditable in self.pfStruct_Common:
                # if C0 or C1 the number bytes to read is given bij dataSize0 and dataSize1
                if bTitle == "c0":bNr = dataSize0
                if bTitle == "c1": bNr = dataSize1
                self.Common[bTitle] = binary_file.read(bNr)
                if bTitle == "dataSize0":dataSize0 = PhotonFile.bytes_to_int(self.Common[bTitle])
                if bTitle == "dataSize1": dataSize1 = PhotonFile.bytes_to_int(self.Common[bTitle])

            # LAYERDEFS
            nLayers = PhotonFile.bytes_to_int(self.Header["nLayers"])
            self.LayerDefs =[dict() for x in range(nLayers)]
            #print("nLayers:", nLayers)
            #print("  hex:", ' '.join(format(x, '02X') for x in self.Header["nLayers"]))
            #print("  dec:", nLayers)
            #print("Reading layer meta-info")
            for lNr in range(0, nLayers):
                #print("  layer: ", lNr)
                for bTitle, bNr,bType,bEditable in self.pfStruct_LayerDef:
                    self.LayerDefs[lNr][bTitle] = binary_file.read(bNr)

            # LAYERRAWDATA
            #print("Reading layer image-info")
            self.LayerData = [dict() for x in range(nLayers)]
            for lNr in range(0, nLayers):
                rawDataSize = PhotonFile.bytes_to_int(self.LayerDefs[lNr]["rawDataSize"])
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
            for bTitle, bNr, bType,bEditable in self.pfStruct_Header:
                binary_file.write(self.Header[bTitle])

            # COMMON
            for bTitle, bNr,bType,bEditable in self.pfStruct_Common:
                binary_file.write(self.Common[bTitle])

            # LAYERDEFS
            nLayers = PhotonFile.bytes_to_int(self.Header["nLayers"])
            for lNr in range(0, nLayers):
                print("  layer: ", lNr)
                print("    def: ", self.LayerDefs[lNr])
                for bTitle, bNr,bType,bEditable in self.pfStruct_LayerDef:
                    binary_file.write(self.LayerDefs[lNr][bTitle])

            # LAYERRAWDATA
            #print("Reading layer image-info")
            for lNr in range(0, nLayers):
                binary_file.write(self.LayerData[lNr]["Raw"])
                binary_file.write(self.LayerData[lNr]["EndOfLayer"])

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
    floatVal=9999.9999563227
    print ("float:",floatVal)
    bytes = (PhotonFile.float_to_bytes(floatVal))
    print("raw bytes: ", bytes, len(bytes))
    hexs = ' '.join(format(h, '02X') for h in bytes)
    print("bytes in hex:", hexs)
    f = PhotonFile.bytes_to_float(bytes)
    print("want :", floatVal)
    print("float:", f)
    if not floatVal==0:print("diff :", 100*(floatVal-f)/floatVal,"%")
    quit()
    print("-----------")
    intVal=313
    print ("int:",intVal)
    bytes = (PhotonFile.int_to_bytes(intVal))
    print("raw bytes: ", bytes)
    hexs = ' '.join(format(h, '02X') for h in bytes)
    print("bytes in hex:", hexs)
    i = PhotonFile.bytes_to_int(bytes)
    print("int:", i)
    print("-----------")
    hexStr='00 A1 7D DF'
    print ("hex:",hexStr)
    bytes = (PhotonFile.hex_to_bytes(hexStr))
    print("raw bytes: ", bytes)
    h = PhotonFile.bytes_to_hex(bytes)
    print("hex:", h)
    print("-----------")
    quit()
#testDataConversions()
#quit()

