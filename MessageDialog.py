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
## Class MessageDialog
########################################################################################################################

class MessageDialog():
    #Button constants
    OK=0
    YESNO=1
    OKCANCEL=2
    buttonChoice=OK

    winrect=None
    titlerect=None
    margins=GRect(8,4,4,4)
    waiting=False
    dragDiff = None

    bordercolor=(0,0,0)
    titlebackcolor=defTitlebarBackground
    titletextcolor=(0,0,0)
    formcolor=defFormBackground
    fontname = defFontName
    fontsize = defFontSize
    listbox=None
    btnRight=None
    titleheight=24
    footerHeight=40
    buttonHeight=28
    buttonWidth=64
    controls=[]

    def reposControls(self): #called initially and after winrect is moved
        """ Recalculates all positions after moving dialog box. """
        self.winrect.height=self.titleheight+self.margins.y+self.label.rect.height+self.footerHeight+self.margins.height
        self.titlerect = GRect(self.winrect.x, self.winrect.y, self.winrect.width, self.titleheight)
        self.footerTop = self.winrect.y + self.winrect.height - self.margins.height - self.footerHeight
        self.label.rect.x=self.winrect.x+self.margins.x
        self.label.rect.y=self.winrect.y+self.titleheight+self.margins.y
        self.btnRight.rect=GRect(self.winrect.x + self.winrect.width - self.margins.width - self.buttonWidth, self.footerTop + self.margins.x, self.buttonWidth, self.buttonHeight)
        if not self.buttonChoice==self.OK: # two buttons
            self.btnLeft.rect=GRect.copy(self.btnRight.rect)
            self.btnLeft.rect.left=self.btnLeft.rect.left-self.margins.width - self.buttonWidth

    def __init__(self, pyscreen,
                 pos, width=300,
                 center=True,
                 title="Message Dialog",message="Read this carefully... \n ...before entering Ok!",
                 dfontname=defFontName, dfontsize=defFontSize,
                 buttonChoice=OK,
                 handleOK=None,
                 handleCANCEL = None,
                 handleYES = None,
                 handleNO = None,
                 parentRedraw=None):
        """ Saves all values to internal variables and calculates some extra internal vars. """
        # Save variables
        self.pyscreen = pyscreen
        self.parentRedraw=parentRedraw
        self.winrect=GRect(pos[0], pos[1], width, 160)
        self.title=title
        self.message=message
        self.font = pygame.font.SysFont(dfontname, dfontsize)
        self.buttonChoice=buttonChoice
        self.handleOK=handleOK
        self.handleCANCEL=handleCANCEL
        self.handleNO = handleNO
        self.handleYES = handleYES

        # Calculate extra variables
        dummy, textheight = self.font.size("MinimalText")
        self.titleheight=textheight+self.margins.y+self.margins.height
        self.footerTop = self.winrect.y + self.winrect.height - self.margins.height - self.footerHeight

        # Add GUI.Label and GUI.Button(s)
        rectLabel=GRect(0,0,self.winrect.width-self.margins.x-self.margins.width,0)
        self.label=Label(pyscreen,text=message,fontname=dfontname,fontsize=dfontsize,rect=rectLabel,autoheight=True,center=center,backcolor=self.formcolor,autowrap=True)
        self.controls.append(self.label)
        self.btnRight=Button(pyscreen, text="OK", func_on_click=self.handleRight, rect=GRect())
        self.controls.append(self.btnRight)
        if buttonChoice==self.YESNO:
            self.btnLeft = Button(pyscreen, text="YES", func_on_click=self.handleLeft, rect=GRect())
            self.btnRight = Button(pyscreen, text="NO", func_on_click=self.handleRight, rect=GRect())
            self.controls.append(self.btnLeft)
            self.controls.append(self.btnRight)
        if buttonChoice == self.OKCANCEL:
            self.btnLeft = Button(pyscreen, text="OK", func_on_click=self.handleLeft, rect=GRect())
            self.btnRight=Button(pyscreen, text="CANCEL", func_on_click=self.handleRight, rect=GRect())
            self.controls.append(self.btnLeft)
            self.controls.append(self.btnRight)

        # (Re)calculate remaining variables
        self.reposControls()


    def show(self):
        """ Returns selected button and closes dialog. """
        self.waiting=True
        self.waitforuser()
        return self.lastaction

    def redraw(self):
        """ Redraws dialogbox. """

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
        self.label.redraw()
        self.btnRight.redraw()
        if not self.buttonChoice==self.OK: self.btnLeft.redraw()


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


    def handleRight(self):
        """ If OK we tell main loop we are ready waiting. """
        if self.buttonChoice==self.OK: self.lastaction="OK"
        if self.buttonChoice==self.OKCANCEL: self.lastaction="CANCEL"
        if self.buttonChoice == self.YESNO: self.lastaction = "NO"
        self.waiting=False

    def handleLeft(self):
        """ If OK we tell main loop we are ready waiting. """
        if self.buttonChoice==self.OKCANCEL: self.lastaction="OK"
        if self.buttonChoice == self.YESNO: self.lastaction = "YES"
        self.waiting=False

