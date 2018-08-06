"""
Workflow:
- erode model
- cut away pattern from model (e.g. grid(
- cut away eroded&patternen model from original image leaving hollowed model with infill
"""

import numpy
import scipy.ndimage
import cv2
import time
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
    offset=[0,0,0]

    def saveLayer(self,layerNr,filename):
        img=self.voxels[layerNr].astype(int)*255
        cv2.imwrite(filename, img)

    def saveLayerVoxels(self,layerVoxels,filename):
        img=layerVoxels.astype(int)*255
        cv2.imwrite(filename, img)


    def __init__(self, photonfile,reducef):
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

            boolsubvoxels = (subvoxels > 128).astype(bool)
            print("OUT layerNr", intLayerNr//reducef)
            self.voxels[intLayerNr//reducef]=boolsubvoxels

        # Store boundingbox
        self.findBoundBox()
        self.cropVoxels()

        #layerimg=voxels[40].astype(int)
        #layerimg=layerimg*255
        #cv2.imwrite("slicer/filled/test.png", layerimg )
        nbytes=self.voxels.nbytes
        if nbytes<1024:
            print ("Mem (B)", nbytes)
        elif nbytes<(1024*1024):
            print("Mem (KB)", int(round(nbytes/(1024))))
        else:
            print("Mem (GB)", int(round(nbytes/(1024*1024))))
        print ("Min,Max,Size",self.bboxMin,self.bboxMax,self.bboxSize)

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
        self.bboxSize=(rmax-rmin,cmax-cmin,zmax-zmin)
        self.offset=self.bboxMin

    def cropVoxels(self):
        cropped = self.voxels[self.bboxMin[0]:self.bboxMax[0]+1,
                              self.bboxMin[1]:self.bboxMax[1]+1,
                              self.bboxMin[2]:self.bboxMax[2]+1]
        print ("Nr elements in Cropped:",cropped.sum())
        self.voxels=cropped

    def padVoxels(self):
        None

    def erode(self,nrCyles=10):
        """ Serves as a mask to hollow a voxel object.
        """
        # https://stackoverflow.com/questions/51695747/numpy-3d-voxels-erosion
        # https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.ndimage.morphology.binary_erosion.html
        # pixel = 0.047mm => 10 cycles is 0.47mm
        startTime = time.time()
        new_voxels=scipy.ndimage.morphology.binary_erosion(self.voxels, structure=None, iterations=1, mask=None, output=None, border_value=0, origin=0, brute_force=False).astype(self.voxels.dtype)
        for i in range(0,nrCyles-1):
            new_voxels = scipy.ndimage.morphology.binary_erosion(new_voxels, structure=None, iterations=1, mask=None,
                                                                 output=None, border_value=0, origin=0,
                                                                 brute_force=False).astype(self.voxels.dtype)

        endTime=time.time()
        deltaTime=endTime-startTime
        #print (new_voxels)
        print ("time",deltaTime)
        print ("Nr elements",new_voxels.sum())
        for layerNr in range(new_voxels.shape[0]):
            self.saveLayer(layerNr, "slicer/filled/origi" + str(layerNr) + ".png")
            self.saveLayerVoxels(new_voxels[layerNr],"slicer/filled/erode"+str(layerNr)+".png")
        return (new_voxels)

    def overlayPattern(self,pattern):
        """ Overlays black pattern (like a grid)on eroded voxels to remove voxels.
        The resulting pattern can be used as a mask to hollow voxel object but leave a inner pattern (grid)
        """

        vshape=self.voxels.shape
        pshape=pattern.shape
        nrs=(1,1+vshape[1]//pshape[0],1+vshape[2]//pshape[1])
        grid=numpy.tile(pattern,nrs)
        grid=grid[0:vshape[0],0:vshape[1],0:vshape[2]]
        overlayed=self.voxels and grid
        return overlayed

    def makeGridPattern(size):
        grid = numpy.zeros(shape=[size,size],dtype=bool)
        for row in range(size):
            grid[row,size//2]=True
        for col in range(size):
            grid[size//2,col]=True
        return grid

"""
#photonfile=PhotonFile("SamplePhotonFiles/Smilie.photon")
#photonfile=PhotonFile("SamplePhotonFiles/3DBenchy.photon")
photonfile=PhotonFile("SamplePhotonFiles/bunny.photon")
photonfile.readFile()
vx=Voxels(photonfile,4)
#vx.croppedVoxels()
#c,b=vx.findBoundBox()

#arr=numpy.arange(0,27).reshape((3,3,3))
#print (arr)
#print (arr.mean((0,1))
#arrn=rebin(arr,(1,1,3))
#print (arrn)

eroded=vx.erode()
grid=Voxels.makeGridPattern(7)
vx.overlayPattern(grid)
quit()
"""
