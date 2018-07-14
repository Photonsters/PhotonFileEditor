from OGLEngine import *
from STLFile import *
from Helpers3D import *


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
            filename='SamplePhotonFiles/STLs/test_cube.stl'
            #stl.load_binary_stl('resources/HollowCube.stl', 1)
            # self.load_stl('resources/Door-handle-ascii.stl',0.03)
            # self.load_stl('resources/Door-handle.stl', 0.03)
            # self.load_binary_stl('resources/3DBenchy.stl', 1)
            # self.load_binary_stl('resources/test_cube.stl', 1)

            # self.load_binary_stl('resources/OrientationCube.stl',1)
            # self.load_text_stl('resources/test.stl', 0.03)
            # self.load_binary_+-stl('resources/knight.stl', 0.3)

        print ("load...")
        stl.load_binary_stl(filename, 1)

        print ("setModel...")
        aGL.setModel(stl.points, stl.model)

        #print ("calc normals...")
        stl.calcPointNormals() # needed to stl.createInnerWall
        #return

        self.stl=stl
        print ("done...")

    def hollow(self, wallthickness=5):
        #stl.createInnerWall(wallthickness)
        None

    def slice(self):
        #clear slice directory
        path = os.path.join(os.getcwd(), "slicer"


        stl=self.stl

        print ("Start slice")
        modelBottomHeight=0
        modelTopHeight=20
        sliceHeight=3

        sliceNr=0
        sliceBottom=0
        for height in range(modelBottomHeight,modelTopHeight,sliceHeight):
            sliceTop=sliceBottom+sliceHeight
            nrStr = "%04d" % sliceNr
            filename=os.path.join(os.getcwd(),"slicer/slice__"+nrStr+".png")
            print ("Slice: ",sliceNr," from-to: ",sliceBottom,sliceTop," save as:",filename)
            points,slice=stl.takeSlice(sliceBottom,sliceTop)
            stl.slice2bmp(points, slice, filename)
            sliceNr+=1
            sliceBottom+=sliceHeight

        #aGL.setModel(stl.points,stl.model)
        #aGL.setInnerWallModel(stl.innerpoints)
        #aGL.setModel(points, slice)



        print("-0-------")

        print (List2Str(stl.points))
        #print ("-0-------")
        #print (List2Str(stl.innerpoints))





