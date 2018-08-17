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
## Class PopupDialog
########################################################################################################################

class ProgressDialog():
    winrect=None
    titlerect=None
    margins=GRect(8,4,8,4)
    waiting=False
    dragDiff = None

    bordercolor=(0,0,0)
    titlebackcolor=defTitlebarBackground
    titletextcolor=(0,0,0)
    formcolor=defFormBackground
    fontname = defFontName
    fontsize = defFontSize
    progbar=None
    proglabel=None
    btnCancel=None
    titleheight=24
    footerHeight=40
    buttonHeight=28
    buttonWidth=64
    progHeight = 28
    labelHeight=24*3
    cancel=False


    def reposControls(self): #called after winrect is moved
        """ Recalculates all positions after moving dialog box. """
        self.winrect.height = self.titleheight + self.margins.y + self.labelHeight + self.progHeight +self.footerHeight + self.margins.height
        self.titlerect = GRect(self.winrect.x, self.winrect.y, self.winrect.width, self.titleheight)

        self.label.rect.x = self.winrect.x + self.margins.x
        self.label.rect.y = self.titlerect.y + self.titleheight + self.margins.y
        self.label.rect.width=self.winrect.width-self.margins.x-self.margins.width
        self.label.rect.height = self.labelHeight# self.progbar.rect.y- (self.titlerect.y-self.titlerect.height)

        self.progbar.rect=self.label.rect.copy()
        self.progbar.rect.y=self.label.rect.y+self.labelHeight
        self.progbar.rect.width=self.winrect.width-self.margins.x-self.margins.width
        self.progbar.rect.height=self.progHeight
        self.proglabel.rect=self.progbar.rect.copy()

        self.footerTop = self.winrect.y + self.winrect.height - self.margins.height - self.footerHeight
        self.btnCancel.rect = GRect(self.winrect.x + self.winrect.width - self.margins.width - self.buttonWidth,
                                   self.footerTop + self.margins.x, self.buttonWidth, self.buttonHeight)


    def __init__(self, flipFunc,pyscreen, pos, width=300,title="Progress Dialog",
                 message="Wait or... \n ...press Cancel!",
                 dfontname=defFontName, dfontsize=defFontSize,
                 showCancel=True):
        """ Saves all values to internal variables and calculates some extra internal vars. """
        self.flipFunc=flipFunc
        self.pyscreen = pyscreen
        #self.parentRedraw=parentRedraw
        self.winrect=GRect(pos[0], pos[1], width, 160)
        self.title=title
        self.message=message
        self.font = pygame.font.SysFont(dfontname, dfontsize)
        self.showCancel=showCancel

        # Calculate extra variables
        dummy, textheight = self.font.size("MinimalText")
        self.titleheight=textheight +self.margins.y+self.margins.height
        self.footerTop = self.winrect.y + self.winrect.height - self.margins.height - self.footerHeight

        # Add GUI.Label
        rectLabel = GRect(0, 0, self.winrect.width - self.margins.x - self.margins.width, 0)
        self.label=Label(pyscreen,text=message,fontname=dfontname,fontsize=dfontsize,rect=rectLabel ,autoheight=False,center=True,backcolor=self.formcolor,autowrap=True)

        # Add GUI.ProgressBar
        self.progbar=ProgressBar(pyscreen,GRect())

        # Add GUI.Label
        rectLabel = GRect(0, 0, self.winrect.width - self.margins.x - self.margins.width, 0)
        self.proglabel=Label(pyscreen,text="",fontname=dfontname,fontsize=dfontsize,rect=rectLabel,autoheight=False,center=True,istransparent=True,autowrap=False)

        # Add GUI.Button
        self.btnCancel=Button(pyscreen, text="CANCEL", func_on_click=self.handleCancel, rect=GRect())

        # (Re)calculate remaining variables
        self.reposControls()

    def setProgress(self, progProc):
        self.progbar.progress=progProc
        self.proglabel.setText(str(int(progProc))+"%")
        #print (self.proglabel.text)

    def setProgressLabel(self, progText):
        self.proglabel.setText( progText)

    def show(self):
        """ Just draw me. """
        self.redraw()


    def hide(self):
        """ Do nothing. """
        return

    def redraw(self):
        """ Redraws dialogbox. """
        self.reposControls()

        # Draw form background
        pygame.draw.rect(self.pyscreen, self.formcolor, self.winrect.tuple(), 0)

        # Draw title bar
        pygame.draw.rect(self.pyscreen, self.titlebackcolor,self.titlerect.tuple(), 0)
        self.font.set_bold(True)
        textsurface = self.font.render(self.title, True, self.titletextcolor)
        self.pyscreen.blit(textsurface, (self.winrect.x + self.margins.x, self.winrect.y + self.margins.y))
        self.font.set_bold(False)

        # Draw form border
        pygame.draw.rect(self.pyscreen, self.bordercolor, self.winrect.tuple(), 1)

        # Draw controls
        self.label.redraw()
        self.progbar.redraw()
        self.proglabel.redraw()
        if self.showCancel: self.btnCancel.redraw()
        self.flipFunc()

    def handleEvents(self):
        self.redraw()

        for event in pygame.event.get():
            pos = pygame.mouse.get_pos()
            gpos = GPoint().fromTuple(pos)

            if event.type == pygame.MOUSEBUTTONUP:
                if self.dragDiff == None:
                    self.btnCancel.handleMouseUp(pos, event.button)
                else:  # handle window move
                    self.dragDiff = None

            if event.type == pygame.MOUSEBUTTONDOWN:
                if gpos.inGRect(self.titlerect):
                    self.dragDiff = gpos - self.winrect.p1
                else:
                    self.btnCancel.handleMouseDown(pos, event.button)

            if event.type == pygame.MOUSEMOTION:
                if not self.dragDiff == None:
                    self.winrect.p1 = gpos - self.dragDiff
                    self.reposControls()
                else:
                    self.btnCancel.handleMouseMove(pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    print("Escape key pressed down.")
                    self.waiting = False




    def handleCancel(self):
        """ If Cancel """
        self.cancel=True


