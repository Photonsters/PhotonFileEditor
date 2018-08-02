from OGLEngine import *
from STLFile import *
from Helpers3D import *

from functools import partial
from concurrent.futures import ProcessPoolExecutor

"""
Bepaal van ieder punt de normaal als gemiddelde van de driehoeken waarvan de punt deel uitmaakt.

Gebruik deze normalen om iedere driehoek de gewenste wanddikte naar binnen de extruden. De max. wanddikte wordt bepaald door:
-      Of ze convergeren en de driehoeksnormaal draait om
-      Of 1 van de drie hoekpunten snijdt het vlak van een andere driehoek binnen de drie punten
Dit genereert een nieuwe driehoek die samen met de basisdriehoek een prisma vormt. 
Sla de basisdriekhoek en de nieuwe driehoek op in een nieuwe class prism

Bepaal van iedere driehoek de doorsnedes met ieder xz-vlak op laagste hoogte y tot en hoogste hoogte y en een interval gelijk aan de laagdikte van de 3d printer
Dit kunnen vierhoeken of driehoeken zijn. Sla deze doorsnedes als puntenverzamelingen op in de class instamce prism.

Maak nu iedere slice door alle prisms af te gaan en met de puntenverzamelingen van dezelfde hoogte als de slice een 2d driehoek of vierhoek te tekenen in de bitmap.

Ter controle kunnen alle bitmaps geladen worden in een voxelviewer


"""


########################################################################################################################
## Class Slicer
########################################################################################################################

class Slicer:
    stl=None

    def __init__(self,oglengine,filename=None):
        cloud=[Point3D((0,0,0)),Point3D((0,0,3)),Point3D((0,3,0))]
        p0=0
        p1=1
        p2=2
        tri=Triangle3D(cloud,p0,p1,p2)
        print ("norm",tri.normal)
        origin=Point3D((4,0,0))
        dir=Vector((-0.2,13,-40))
        line3d=Line3D(origin,dir)
        plane = Plane3D.fromTriangle(tri)
        d = line3d.planeDistance(plane)
        print (d)
        #quit()

        aGL = oglengine
        stl=self.stl
        stl=STLFile()
        if filename==None:
            #stl.load_binary_stl('resources/SliceTester.stl', 1)
            #filename='SamplePhotonFiles/HollowCube.stl'
            #filename = 'SamplePhotonFiles/Cube.stl'
            filename = 'SamplePhotonFiles/STLs/bunny.stl'
            #stl.load_binary_stl('resources/HollowCube.stl', 1)
            # self.load_stl('resources/Door-handle-ascii.stl',0.03)
            # self.load_stl('resources/Door-handle.stl', 0.03)
            # self.load_binary_stl('resources/3DBenchy.stl', 1)
            # self.load_binary_stl('resources/test_cube.stl', 1)

            # self.load_binary_stl('resources/OrientationCube.stl',1)
            # self.load_text_stl('resources/test.stl', 0.03)
            # self.load_binary_+-stl('resources/knight.stl', 0.3)

        print ("load...")
        stl.load_binary_stl(filename, 0.4)

        print ("setModel...")
        aGL.setModel(stl.points, stl.model)

        self.stl=stl
        print ("done...")

    def hollow(self, wallthickness=5):
        #stl.createInnerWall(wallthickness)
        None

    def slice_seq(self):
        # Clear slice directory
        dir = os.path.join(os.getcwd(), "slicer")

        filelist = [f for f in os.listdir(dir) if f.endswith(".png")]
        for f in filelist:
            os.remove(os.path.join(dir, f))

        # Fill slice directory
        stl=self.stl

        print ("Start slice")
        modelBottomHeight=0
        modelTopHeight=10
        sliceHeight=1

        sliceNr=0
        sliceBottom=0
        t1=pygame.time.get_ticks()
        for height in range(modelBottomHeight,modelTopHeight,sliceHeight):
            sliceTop=sliceBottom+sliceHeight
            nrStr = "%04d" % sliceNr
            filename=os.path.join(os.getcwd(),"slicer/slice__"+nrStr+".png")
            print ("-----------")
            print ("Slice: ",sliceNr," from-to: ",sliceBottom,sliceTop," save as:",filename)
            points,slice=stl.takeSlice(sliceBottom,sliceTop)
            #25325 for slice2bmp_pil (pill fill)
            #63831 for slice2bmp_native (python fill)
            #12233 for slice2bmp_ocv (cv2 fill)
            stl.slice2bmp_ocv(points, slice, filename)
            sliceNr+=1
            sliceBottom+=sliceHeight

        dt = pygame.time.get_ticks()-t1
        print ("Elapsed:",dt)



        #aGL.setModel(stl.points,stl.model)
        #aGL.setInnerWallModel(stl.innerpoints)
        #aGL.setModel(points, slice)



        print("-0-------")

        print (List2Str(stl.points))
        #print ("-0-------")
        #print (List2Str(stl.innerpoints))


    def test(self,nr):
        print (nr)

    def slicefillLayer(self,sliceNr,sliceBottom,sliceTop):
        nrStr = "%04d" % sliceNr
        filename = os.path.join(os.getcwd(), "slicer/slice__" + nrStr + ".png")
        #print("-----------")
        #print("Slice: ", sliceNr, " from-to: ", sliceBottom, sliceTop, " save as:", filename)
        stl=self.stl
        points, slice = stl.takeSlice(sliceBottom, sliceTop)
        # If above model we don't have anything to return
        if len(points)==0: return False
        stl.slice2bmp_ocv(points, slice, filename)
        return True

    def slice(self,sliceHeight=0.1):
        # Clear slice directory
        dir = os.path.join(os.getcwd(), "slicer")

        filelist = [f for f in os.listdir(dir) if f.endswith(".png")]
        for f in filelist:
            os.remove(os.path.join(dir, f))

        # Fill slice directory
        stl=self.stl

        sliceNr=0
        sliceBottom=0
        executor=ProcessPoolExecutor()
        res=[]
        topReached=False
        while not topReached:
            sliceTop=sliceBottom+sliceHeight
            nrStr = "%04d" % sliceNr
            filename=os.path.join(os.getcwd(),"slicer/slice__"+nrStr+".png")
            print ("-----------")
            print ("Slice: ",sliceNr," from-to: ",str(int(sliceBottom*1000))+"um",str(int(sliceTop*1000))+"um", "save as:",filename)
            points,slice=stl.takeSlice(sliceBottom,sliceTop)
            ret=executor.submit(self.slicefillLayer, sliceNr=sliceNr, sliceBottom=sliceBottom, sliceTop=sliceTop)
            # Check if we get return False and thus an empty image (top of model reached)
            if ret.result()==False:topReached=True
            res.append(ret.result())
            sliceNr+=1
            sliceBottom+=sliceHeight

        print ("Results", res)

        #aGL.setModel(stl.points,stl.model)
        #aGL.setInnerWallModel(stl.innerpoints)
        #aGL.setModel(points, slice)
        #print("-0-------")
        #print (List2Str(stl.points))
        #print ("-0-------")
        #print (List2Str(stl.innerpoints))


