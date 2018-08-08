"""
This Voxel class is a prove of concept. The speed of python is probably to slow to
make this class a competitor to plugins written in java(script)

Voxel class:
- Load a photonfile to a (scaled down) voxel model
- Crop model
- Save/Load as voxel file
- Erode voxel model
- Overlay grid on model
- Cut model away from photonfile (hollowAndFillPhotonFile)
"""

#todo: make a 1 voxel wide shell of voxelmodel so we can display this with OpenGL engine
#todo: a boolean array can be packed binary (packbits)and thus save file could be 8x smaller
#todo: improve infill patterns

import numpy
import scipy.ndimage
import scipy.interpolate
import cv2
import time
import json
from PhotonFile import *

# try; https://twistedpairdevelopment.wordpress.com/2011/06/09/creating-voxel-volumes-quicky-in-python/

def rebin(a, shape):
    """ Scales down an image array by averages blocks of pixels to new pixel value
        https://stackoverflow.com/questions/8090229/resize-with-averaging-or-rebin-a-numpy-2d-array
    """
    sh = shape[0],a.shape[0]//shape[0],shape[1],a.shape[1]//shape[1]
    return a.reshape(sh).mean(-1).mean(1)

class Voxels():
    voxels=None
    bboxMin=[0,0,0]
    bboxMax=None
    bboxSize=None
    uncroppedSize=None
    photonfile=None
    scalefactor=0

    def saveLayer(self,layerNr,filename):
        img=self.voxels[layerNr].astype(int)*255
        cv2.imwrite(filename, img)

    def saveLayerVoxels(self,layerVoxels,filename):
        img=layerVoxels.astype(int)*255
        cv2.imwrite(filename, img)

    def saveVoxels(self,filename):
        tstart=time.time()
        metadata={
            "shape": str(self.voxels.shape),
            "bboxMin":str(self.bboxMin),
            "bboxMax": str(self.bboxMax),
            "bboxSize": str(self.bboxSize),
            "uncroppedSize": str(self.uncroppedSize),
        }
        with open(filename,mode='w+b') as file:
            jsondata=json.dumps(metadata,indent=2)
            print ("jsondata",jsondata)
            ba=int.to_bytes(len(jsondata),length=2,byteorder='big')
            # Write length of json data using 2 bytes
            file.write(ba)
            # Seperate with 0
            file.write(b'\0')
            # Write json data
            file.write(jsondata.encode('ascii'))
            # Seperate with 0
            file.write(b'\0')
            # Write voxeldata
            file.write(self.voxels.tostring())
            #self.voxels.tofile(file)

        print ("elapsed",time.time()-tstart)

    def loadVoxels(self,filename):
        tstart=time.time()
        with open(filename,mode='rb') as file:
            b12=file.read(2)
            lenMD=int.from_bytes(b12,byteorder='big')
            file.read(1) # read seperator
            metadata=file.read(lenMD).decode('ascii')
            file.read(1)  # read seperator
            #self.voxels=numpy.fromfile(file,dtype=numpy.bool)
            print (lenMD,metadata)
            js=json.loads(str(metadata))
            shape = tuple(map(int, js["shape"][1:-1].split(',')))
            self.bboxMin  = tuple(map(int, js["bboxMin"][1:-1].split(',')))
            self.bboxMax  = tuple(map(int, js["bboxMax"][1:-1].split(',')))
            self.bboxSize = tuple(map(int, js["bboxSize"][1:-1].split(',')))
            print (shape,self.bboxMin,self.bboxMax,self.bboxSize)
            self.voxels=numpy.fromstring(file.read(),dtype=numpy.bool)
            self.voxels.reshape(shape)
        print ("elapsed",time.time()-tstart)

    def __init__(self, photonfile=None, reducef=1):
        """
        """
        # Check if user wants clean/empty Voxel instance
        if photonfile==None: return

        # Load photonfile if we got a filename
        if isinstance(photonfile, str):
            photonfile = PhotonFile(photonfile)
            photonfile.readFile()
        self.photonfile=photonfile

        self.scalefactor=reducef
        nLayers = photonfile.nrLayers()
        print ("nLayers",nLayers)

        newshape2D = (2560//reducef,1440//reducef)
        newshape3D = (nLayers//reducef+1, newshape2D[0],newshape2D[1])
        self.voxels = numpy.zeros(newshape3D, dtype=numpy.bool)

        # Read each layer and rescale
        for intLayerNr in range(0,nLayers,reducef):
            # print (arr.shape)
            # rescale
            # print ("newshape",newshape)
            subvoxels = numpy.zeros(newshape2D, dtype=numpy.int)
            for subLayerNr in range (reducef):
                # Build layernr
                layerNr=intLayerNr+subLayerNr
                # get (unscaled) layer array
                if layerNr<(nLayers-1):
                    arr = photonfile.getBitmap_withnumpy(layerNr, (0, 0, 255, 0), (0,0, 0, 0), (1,1), True)
                    arr_scaled = rebin(arr, (newshape2D))

                else:
                    arr_scaled=numpy.zeros(newshape2D, dtype=numpy.int)
                subvoxels = subvoxels+arr_scaled/reducef
                print ("IN layerNr",layerNr)
                #print (arr_scaled[764//4:788//4,720//4])
                #print (subvoxels[764 // 4:788 // 4, 720 // 4])

            boolsubvoxels = (subvoxels > 128).astype(numpy.bool)
            print("OUT layerNr", intLayerNr//reducef)
            self.voxels[intLayerNr//reducef]=boolsubvoxels

        # Store boundingbox
        self.uncroppedSize = [nLayers // reducef, 2560 // reducef, 1440 // reducef]
        self.bboxMin=[0,0,0]
        self.bboxMax=[nLayers//reducef,2560//reducef,1440//reducef]
        self.bboxSize=[nLayers//reducef,2560//reducef,1440//reducef]
        self.findBoundBox()
        self.cropVoxels()

        #layerimg=voxels[40].astype(int)
        #layerimg=layerimg*255
        #cv2.imwrite("slicer/filled/test.png", layerimg )
        nbytes=self.voxels.nbytes
        if nbytes<1024:
            print ("Mem (B)", nbytes)
        elif nbytes<(1024*1024):
            print("Mem (KB)", '%.2f' % (nbytes/(1024)))
        elif nbytes<(1024*1024*1024):
            print("Mem (MB)", '%.2f' % (nbytes /(1024*1024)))
        else:
            print("Mem (GB)", '%.2f' % (nbytes/(1024*1024*1024)))
        print ("Min,Max,Size",self.bboxMin,self.bboxMax,self.bboxSize)
        print ("Shape",self.voxels.shape)
        print("Nr elements:", self.voxels.sum())
        #print (voxels)

    def findBoundBox(self):
        """returns boundbox coord and size
           https://stackoverflow.com/questions/31400769/bounding-box-of-numpy-array
        """
        r = numpy.any(self.voxels, axis=(1, 2))
        c = numpy.any(self.voxels, axis=(0, 2))
        z = numpy.any(self.voxels, axis=(0, 1))

        rmin, rmax = numpy.where(r)[0][[0, -1]]
        cmin, cmax = numpy.where(c)[0][[0, -1]]
        zmin, zmax = numpy.where(z)[0][[0, -1]]

        self.bboxMin =(rmin,cmin,zmin)
        self.bboxMax =(rmax,cmax,zmax)
        self.bboxSize=(rmax-rmin+1,cmax-cmin+1,zmax-zmin+1)

    def cropVoxels(self):
        """ Crops the voxel model to minimize memory storage."""
        cropped = self.voxels[self.bboxMin[0]:self.bboxMax[0]+1,
                              self.bboxMin[1]:self.bboxMax[1]+1,
                              self.bboxMin[2]:self.bboxMax[2]+1]
        print ("Nr elements in Cropped:",cropped.sum())
        self.voxels=cropped

    def padVoxels(self):
        """ Restores voxel model to state before cropVoxels.
            !!! NEEDS FURTHER TESTING !!!
        """
        rowPad = (self.bboxMin[1], self.uncroppedSize[1] - self.bboxMax[1] - 1)
        colPad = (self.bboxMin[2], self.uncroppedSize[2] - self.bboxMax[2] - 1)
        self.voxels = numpy.pad(self.voxels, [rowPad, colPad], 'constant')

    def erode(self,nrCyles=10):
        """ Eats outer voxels so the model can serves to cut out the inner part of the source and hollow a photon file.
        """
        # https://stackoverflow.com/questions/51695747/numpy-3d-voxels-erosion
        # https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.ndimage.morphology.binary_erosion.html
        # pixel = 0.047mm => 10 cycles is 0.47mm
        startTime = time.time()
        self.voxels=scipy.ndimage.morphology.binary_erosion(self.voxels, structure=None, iterations=1, mask=None, output=None, border_value=0, origin=0, brute_force=False).astype(self.voxels.dtype)
        for i in range(0,nrCyles-1):
            self.voxels = scipy.ndimage.morphology.binary_erosion(self.voxels, structure=None, iterations=1, mask=None,
                                                                 output=None, border_value=0, origin=0,
                                                                 brute_force=False).astype(self.voxels.dtype)

        endTime=time.time()
        deltaTime=endTime-startTime
        #print (new_voxels)
        print ("time",deltaTime)
        print ("Nr elements",self.voxels.sum())
        #for layerNr in range(self.voxels.shape[0]):
        #    self.saveLayer(layerNr, "slicer/filled/origi" + str(layerNr) + ".png")
            #self.saveLayerVoxels(self.voxels[layerNr],"slicer/filled/erode"+str(layerNr)+".png")

    def overlayPattern(self,pattern):
        """ Overlays black pattern (like a grid)on eroded voxels to remove voxels.
        The resulting pattern can be used as a mask to hollow voxel object but leave a inner pattern (grid)
        """
        vshape=self.voxels.shape
        pshape=pattern.shape
        print ("p,v",pshape,vshape)
        nrs=(vshape[0],1+vshape[1]//pshape[0],1+vshape[2]//pshape[1])
        print ("Nrs",nrs)
        grid=numpy.tile(pattern,nrs)
        grid=grid[0:vshape[0],0:vshape[1],0:vshape[2]]
        print ("Shapes", self.voxels.shape,grid.shape)
        self.voxels=numpy.logical_and(self.voxels,grid)

    def makeGridPattern(self,size=10,thickness=1):
        grid = numpy.ones(shape=[size,size],dtype=numpy.uint8)
        black=(0,0,0)
        cv2.line(grid, (size // 2,0), (size // 2,size-1), black, thickness)
        cv2.line(grid, (0,size // 2), (size-1,size // 2), black, thickness)
        #print (grid)
        grid=grid.astype(numpy.bool)
        return grid

    def makeHexPattern(self,size=10,thickness=1):
        sqrt3=math.sqrt(3)
        # hex points
        p0 = (int(0      *size)  , int(0.25*size)*1+1)
        p1 = (int(sqrt3/4*size)*1, int(0.25*size)*0+1)
        p2 = (int(sqrt3/4*size)*2, int(0.25*size)*1+1)
        p3 = (int(sqrt3/4*size)*2, int(0.25*size)*3+1)
        p4 = (int(sqrt3/4*size)*1, int(0.25*size)*4+1)
        p5 = (int(0      *size)  , int(0.25*size)*3+1)
        # line to bottom
        p6 = (int(sqrt3/4*size)*1, int(0.25*size)*6+1)
        grid = numpy.ones(shape=[int(0.25*size)*6+1,int(sqrt3/4*size)*2+1,],dtype=numpy.uint8)
        black=(0,0,0)
        cv2.line(grid, p0, p1, black, thickness)
        cv2.line(grid, p1, p2, black, thickness)
        cv2.line(grid, p2, p3, black, thickness)
        cv2.line(grid, p3, p4, black, thickness)
        cv2.line(grid, p4, p5, black, thickness)
        cv2.line(grid, p5, p0, black, thickness)
        cv2.line(grid, p4, p6, black, thickness)
        #print (grid)
        grid=grid.astype(numpy.bool)
        #cv2.imwrite("slicer/filled/hexgrid.png", grid.astype(numpy.int) * 255)
        return grid

    def cutFromFile(self,doLayerNr=-1):
        nLayers = self.photonfile.nrLayers()
        print("nLayers", nLayers)
        print("reducef",self.scalefactor)
        tstart = time.time()
        for layerNr in range(nLayers):
            if doLayerNr==-1 or doLayerNr==layerNr:
                print ("Hollow layerNr",layerNr)
                arr = self.photonfile.getBitmap_withnumpy(layerNr, (0, 0, 255, 0), (0, 0, 0, 0), (1, 1), True)
                modelvoxels = (arr > 128).astype(numpy.bool)
                #retrieve correct layer
                vLayerNr=layerNr//self.scalefactor
                if vLayerNr>=self.voxels.shape[0]: vLayerNr=self.voxels.shape[0]-1
                hollowvoxels= self.voxels[vLayerNr]
                #pad layer with zeros
                rowPad=(self.bboxMin[1],self.uncroppedSize[1]-self.bboxMax[1]-1)
                colPad=(self.bboxMin[2],self.uncroppedSize[2]-self.bboxMax[2]-1)
                paddedvoxels=numpy.pad(hollowvoxels,[rowPad,colPad],'constant')
                #rescale layer
                greyvoxels=paddedvoxels.astype(dtype=numpy.int)*255
                rescaledVoxelsGrey = scipy.misc.imresize(greyvoxels, (2560,1440),interp='bilinear')
                #rescaledVoxelsGrey = scipy.ndimage.zoom(greyvoxels, self.scalefactor)
                #rescaledVoxelsGrey = cv2.resize(greyvoxels, (2560, 1440))

                rescaledVoxelsBool = numpy.where(rescaledVoxelsGrey>128,True,False)

                #cv2.imwrite("slicer/filled/1model.png",   modelvoxels.astype(numpy.int) * 255)
                #cv2.imwrite("slicer/filled/2maskpre.png", hollowvoxels.astype(numpy.int) * 255)
                #cv2.imwrite("slicer/filled/3padded.png", paddedvoxels.astype(numpy.int) * 255)
                #cv2.imwrite("slicer/filled/4grey.png", greyvoxels.astype(numpy.int) * 255)
                #cv2.imwrite("slicer/filled/5rescaledG.png", rescaledVoxelsGrey.astype(numpy.int)*255 )
                #cv2.imwrite("slicer/filled/6rescaledB.png",rescaledVoxelsBool.astype(numpy.int)*255 )

                img=numpy.logical_xor(modelvoxels,rescaledVoxelsBool)
                cv2.imwrite("slicer/result"+str(layerNr)+".png", img.astype(numpy.int) * 255)
        print("elapsed",time.time()-tstart)


    def hollowAndFillPhotonFile(photonfile,wallthickness=1,pattern='grid',patternsize=3, patternthickness=2):
        """ Hollow a photonfile, fills it with a pattern and saves slices to 'slicer' dir
            wallthickness in mm
        """

        # Convert wallthickness and patternsize to pixels
        wallthickness=wallthickness/0.047
        patternsize=patternsize/0.047
        patternthickness=patternthickness/0.047

        # Apply scale to wallthickness and patternsize
        scale=4
        wallthickness = int(wallthickness / scale)
        patternsize = int(patternsize / scale)
        patternthickness = int(patternthickness / scale)
        if wallthickness<1: wallthickness=1
        if patternsize<1: patternsize=1
        if patternthickness<1: patternthickness=1

        print ("wallthickness (scaled px)", wallthickness)
        print ("patternsize   (scaled px)", patternsize)
        print ("patternthickness (scaled px)", patternthickness)

        # Construct scaled down voxel model /cut model (inner core which is to be cut from photonfile)
        vx = Voxels(photonfile, scale)

        # Erode model to create inner model to cut away
        vx.erode(wallthickness)

        if pattern=='grid':
            pat=vx.makeGridPattern(size=patternsize, thickness=patternthickness)
        elif pattern=='hex':
            pat = vx.makeHexPattern(size=patternsize, thickness=patternthickness)

        # Overlay pattern on cutmodel
        vx.overlayPattern(pat)

        # Cut voxel model from each layer in file
        vx.cutFromFile(doLayerNr=-1)

        return vx


    def encodedRLE(self):
        """ Converts voxel data to RLE encoded byte string.
            Based on https://gist.github.com/itdaniher/3f57be9f95fce8daaa5a56e44dd13de5
            Encoding scheme:
                Highest bit of each byte is color (black or white)
                Lowest 7 bits of each byte is repetition of that color, with max of 125 / 0x7D
        """

        tstart=time.time()

        # Flatten array
        shape = self.voxels.shape
        x = self.voxels.flatten()
        print ("flatten",x.shape)

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
            color = (abs(col)>1)
            while nr > 0x7D:
                encValue = (color << 7) | 0x7D
                rleData.append(encValue)
                nr = nr - 0x7D
            encValue = (color << 7) | nr
            rleData.append(encValue)


        # Restore shape of voxels
        x.reshape(shape)

        print ("elapsed",time.time()-tstart)

        # Needed is an byte string, so convert
        return bytes(rleData)

"""
#vx=Voxels(None,2)
#pat=vx.makeHexPattern(10,2)
#quit()

photonfile=PhotonFile("SamplePhotonFiles/Smilie.photon")
#photonfile=PhotonFile("SamplePhotonFiles/3DBenchy.photon")
#photonfile=PhotonFile("SamplePhotonFiles/bunny.photon")
photonfile.readFile()
Voxels.hollowAndFillPhotonFile(photonfile,0.1,'grid',3,0.1)
#Voxels.hollowAndFillPhotonFile("SamplePhotonFiles/Smilie.photon",0.1,'grid',3,0.1)
quit()

# TEST EROSION AND INFILL
#vx=Voxels(photonfile,4)
#print (vx.encodedRLE())
#vx.erode(4)
#pat=vx.makeGridPattern(10,2)
pat=vx.makeHexPattern(size=20,thickness=2)
vx.overlayPattern(pat)
vx.cutFromFile(doLayerNr=-1)
quit()

# TEST READ/WRITE SPEED SINGLE VOXEL FILE
vx=Voxels(photonfile,2)
vx.saveVoxels("slicer/filled/voxels.dat")
#vx=Voxels()
vx.loadVoxels("slicer/filled/voxels.dat")
#print (vx.voxels.shape)
quit()
"""
