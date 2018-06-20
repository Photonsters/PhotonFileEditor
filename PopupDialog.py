
import os
import pygame
from pygame.locals import *
from GUI import *

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
        self.titlerect = GRect(self.winrect.x, self.winrect.y, self.winrect.width, self.titleheight)
        self.footerTop = self.winrect.y + self.winrect.height - self.margins.height - self.footerHeight
        x=self.winrect.x+self.margins.x
        y=self.winrect.y + self.titleheight + self.margins.y
        w=self.winrect.width - self.margins.x - self.margins.width
        h=self.winrect.height - self.titleheight - self.margins.y - self.footerHeight- self.margins.height
        self.label.rect=GRect(x,y, w, h)
        self.label.setText(self.message)

    def __init__(self, pyscreen, pos, title="Message Dialog",message="Read this carefully... \n ...before entering Ok!", dfontname=defFontName, dfontsize=defFontSize):
        self.pyscreen = pyscreen
        #self.parentRedraw=parentRedraw
        self.winrect=GRect(pos[0], pos[1], 300, 160)
        self.title=title
        self.message=message
        self.font = pygame.font.SysFont(dfontname, dfontsize)
        width, height = self.font.size("MinimalText")
        self.titleheight=height+self.margins.y+self.margins.height

        self.footerTop = self.winrect.y + self.winrect.height - self.margins.height - self.footerHeight
        self.label=Label(pyscreen,text=message,fontname=dfontname,fontsize=dfontsize,rect=GRect(),autoheight=False,center=True,backcolor=self.formcolor,autowrap=True)
        self.reposControls()
        #todo: need two times to reorder lines correctly
        #self.reposControls()
        self.controls.append(self.label)


    def show(self):
        self.redraw()

    def hide(self):
        return

    def redraw(self):
        #draw form
        pygame.draw.rect(self.pyscreen, self.formcolor, self.winrect.tuple(), 0)
        #draw title bar
        pygame.draw.rect(self.pyscreen, self.titlebackcolor,self.titlerect.tuple(), 0)
        self.font.set_bold(True)
        textsurface = self.font.render(self.title, True, self.titletextcolor)
        self.pyscreen.blit(textsurface, (self.winrect.x + self.margins.x, self.winrect.y + self.margins.y))
        self.font.set_bold(False)
        #draw border
        pygame.draw.rect(self.pyscreen, self.bordercolor, self.winrect.tuple(), 1)

        # draw message
        self.label.redraw()
        pygame.display.flip()



