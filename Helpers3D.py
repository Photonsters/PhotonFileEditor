import math

nrDecimals=2

def setNrDecimals(nr):
    global nrDecimals
    nrDecimals=nr

def signif(n, nr=None):
    if nr==None: nr=nrDecimals
    if n<0:
        format="%."+str(nr)+"f"
    else:
        format = " %." + str(nr) + "f"
    return (format % round(n,nr))

def signif_tuple(t,nr=None):
    if nr==None: nr=nrDecimals
    r=[]
    for n in t:
        r.append(signif(n,nr))
    return r

def matrixStr(matrix):
    for i in range(0, 16, 4):
        print([signif(n) for n in matrix[i + 0:i + 4]])

def List2Str(points):
    ret="["
    for point in points:
        ret+=(str(point)+" ")
    ret+="]"
    return ret

########################################################################################################################
## Class Vector
########################################################################################################################

class Vector:
    x=0
    y=0
    z=0

    def __init__(self,p):
        self.x = p[0]
        self.y = p[1]
        self.nrDims=len(p)
        if self.nrDims==3: self.z = p[2]
        if self.nrDims<2 or self.nrDims>3:
            raise Exception("Only 2D and 3D are currently supported.")

    def item(self,nr):
        if nr == 0: return x
        if nr == 1: return y
        if self.nrDims==3 and nr == 2: return z

    def normalize(self):
        l=math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z)
        if l==0: return
        self.x = self.x / l
        self.y = self.y / l
        self.z = self.z / l

    def copy(self):
        return Vector((self.x,self.y,self.z))

    def fromPoint3D(p3D):
        return Vector(p3D.toTuple())

    def fromX():
        return Vector((1,0,0))

    def fromY():
        return Vector((0,1,0))

    def fromZ():
        return Vector((0,0,1))

    def toTuple(self):
        if self.nrDims == 3: return (self.x,self.y,self.z)
        if self.nrDims == 2: return (self.x, self.y)

    def toInt(self):
        self.x = int(self.x)
        self.y = int(self.y)
        self.z = int(self.z)

    def toInverted(self):
        return Vector((-self.x,-self.y,-self.z))

    def length(self):
        return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z)

    def __add__(self, other):
        if self.nrDims == 3: return Vector((self.x + other.x, self.y + other.y, self.z + other.z))
        if self.nrDims == 2: return Vector((self.x + other.x, self.y + other.y))

    def __sub__(self, other):
        if self.nrDims == 3: return Vector((self.x - other.x, self.y - other.y, self.z - other.z))
        if self.nrDims == 2: return Vector((self.x - other.x, self.y - other.y))

    def __mul__(self, scale):
        if self.nrDims == 3: return Vector((self.x * scale, self.y * scale, self.z * scale))
        if self.nrDims == 2: return Vector((self.x * scale, self.y * scale))

    def __eq__(self, other):
        try:
            # print ("comp to gpoints")
            if self.nrDims == 3: return (self.x == other.x and self.y == other.y and self.z == other.z)
            if self.nrDims == 2: return (self.x == other.x and self.y == other.y)
        except:
            # print ("error - compare types")
            return type(self) == type(other)

    def minus(self, other):
        self.x=self.x - other.x
        self.y=self.y - other.y
        self.z=self.z - other.z

    def plus(self, other):
        self.x=self.x + other.x
        self.y=self.y + other.y
        self.z=self.z + other.z

    def scale(self, scale):
        self.x=self.x * scale
        self.y=self.y * scale
        self.z=self.z * scale

    def scale3D(self, scale):
        self.x=self.x * scale.x
        self.y=self.y * scale.y
        self.z=self.z * scale.z

    def crossproduct(self,other):
        r = Vector((0, 0, 0))
        if self.nrDims==3:
            r.x = self.y * other.z - self.z * other.y
            r.y = self.z * other.x - self.x * other.z
            r.z = self.x * other.y - self.y * other.x
        if self.nrDims==2:
            r = self.x * other.y - self.y-other.x
        return r

    def inproduct(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def equals(self,other):
        return (self.x==other.x and self.y==other.y and self.z==other.z)

    def __str__(self):
        if self.nrDims == 3: return str((signif(self.x), signif(self.y), signif(self.z) ))
        if self.nrDims == 2: return str((signif(self.x), signif(self.y)))



########################################################################################################################
## Class 3DPoint
########################################################################################################################

# class for a 3d point
class Point3D:
    x=0
    y=0
    z=0
    n=None

    def __init__(self, p, c=(1, 0, 0),n=None):
        self.point_size = 0.5
        self.color = c
        self.x = p[0]
        self.y = p[1]
        self.z = p[2]
        if not n==None: self.n=n

    #def glvertex(self):
    #    glVertex3f(self.x,self.y,self.z)

    def snapOnGrid(self, gridsize=0.047):
        # round on grid of printer
        self.x = round((self.x / gridsize)) * gridsize
        self.y = round((self.y / gridsize)) * gridsize
        self.z = round((self.z / gridsize)) * gridsize

    def toTuple(self):
        return (self.x,self.y,self.z)

    def __add__(self, other):
        return Point3D((self.x + other.x, self.y + other.y, self.z + other.z))

    def __mul__(self, other):
        return Point3D((self.x * other, self.y * other, self.z * other))

    def __sub__(self, other):
        return Point3D((self.x - other.x, self.y - other.y, self.z - other.z))

    def equals(self,other):
        return (self.x==other.x and self.y==other.y and self.z==other.z)

    def strN(self):
        return str(self)+ " "+str(self.n)

    def __str__(self):
        return    ( "( "+
                   signif(self.x) + " " +
                   signif(self.y) + " " +
                   signif(self.z) +
                    ")")

########################################################################################################################
## Class 3DPoint
########################################################################################################################
class Line3D:
    point=None
    direction=None

    def __init__(self,point,direction):
        self.point=point
        self.direction=direction


    def planeDistance(self,plane):
        """
        :param point: Point3D
        :param direction: Vector
        :return:
        """

        print ("line ",str(self.point), " > ",str(self.direction))
        print ("plane", str(plane))
        relPoint=self.point-plane.origin
        distancePerpendicular= plane.normal.inproduct(relPoint)

        inp=plane.normal.inproduct(self.direction)
        if inp==0: #line is perpendicular to plane
            return None
        else:
            alignment=-1/inp

        return distancePerpendicular*alignment

        #return distancePerpendicular

    def __str__(self):
        return str(self.point)+ " -> "+str(self.direction)

class Plane3D:
    origin=None
    vector1=None
    vector2=None
    normal=None

    def __init__(self,origin,vector1,vector2,normal):
        self.origin=origin
        self.vector1 = vector1
        self.vector2 = vector2
        self.normal=normal

    def fromTriangle(tri):
        return Plane3D(
            tri.coord(0),
            tri.coord(1)-tri.coord(0),
            tri.coord(2)-tri.coord(0),
            tri.normal)

    def __str__(self):
        return   str(self.origin)+ " -> "+str(self.vector1)+" "+ str(self.vector2)+" "+str(self.normal)


########################################################################################################################
## Class Triangle3D
########################################################################################################################

# class for a 3d face on a model
class Triangle3D:
    __cloud  = None # array of points in model
    __points = None # indices of points which make up this triangle
    normal = None # vector

    def __init__(self, cloud, p1, p2, p3):#, n=None):
        # 3 points of the triangle
        self.__points = [p1, p2, p3]
        self.__cloud=cloud

        # triangles normal
        self.normal = self.calculate_normal() # (0,1,0)

    def calculate_normal(self):
        (p3,p2,p1)=self.__points
        p3=  self.__cloud[self.__points[0]]
        p2 = self.__cloud[self.__points[1]]
        p1 = self.__cloud[self.__points[2]]
        #print ("p123: ",p1,p2,p3)
        a = Vector.fromPoint3D(p2 - p1)
        b = Vector.fromPoint3D(p3 - p2)
        c = Vector.crossproduct(a, b)
        c.normalize()
        return c

    def pindex(self,idx):
        return self.__points[idx]

    def remap(self, newcloud,indexoffset):
        self.__cloud=newcloud
        for idx in range(0,3) :
            self.__points[idx]+=indexoffset

    def coord(self,idx,cloud=None):
        debug=False
        if cloud==None:
            if debug: print ("idx",idx,self.__points,self.__cloud)
            return self.__cloud[self.__points[idx]]
        else:
            return cloud[self.__points[idx]]

    def hasPoint(self,pointSearch):
        for pidx in self.__points:
            if pointSearch==self.__cloud[pidx]: return True
        return False

    def toTuples(self):
        return (self.coord(0).toTuple(),
                self.coord(1).toTuple(),
                self.coord(2).toTuple())

    def toNTuples(self):
        return (self.coord(0).n.toTuple(),
                self.coord(1).n.toTuple(),
                self.coord(2).n.toTuple())

    def toArray(self):
        return [self.__points[0].toTuple(),
                self.__points[1].toTuple(),
                self.__points[2].toTuple()]

    #Discard types
    RET_BOTH=0        # Return all, just split
    RET_ABOVE=1      # Return above line
    RET_BELOW=2      # Return below line

    def splitOnPlaneY(self,height,ret_side, ret_onplane,cloud=None):
        debug=False
        # Triangles could be oriented in several ways relative to the layer bottom and top:
        #             (1)        (2)             (3)                     (4)             (5)
        #            Above      Below       points on Line              Middle        Intersect
        #                                2     1     2      3                         one point
        #              *
        #             * *
        #            *****                *                            *                *
        #                                ***                          * *   *******     * *
        # height -----------------------*****--*-- *****---****------*   *---*   *------*   *----
        #                          *          * *   * *             *******   * *       * *
        #                         * *        *****   *                         *        *
        #                        *****

        #normals
        p0n = self.coord(0,cloud).n
        p1n = self.coord(1,cloud).n
        p2n = self.coord(2,cloud).n
        p0nt = p0n.toTuple()
        p1nt = p1n.toTuple()
        p2nt = p2n.toTuple()

        #coordinates
        p0 = self.coord(0,cloud)
        p1 = self.coord(1,cloud)
        p2 = self.coord(2,cloud)
        p0t = p0.toTuple()
        p1t = p1.toTuple()
        p2t = p2.toTuple()
        n = self.normal

        s01 = -1
        s12 = -1
        s20 = -1
        d0ab= (p0.y >  height)
        d1ab= (p1.y >  height)
        d2ab= (p2.y >  height)
        d0bl= (p0.y <  height)
        d1bl= (p1.y <  height)
        d2bl= (p2.y <  height)
        d0eq= (p0.y == height)
        d1eq= (p1.y == height)
        d2eq= (p2.y == height)

        nrAbove = int(d0ab) + int(d1ab) + int(d2ab)
        nrBelow = int(d0bl) + int(d1bl) + int(d2bl)
        nrOnline= int(d0eq) + int(d1eq) + int(d2eq)

        if debug: print ("SPLITTING TRI ", p0t,p1t,p2t)

        # (1) Check Above
        if nrAbove==3:
            if debug: print ("All points above")
            if ret_side==self.RET_ABOVE: return [(self.toTuples(),self.toNTuples())]
            else: return []

        # (2) Check Below
        if nrBelow==3:
            if debug: print("All points below")
            if ret_side==self.RET_BELOW :return [(self.toTuples(),self.toNTuples())]
            else:return []

        # (3) Three, Two or One points on line
        if nrOnline==3:
            if debug: print("All points on line")
            if ret_onplane:
                return [(self.toTuples(),self.toNTuples())]

        if nrOnline==2:
            if debug: print("Two points on line")
            if ret_side==self.RET_ABOVE:
                if d0ab or d1ab or d2ab:return [(self.toTuples(),self.toNTuples())]
                else: return []
            if ret_side==self.RET_BELOW:
                if d0bl or d1bl or d2bl:return [(self.toTuples(),self.toNTuples())]
                else:return []
            if debug: print ("error, we should have found 1 point above/below!")

        #if 1 point on line and two other points on same side
        if nrOnline==1:
            if debug: print("One point on line")
            if ret_side==self.RET_ABOVE:
                if nrAbove==2: return [(self.toTuples(),self.toNTuples())]
                else: return []
            if ret_side==self.RET_BELOW:
                if nrBelow==2: return [(self.toTuples(),self.toNTuples())]
                else: return []
            if debug: print("error, we should have found 1 point above/below!")

        # (4,5) S0,S1,S2 is splitpoint for each line p0-p1, p1-p2, p2-p3
        # If we reached this stage, we are not above plane, not below plane, and not with 1/2/3 points on plane
        # So only check if two points at same height
        if (p0.y==p1.y): s01=-1
        else:            s01 = (p0.y - height) / (p0.y - p1.y)
        if (p1.y==p2.y): s12=-1
        else:            s12 = (p1.y - height) / (p1.y - p2.y)
        if (p2.y==p0.y): s20=-1
        else:            s20 = (p2.y - height) / (p2.y - p0.y)

        if debug: print("s01 s12 s20", signif(s01), signif(s12), signif (s20))

        p01 = [p0.x + s01 * (p1.x - p0.x),
               height,
               p0.z + s01 * (p1.z - p0.z)]
        p12 = [p1.x + s12 * (p2.x - p1.x),
               height,
               p1.z + s12 * (p2.z - p1.z)]
        p20 = [p2.x + s20 * (p0.x - p2.x),
               height,
               p2.z + s20 * (p0.z - p2.z)]

        p01n = p0n * s01 + p1n * (1 - s01)
        p12n = p1n * s12 + p2n * (1 - s12)
        p20n = p2n * s20 + p0n * (1 - s20)
        p01n = p01n.toTuple()
        p12n = p12n.toTuple()
        p20n = p20n.toTuple()

        # (4) two intersections
        if debug: print("splitting tri with two intersections")

        if (nrAbove==2 and nrBelow==1) or (nrAbove==1 and nrBelow==2):
            if debug: print("nrAbove, ret_ABOVE", nrAbove, ret_side==self.RET_ABOVE)
            if s01 < 0 or s01 > 1:   # so interesection on s12 and s20
                t1=((p12,p2t,p20),(p12n,p2nt,p20n))
                t2=((p1t,p20,p0t),(p1nt,p20n,p0nt))
                t3=((p1t,p12,p20),(p1nt,p12n,p20n))
                if nrAbove == 1 and ret_side==self.RET_BELOW: return [t2,t3]
                if nrAbove == 2 and ret_side == self.RET_BELOW: return [t1]
                if nrAbove == 1 and ret_side==self.RET_ABOVE: return [t1]
                if nrAbove == 2 and ret_side == self.RET_ABOVE: return [t2,t3]
            elif s20 < 0 or s20 > 1: # so interesection on s12 and s01
                t1=((p01,p1t,p12),(p01n,p1nt,p12n))
                t2=((p0t,p01,p2t),(p0nt,p01n,p2nt))
                t3=((p01,p12,p2t),(p01n,p12n,p2nt))
                if nrAbove == 1 and ret_side==self.RET_BELOW: return [t2,t3]
                if nrAbove == 2 and ret_side == self.RET_BELOW: return [t1]
                if nrAbove == 1 and ret_side==self.RET_ABOVE: return [t1]
                if nrAbove == 2 and ret_side == self.RET_ABOVE: return [t2,t3]
            elif s12 < 0 or s12 > 1: # so interesection on s01 and s20
                t1=((p0t,p01,p20),(p0nt,p01n,p20n))
                t2=((p01,p1t,p2t),(p01n,p1nt,p2nt))
                t3=((p01,p2t,p20),(p01n,p2nt,p20n))
                if nrAbove == 1 and ret_side==self.RET_BELOW: return [t2,t3]
                if nrAbove == 2 and ret_side == self.RET_BELOW: return [t1]
                if nrAbove == 1 and ret_side==self.RET_ABOVE:return [t1]
                if nrAbove == 2 and ret_side == self.RET_ABOVE: return [t2,t3]

        # (5) one intersections
        if debug: print("splitting tri with ONE intersections")
        if nrOnline == 1 and nrAbove == 1 and nrBelow == 1:
            if p0[y]==height: # so intersection on s12
                t1 = ((p0t, p1t, p12),(p0nt, p1nt, p12n))
                t2 = ((p0t, p12, p2t),(p0nt, p12n, p2nt))
                return [t1,t2]
            if p1[y]==height: # so intersection on s20
                t1 = ((p1t, p2t, p20),(p1nt, p2nt, p20n))
                t2 = ((p1t, p20, p0t),(p1nt, p20n, p0nt))
                return [t1,t2]
            if p2[y]==height: # so intersection on s01
                t1 = ((p2t, p0t, p01),(p2nt, p0nt, p01n))
                t2 = ((p2t, p01, p1t),(p2nt, p01n, p1nt))
                return [t1,t2]

        # if we come here something in this method is wrong
        raise Exception ("Coding error in Triangle.splitOnPlaneY")


    def __str__(self):
        ret=""
        for idx in range(0,3):
            ret=ret+ str(self.pindex(idx))+ ":"+str(self.coord(idx))+" "
        ret=ret+" | n:"+ str(self.normal)
        return ret
