
import os
import pygame
from pygame.locals import *
from GUI import *

class MessageDialog():
    winrect=None
    titlerect=None
    margins=GRect(8,4,4,4)
    waiting=False
    dragDiff = None

    bordercolor=(0,0,0)
    titlebackcolor=(192,192,192)
    titletextcolor=(0,0,0)
    formcolor=(128,128,128)
    fontname = "Consolas"
    fontsize = 24
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
        self.btnOK.rect=GRect(self.winrect.x+self.winrect.width-self.margins.width-self.buttonWidth,self.footerTop+self.margins.x,self.buttonWidth,self.buttonHeight)

    def __init__(self, pyscreen, pos, title="Message Dialog",message="Read this carefully... \n ...before entering Ok!", dfontname=None,dfontsize=24,parentRedraw=None):
        self.pyscreen = pyscreen
        self.parentRedraw=parentRedraw
        self.winrect=GRect(pos[0], pos[1], 300, 160)
        self.title=title
        self.message=message
        self.font = pygame.font.SysFont(dfontname, dfontsize)
        width, height = self.font.size("MinimalText")
        self.titleheight=height+self.margins.y+self.margins.height

        self.footerTop = self.winrect.y + self.winrect.height - self.margins.height - self.footerHeight
        self.label=Label(pyscreen,text=message,fontname=dfontname,fontsize=dfontsize,rect=GRect(),autoheight=False,center=True,backcolor=self.formcolor)
        self.btnOK=Button(pyscreen,text="OK",func_on_click=self.handleOK, rect=GRect())
        self.reposControls()
        #todo: need two times to reorder lines correctly
        #self.reposControls()

        self.controls.append(self.label)
        self.controls.append(self.btnOK)


    def show(self):
        self.waiting=True
        self.waitforuser()

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
        self.label.redraw()
        self.btnOK.redraw()

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

    def handleOK(self):
        self.lastaction = "OK"
        self.waiting=False

