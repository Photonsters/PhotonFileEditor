"""
Shows message dialog to user
"""

__version__ = "alpha"
__author__ = "Nard Janssens, Vinicius Silva, Robert Gowans, Ivan Antalec, Leonardo Marques - See Github PhotonFileUtils"

import os

import pygame
from pygame.locals import *

from GUI import *

########################################################################################################################
## Class FileDialog
########################################################################################################################

class FileDialog():
    winrect=None
    titlerect=None
    filerect=None
    margins=GRect(8,4,4,4)
    waiting=False
    dragDiff = None

    bordercolor=(0,0,0)
    titlebackcolor=defTitlebarBackground
    titletextcolor=(0,0,0)
    formcolor=defFormBackground
    filebackcolor=defEditorBackground
    filetextcolor=(0,0,0)
    fontname = defFontName
    fontsize = defFontSize
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
        """ Recalculates all positions after moving dialog box. """
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


    def __init__(self, pyscreen, pos, height=300,startdir=None, title="Open File Dialog",defFilename="newfile.txt", dfontname=defFontName, dfontsize=defFontSize, ext="*",parentRedraw=None):
        """ Saves all values to internal variables and calculates some extra internal vars. """
        # Save variables
        self.pyscreen = pyscreen
        self.parentRedraw=parentRedraw
        if startdir==None: self.startdir=os.getcwd()
        self.ext=ext
        self.winrect=GRect(pos[0], pos[1], 350, height)
        self.title=title
        self.defFilename=defFilename
        self.font = pygame.font.SysFont(dfontname, dfontsize)

        # Calculate extra variables
        dummy, textheight = self.font.size("MinimalText")
        self.titleheight=textheight +self.margins.y+self.margins.height
        self.footerTop = self.winrect.y + self.winrect.height - self.margins.height - self.footerHeight

        # Add GUI.Listbox, GUI.Textbox and GUI.Buttons
        self.listbox=ListBox(pyscreen,fontname=dfontname,fontsize=dfontsize,func_on_click=self.handleListboxSelect, rect=GRect())
        self.btnOK=Button(pyscreen,text="OK",func_on_click=self.handleOK, rect=GRect())
        self.btnCancel = Button(pyscreen, text="Cancel",func_on_click=self.handleCancel, rect=GRect())
        self.tbFilename= TextBox(pyscreen,backcolor=(255,255,255),textcolor=(0,0,0),bordercolor=(0,0,0),rect=GRect(),text=defFilename)
        self.controls.append(self.listbox)
        self.controls.append(self.tbFilename)
        self.controls.append(self.btnOK)
        self.controls.append(self.btnCancel)

        # (Re)calculate remaining variables
        self.reposControls()

        # Fill listbox with directory items
        self.readDirectory()
        self.listbox.setItems(self.dirsandfiles)

        #print ("starting with: ", self.startdir)


    def getFile(self):
        """ Get Existing Filename from user. """
        # Hide texbox to input filename and show files in listbox
        self.tbFilename.visible=False
        self.showFilenames=True
        # Read content of directory and update self.dirsandfiles variable to show in listbox
        self.readDirectory()
        # Wait for user to select file and press OK
        self.waiting=True
        self.waitforuser()
        if self.lastaction=="OK":
            fullpath = os.path.join(self.startdir, self.selFilename)
            return fullpath
        else:
            return None


    def getDirectory(self):
        """ Get Directory from user. """
        # Hide texbox to input filename and hide files in listbox
        self.tbFilename.visible=False
        self.showFilenames=False
        # Read content of directory and update self.dirsandfiles variable to show in listbox
        self.readDirectory()
        # Wait for user to select file and press OK
        self.waiting=True
        self.waitforuser()
        if self.lastaction=="OK":
            return self.selDirectory
        else:
            return None


    def newFile(self):
        """ Get New Filename from user. """
        # Show texbox to input filename and show files in listbox
        self.tbFilename.visible=True
        self.showFilenames=True
        # Read content of directory and update self.dirsandfiles variable to show in listbox
        self.readDirectory()
        # Wait for user to select file and press OK
        self.waiting=True
        self.waitforuser()
        if self.lastaction=="OK":
            fullpath = os.path.join(self.startdir, self.tbFilename.text)
            return fullpath
        else:
            return None


    def readDirectory(self):
        """ Read content of directory and update self.dirsandfiles variable to use on redraw. """

        # Always make sure we can go back
        dirs = [".."]

        # Check if we have access to dir
        hasAccess=os.access(self.startdir,os.R_OK)
        if not hasAccess:
            print ("User has no access to "+self.startdir)
            self.dirsandfiles=dirs
            return

        # Read dirs and files
        direntries = os.listdir(self.startdir)

        # Extract dirs
        for entry in direntries:
            if not entry.startswith("$"):   # recycle bin in windows
                fullname = os.path.join(self.startdir, entry)
                if os.path.isdir(fullname): dirs.append(entry + "/")
        dirs.sort(key=str.lower)

        # Extract files and apply filter
        files = []
        if self.showFilenames:
            if not self.ext == "*":
                for entry in direntries:
                    if entry.endswith(self.ext): files.append(entry)
            files.sort(key=str.lower)

        # Make one list of dirs and files
        self.dirsandfiles = dirs + files
        #print("dirs : ",dirs)
        #print("files: ", files)


    def redraw(self):
        """ Redraws filedialog. """

        # First call parent / window to redraw itself
        self.parentRedraw()

        # Draw form background
        pygame.draw.rect(self.pyscreen, self.formcolor, self.winrect.tuple(), 0)

        # Draw title bar including title text
        pygame.draw.rect(self.pyscreen, self.titlebackcolor,self.titlerect.tuple(), 0)
        self.font.set_bold(True)
        textsurface = self.font.render(self.title, True, self.titletextcolor)
        self.pyscreen.blit(textsurface, (self.winrect.x + self.margins.x, self.winrect.y + self.margins.y))
        self.font.set_bold(False)

        # Draw form border
        pygame.draw.rect(self.pyscreen, self.bordercolor, self.winrect.tuple(), 1)

        # Call upon label and button to redraw themselves.
        self.listbox.redraw()
        self.btnCancel.redraw()
        self.btnOK.redraw()
        self.tbFilename.redraw()


    def waitforuser(self):
        """ Blocks all events to Main window and wait for user to click OK. """

        while self.waiting:
            self.redraw()
            pygame.display.flip()

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
                    else:
                        for ctrl in self.controls:
                            ctrl.handleMouseMove(pos)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print("Escape key pressed down.")
                        self.waiting = False
                    else:
                        self.tbFilename.handleKeyDown(event.key, event.unicode)


    def handleListboxSelect(self,text):
        """ If Listbox item selected and directory, we read new directory of if not put filename in textbox. """

        #print ("[handleListboxSelect]")
        #text=self.listbox.activeText()
        #print ("  parse: ", text)
        #print ("  direct:", itext)

        # Check if user wants to go up.
        if text=="..":
            self.startdir=os.path.dirname(self.startdir)
            self.selDirectory = self.startdir
            self.readDirectory()
            self.listbox.setItems(self.dirsandfiles)
        # Check if user selects a directory
        elif text.endswith("/"):
            self.startdir=os.path.join(self.startdir,text[:-1])
            self.selDirectory = self.startdir
            self.readDirectory()
            self.listbox.setItems(self.dirsandfiles)
            print ("Nav to dir: ",self.selDirectory)
        # Else user selected a file
        else:
            self.tbFilename.text=self.listbox.activeText()
            self.selFilename=self.listbox.activeText()
            #print ("Selected: ",self.selFilename," -> ", self.selDirectory,self.selFilename)

    def handleCancel(self):
        """ If Cancel we tell main loop we are ready waiting. """
        self.lastaction="Cancel"
        self.waiting=False


    def handleOK(self):
        """ If OK we tell main loop we are ready waiting. """
        self.lastaction = "OK"
        self.waiting=False