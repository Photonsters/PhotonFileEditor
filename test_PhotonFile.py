from PhotonFile import *

#TODO: repace all the prints with proper assertions
class TestPhotonFile:
    # testDataConversions()
    def test_ImageReplacement(self):
        PhotonFile.encodedBitmap_Bytes(os.path.join("tests","test0.bmp"))
        photonfile = PhotonFile(os.path.join("SamplePhotonFiles","3DBenchy.photon"))
        photonfile.readFile()
        photonfile.replaceBitmaps(os.path.join("tests"))

    # testImageReplacement()
    def test_Rle(self):
        rle=Rle(os.path.join("resources","arrow-down.png"))
        rleData=bytearray()
        for (nr,col) in rle:
            color=0
            if col>1:color=1
            while nr>0x7D:
                encValue = (color << 7) | 0x7D
                rleData.append(encValue)
                nr=nr-0x7D
            encValue = (color << 7) | color
            rleData.append(encValue)
        print (len(rleData))

    def test_Rld(self):
        nr=numpy.array((3,5,2,6,1),numpy.uint8)
        val=numpy.array((0,1,0,1,0),numpy.uint8)
        print(nr.size, nr)
        print (val.size,val)
        #rleseq = numpy.ravel(numpy.column_stack((nr, val)))
        rleseq=numpy.column_stack((nr,val))
        #rleseq = numpy.empty((nr.size , val.size,), dtype=numpy.uint8)
        print (rleseq)

        #rleseq2 = [(3, 0), (5, 1), (2, 0), (6, 1), (1, 0)]
        #rleseq2=numpy.array(rleseq2,dtype=numpy.uint8)
        #print("rleseq2: ",rleseq2)
        runs=numpy.asarray (rleseq)
        print (runs)
        ret=rld(runs)
        print (ret)

    def test_DataConversions(self):
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
        print("diff :", 100 * (floatVal - f) / floatVal, "%")
        assert not floatVal == 0
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