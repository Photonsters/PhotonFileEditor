import struct
import pygame
import pygame.gfxdraw
from Helpers3D import *
import numpy


# load stl file detects if the file is a text file or binary file

class STLFile:
    cmin = [100, 100, 100]
    cmax = [-100, -100, -100]
    points = []
    model = []
    innerpoints=[]
    innermodel=[]
    testTris=[35,33] # opposite walls
    testTris = [35,31]
    testTris = [0, 2,3]
    testTris = []


    def load_stl(self, filename, scale):
        # read start of file to determine if its a binary stl file or a ascii stl file
        fp = open(filename, 'rb')
        h = fp.read(80)
        type = h[0:5]
        fp.close()
        # print ("filename",filename)
        # print ("type",type)

        if type == b'solid':
            print("reading text file " + str(filename))
            self.load_text_stl(filename, scale)
        else:
            print("reading binary stl file " + str(filename, ))
            self.load_binary_stl(filename, scale)
        print("...loaded")


    # read text stl match keywords to grab the points to build the model
    def load_text_stl(self, filename, scale):
        print("load_text_stl", filename)
        fp = open(filename, 'r')
        for line in fp.readlines():
            # print (line)
            words = line.split()
            if len(words) > 0:
                if words[0] == 'solid':
                    self.name = words[1]

                if words[0] == 'facet':
                    center = [0.0, 0.0, 0.0]
                    triangle = []
                    normal = (eval(words[2]), eval(words[3]), eval(words[4]))

                if words[0] == 'vertex':
                    triangle.append((eval(words[1]) * scale, eval(words[2]) * scale, eval(words[3]) * scale))
                    # print ((eval(words[1]), eval(words[2]), eval(words[3])))

                if words[0] == 'endloop':
                    # make sure we got the correct number of values before storing
                    if len(triangle) == 3:
                        self.model.append(Triangle3D(triangle[0], triangle[1], triangle[2], normal))
        fp.close()
        print("Nr triangles:", len(self.model))
        return self.model


    # load binary stl file check wikipedia for the binary layout of the file
    # we use the struct library to read in and convert binary data into a format we can use
    def appendFast(self,object,list,idx):
        #print ("in list: ",len(list),id(list))
        if idx>=len(list):
            list=list+[None]*1000
            print ("resized: ",len(list), id(list))
        list[idx]=object
        return list


    def load_binary_stl(self, filename, scale=1):
        fp = open(filename, 'rb')
        h = fp.read(80)

        l = struct.unpack('I', fp.read(4))[0]
        count = 0

        #self.points=[None]*1000
        pidx=0

        while True:
            try:
                p = fp.read(12)
                if len(p) == 12:
                    n = struct.unpack('f', p[0:4])[0], struct.unpack('f', p[4:8])[0], struct.unpack('f', p[8:12])[0]

                p = fp.read(12)
                if len(p) == 12:
                    p1 = struct.unpack('f', p[0:4])[0], struct.unpack('f', p[4:8])[0], struct.unpack('f', p[8:12])[0]

                p = fp.read(12)
                if len(p) == 12:
                    p2 = struct.unpack('f', p[0:4])[0], struct.unpack('f', p[4:8])[0], struct.unpack('f', p[8:12])[0]

                p = fp.read(12)
                if len(p) == 12:
                    p3 = struct.unpack('f', p[0:4])[0], struct.unpack('f', p[4:8])[0], struct.unpack('f', p[8:12])[0]

                if len(p) == 12:
                    # switch coordinates to OpenGL
                    a = 0
                    b = 2
                    c = 1
                    n = [n[a], n[b], n[c]]
                    p1 = [p1[a], p1[b], p1[c]]
                    p2 = [p2[a], p2[b], p2[c]]
                    p3 = [p3[a], p3[b], p3[c]]

                    # scale model
                    if not scale==1:
                        p1s = [i * scale for i in p1]
                        p2s = [i * scale for i in p2]
                        p3s = [i * scale for i in p3]
                    else:
                        p1s=p1
                        p2s=p2
                        p3s=p3

                    self.points.append(p1s)
                    self.points.append(p2s)
                    self.points.append(p3s)

                count += 1
                fp.read(2)

                # Check if we reached end of file
                if len(p) == 0:
                    break
            except EOFError:
                break
        fp.close()

        # convert to numpy
        npoints=numpy.array(self.points)

        #find max and min of x, y and z
        x = npoints[:, 0]
        y = npoints[:, 1]
        z = npoints[:, 2]
        self.cmin = (x.min(), y.min(), z.min())
        self.cmax = (x.max(), y.max(), z.max())

        # Create list of unique points and a list indices which translates npoints to indices in list of unique points
        upoints, indices=numpy.unique(npoints,axis=0,return_inverse=True)

        # convert tuple coordinates to point3D instances
        self.points=[]
        for p in upoints:
            self.points.append(Point3D(p))

        # construct triangles
        for i in range(0,len(indices),3):
            p0 = indices[i+0]
            p1 = indices[i+1]
            p2 = indices[i+2]
            tri = Triangle3D(self.points, p0, p1, p2)
            self.model.append(tri)


        print("Loaded file.")
        print("  Nr points:", len(self.points))
        print("  Nr triangles:", len(self.model))
        print("  min-max", self.cmin, self.cmax)
        trans = [0, 0, 0]
        trans[0] = -(self.cmax[0] - self.cmin[0]) / 2 - self.cmin[0]
        trans[2] = -(self.cmax[2] - self.cmin[2]) / 2 - self.cmin[2]
        trans[1] = -self.cmin[1]
        for p in self.points:
            p.x = p.x + trans[0]
            p.y = p.y + trans[1]
            p.z = p.z + trans[2]

        #for triangle in self.model:
        #    for point in triangle.points:
        #        point.x = point.x + trans[0]
        #        point.y = point.y + trans[1]
        #        point.z = point.z + trans[2]

        return self.points,self.model

    def calcPointNormals(self):
        # First copy

        for nr,p in enumerate(self.points):
            sharedNormal = Vector((0,0,0))
            sharedNr=0
            for tri in self.model:
                if tri.pindex(0)==nr or tri.pindex(1)==nr or tri.pindex(2)==nr:
                    sharedNormal+=tri.normal
                    sharedNr+=1
            #sharedNormal=sharedNormal*(1/sharedNr)
            sharedNormal.normalize()
            p.n=sharedNormal

    def createInnerWall(self, wallThickness):
        setNrDecimals(1)

        for nr,tri in enumerate(self.model):
            print("tri ", nr," : ",str(tri))

        self.innerpoints=len(self.points)*[None]
        for nr, p in enumerate(self.points):
            innerDir=p.n.toInverted()
            line3d=Line3D(p,innerDir)
            print ("---------------------------")
            print ("POINT #", nr)
            print("line ", str(line3d))
            # Calculate first triangle we encounter and set as maximum distance to extrude
            minDist=wallThickness
            for nrt,tri in enumerate(self.model):
                if not tri.hasPoint(p):
                    print ("TRI #",str(nrt)," | ",str(tri))
                    plane=Plane3D.fromTriangle(tri)
                    print ("plane",str(plane))
                    relD=line3d.planeDistance(plane)
                    print ("relD ",relD)
                    if not relD==None: # line perpendicular to plane/tri
                        if relD > 0:
                            absD = relD * line3d.direction.length()
                            print("absD ", absD)
                            minDist = min(absD, minDist)
                else:
                    print("TRI # Has this point!")

            # Determine if wallThickness encounters a triangle (larger than minDist
            dist=min(minDist,wallThickness)
            print ("dist ",dist)

            # Extrude with allowed distance
            innerVector=innerDir*dist

            # Offset with p
            print ("innerV", innerVector)
            innerPoint=p+innerVector

            # Add normal of original P
            innerPoint.n=p.n.toInverted()
            print (type(innerPoint.n))
            print ("innerP", innerPoint.strN())

            if innerPoint==None:
                raise Exception("Calc failed!")
            # Add to innerwall
            self.innerpoints[nr]=innerPoint

        return self.innerpoints


    #Discard types
    RET_BOTH=0        # Return all, just split
    RET_ABOVE=1      # Return above line
    RET_BELOW=2      # Return below line

    def __takeSlice(self, fullpoints,fullmodel,Y, ret_side):
        slice=[]
        points=[]
        if fullpoints==None or fullmodel==None or len(fullpoints)==0 or len(fullmodel)==0:
            return points,slice

        print ("fullpoints[0]",fullpoints[0].strN())
        print("fullpoints[1]", fullpoints[1].strN())
        print("fullpoints[2]", fullpoints[2].strN())
        print("fullmodel[0]", fullmodel[0].pindex(0), fullmodel[0].pindex(1), fullmodel[0].pindex(2))

        for idx,triangle in enumerate(fullmodel):
            print ("====",idx)
            triList=triangle.splitOnPlaneY(Y,ret_side,ret_onplane=True,cloud=fullpoints)
            #triList=[triangle.toTuples()]
            print ("trilist",triList)
            for tri,norm in triList:
                print("----")
                print ("tri",tri)
                for pnr in range(0,3):
                    coord=tri[pnr]
                    normal=Vector(norm[pnr])
                    print ("tric", coord,normal)
                    points.append(Point3D(coord,n=normal))
                p0 = len(points) - 3
                p1 = len(points) - 2
                p2 = len(points) - 1
                tri=Triangle3D(points,p0,p1,p2)
                print ("tri",tri)
                slice.append(tri)
                print ("len", len(slice))
        return points,slice


    def takeSlice(self, fromY, toY):
        """ Returns sliced and joined external model and inner model
        """

        # First extract all from mode and inner model above fromY
        pointsAbove,sliceAbove=self.__takeSlice(self.points,self.model,fromY,self.RET_ABOVE)
        innerpointsAbove, innersliceAbove = self.__takeSlice(self.innerpoints, self.model, fromY, self.RET_ABOVE)

        # Using extraction, extract all from mode and inner model below fromY
        pointsBelow, sliceBelow = self.__takeSlice(pointsAbove, sliceAbove, toY, self.RET_BELOW)
        innerpointsBelow, innersliceBelow = self.__takeSlice(innerpointsAbove, innersliceAbove, toY, self.RET_BELOW)

        # We join the inner and outer model and remap point indices in triangles to match new point cloud
        points=pointsBelow+innerpointsBelow
        slice=sliceBelow+innersliceBelow
        #print(points)
        #quit()
        print ("=====================================")

        for idx,tri in enumerate( innersliceBelow):
            print ("bef",idx, str(tri))
            tri.remap(points,len(pointsBelow))
            print ("rem",str(tri))

        return points,slice



    def vector2dir(self,v):
        return (int(v.x > 0) - int(v.x < 0),
                int(v.y > 0) - int(v.y < 0),
                int(v.z > 0) - int(v.z < 0))


    def fillBmp(self, pixarray, fromPoint,fromColor,toColor):
        #array has bounds pixarray[1439,2559]

        stack=[]
        stack.append(fromPoint)
        while len(stack)>0:
            fromPoint=stack.pop()
            fromX,fromY=fromPoint
            color = pixarray[fromX,fromY]
            if color == fromColor:
                pixarray[fromPoint]=toColor
                if fromX-1>0:    stack.append((fromX-1,fromY))
                if fromX+1<1439: stack.append((fromX+1, fromY))
                if fromY-1>0:    stack.append((fromX, fromY-1))
                if fromY+1<2559: stack.append((fromX, fromY+1))

    def slice2bmp(self,points,slice,filename):
        offset=Vector((67.5/2,0,120/2))
        scale=Vector((1440/67.5,1,2560/120))
        img = pygame.Surface((1440 , 2560 ))
        fillPoints=[]
        for tri in slice:
            #Draw/project (filled) triangles
            #print ("=================")
            p0r = tri.coord(0,points)
            p1r = tri.coord(1,points)
            p2r = tri.coord(2,points)

            #print("save: ", p0, p1, p2)
            p0 = offset+p0r
            p1 = offset+p1r
            p2 = offset+p2r
            #print("save: ", p0, p1, p2)
            p0.scale3D(scale)
            p1.scale3D(scale)
            p2.scale3D(scale)

            #Fill from outer to inner walls
            #n0 = p0.n.copy()
            #n1 = p1.n.copy()
            #n2 = p2.n.copy()
            #n0 = vector2dir(n0)
            #n1 = vector2dir(n1)
            #n2 = vector2dir(n2)
            #pn0 = p0 + n0
            #pn1 = p1 + n1
            #pn2 = p2 + n2

            pn0 = p0 - p0r.n
            pn1 = p1 - p1r.n
            pn2 = p2 - p2r.n
            pn0.toInt()
            pn1.toInt()
            pn2.toInt()


            p0.toInt()
            p1.toInt()
            p2.toInt()
            #print ("save: ",p0,p1,p2)

            white=(255,255,255)
            red=(255,0,0)
            black=(0,0,0)
            w=1
            pygame.gfxdraw.filled_trigon(img,p0.x,p0.z,p1.x,p1.z,p2.x,p2.z,white)
            pygame.draw.line(img, white, (p0.x, p0.z), (p1.x, p1.z),w)
            pygame.draw.line(img, white, (p1.x, p1.z), (p2.x, p2.z),w)
            pygame.draw.line(img, white, (p2.x, p2.z), (p0.x, p0.z),w)

            fillPoints.append( (pn0.x, pn0.z))
            fillPoints.append ((pn1.x, pn1.z))
            fillPoints.append ((pn2.x, pn2.z))

        pixarray = pygame.surfarray.pixels2d(img)

        def color2int(color):
            return (color[0]*256+color[1])*256+color[2]

        redi=color2int(red)
        blacki=color2int(black)
        for fillPoint in fillPoints:
            self.fillBmp(pixarray,(fillPoint),blacki,redi)
            pygame.draw.line(img, red, fillPoint, fillPoint, 1)


        #img=pygame.transform.rotate(img,90)
        try:
            pygame.image.save(img,filename)
            print ("Sliced: ",filename)
        except Exception as err:
            print ("Error while writing slice image! \n",filename,err)