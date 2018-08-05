import numpy
import scipy.ndimage
import time
# try; https://twistedpairdevelopment.wordpress.com/2011/06/09/creating-voxel-volumes-quicky-in-python/
class Voxels():
    voxels=None

    def init(self):
        None
        # Make array of 20 layers, width 20 and height 20
        voxels=numpy.zeros((4,8,8),dtype=numpy.int)
        for layerNr in range (1,3):
            for x in range (1,7):
                for y in range (1,7):
                    voxels[layerNr,x,y]=True

        #print (voxels.nbytes)
        #print (voxels)

#bool    :  3276800
#None/int: 26214400
    def findBoundBox(self):
        """returns boundbox coord and size"""
        boundbox=self.new_voxels.shape
        coord=[0,0,0]
        return (coord,boundbox)

    def erode(self):
        # https://stackoverflow.com/questions/51695747/numpy-3d-voxels-erosion
        # https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.ndimage.morphology.binary_erosion.html
        w,h,l=2560,1280,5
        #  5 layers: 0.44 sec
        # 10 layers: 2.15 sec
        self.voxels = numpy.zeros((w,h,l), dtype=numpy.int)
        self.voxels[1:w-1, 1:h-1,1:l-1] = 1
        print (self.voxels)
        print ("-----")
        startTime = time.time()
        new_voxels=scipy.ndimage.morphology.binary_erosion(self.voxels, structure=None, iterations=1, mask=None, output=None, border_value=0, origin=0, brute_force=False).astype(self.voxels.dtype)
        endTime=time.time()
        deltaTime=endTime-startTime
        print (new_voxels)
        print ("time",deltaTime)
        return (new_voxels)


"""
vx=Voxels()
vx.init()
c,b=vx.findBoundBox()

vx.erode()
quit()
"""