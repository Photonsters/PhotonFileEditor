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

class PopupDialog():
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
    btnOK=None
    titleheight=24
    footerHeight=40
    buttonHeight=28
    buttonWidth=64
    controls=[]


    def reposControls(self): #called after winrect is moved
        """ Recalculates all positions after moving dialog box. """
        self.titlerect = GRect(self.winrect.x, self.winrect.y, self.winrect.width, self.titleheight)
        self.footerTop = self.winrect.y + self.winrect.height - self.margins.height - self.footerHeight
        x=self.winrect.x+self.margins.x
        y=self.winrect.y + self.titleheight + self.margins.y
        w=self.winrect.width - self.margins.x - self.margins.width
        h=self.winrect.height - self.titleheight - self.margins.y - self.footerHeight- self.margins.height
        self.label.rect=GRect(x,y, w, h)
        self.label.setText(self.message)


    def __init__(self, pyscreen, pos, title="Message Dialog",message="Read this carefully... \n ...before entering Ok!", dfontname=defFontName, dfontsize=defFontSize):
        """ Saves all values to internal variables and calculates some extra internal vars. """
        self.pyscreen = pyscreen
        #self.parentRedraw=parentRedraw
        self.winrect=GRect(pos[0], pos[1], 300, 160)
        self.title=title
        self.message=message
        self.font = pygame.font.SysFont(dfontname, dfontsize)

        # Calculate extra variables
        dummy, textheight = self.font.size("MinimalText")
        self.titleheight=textheight +self.margins.y+self.margins.height
        self.footerTop = self.winrect.y + self.winrect.height - self.margins.height - self.footerHeight

        # Add GUI.Label
        self.label=Label(pyscreen,text=message,fontname=dfontname,fontsize=dfontsize,rect=GRect(),autoheight=False,center=True,backcolor=self.formcolor,autowrap=True)
        self.controls.append(self.label)

        # (Re)calculate remaining variables
        self.reposControls()


    def show(self):
        """ Just draw me. """
        self.redraw()


    def hide(self):
        """ Do nothing. """
        return


    def redraw(self):
        """ Redraws dialogbox. """

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

        # Draw message
        self.label.redraw()
        pygame.display.flip()



