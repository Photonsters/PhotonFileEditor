import math

from OpenGL.GL import *
import pygame
from pygame.locals import *
from Helpers3D import *
from PhotonFile import *


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

    def drawBox(self, pos, dim,type,color=(255,255,255)):
        self.drawSquare((pos[0],pos[1],pos[2]), 0, dim[1],dim[2],type)
        self.drawSquare((pos[0]+dim[0], pos[1], pos[2]), 0, dim[1], dim[2],type)

        self.drawSquare((pos[0],pos[1],pos[2]), 1, dim[0],dim[2],type)
        self.drawSquare((pos[0], pos[1]+dim[1], pos[2]), 1, dim[0], dim[2],type)

        self.drawSquare((pos[0],pos[1],pos[2]), 2, dim[0],dim[1],type)
        self.drawSquare((pos[0], pos[1], pos[2]+dim[2]), 2, dim[0], dim[1],type)

    voxelIdx=-1
    def store_voxels(self,img,y):
        # y=0-1
        self.voxelIdx= glGenLists(1)
        #print ("layerNr",layerNr)
        #img = photonfile.getBitmap(layerNr,(0,0,0),(255,255,255),(1,1))
        pixarray=pygame.surfarray.pixels2d(img)
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, (0,0,0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0,0,0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS,0.0)
        glNewList(self.voxelIdx, GL_COMPILE)
        #glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, (0.2,0.2,0.2))
        #glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.8, 0.8, 1.0))
        #glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS,20.0)

        #nrLayers=photonfile.nrLayers()
        #print (img.get_width(),img.get_height())
        #glColor3f(0,128,0)
        #self.drawBox((0, 0, 0), (3,3, 3), GL_TRIANGLES)
        maxf=60/720/2
        count=0
        for row in range (500,2000):#2560
            for col in range (0,1440):
                rgb=pixarray[col,row]

                x=col-720   # x=0-1
                z=row-1280  # z=0-1
                x=x*maxf
                z=z*maxf
                y=y*maxf
                y=10
                #y=2*layerNr/nrLayers-1
                #print ("col,row",col,row)
                #if rgb > 0: self.drawBox   ((x, y, z), (maxf*5,maxf*5,maxf*5),GL_TRIANGLES)
                if rgb > 0: self.drawSquare((x, y, z), 1,maxf * 5, maxf * 5, GL_TRIANGLES)
                count=count+1
                #print (x,y,z)
                #print (col,row,rgb)
            #print("======")
            #print (row)
        glEndList()
        print ("nrSquares:",count)

        return self.voxelIdx


    def draw_voxels(self):
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, (0,0,0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0,0,0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS,0.0)

        glColor3f(0,128,0)
        #self.drawBox((0, 0, 0), (3,3, 3), GL_TRIANGLES)
        glCallList(self.voxelIdx)

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

    def make_model(self):
        frad=1/180*math.pi
        stepi = 10
        stepj = 10
        r=20
        for j in range(0,180,stepj):
            jrad1 = j * frad
            jrad2 = (j+stepj) * frad
            for i in range (0,360,stepi):
                irad1 = i * frad
                irad2 = (i+stepi) * frad
                y1 = -cos(jrad1) * r
                y2 = -cos(jrad2) * r
                r1 = sin(jrad1) * r
                r2 = sin(jrad2) * r

                x1 = sin(irad1) * r1
                z1 = cos(irad1) * r1
                x2 = sin(irad2) * r1
                z2 = cos(irad2) * r1

                x3 = sin(irad2) * r2
                z3 = cos(irad2) * r2
                x4 = sin(irad1) * r2
                z4 = cos(irad1) * r2

                p1=Point3D ((x1,y1,z1))
                p2=Point3D ((x2,y1,z2))
                p3=Point3D ((x3,y2,z3))
                p4=Point3D ((x4,y2,z4))
                nr1 = len(self.points)
                self.points.append(p1)
                nr2 = len(self.points)
                self.points.append(p2)
                nr3 = len(self.points)
                self.points.append(p3)
                nr4 = len(self.points)
                self.points.append(p4)
                tri1 = Triangle3D(self.points, nr1, nr2, nr3)
                tri2 = Triangle3D(self.points, nr1, nr3, nr4)
                self.model.append(tri1)
                self.model.append(tri2)

    modelListIdx=-1
    def store_model(self,points,model,colorFront=(0.1,0.3,1),colorBack=(1,0.3,0.3)):
        # create one display list
        self.modelListIdx = glGenLists(1)

        print ("self.displayListIdx",self.modelListIdx)

        glNewList(self.modelListIdx, GL_COMPILE)

        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, (0.2,0.2,0.2))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.8, 0.8, 1.0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS,50.0)

        #first color back face of triangles
        glEnable(GL_CULL_FACE)

        glCullFace(GL_BACK)
        glBegin(GL_TRIANGLES)
        glColor3fv(colorBack)
        for tri in model:
            glNormal3fv(tri.normal.toTuple())
            glVertex3fv(tri.coord(0,points).toTuple())
            glVertex3fv(tri.coord(1,points).toTuple())
            glVertex3fv(tri.coord(2,points).toTuple())
        glEnd()

        # next color front face of triangles
        glCullFace(GL_FRONT)
        glBegin(GL_TRIANGLES)
        glColor3fv(colorFront)
        for tri in model:
            glNormal3fv(tri.normal.toTuple())
            glVertex3fv(tri.coord(0,points).toTuple())
            glVertex3fv(tri.coord(1,points).toTuple())
            glVertex3fv(tri.coord(2,points).toTuple())
        glEnd()

        # Draw normals for debuggin
        self.draw_pointnormals()

        glDisable(GL_CULL_FACE)

        glEndList()

        return self.modelListIdx

    def draw_model(self,type=GL_FILL): #or GL_LINE
        glPolygonMode(GL_FRONT_AND_BACK, type)
        if len(self.model)>0:
            glCallList(self.modelListIdx)

        #if not self.innerpoints==None:
        #    glCallList(self.innerwallListIdx)

        #self.draw_pointnormals()
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def setModel(self,points,model):
        self.points=points
        self.model=model
        self.modelListIdx=self.store_model(self.points,self.model)

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

        glClearDepth(1.0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        self.initDraw()
        #self.userLoop()
        #self.sliceLoop()

    def initDraw(self):
        # setup display

        #nshading/color
        #glShadeModel(GL_SMOOTH)
        glShadeModel(GL_FLAT)
        glClearColor(0,0,0,0)#(0.4, 0.4, 0.4, 0.0)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_LIGHTING)

        glMatrixMode(GL_PROJECTION)

        #initial position of camera
        glLoadIdentity()
        gluPerspective(45, (self.display_size[0] / self.display_size[1]), 0.1,8)  # 10.0,10.05)
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


    def poll(self,pollModel=False,event=None):
        if pollModel:
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
                    if event.key == pygame.K_UP:
                        glTranslatef(+pan * zaxis[0], +pan * zaxis[1], +pan * zaxis[2])
                    if event.key == pygame.K_DOWN:
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
                    self.mousedownpos = pos = pygame.mouse.get_pos()
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


    def redraw(self, guiSurface, drawModel=False):
        matrix = (GLfloat * 16)()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if drawModel:
            # correct normals with wrong direction
            glEnable(GL_NORMALIZE)

            #some lights
            #renew matrix after rotation/translation above
            glGetFloatv(GL_PROJECTION_MATRIX, matrix)
            yaxis = (matrix[1], matrix[5], matrix[9])
            zaxis = (matrix[2], matrix[6], matrix[10])
            l=-150
            h=-l/4
            posl = (zaxis[0] * l + yaxis[0] * h, zaxis[1] * l + yaxis[1] * h, zaxis[2] * l + yaxis[2] * h)

            glEnable(GL_LIGHT0)
            glLight(GL_LIGHT0, GL_AMBIENT, (0.6, 0.6, 0.4, 1))
            glLight(GL_LIGHT0, GL_POSITION, posl)
            glLight(GL_LIGHT0, GL_SPOT_DIRECTION, (-zaxis[0],-zaxis[1],-zaxis[2]))

            # Draw build area
            self.draw_buildarea()

            #Draw slice
            #self.draw_slice()

            #apply model angle and translation)
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
            #glDisable(GL_LIGHT1)

        #draw overlay
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






#quit()