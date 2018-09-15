import math

from OpenGL.GL import *
import pygame
from pygame.locals import *
from Helpers3D import *
from PhotonFile import *
from concurrent.futures import ProcessPoolExecutor


def gluPerspective( fovY, aspect, zNear, zFar ):
    pi = 3.1415926535897932384626433832795

    #fH = tan( (fovY / 2) / 180 * pi ) * zNear
    fH = math.tan( fovY / 360 * pi ) * zNear
    fW = fH * aspect

    glFrustum( -fW, fW, -fH, fH, zNear, zFar )

#http://www.songho.ca/opengl/gl_displaylist.html
# https://github.com/quxiaofeng/python-stl/blob/master/src/stl-loading.py
# https://www.linux.com/blog/python-stl-model-loading-and-display-opengl
# Uses PyOpenGL


def printModelMatrix():
    matrix = (GLfloat * 16)()
    glGetFloatv(GL_MODELVIEW_MATRIX, matrix)
    print (matrixStr(matrix))


class GL():
    #https://pythonprogramming.net/opengl-rotating-cube-example-pyopengl-tutorial/
    model = []
    points=[]
    innerpoints=None
    slice=[]
    #polygonlines = []
    #polygonpoints = []
    #polygonpoints_anglevectors=[]
    sliceheight=0.05
    mousedownpos=None
    mousedownbutton=0
    drawmodel = True
    displayListIdx = 0
    scDisplay=2
    model_angles=[0,0,0]
    model_trans=[0,0,0]
    model_scale = 1
    voxel_stepsize=16

    def drawSquare(self,pos,axis,width,height,type):
        if axis==0:
            pos0=pos
            pos1=  (pos[0], pos[1] + width, pos[2])
            pos2 = (pos[0], pos[1] + width, pos[2] + height)
            pos3 = (pos[0], pos[1] , pos[2] + height)

        if axis==1:
            pos0=pos
            pos1=(pos[0]+width,pos[1],pos[2])
            pos2 = (pos[0] + width, pos[1], pos[2]+height)
            pos3 = (pos[0], pos[1], pos[2]+height)

        if axis==2:
            pos0=pos
            pos1=(pos[0]+width,pos[1],pos[2])
            pos2 = (pos[0] + width, pos[1]+height, pos[2])
            pos3 = (pos[0], pos[1] + height, pos[2])

        if type==GL_TRIANGLES:
            glBegin(GL_TRIANGLES)
            glVertex3fv(pos0)
            glVertex3fv(pos1)
            glVertex3fv(pos2)

            glVertex3fv(pos0)
            glVertex3fv(pos2)
            glVertex3fv(pos3)
            glEnd()

        if type==GL_LINES:
            glBegin(GL_LINES)
            glVertex3fv(pos0)
            glVertex3fv(pos1)
            glVertex3fv(pos1)
            glVertex3fv(pos2)
            glVertex3fv(pos2)
            glVertex3fv(pos3)
            glVertex3fv(pos3)
            glVertex3fv(pos0)
            glEnd()

    def drawBox(self, pos, dim,type):
        #glColor3f(0,128,0)
        self.drawSquare((pos[0],pos[1],pos[2]), 0, dim[1],dim[2],type)
        self.drawSquare((pos[0]+dim[0], pos[1], pos[2]), 0, dim[1], dim[2],type)

        #glColor3f(128, 0, 0)
        self.drawSquare((pos[0],pos[1],pos[2]), 1, dim[0],dim[2],type)
        self.drawSquare((pos[0], pos[1]+dim[1], pos[2]), 1, dim[0], dim[2],type)

        #glColor3f(0, 0, 128)
        self.drawSquare((pos[0],pos[1],pos[2]), 2, dim[0],dim[1],type)
        self.drawSquare((pos[0], pos[1], pos[2]+dim[2]), 2, dim[0], dim[1],type)

    def storeSquare(self,pos,axis,width,height,points,order=-1):
        if axis==0:
            pos0=pos
            pos1 = (pos[0], pos[1] + width, pos[2])
            pos2 = (pos[0], pos[1] + width, pos[2] + height)
            pos3 = (pos[0], pos[1] , pos[2] + height)

        if axis==1:
            pos0=pos
            pos1 = (pos[0]+width,pos[1],pos[2])
            pos2 = (pos[0] + width, pos[1], pos[2]+height)
            pos3 = (pos[0], pos[1], pos[2]+height)

        if axis==2:
            pos0=pos
            pos1 = (pos[0]+width,pos[1],pos[2])
            pos2 = (pos[0] + width, pos[1]+height, pos[2])
            pos3 = (pos[0], pos[1] + height, pos[2])

        if order==-1:
            for i in range(3): points.append(pos0[i])
            for i in range(3): points.append(pos1[i])
            for i in range(3): points.append(pos2[i])

            for i in range(3): points.append(pos0[i])
            for i in range(3): points.append(pos2[i])
            for i in range(3): points.append(pos3[i])
        else:
            for i in range(3): points.append(pos2[i])
            for i in range(3): points.append(pos1[i])
            for i in range(3): points.append(pos0[i])

            for i in range(3): points.append(pos3[i])
            for i in range(3): points.append(pos2[i])
            for i in range(3): points.append(pos0[i])

    def storeBox(self, pos, dim,points,normals):
        self.storeSquare((pos[0],pos[1],pos[2]), 0, dim[1],dim[2],points,-1)
        self.storeSquare((pos[0]+dim[0], pos[1], pos[2]), 0, dim[1], dim[2],points,1)
        for i in range(6): normals.extend([-1,0,0])
        for i in range(6): normals.extend([1,0,0])

        self.storeSquare((pos[0],pos[1],pos[2]), 1, dim[0],dim[2],points,-1)
        self.storeSquare((pos[0], pos[1]+dim[1], pos[2]), 1, dim[0], dim[2],points,1)
        for i in range(6): normals.extend([0,-1,0])
        for i in range(6): normals.extend([0,1,0])

        self.storeSquare((pos[0],pos[1],pos[2]), 2, dim[0],dim[1],points,-1)
        self.storeSquare((pos[0], pos[1], pos[2]+dim[2]), 2, dim[0], dim[1],points,1)
        for i in range(6): normals.extend([0,0,-1])
        for i in range(6): normals.extend([0,0,1])

    voxelPtBufferIdx = -1
    voxelPtBufferLen = -1
    voxelNmBufferIdx = -1
    voxelNmBufferLen = -1

    def store_voxels_asbuffer(self,photonfile,progressDialog=None):
        #from collections import deque # more memory efficient list and just as fast (faster than numpy)
        from array import array # we can make array with signed shorts using "h" but append is slower than list

        # Retrieve raw image data and add last byte to complete the byte array
        scale = 0.047
        nLayers=photonfile.nrLayers()
        layerHeight=PhotonFile.bytes_to_float(photonfile.Header["Layer height (mm)"])
        stepsize=int(self.voxel_stepsize*layerHeight/scale)
        #layerHeight=int(layerHeight/scale*stepsize)
        print ("layerHeight",layerHeight)
        #arr=deque()
        points = numpy.array([], dtype=numpy.int16)
        normals = numpy.array([], dtype=numpy.int8)
        tstart=time.time()
        nrdraws = 0

        for layerNr in range(0,nLayers,stepsize):
            layerpoints = array("h")
            layernormals = array("b")
            bA = photonfile.LayerData[layerNr]["Raw"]
            # add endOfLayer Byte
            bA = bA + photonfile.LayerData[layerNr]["EndOfLayer"]

            #"""
            # SolidCube: 428 voxels, 1.41sec
            # Benchy: 325.357 voxels, 87sec
            # Decode bytes to colors and draw lines of that color on the pygame surface
            oldx=0
            oldy=0
            offset=1# some offset in y will prevent tearing due to collision of base of model with work area
            oldval=0
            oldnr=0

            for idx, b in enumerate(bA):

                nr = b & ~(1 << 7)  # turn highest bit of
                val = b >> 7  # only read 1st bit
                oldx_center = oldx - 1440//2
                oldy_center = oldy - 2560//2
                #print (oldx,oldy,oldval,oldnr,val,nr)

                # If newcolor is oldcolor and repetitions (nr) can be added (to oldnr) do so
                if val==oldval and (oldx+oldnr+nr)<1440:
                    oldnr=oldnr+nr
                    #print ("add nr",val,nr,oldnr)
                    if idx==(len(bA)-1):
                        #print("close layer", oldx, oldy, oldnr, oldval)
                        self.storeBox([oldx_center, layerNr + offset, oldy_center], [oldnr, stepsize, 1], layerpoints,layernormals)
                else:
                    if not val==oldval:
                        # Draw/store prev run
                        #print ("new color")
                        if not oldval==0:
                            self.storeBox([oldx_center, layerNr+offset, oldy_center], [oldnr, stepsize, 1], layerpoints, layernormals)
                            #print("draw", oldx,oldy,oldnr,oldval)
                            nrdraws+=1
                        #else: print("draw blank")
                        # Reset for this run
                        oldx=oldx+oldnr
                        oldnr=nr
                        oldval=val
                        #print("reset", oldx, oldy, oldnr,oldval)
                    elif oldx+oldnr+nr>=1440:
                        #print("close line")
                        newnr=(oldx+oldnr+nr)-1440
                        oldnr=1440-oldx
                        # Draw/store prev run
                        if not oldval==0:
                            self.storeBox([oldx_center, layerNr+offset, oldy_center], [oldnr, 1, 1], layerpoints, layernormals)
                            print("draw", oldx,oldy,oldnr,oldval)
                            nrdraws+=1
                        #else: print("draw blank")
                        # Reset for this run
                        oldx=0
                        oldy+=1
                        oldnr=newnr
                        oldval=val
                        #print("reset", oldx, oldy, oldnr,oldval)
                    else:
                        print ("decoding bug")
                        print (oldval,val,oldx,oldnr,nr)
                        #quit()

            #print (oldy,idx,(len(bA)-1)  )
            #quit()

            """
            # SolidCube: 1712 voxels, 3.1 sec
            # Benchy: 400.818 voxels,94 sec
            # Decode bytes to colors and draw lines of that color on the pygame surface
            x = 0
            y = 0
            d = 1 # some offset in y will prevent tearing due to collision of base of model with work area

            for idx, b in enumerate(bA):
                # From each byte retrieve color (highest bit) and number of pixels of that color (lowest 7 bits)
                nr = b & ~(1 << 7)  # turn highest bit of
                val = b >> 7  # only read 1st bit

                # The surface to draw on is smaller (scale) than the file (1440x2560 pixels)
                x1 = x
                xd = nr
                yd = 1
                zd = 1

                # Bytes and repetions of pixels with same color can span muliple lines (y-values)
                if (x + nr) > 1440:
                    xd = 1440-x1
                if not val==0:
                    x1 = x - 1440//2
                    y1 = y - 2560//2
                    self.storeBox([x1, layerNr+d, y1], [xd, zd, yd], layerpoints, layernormals)
                    #print ([x1,y1,z1],[xd,yd,zd])
                    nrdraws+=1
                x = x + nr
                if x >= 1440:
                    nr = x - 1440
                    x  = 0
                    y  = y + 1
                    xd = nr
                    if not val == 0:
                        x1 = x - 1440 // 2
                        y1 = y - 2560 // 2
                        self.storeBox([x1, layerNr+d, y1], [xd, zd, yd], layerpoints,layernormals)
                        nrdraws += 1
                    x = x + nr
            """

            points=numpy.append(points,layerpoints)
            normals=numpy.append(normals,layernormals)
            #print(len(layerpoints), len(layernormals))
            #print(len(points) , len(normals))
            #print (len(points)/len(normals))
            #print(layerNr, "/", nLayers, "arr-size", len(arr), len(points))
            if not progressDialog==None:
                progressDialog.setProgress(100*layerNr/nLayers)
                progressDialog.handleEvents()

        print ("Time elapsed",time.time()-tstart)

        #"""
        # ===============================================
        # First add points to buffer
        # ===============================================
        points = numpy.array(points,dtype=numpy.float32)
        points=points * scale
        self.voxelPtBufferLen = len(points) // 3

        #glEnableClientState(GL_VERTEX_ARRAY)
        self.voxelPtBufferIdx = glGenBuffers(1)
        dataSizePt = points.nbytes

        # print ("datasize",dataSize)
        glBindBuffer(GL_ARRAY_BUFFER, self.voxelPtBufferIdx)
        glBufferData(GL_ARRAY_BUFFER, dataSizePt, points, GL_STATIC_DRAW)
        #glDisableClientState(GL_VERTEX_ARRAY)

        # ===============================================
        # Second add normals for each triangle to buffer
        # ===============================================
        normals = numpy.array(normals, dtype=numpy.float32)
        self.voxelNmBufferLen = len(normals)

        #glEnableClientState(GL_NORMAL_ARRAY)
        self.voxelNmBufferIdx = glGenBuffers(1)
        dataSizeNm = normals.nbytes

        glBindBuffer(GL_ARRAY_BUFFER, self.voxelNmBufferIdx)
        glBufferData(GL_ARRAY_BUFFER, dataSizeNm, normals, GL_STATIC_DRAW)
        #glDisableClientState(GL_NORMAL_ARRAY)

        print ("nrVoxels",nrdraws)
        return


    def draw_voxels(self):
        if self.voxelPtBufferIdx==-1: return

        colorFront = (0.1, 0.1, 0.1)
        glColor3fv(colorFront)
        #glEnable(GL_COLOR_MATERIAL)
        #glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE )
        sides=GL_FRONT_AND_BACK
        glMaterialfv(sides, GL_AMBIENT, (0.0, 0.0, 0.0))
        glMaterialfv(sides, GL_DIFFUSE, (0.7, 0.7, 0.7))
        glMaterialfv(sides, GL_SPECULAR, (1.0, 1.0, 1.0))
        glMaterialfv(sides, GL_EMISSION, (0.0, 0.0, 0.0))
        glMaterialfv(sides, GL_SHININESS,  70.0)

        glEnable(GL_NORMALIZE)

        # ENABLE CULLING / DISCARDING OF BACK FACES
        glEnable(GL_CULL_FACE)
        glFrontFace(GL_CW)
        glCullFace(GL_BACK)

        # DRAW VOXELS
        glEnableClientState(GL_VERTEX_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, self.voxelPtBufferIdx)
        glVertexPointer(3,GL_FLOAT,0,None)

        glEnableClientState(GL_NORMAL_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, self.voxelNmBufferIdx)
        glNormalPointer(GL_FLOAT, 0, None)

        glDrawArrays(GL_TRIANGLES, 0, self.voxelPtBufferLen)

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)

        # DISABLE CULLING
        glDisable(GL_CULL_FACE)


    def draw_buildarea(self):
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, (0,0,0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0,0,0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS,0.0)

        glColor3f(1,1,1)
        self.drawBox((-67.5/2,0,-120/2),(67.5,150,120),GL_LINES)

        self.drawSquare((-67.5/2,0,-120/2),1,67.5,120,GL_TRIANGLES)

        glBegin(GL_LINES)
        glColor3f(0.3, 0.3, 0.3)
        for x in range (-34,34):
            if x%10==0:
                glVertex3f(x, 0,-120/2)
                glVertex3f(x, 0, 120 / 2)
        for z in range (-59,59):
            if z%10==0:
                glVertex3f(-67.5/2, 0, z)
                glVertex3f(67.5/2, 0, z)
        glEnd()

        #mark sliceheight
        glColor3f(1, 0, 0)
        self.drawSquare((-67.5 / 2, self.sliceheight, -120 / 2), 1, 67.5, 120, GL_LINES)



    def save_slice(self):
        f=2
        sliceimg = pygame.Surface((2560/f, 1440/f))
        sliceimg.fill((0, 0, 0))
        s=2560/120/f
        dx=60
        dy=34
        for c0, c1 in self.polygonlines:
            pygame.draw.line(sliceimg,(255,255,255),((dx+c0[0])*s,(dy+c0[2])*s), ((dx+c1[0])*s,(dy+c1[2])*s))
            #print (c0,c1)
        pygame.image.save(sliceimg,"slice_test.png")

    def draw_slice(self):
        #print("nr line segments found: ", len(self.polygonlines))
        glLineWidth(3)
        #glBegin(GL_LINES)
        glBegin(GL_POLYGON)
        glColor3f(1,0, 0)
        for l in self.slice:
            for c in l:
                #print (c)
                glVertex3fv(c)
        glEnd()
        glLineWidth(1)


    def draw_pointnormals(self):
        #print ("len:",len(self.points))
        # print("nr line segments found: ", len(self.polygonlines))
        glLineWidth(2)
        glBegin(GL_LINES)
        # glBegin(GL_POLYGON)
        glColor3f(0.5, 0, 0.5)
        for p in self.points:
            #print("draw:", nr, len(self.polygonpoints), len(self.polygonpoints_anglevectors))
            n = p.n
            #print ("p,v",p,v)
            n=n*2
            q = p + n
            glVertex3fv(p.toTuple())
            glVertex3fv(q.toTuple())
        glEnd()
        glLineWidth(1)


    modelPtBufferIdx=-1
    modelPtBufferLen=-1
    modelNmBufferIdx=-1
    modelNmBufferLen=-1
    def store_model_asbuffer(self,points,normals):
        # https://www.opengl.org/discussion_boards/showthread.php/183305-How-to-use-glDrawArrays%28%29-with-VBO-Vertex-Buffer-Object-to-display-stl-geometry

        # ===============================================
        # First add points to buffer
        # ===============================================
        points=points.flatten()
        points = points.astype(numpy.float32)
        self.modelPtBufferLen = len(points) // 3

        #print("points", points)
        #print ("len",self.modelBufferLen)
        glEnableClientState(GL_VERTEX_ARRAY)
        self.modelPtBufferIdx = glGenBuffers(1)
        dataSize = points.nbytes

        #print ("datasize",dataSize)
        glBindBuffer(GL_ARRAY_BUFFER, self.modelPtBufferIdx)
        glBufferData(GL_ARRAY_BUFFER, dataSize,points, GL_STATIC_DRAW)

        # ===============================================
        # Second add normals for each triangle to buffer
        # ===============================================

        normals = normals.flatten()
        # we have normals per triangle but need normals per vertex ( = tri-point)
        normals = numpy.repeat(normals, 3)
        normals = normals.astype(numpy.float32)
        self.modelNmBufferLen = len(normals)

        glEnableClientState(GL_NORMAL_ARRAY)
        self.modelNmBufferIdx = glGenBuffers(1)
        dataSize = normals.nbytes

        glBindBuffer(GL_ARRAY_BUFFER, self.modelNmBufferIdx)
        glBufferData(GL_ARRAY_BUFFER, dataSize,normals, GL_STATIC_DRAW)

        #print ("p/n",len(points),len(normals))


    def draw_model(self,type=GL_FILL): #or GL_LINE

        if self.modelPtBufferIdx==-1: return

        colorFront = (0.1, 0.3, 1)
        glPolygonMode(GL_FRONT_AND_BACK, type)
        glColor3fv(colorFront)

        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, (0.3, 0.3, 0.3))
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, (0.85, 0.85, 0.85))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.8, 0.8, 1.0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, 10.0)

        glEnable(GL_NORMALIZE)

        # ENABLE CULLING / DISCARDING OF BACK FACES
        glEnable(GL_CULL_FACE)
        glFrontFace(GL_CW)
        glCullFace(GL_BACK)
        glColor3fv(colorFront)

        # DRAW MODEL BUFFER ARRAY
        glEnableClientState(GL_VERTEX_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, self.modelPtBufferIdx)
        glVertexPointer(3,GL_FLOAT,0,None)

        glEnableClientState(GL_NORMAL_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, self.modelNmBufferIdx)
        glNormalPointer(GL_FLOAT, 0, None)

        glDrawArrays(GL_TRIANGLES, 0, self.modelPtBufferLen)

        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)

        # DISABLE CULLING
        glDisable(GL_CULL_FACE)


        #if not self.innerpoints==None:
        #    glCallList(self.innerwallListIdx)
        #self.draw_pointnormals()



    def setModel(self,points,model,arrpoints=None,arrnormals=None):
        self.points=points
        self.model=model
        self.store_model_asbuffer(arrpoints,arrnormals)

    def setInnerWallModel(self,innerpoints):
        self.innerpoints=innerpoints
        self.innerwallListIdx=self.store_model(self.innerpoints,self.model,(0,1,1),(1,1,0))

    def __init__(self,display_size,callback=None):

        self.display_size=display_size
        self.callback=callback
        self.model_angle = 0  # 30
        self.model_rotaxis = [1, 0, 0]
        self.model_trans = [0, 0, 0]  # (0,5,0

        #(860,640)

        pygame.display.set_mode(self.display_size, DOUBLEBUF | OPENGL | OPENGLBLIT)
        #self.make_model()
        #self.store_model(self.points,self.model)

        print("Detected OpenGL Drivers:")
        print("",glGetString(GL_VENDOR).decode('ascii'))
        print("",glGetString(GL_VERSION).decode('ascii'))

        self.initDraw()
        #self.userLoop()
        #self.sliceLoop()

    def initDraw(self):
        # setup display
        glClearDepth(1.0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        #nshading/color
        #glShadeModel(GL_SMOOTH)
        glShadeModel(GL_FLAT)
        glClearColor(0,0,0,0)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_LIGHTING)

        glMatrixMode(GL_PROJECTION)

        #initial position of camera
        glLoadIdentity()
        gluPerspective(45, (self.display_size[0] / self.display_size[1]), 0.01,15)  # 10.0,10.05)
        glScalef(0.02, 0.02, 0.02)
        glTranslatef(0.0, 0.0, -150)
        glRotatef(30,1,0,0)


        self.model_angles=[0,0,0]
        self.model_trans= [0,0,0]
        self.model_scale = 1
        print ("Use arrow keys and ctrl/shift or mouse to move,rotate,zoom")
        print ("Use arrow keys and left-alt to move model, left-alt+shift to rotate model, right-alt to scale model")
        print ("Use numpad + and - to set slice height.")
        print ("Use enter to toggle 3d model and f5 to save slice")


    def poll(self):
        for event in pygame.event.get():
            # Check for close window
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:return False

            #print ("OGL Mousedown",event.type == pygame.MOUSEBUTTONDOWN)
            matrix = (GLfloat * 16)()

            #if not event.type == pygame.MOUSEMOTION:
            #    print (event, event.type)

            #event=pygame.event.wait() # uses a lot less resources than continously looping with evet.get!
            isLCtrl = (pygame.key.get_mods() & pygame.KMOD_LCTRL)
            isLShift = (pygame.key.get_mods() & pygame.KMOD_LSHIFT)
            isLAlt = (pygame.key.get_mods() & pygame.KMOD_LALT)
            isRAlt = (pygame.key.get_mods() & pygame.KMOD_RALT)

            glGetFloatv(GL_PROJECTION_MATRIX, matrix)
            xaxis = (matrix[0],matrix[4],matrix[8])
            yaxis = (matrix[1], matrix[5], matrix[9])
            zaxis = (matrix[2], matrix[6], matrix[10])

            pan=50
            rot=15

            if not isLAlt and not isRAlt:# translate or slice height
                if isLCtrl: # slice height
                    if event.key == pygame.K_DOWN:
                        glTranslatef(+pan * zaxis[0], +pan * zaxis[1], +pan * zaxis[2])
                    if event.key == pygame.K_UP:
                        glTranslatef(-pan * zaxis[0], -pan * zaxis[1], -pan * zaxis[2])
                elif not isLCtrl: # pan / rotate view
                    if not isLShift: # pan view
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_LEFT:
                                glTranslatef(-pan*xaxis[0], -pan*xaxis[1], -pan*xaxis[2])
                            if event.key == pygame.K_RIGHT:
                                glTranslatef(pan*xaxis[0], pan*xaxis[1], pan*xaxis[2])
                            if event.key == pygame.K_UP:
                                glTranslatef(+pan * yaxis[0], +pan * yaxis[1], +pan * yaxis[2])
                            if event.key == pygame.K_DOWN:
                                glTranslatef(-pan * yaxis[0], -pan * yaxis[1], -pan * yaxis[2])
                            if event.key==pygame.K_KP_PLUS:
                                self.sliceheight=self.sliceheight+0.01#0.02
                                #print ("Slice Height:",self.sliceheight)
                                #self.get_slice(self.sliceheight,self.sliceheight+1)
                            if event.key==pygame.K_KP_MINUS:
                                self.sliceheight=self.sliceheight-0.01#0.02
                                #print ("Slice Height:",self.sliceheight)
                            if event.key == pygame.K_RETURN:
                                self.drawmodel=not self.drawmodel
                            if event.key == pygame.K_F5:
                                print ("slicing")
                                if not self.callback==None:
                                    self.callback.slice()
                            if event.key == pygame.K_q:
                                self.initDraw()

                    elif isLShift: # rotate view
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_UP:
                                glRotatef(-rot, xaxis[0], xaxis[1], xaxis[2])
                            if event.key == pygame.K_DOWN:
                                glRotatef(+rot, xaxis[0], xaxis[1], xaxis[2])
                            if not isLCtrl:
                                if event.key == pygame.K_LEFT:
                                    glRotatef(-rot, yaxis[0], yaxis[1], yaxis[2])
                                if event.key == pygame.K_RIGHT:
                                    glRotatef(+rot, yaxis[0], yaxis[1], yaxis[2])

            elif isRAlt and not isLAlt: # if RAlt we scale model
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_KP_MINUS:
                        self.model_scale=self.model_scale/1.2
                    if event.key == pygame.K_KP_PLUS:
                        self.model_scale=self.model_scale*1.2

            elif isLAlt and not isRAlt: # if LAlt then translate/rotate model
                if event.type == pygame.KEYDOWN:
                    if not isLShift: # translate
                        # Translate will be parallel/perpendicular to build volume
                        if event.key == pygame.K_LEFT:
                            self.model_trans[0] = self.model_trans[0] - pan / 10
                        if event.key == pygame.K_RIGHT:
                            self.model_trans[0] = self.model_trans[0] + pan / 10
                        if event.key == pygame.K_UP:
                            self.model_trans[2] = self.model_trans[2] - pan / 10
                        if event.key == pygame.K_DOWN:
                            self.model_trans[2] = self.model_trans[2] + pan / 10
                        if event.key == pygame.K_KP_PLUS:
                            self.model_trans[1] = self.model_trans[1] + pan / 10
                        if event.key == pygame.K_KP_MINUS:
                            self.model_trans[1] = self.model_trans[1] - pan / 10

                    elif isLShift and not isLCtrl: # rotate model
                        # Translate will be parallel/perpendicular to build volume
                        if event.key == pygame.K_LEFT:
                            self.model_angles[1]+=15
                        if event.key == pygame.K_RIGHT:
                            self.model_angles[1] -= 15
                        if event.key == pygame.K_UP:
                            self.model_angles[0] -= 15
                        if event.key == pygame.K_DOWN:
                            self.model_angles[0] += 15
                        if event.key == pygame.K_KP_PLUS:
                            self.model_angles[2] -= 15
                        if event.key == pygame.K_KP_MINUS:
                            self.model_angles[2] += 15


            if event.type == pygame.MOUSEBUTTONDOWN:
                print ("Mousedown", pygame.time.get_ticks() )
                span=10*pan
                if event.button == 4:
                    glTranslatef(-span* zaxis[0], -span * zaxis[1], -span * zaxis[2])

                elif event.button == 5:
                    glTranslatef(+span* zaxis[0], +span * zaxis[1], +span * zaxis[2])

                else:
                    self.mousedownpos = pygame.mouse.get_pos()
                    self.mousedownbutton=event.button
                    #print ("click button: ",self.mousedownbutton)


            if event.type == pygame.MOUSEBUTTONUP:
                print ("Mouseup\n")
                self.mousedownpos=None
                pygame.event.clear()

            # On linux the mouseup is sometimes missed. So extra check
            if not self.mousedownpos==None:
                #print ("buttons: ",pygame.mouse.get_pressed(), self.mousedownbutton)
                if not pygame.mouse.get_pressed()[self.mousedownbutton-1]:
                    self.mousedownpos=None
                    print("Mouse Correct")
                    #print ("POST")

            if event.type == pygame.MOUSEMOTION and not self.mousedownpos==None:
                newpos=pygame.mouse.get_pos()
                panf=3
                rotf=50
                dx = newpos[0] - self.mousedownpos[0]
                dy = -(newpos[1] - self.mousedownpos[1])
                if self.mousedownbutton==1:#translate
                    glTranslatef(dx * panf*xaxis[0], dx * panf*xaxis[1], dx * panf*xaxis[2])
                    glTranslatef(dy * panf*yaxis[0], dy * panf*yaxis[1], dy * panf*yaxis[2])
                if self.mousedownbutton==3:#rotate
                    glRotatef(-dy/rotf*rot, xaxis[0], xaxis[1], xaxis[2])
                    glRotatef(+dx/rotf*rot, yaxis[0], yaxis[1], yaxis[2])
                self.mousedownpos = newpos
        return True


    def redraw(self, guiSurface, drawModel=False):
        matrix = (GLfloat * 16)()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if drawModel:
            # Correct normals with wrong direction
            glEnable(GL_NORMALIZE)

            # Add some lights
            #renew matrix after rotation/translation above
            glGetFloatv(GL_PROJECTION_MATRIX, matrix)
            yaxis = (matrix[1], matrix[5], matrix[9])
            zaxis = (matrix[2], matrix[6], matrix[10])
            l=-150
            h=10
            directional=1
            positional=0
            #posl = (zaxis[0] * l + yaxis[0] * h, zaxis[1] * l + yaxis[1] * h, zaxis[2] * l + yaxis[2] * h)
            #dirl = (-zaxis[0],-zaxis[1],-zaxis[2])
            #posl = (-50,-100,50)
            #dirl = (50,100,-50)
            posl = (-50, h,0,positional)
            #dirl = ( 50,-h,0)
            glEnable(GL_LIGHT0)
            glLight(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.4, 1))
            glLight(GL_LIGHT0, GL_DIFFUSE, (0.0, 0.0, 0.7, 1))
            glLight(GL_LIGHT0, GL_SPECULAR, (0.0, 0.0, 1.0, 1))
            glLight(GL_LIGHT0, GL_POSITION, posl)
            #glLight(GL_LIGHT0, GL_SPOT_DIRECTION, dirl)
            glColor3f(0,0,0.7)
            self.drawBox(posl,(3,3,3),GL_LINES)

            posl = ( 50, h,0,positional)
            #dirl = (-50,-h,0)
            glEnable(GL_LIGHT3)
            glLight(GL_LIGHT3, GL_AMBIENT, (0.2, 0.2, 0.4, 1))
            glLight(GL_LIGHT3, GL_DIFFUSE, (0.0, 0.0, 0.7, 1))
            glLight(GL_LIGHT3, GL_SPECULAR, (0.0, 0.0, 1.0, 1))
            glLight(GL_LIGHT3, GL_POSITION, posl)
            #glLight(GL_LIGHT3, GL_SPOT_DIRECTION, dirl)
            glColor3f(0,0,0.7)
            self.drawBox(posl,(3,3,3),GL_LINES)

            posl = (0, h, 50,positional)
            #dirl = (0,-h,-50)
            glEnable(GL_LIGHT1)
            glLight(GL_LIGHT1, GL_AMBIENT, (0.2, 0.2, 0.2, 1))
            glLight(GL_LIGHT1, GL_DIFFUSE, (0.7, 0.0, 0.0, 1))
            glLight(GL_LIGHT1, GL_SPECULAR, (1.0, 0.0, 0.0, 1))
            glLight(GL_LIGHT1, GL_POSITION, posl)
            #glLight(GL_LIGHT1, GL_SPOT_DIRECTION, dirl)
            glColor3f(0.7,0,0)
            self.drawBox(posl,(3,3,3),GL_LINES)

            posl = (0, h,-50,positional)
            #dirl = (0,-h, 50)
            glEnable(GL_LIGHT2)
            glLight(GL_LIGHT2, GL_AMBIENT, (0.2, 0.2, 0.2, 1))
            glLight(GL_LIGHT2, GL_DIFFUSE, (0.7, 0.0, 0.0, 1))
            glLight(GL_LIGHT2, GL_SPECULAR, (1.0, 0.0, 0.0, 1))
            glLight(GL_LIGHT2, GL_POSITION, posl)
            #glLight(GL_LIGHT2, GL_SPOT_DIRECTION, dirl)
            glColor3f(0.7,0,0)
            self.drawBox(posl,(3,3,3),GL_LINES)

            """
            points2=[]
            normals2=[]
            self.storeBox([-10,1,-10],[20,3,20],points2,normals2)
            #for i in range(6):
            #    for j in range(6):
            #        print (points2[0 + j*i * 3:3 + j*i * 3])
            #    print("---")
            #quit()
            glColor3f(0.5,0.5,0.5)
            glBegin(GL_TRIANGLES)
            for i in range(6*6):
               glVertex3fv(points2[0+i*3:3+i*3])
               glNormal3fv(normals2[0+i*3:3+i*3])
            glEnd()
            """

            #glBegin(GL_QUADS)
            #glVertex3f(-10,1,10)
            #glVertex3f(10, 1, 10)
            #glVertex3f(10, 1, -10)
            #glVertex3f(-10, 1, -10)
            #glEnd()

            # Draw build area
            self.draw_buildarea()

            # Draw voxels
            self.draw_voxels()

            # Draw model (after apply model angle and translation)
            glPushMatrix()
            glTranslatef(self.model_trans[0], self.model_trans[1], self.model_trans[2])
            glRotatef(self.model_angles[0], 0, 0, 1)
            glRotatef(self.model_angles[1], 0, 1, 0)
            glRotatef(self.model_angles[2], 1, 0, 0)
            glScalef(self.model_scale,self.model_scale,self.model_scale)
            self.draw_model()
            glPopMatrix()

            #lights finished
            glDisable(GL_LIGHT0)
            glDisable(GL_LIGHT1)
            glDisable(GL_LIGHT2)
            glDisable(GL_LIGHT3)

        #draw GUI overlay
        glPushMatrix()
        glLoadIdentity()
        #gluPerspective(45, (display[0] / display[1]), 0.1, 8)  # 10.0,10.05)
        #glScalef(0.02, 0.02, 0.02)
        #glTranslatef(0.0, 0.0, -150)
        #self.drawSquare((-1,-1,0),2,2,2,GL_TRIANGLES,(255,0,0))
        glEnable(GL_LIGHT0)
        glLight(GL_LIGHT0, GL_AMBIENT, (1, 1, 1, 1))
        glLight(GL_LIGHT0, GL_POSITION, (0,0,4))
        glLight(GL_LIGHT0, GL_SPOT_DIRECTION, (0,0,-1))
        self.drawGUI(guiSurface)
        glDisable(GL_LIGHT0)
        glPopMatrix()


    def drawGUI(self,guiSurface):
        w,h=self.display_size
        wf=w/1024
        hf=h/1024
        #print (wf,hf)

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.loadTexture(guiSurface)
        glColor3f(1,1,1)
        glBegin(GL_TRIANGLES)
        #glNormal3f(0,0,1)

        # Upper Left triangle
        glTexCoord2f(0,(1-hf))
        glVertex3f(-1,-1,0)

        glTexCoord2f(0, 1)
        glVertex3f(-1, 1, 0)

        glTexCoord2f(wf, 1)
        glVertex3f(1, 1, 0)

        # Lower Right triangle
        glTexCoord2f(0,(1-hf))
        glVertex3f(-1,-1,0)

        glTexCoord2f(wf, 1)
        glVertex3f(1, 1, 0)

        glTexCoord2f(wf, (1-hf))
        glVertex3f(1, -1, 0)

        glEnd()

        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)


    texid=-1
    def loadTexture(self,guiSurface):
        #textureSurface = pygame.image.load(
        #    'C:/Users/RosaNarden/Documents/Python3/PhotonFileUtils/SamplePhotonFiles/Smilie.bitmaps/_Smilie_preview_0.png')
        w,h=1024,1024
        textureSurface2 = pygame.transform.scale(guiSurface, (w, h))
        textureData = pygame.image.tostring(textureSurface2, "RGBA", 1)
        width = guiSurface.get_width()
        height = guiSurface.get_height()

        # glTexImage2D creates the storage for the texture, defining the size/format and removing all previous pixel data.
        # glTexSubImage2D only modifies pixel data within the texture. It can be used to update all the texels, or simply a portion of them.

        if self.texid==-1:
            self.texid = glGenTextures(1)

            glBindTexture(GL_TEXTURE_2D, self.texid)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, textureData)

        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE, textureData)
        return self.texid

        #except Exception as err:
         #   print ("Error while retreiving GUI image:")
         #   print (err)
          #  return None

"""
tstart=time.time()
print ((2560*1440*1000) / (1024*1024*1024),"GB")
print ("Limit (for 32 bit process is 4GB")
a=numpy.full((2560, 1440,500), 1,dtype=numpy.uint8)
a-=1 #a=a+1 creates a new array, a+=1 does add in place
print ("elapsed",(time.time()-tstart))
quit()
"""

