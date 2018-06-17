import os
import pygame
from pygame.locals import *
from GUI import *

class FileDialog():
    winrect=None
    titlerect=None
    filerect=None
    margins=GRect(8,4,4,4)
    waiting=False
    dragDiff = None

    bordercolor=(0,0,0)
    titlebackcolor=(192,192,192)
    titletextcolor=(0,0,0)
    formcolor=(128,128,128)
    filebackcolor=(255,255,255)
    filetextcolor=(0,0,0)
    fontname = "Consolas"
    fontsize = 24
    listbox=None
    btnOK=None
    btnCancel=None
    tbFilename=None
    titleheight=24
    footerHeight=40
    buttonHeight=28
    buttonWidth=64
    controls=[]
    ext="*"
    startdir=""
    selFilename="None selected"
    selDirectory = "None selected"
    showFilenames=True
    lastaction=""


    def reposControls(self): #called after winrect is moved
        self.titlerect = GRect(self.winrect.x, self.winrect.y, self.winrect.width, self.titleheight)
        self.footerTop = self.winrect.y + self.winrect.height - self.margins.height - self.footerHeight
        x=self.winrect.x+self.margins.x
        y=self.winrect.y + self.titleheight + self.margins.y
        w=self.winrect.width - self.margins.x - self.margins.width
        h=self.winrect.height - self.titleheight - self.margins.y - self.footerHeight- self.margins.height
        self.listbox.rect=GRect(x,y, w, h)
        self.btnOK.rect=GRect(self.winrect.x+self.winrect.width-self.margins.width-self.buttonWidth,self.footerTop+self.margins.x,self.buttonWidth,self.buttonHeight)
        self.btnCancel.rect= GRect(self.winrect.x + self.winrect.width - 2*self.margins.width - 2*self.buttonWidth,self.footerTop + self.margins.x, self.buttonWidth, self.buttonHeight)
        self.tbFilename.rect =GRect(self.winrect.x+self.margins.x,self.footerTop+self.margins.x,self.winrect.width-4*self.margins.x-2*self.buttonWidth,self.buttonHeight)

    def __init__(self, pyscreen, pos, startdir=None, title="Open File Dialog",defFilename="newfile.txt", dfontname=None,dfontsize=24, ext="*",parentRedraw=None):
        self.pyscreen = pyscreen
        self.parentRedraw=parentRedraw
        if startdir==None: self.startdir=os.getcwd()
        self.ext=ext
        self.winrect=GRect(pos[0], pos[1], 300, 200)
        self.title=title
        self.defFilename=defFilename
        self.font = pygame.font.SysFont(dfontname, dfontsize)
        width, height = self.font.size("MinimalText")
        self.titleheight=height+self.margins.y+self.margins.height

        self.footerTop = self.winrect.y + self.winrect.height - self.margins.height - self.footerHeight
        self.listbox=ListBox(pyscreen,fontname=dfontname,fontsize=dfontsize,func_on_click=self.handleListboxSelect, rect=GRect())
        self.btnOK=Button(pyscreen,text="OK",func_on_click=self.handleOK, rect=GRect())
        self.btnCancel = Button(pyscreen, text="Cancel",func_on_click=self.handleCancel, rect=GRect())
        self.tbFilename= TextBox(pyscreen,backcolor=(255,255,255),textcolor=(0,0,0),bordercolor=(0,0,0),rect=GRect(),text=defFilename)
        self.reposControls()

        self.controls.append(self.listbox)
        self.controls.append(self.tbFilename)
        self.controls.append(self.btnOK)
        self.controls.append(self.btnCancel)


    def getFile(self):
        self.tbFilename.visible=False
        self.showFilenames=True
        self.readDirectory()
        self.waiting=True
        self.waitforuser()
        if self.lastaction=="OK":
            fullpath = os.path.join(self.startdir, self.selFilename)
            return fullpath
        else:
            return None

    def getDirectory(self):
        self.tbFilename.visible=False
        self.showFilenames=True#False
        self.readDirectory()
        self.waiting=True
        self.waitforuser()
        if self.lastaction=="OK":
            return self.selDirectory
        else:
            return None

    def newFile(self):
        self.tbFilename.visible=True
        self.showFilenames=True
        self.readDirectory()
        self.waiting=True
        self.waitforuser()
        if self.lastaction=="OK":
            fullpath = os.path.join(self.startdir, self.tbFilename.text)
            return fullpath
        else:
            return None

    def readDirectory(self):
        #read dirs and files
        #print(self.startdir)
        direntries = os.listdir(self.startdir)
        # extract dirs

        #find dirs
        dirs = [".."]
        for entry in direntries:
            fullname = os.path.join(self.startdir, entry)
            if os.path.isdir(fullname): dirs.append(entry + "/")
        dirs.sort()

        # apply filter
        files = []
        if self.showFilenames:
            if not self.ext == "*":
                for entry in direntries:
                    if entry.endswith(self.ext): files.append(entry)
            files.sort()

        # make one list
        # print("dirs : ",dirs)
        # print("files: ", files)
        self.dirsandfiles = dirs + files

        #print("both : ", self.dirsandfiles)

    def redraw(self):
        #draw form
        pygame.draw.rect(self.pyscreen, self.formcolor, self.winrect.tuple(), 0)
        #draw title bar
        pygame.draw.rect(self.pyscreen, self.titlebackcolor,self.titlerect.tuple(), 0)
        self.font.set_bold(True)
        textsurface = self.font.render(self.title, False, self.titletextcolor)
        self.pyscreen.blit(textsurface, (self.winrect.x + self.margins.x, self.winrect.y + self.margins.y))
        self.font.set_bold(False)
        #draw border
        pygame.draw.rect(self.pyscreen, self.bordercolor, self.winrect.tuple(), 1)

        # draw listbox with files
        self.listbox.items=self.dirsandfiles
        self.listbox.redraw()
        self.btnCancel.redraw()
        self.btnOK.redraw()
        self.tbFilename.redraw()


    def waitforuser(self):
        while self.waiting:
            for event in pygame.event.get():
                pos = pygame.mouse.get_pos()
                gpos=GPoint().fromTuple(pos)

                if event.type == pygame.MOUSEBUTTONUP:
                    if self.dragDiff==None:
                        for ctrl in self.controls:
                            ctrl.handleMouseUp(pos,event.button)
                    else:  # handle window move
                        self.dragDiff=None

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if gpos.inGRect(self.titlerect):
                        self.dragDiff = gpos - self.winrect.p1
                    else:
                        for ctrl in self.controls:
                            ctrl.handleMouseDown(pos,event.button)

                if event.type == pygame.MOUSEMOTION:
                    if not self.dragDiff==None:
                        self.winrect.p1=gpos-self.dragDiff
                        self.reposControls()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print("Escape key pressed down.")
                        self.waiting = False
                    else:
                        self.tbFilename.handleKeyDown(event.key, event.unicode)

            self.parentRedraw()
            self.redraw()
            pygame.display.flip()

    def handleListboxSelect(self):
        #print ("[handleListboxSelect]")
        text=self.listbox.activeText()
        if text=="..":
            self.startdir=os.path.dirname(self.startdir)
            self.selDirectory = self.startdir
            self.readDirectory()
            self.listbox.activeItem=-1
        elif text.endswith("/"):
            self.startdir=os.path.join(self.startdir,text[:-1])
            self.selDirectory = self.startdir
            self.readDirectory()
            self.listbox.activeItem = -1
        else:
            self.tbFilename.text=self.listbox.activeText()
            self.selFilename=self.listbox.activeText()
        #print ("Selected: ",self.selDirectory,self.selFilename)

    def handleCancel(self):
        self.lastaction="Cancel"
        self.waiting=False

    def handleOK(self):
        self.lastaction = "OK"
        self.waiting=False