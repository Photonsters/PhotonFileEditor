from OGLEngine import *
from STLFile import *
from Helpers3D import *

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
import time

class Slicer:
    stl=None
    oglengine=None

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
        self.oglengine=oglengine
        stl=self.stl
        stl=STLFile()
        if filename==None:
            #stl.load_binary_stl('resources/SliceTester.stl', 1)
            #filename='SamplePhotonFiles/HollowCube.stl'
            #filename = 'SamplePhotonFiles/Cube.stl'
            #filename = 'SamplePhotonFiles/STLs/bunny.stl'
            #filename = 'SamplePhotonFiles/STLs/smilie.stl'

            #stl.load_binary_stl('resources/HollowCube.stl', 1)
            # self.load_stl('resources/Door-handle-ascii.stl',0.03)
            # self.load_stl('resources/Door-handle.stl', 0.03)
            # self.load_binary_stl('resources/3DBenchy.stl', 1)
            # self.load_binary_stl('resources/test_cube.stl', 1)

            # self.load_binary_stl('resources/OrientationCube.stl',1)
            # self.load_text_stl('resources/test.stl', 0.03)
            # self.load_binary_+-stl('resources/knight.stl', 0.3)
            None

        if not filename==None:
            print ("load...")
            arrpoints,arrnormals=stl.load_stl(filename, 0.4)

            print ("setModel...")
            aGL.setModel(stl.points, stl.triangles,arrpoints,arrnormals)

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

    def slicefillLayer(self,sliceNr,sliceBottom,sliceTop,filename=None):
        """ Retrieves a filled slice from the stl model and save it to single images or photonfile instance.
        """

        # Get slice
        stl=self.stl
        points, slice = stl.takeSlice(sliceBottom, sliceTop)
        imgarrRGB = stl.slice2bmp_ocv(points, slice, filename)

        # Convert slice to 1 color component (keep white and red)
        imgarr8= imgarrRGB[:,:,2]

        # If above model we don't have anything to return
        if len(points)==0:
            print ("Slice has no points")
            return None

        # Save numpy imgarr to image using OpenCV
        if not filename==None:
            nrStr = "%04d" % sliceNr
            filename = os.path.join(os.getcwd(), "slicer/slice__" + nrStr + ".png")
            cv2.imwrite(filename, imgarr8)
            return imgarr8

        # Save numpy imgarr to ENCODED layer in photonfile
        else:
            # we need to rotate img 90 degrees
            imgarr8 = numpy.rot90(imgarr8, axes=(1, 0))  # we need 1440x2560
            # encode bitmap numpy array to rle
            rle=PhotonFile.encodedBitmap_Bytes_withnumpy(imgarr8)
            # add rle to photonfile.LayerData[slicenr]
            return [sliceNr,rle]


    def slice(self,sliceHeight=0.1,progressDialog=None,photonfile=None):

        # If no photonfile we export to images
        if photonfile==None:
            # Clear slice directory
            dir = os.path.join(os.getcwd(), "slicer")
            filelist = [f for f in os.listdir(dir) if f.endswith(".png")]
            for f in filelist:
                os.remove(os.path.join(dir, f))

        # Apply model modifiers (translate,rotate,scale) to model
        stl=self.stl
        stl.applyModifiers(self.oglengine.model_trans,
                           self.oglengine.model_angles,
                           self.oglengine.model_scale)


        # Prepare a clean rlestack
        # (Since we don't know number of layer beforehand we cannot yet make an relstack list
        # So rledict is intermediary)
        rledict={}

        # Use ProcessPoolExecutor to process slicefillLayer in parallel
        # See https://pymotw.com/3/concurrent.futures/
        #maxworkers=concurrent. multiprocessing.cpu_count()-1
        sliceBottom=0
        res=[]
        approxNrSlices=int(stl.modelheight/sliceHeight)+1
        tstart=time.time()

        # slice bunny.stl on Linux Toshiba NJ: 0.21 sec/slice (184sec for 858 slices - 42mm with 0.05 slice height)
        """
        points, slice = stl.takeSlice(0.10, 0.15)
        nr=10
        for i in range(nr):
            #points, slice = stl.takeSlice(0.10, 0.15)
            imgarrRGB = stl.slice2bmp_ocv(points, slice, None)
        print ("Elapsed %0.1f ms" % ((time.time()-tstart)/nr*1000))
        quit()
        """

        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Submit all jobs to ProcessPoolExecutor
            for sliceNr in range(approxNrSlices):
                sliceTop=sliceBottom+sliceHeight
                if photonfile==None:
                    nrStr = "%04d" % sliceNr
                    filename=os.path.join(os.getcwd(),"slicer/slice__"+nrStr+".png")
                else:
                    filename=None
                print ("-----------")
                print ("Slice: ",sliceNr," from-to: ",str(int(sliceBottom*1000))+"um",str(int(sliceTop*1000))+"um", "save as:",filename)
                job = executor.submit(self.slicefillLayer, sliceNr=sliceNr, sliceBottom=sliceBottom, sliceTop=sliceTop,filename=filename)
                res.append(job)
                sliceBottom += sliceHeight

            # Handle all results as they come available
            sliceNr=0
            for ret in concurrent.futures.as_completed(res):
                # Check if we get return False and thus an empty image (top of model reached)
                if not ret.result()==None: # result is None if no slice was drawn
                    if not photonfile == None:
                        sliceNr,rle=ret.result()
                        rledict[sliceNr]=rle
                        sliceNr+=1
                    if not filename == None: None # we do nothing, file was already saves
                if not progressDialog==None:
                    perc=100*sliceNr/approxNrSlices
                    if perc>100: perc=100
                    progressDialog.setProgress(perc)
                    progressDialog.setProgressLabel(str(sliceNr) + "/" + str(approxNrSlices))
                    progressDialog.handleEvents()
                    if progressDialog.cancel:
                        #  Reset total number of layers to last layer we processes
                        self.cancelReplace=True
                        executor.shutdown(False)
                        print ("Abort with ",sliceNr,"layers.")

        print ("Elapsed %0.2f sec" % (time.time()-tstart))

        # Import to photonfile
        if not photonfile==None:
            # Copy reldict to rlestack in right order and without empty layers
            nrSlices=approxNrSlices
            rlestack=nrSlices*[None]
            for sliceNr in range(nrSlices):
                rlestack[sliceNr]=rledict[sliceNr]

            # Replace layers in photonfile with images in rlestack
            photonfile.replaceBitmaps(rlestack)



