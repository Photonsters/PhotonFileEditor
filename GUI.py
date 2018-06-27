"""
Classes to draw GUI elements on the screen like buttons, menus, textboxes etc.
"""

__version__ = "alpha"
__author__ = "Nard Janssens, Vinicius Silva, Robert Gowans, Ivan Antalec, Leonardo Marques - See Github PhotonFileUtils"

import math
import time

import pygame
from pygame.locals import *

import GUIhelpers
from GUIhelpers import *

# Common constants which make up the Theme of the GUI
defFontName="Verdana"   #Fontname None will take default system font
defFontSize=16#24
defFormBackground=(232,232,232)
defFormForeground=(0,0,0)
defMenuBackground=defFormBackground
defMenuForeground=(0,0,0)
defHighMenuForeground=(255,255,255)
defHighMenuBackground=(68,123,213)
defHighSelectForeground=defHighMenuForeground
defHighSelectBackground=defHighMenuBackground
defEditorBackground=(255,255,255)
defEditorForeground=(0,0,0)
defHighEditorBackground=(255,255,12*16)
defHighEditorForeground=(0,0,0)
defTitlebarBackground=(215,215,215)
#defButtonBackground=(68,123,213)
defButtonBackground=(205,205,205)
defBorder=(173,173,173)
defBorderHover=defHighMenuBackground


########################################################################################################################
## Class MenuBar
########################################################################################################################

class MenuBar():
    menus=[]
    margins = GRect(4, 4, 4, 4)
    height = -1
    spacing = 4
    minwidth=50
    isVisible=True
    textcolor=defMenuForeground
    backcolor=defMenuBackground
    highbackcolor=defHighMenuBackground
    highforecolor=defHighMenuForeground
    bordercolor = defBorder
    activeMenu=None

    def __init__(self, pyscreen,fontname=defFontName, fontsize=defFontSize):
        """ Saves all values to internal variables. """
        self.pyscreen = pyscreen
        self.font = pygame.font.SysFont(fontname, fontsize)
        self.fontsize=fontsize #store to init menuitems
        self.fontname=fontname  #store to init menuitems

        # Enlarge menubar height if text does not fit
        height = self.font.get_linesize() * 0.5
        if (height + self.margins.y + self.margins.height) > self.height:
            self.height = height + self.margins.y + self.margins.height


    def addMenu(self, menutitle,shortcutChar):
        """ Adds new menu in the menubar (with empty menulist)."""

        # Determine left position of new menu
        prevIdx=len(self.menus)-1
        if prevIdx==-1:
            x=self.margins.x
        else:
            prevTitle = self.menus[prevIdx]["title"]
            prevLeft =self.menus[prevIdx]["left"]
            prevWidth = self.menus[prevIdx]["width"]#, height = self.font.size(prevTitle)
            #if prevWidth<self.minwidth: prevWidth=self.minwidth
            x= prevLeft+prevWidth#+ self.spacing
        scNr=0

        # Determine width of new menu
        width, height = self.font.size(menutitle)
        width=width+self.spacing
        if width<self.minwidth: width=self.minwidth+self.spacing

        # Get position of shortcutchar
        for idx,ch in enumerate(menutitle):
            if ch==shortcutChar:
                scNr=idx
        #print (scNr)

        # Make menulist
        loc=(x,self.height+self.margins.x+self.margins.height+1)
        menulist=MenuList(pyscreen=self.pyscreen,location=loc, fontname = self.fontname, fontsize = self.fontsize, title=menutitle)

        # Store (menu title, position, position of shortcutchar and menulist) in menudata
        menudata={"title":menutitle,"left":x,"width":width,"scChar":scNr, "menulist":menulist}
        self.menus.append(menudata)


    def addItem(self, menutitle, menuitem, func_on_click):
        """ Adds new item to menulist. """

        # Find menu in menus, retrieve menulist and add item
        for menu in self.menus:
            if menu["title"]==menutitle:
                menulist=menu["menulist"]
                menulist.addItem(menuitem,func_on_click)


    def redraw(self):
        """ Redraws MenuBar. """

        # If not visible, nothing to do
        if not self.isVisible: return

        # Draw menubar background and border.
        w, dummy = pygame.display.get_surface().get_size()
        h=self.height+self.margins.y+self.margins.height
        pygame.draw.rect(self.pyscreen, self.backcolor, (0,0,w,h), 0)
        pygame.draw.rect(self.pyscreen, self.bordercolor , (0, h, w, 1),1)

        for menudata in self.menus:
            menuleft = menudata["left"]
            menuwidth = menudata["width"]
            # Highlight current menu if mouse hovers and set textcolor depending if mouse hover or not.
            if menudata==self.activeMenu:
                #pygame.draw.rect(self.pyscreen, self.highbackcolor, (menuleft-self.spacing, 0,menuwidth, h), 0)
                pygame.draw.rect(self.pyscreen, self.highbackcolor, (menuleft, 0, menuwidth, h), 0)
                localtextcolor=defHighMenuForeground
            else:
                localtextcolor=defMenuForeground

            # Shortcut letter should be underlines, so we cut menu title in different parts for regular and underline
            scNr=menudata["scChar"]
            preStr=menudata["title"][:scNr]
            scStr=menudata["title"][scNr:scNr+1]
            postStr = menudata["title"][scNr + 1:]
            #print (scNr,preStr,scStr,postStr)
            wPre, dummy = self.font.size(preStr)
            wSc, dummy = self.font.size(scStr)
            wPost, dummy = self.font.size(postStr)

            # Draw text before shorcut Char
            self.font.set_underline(False)
            textsurface = self.font.render(preStr, True, localtextcolor)
            self.pyscreen.blit(textsurface, (menuleft+self.margins.x, self.margins.y))

            # Draw shorcut Char
            self.font.set_underline(True)
            textsurface = self.font.render(scStr,True, localtextcolor)
            self.pyscreen.blit(textsurface, (menuleft+self.margins.x +wPre, self.margins.y))

            # Draw text after shorcut Char
            self.font.set_underline(False)
            textsurface = self.font.render(postStr, True, localtextcolor)
            self.pyscreen.blit(textsurface, (menuleft+self.margins.x+wPre+wSc, self.margins.y))

            menudata["menulist"].redraw()


    def handleMouseDown(self, pos,button):
        """ Updates menu states if user clicked on menubar. """

        # If not clicked, nothing to do
        if not button == 1: return

        # Check if mouse clicked within menubar area
        if pos[1]<=(self.height+self.margins.y+self.margins.height):
            # We are handling this so clear queue for others
            pygame.event.clear()

            # If menu visible/active then hide menu, else show
            if self.activeMenu==None:
                for menu in self.menus:
                    if pos[0]>menu["left"] and pos[0]<(menu["left"]+menu["width"]):
                        self.activeMenu=menu
                        menulist=menu["menulist"]
                        menulist.isVisible=True
                    else:
                        menulist = menu["menulist"]
                        menulist.isVisible = False
                return True
            else:
                self.activeMenu["menulist"].isVisible=False
                self.activeMenu=None
                return

        # Call upon menulists to handle mouse (if above menulists). """
        for menu in self.menus:
            if menu["menulist"].handleMouseDown(pos,button): return True


    def handleMouseUp(self, pos,button):
        """ Updates menu states if user clicked on menubar. """
        if not button == 1: return
        # Call upon menulists to handle mouse (if above menulists). """
        for menu in self.menus:
            # If menulist accepts MouseUp we can close menulist and active item in menubar
            if menu["menulist"].handleMouseUp(pos,button):
                # We are handling this so clear queue for others
                pygame.event.clear()
                self.activeMenu["menulist"].isVisible = False
                self.activeMenu = None
                return True

        # If we are below menubar and nothing in menulists (not returned True) then user clicks on workarea of window to hide all menus
        if pos[1]>=(self.height+self.margins.y+self.margins.height):
            if self.activeMenu:
                # We are handling this so clear queue for others
                pygame.event.clear()
                self.activeMenu["menulist"].isVisible=False
                self.activeMenu=None


    def handleMouseMove(self, pos):
        """ Switch open menu if in menubar else call upon menulists to handle mouse (if above menulists). """
        # Move activemenu if mouse is moving within menubar area and menu is active
        if pos[1] <= (self.height + self.margins.y + self.margins.height):
            if not self.activeMenu == None:
                for menu in self.menus:
                    if pos[0] > menu["left"] and pos[0] < (menu["left"] + menu["width"]):
                        self.activeMenu = menu
                        menulist = menu["menulist"]
                        menulist.isVisible = True
                    else:
                        menulist = menu["menulist"]
                        menulist.isVisible = False
                # We are handling this so clear queue for others
                pygame.event.clear()
                return True

        # Let menulist check if mouse moved within their areas
        for menu in self.menus:
            if menu["menulist"].handleMouseMove(pos): return True


    def handleKeyDown(self,key,unicode):
        isAlt = (pygame.key.get_mods() & pygame.KMOD_ALT)
        if isAlt:
            for menu in self.menus:
                scNr=menu["scChar"]
                title=menu["title"]
                scChr=title[scNr]
                scNr=ord(scChr)-ord("A")
                keyNr=key-pygame.K_a
                if keyNr == scNr:
                    self.activeMenu=menu
                    menulist=menu["menulist"]
                    menulist.isVisible=True
                else:
                    menulist = menu["menulist"]
                    menulist.isVisible = False
                # We are handling this so clear queue for others
                pygame.event.clear()

    def openMenu(self,menutitle):
        """ Opens menu. """
        for idx,(title, shortcutChar, items, state) in enumerate(self.menus):
            if title == menutitle:
                self.menus[idx][3]= True
            else:
                self.menus[idx][3] = False


########################################################################################################################
## Class MenuList
########################################################################################################################

class MenuList():
    title=""
    pos=GRect(0, 0, 0, 0)
    items=[]
    margins=GRect(4, 4, 4, 4)
    rowheight=0
    spacing=4
    activeItem=-1
    isVisible=False
    textcolor = defMenuForeground
    backcolor = defMenuBackground
    highbackcolor = defHighMenuBackground
    highforecolor = defHighMenuForeground
    bordercolor = defBorder
    activeItem=-1


    def __init__(self, pyscreen, location, margins=GRect(6, 6, 6, 6), fontname=defFontName, fontsize=defFontSize, title="unknown"):
        """ Saves all values to internal variables. """
        self.pyscreen = pyscreen
        l_x = location[0]
        l_y = location[1]-1
        self.margins=margins
        self.font = pygame.font.SysFont(fontname, fontsize)
        self.title=title
        self.items=[]

        # Enlarge width and height if text does not fit
        width, height = self.font.size("MinimalText")
        l_width = width + self.margins.x + self.margins.width
        l_height= 1*height++ self.margins.y + self.margins.height
        self.pos=GRect(l_x,l_y,l_width,l_height)
        self.rowheight = height


    def addItem(self,menuitem,func_on_click):
        """ Add menulist item and adjust menulist height and width (if needed) """
        #Add item
        itemdata = (menuitem,func_on_click)
        self.items.append(itemdata)

        # Adjust height and width only if needed
        width, height = self.font.size(menuitem)
        if (width+self.margins.x+self.margins.width) >self.pos.width: self.pos.width=width+self.margins.x+self.margins.width
        self.pos.height= len(self.items)*(self.rowheight+self.spacing)+ self.margins.y + self.margins.height-self.spacing # extract 1x spacing at the bottom


    def redraw(self):
        """ Redraws MenuList. """

        # If not visible nothing to do
        if not self.isVisible:
            self.activeItem=-1 # so on reopening we don have floating cursor
            return

        # Draw background and border
        pygame.draw.rect(self.pyscreen, self.backcolor, self.pos.tuple (), 0)
        pygame.draw.rect(self.pyscreen, self.bordercolor, (self.pos.tuple()), 1)

        # Draw item text
        for row,(text,func_on_click) in enumerate(self.items):
            rowtop=self.pos.y+self.margins.y+row*(self.rowheight+self.spacing)
            if row==self.activeItem:
                pygame.draw.rect(self.pyscreen, self.highbackcolor,(self.pos.x+self.margins.x, rowtop-int(self.spacing/2), self.pos.width-self.margins.x-self.margins.width, self.rowheight), 0)
                localtextcolor = defHighMenuForeground
            else:
                localtextcolor = defMenuForeground
            textsurface = self.font.render(text,True, localtextcolor)
            self.pyscreen.blit(textsurface, (self.pos.x+self.margins.x, rowtop))


    def handleMouseMove(self, pos):
        """ Highlights menulist item if mouse hover above."""
        if not self.isVisible: return

        if pos[0] > self.pos.x and pos[0] < (self.pos.x+self.pos.width) and \
            pos[1] < (self.pos.y + self.pos.height):
            rely=pos[1]-self.pos.y
            self.activeItem=int((rely-self.margins.y)/(self.rowheight+self.spacing))
            # We are handling this so clear queue for others
            pygame.event.clear()
            return True


    def handleMouseDown(self, pos,button):
        return

    def handleMouseUp(self, pos,button):
        """ Calls on user function if clicked on menu item."""
        if not button == 1: return
        if not self.isVisible: return
        gpos=GPoint.fromTuple(pos)
        if gpos.inGRect(self.pos):
            # We are handling this so clear queue for others
            pygame.event.clear()
            for row, (item, func_on_click) in enumerate(self.items):
                if row == self.activeItem:
                    if not func_on_click==None:
                        func_on_click()
                        self.isVisible=False
                        return True


########################################################################################################################
## Class ImgBox
########################################################################################################################

class ImgBox():
    rect=GRect()
    img=None
    hoverimg=None
    hoverActive=False
    action=None
    visible=True
    drawBorder=False
    resizeto=GPoint()

    #Tooltip vars
    toolTipLabel=None
    firstHoverTime = 0
    firstHoverPos=GPoint(0,0)

    def __init__(self, pyscreen, filename,filename_hover=None, pos=(0,0),bordercolor=defBorder,borderhovercolor=defBorderHover,drawBorder=False,
                 toolTip="",
                 resizeto=None,func_on_click=None):
        """ Saves all values to internal variables. """
        self.pyscreen = pyscreen
        self.bordercolor = bordercolor
        self.borderhovercolor=borderhovercolor
        self.drawBorder=drawBorder
        self.func_on_click=func_on_click

        # Load image and resize to fit
        self.img=pygame.image.load(filename)
        if not filename_hover==None:
            self.hoverimg = pygame.image.load(filename_hover)

        # If user want other size we try to resize
        try:
            if not resizeto == None:
                self.img=pygame.transform.scale(self.img, resizeto)
                if not filename_hover==None:
                    self.hoverimg = pygame.transform.scale(self.hoverimg, resizeto)
        except Exception as err:
            print(err)

        # Determine size of control based on image size
        imgrect=self.img.get_rect()
        self.rect=GRect(imgrect[0],imgrect[1],imgrect[2],imgrect[3])
        self.rect.x=pos[0]
        self.rect.y=pos[1]

        #And setup tooltip
        # We need to figure out the correct width correct width of tooltip
        if not toolTip=="":
            self.toolTipLabel = Label(pyscreen, rect=GRect(self.rect.right, self.rect.height, 1024, 20),
                                      text=toolTip, drawBorder=True, borderwidth=1, backcolor=defHighEditorBackground,
                                      fontsize=defFontSize-2,
                                      textcolor=defHighEditorForeground, autowrap=True)
            max_width=0
            for line in toolTip.split("\n"):
                text_width, text_height = self.toolTipLabel.font.size(line)  # needed for self.autoheight
                if text_width>max_width: max_width=text_width
            self.toolTipLabel.rect.width=max_width+self.toolTipLabel.margin.x+self.toolTipLabel.margin.width
            self.toolTipLabel.visible=False


    def redraw(self):
        """ Redraws ImgBox. """

        # If not visible nothing to do.
        if not self.visible: return

        # Draw Image to screen
        self.pyscreen.blit(self.img,self.rect.tuple())

        # On hover draw hover image available
        if self.hoverActive and not self.hoverimg==None:
            self.pyscreen.blit(self.hoverimg, self.rect.tuple())
        else:
            self.pyscreen.blit(self.img, self.rect.tuple())

        # On hover drawborder if drawBorder is True
        if self.drawBorder:
            if self.hoverActive:
                pygame.draw.rect(self.pyscreen,self.borderhovercolor, self.rect.tuple(), 1)
            else:
                pygame.draw.rect(self.pyscreen, self.bordercolor, self.rect.tuple(), 1)

    def handleMouseMove(self, pos):
        """ Updates state of ImgBox on hover. """
        gpos=GPoint(pos[0],pos[1])
        if gpos.inGRect(self.rect):
            self.hoverActive=True
            # We are handling this so clear queue for others
            pygame.event.clear()
        else:
            self.hoverActive=False

    def handleMouseUp(self, pos,button):
        """ Calls on user function if clicked."""
        if not button==1: return
        gpos = GPoint(pos[0], pos[1])
        if gpos.inGRect(self.rect):
            # We are handling this so clear queue for others
            pygame.event.clear()
            if not self.func_on_click==None:
                self.func_on_click()

    def handleMouseDown(self,pos,button):
        return

    def handleKeyDown(self,key,unicode):
        return


    def handleToolTips(self,pos):
        """ Returns label control with tooltip if hovered long enough. """
        # if user did not set a tooltip nothing to do
        if self.toolTipLabel==None: return None

        #Check if mouse above control, if not exit
        gpos=GPoint.fromTuple(pos)
        if not gpos.inGRect(self.rect):
            self.firstHoverTime=0
            self.firstHoverPos=GPoint(0,0)
            self.toolTipLabel.visible = False
            return None

        #Check if first time hovering, if so set timer
        if self.firstHoverTime==0:
            self.firstHoverPos=gpos
            self.firstHoverTime=time.time()

        #Check if moved since hovering, if so reset counter and exit
        dif=self.firstHoverPos-gpos
        if math.sqrt(dif.x*dif.x+dif.y*dif.y)>5:
            self.firstHoverPos=GPoint(0,0)
            self.firstHoverTime=0
            self.toolTipLabel.visible = False
            return None

        #Check if hovered enough time and return tooltip
        timeHovered=time.time()-self.firstHoverTime
        if timeHovered>1.5 and not self.toolTipLabel.text=="" :
            self.toolTipLabel.visible=True
            self.toolTipLabel.rect.x = gpos.x
            self.toolTipLabel.rect.y = gpos.y
            #check if tooltip overflow right edge of pyscreen
            if self.toolTipLabel.rect.right>self.pyscreen.get_size()[0]:
                self.toolTipLabel.rect.x=gpos.x-self.toolTipLabel.rect.width
            return self.toolTipLabel


########################################################################################################################
## Class Button
########################################################################################################################

class Button():
    # We need 3 buttonstates so boolean var does not suffice
    normal=0
    hover=1
    down=2
    state= False

    rect=None
    img=None
    hoverimg=None
    downimg = None
    action=None
    borderwidth=1
    visible=True

    def __init__(self, pyscreen, rect=GRect(0,0,60,40),text="Button",  textcolor=(0,0,0),fontname=defFontName, fontsize=defFontSize, backcolor=defButtonBackground,filename=None,filename_hover=None,filename_down=None, bordercolor=defBorder, borderhovercolor=defBorderHover,func_on_click=None):
        """ Saves all values to internal variables. """
        self.pyscreen = pyscreen
        self.text=text
        self.textcolor=textcolor
        self.font = pygame.font.SysFont(fontname, fontsize)
        text_width, text_height = self.font.size(text)
        self.twidth=text_width
        self.theight=text_height
        self.bordercolor = bordercolor
        self.borderhovercolor=borderhovercolor
        self.backcolor=backcolor
        self.func_on_click=func_on_click
        if func_on_click==None: print ("None")

        if not filename_hover==None:
            self.hoverimg = pygame.image.load(filename_hover)
        if not filename_down==None:
            self.downimg = pygame.image.load(filename_down)

        # If button is image than dimensions are determined by image size
        if not filename == None:
            self.img = pygame.image.load(filename)
            imgrect = self.img.get_rect()
            self.rect=GRect(rect.x,rect.y,imgrect[2],imgrect[3])
        # Otherwise we listen to the dimensions the user gave us
        else:
            self.rect=rect


    def redraw(self):
        """ Redraws Button. """

        # If not visible nothing to do.
        if not self.visible: return

        # Draw image (if available) corresponding to button state
        if self.state==self.hover and not self.hoverimg==None:
            self.pyscreen.blit(self.hoverimg, self.rect.tuple())
        elif self.state==self.down and not self.downimg==None:
            self.pyscreen.blit(self.downimg, self.rect.tuple())
        elif not self.img==None:
            if self.state==self.down:#shift image if down
                self.pyscreen.blit(self.img, (self.rect.x + self.borderwidth, self.rect.y + self.borderwidth))
            else:
                self.pyscreen.blit(self.img, self.rect.tuple())
        else:
            pygame.draw.rect(self.pyscreen, self.backcolor,self.rect.tuple(), 0)

        # Draw border (if available) corresponding to button state
        if self.borderwidth>0:
            if self.borderwidth == 1:
                if self.state==self.down or self.state==self.hover:
                    pygame.draw.rect(self.pyscreen, self.borderhovercolor, self.rect.tuple(), 1)
                else:
                    pygame.draw.rect(self.pyscreen, self.bordercolor, self.rect.tuple(), 1)
            else:#make 3d border
                if self.state==self.down:
                    topleftcolor=(64,64,64)
                    bottomrightcolor=(192,192,192)
                else:
                    topleftcolor = (192, 192, 192)
                    bottomrightcolor = (64, 64, 64)
                for inset in range (0,self.borderwidth):
                    #top and left border
                    pygame.draw.rect(self.pyscreen, topleftcolor, (self.rect.x,self.rect.y+inset,self.rect.width-inset,1), 1)
                    pygame.draw.rect(self.pyscreen, topleftcolor, (self.rect.x+inset, self.rect.y, 1, self.rect.height-inset), 1)
                    #bottom en right border
                    pygame.draw.rect(self.pyscreen, bottomrightcolor, (self.rect.x+inset,self.rect.y+self.rect.height-inset,self.rect.width-inset,1), 1)
                    pygame.draw.rect(self.pyscreen, bottomrightcolor, (self.rect.x+self.rect.width-inset, self.rect.y+inset, 1, self.rect.height-inset), 1)

        # Draw text (if available) and shift text if down
        if not self.text=="":
            textsurface = self.font.render(self.text, True,self.textcolor)
            dx=int(self.rect.width-self.twidth)/2
            dy=int(self.rect.height-self.theight)/2
            if self.state == self.down:  # shift text if down
                dx=dx+self.borderwidth
                dy=dy+self.borderwidth
            self.pyscreen.blit(textsurface, (self.rect.x + dx, self.rect.y+dy))

    def handleMouseMove(self, pos):
        """ Updates state of Button on hover. """
        gpos=GPoint(pos[0],pos[1])
        if gpos.inGRect(self.rect):
            self.state=self.hover
            # We are handling this so clear queue for others
            pygame.event.clear()
        else:
            self.state=self.normal
        #print (self.state)

    def handleMouseUp(self, pos,button):
        """ Calls on user function if clicked."""
        if not button == 1: return
        gpos=GPoint(pos[0],pos[1])
        if gpos.inGRect(self.rect):
            self.state=self.normal
            # We are handling this so clear queue for others
            pygame.event.clear()
            if not self.func_on_click==None:
                self.func_on_click()

    def handleMouseDown(self,pos,button):
        """ Updates state of Button on down. """
        if not button == 1: return
        gpos=GPoint(pos[0],pos[1])
        if gpos.inGRect(self.rect):
            # We are handling this so clear queue for others
            pygame.event.clear()
            self.state=self.down

    def handleKeyDown(self,key,unicode):
        return


########################################################################################################################
## Class ScrollBarV
########################################################################################################################

class ScrollBarV():
    # We need 3 buttonstates so boolean var does not suffice
    normal=0
    hover=1
    down=2
    state= False

    rect = None
    action = None
    borderwidth = 1
    visible = True

    #todo: replace forecolor with def constant
    def __init__(self, pyscreen, rect=GRect(0, 0, 60, 40), forecolor=(0,0,0), sfontsize=defFontSize, sbackcolor=defButtonBackground, sbordercolor=defBorder, sborderhovercolor=defBorderHover, func_on_click=None,minScroll=0, maxScroll=128,curScroll=0,smallScroll=1, largeScroll=8):
        """ Saves all values to internal variables. """
        self.pyscreen = pyscreen
        self.rect=rect
        self.bordercolor = sbordercolor
        self.borderhovercolor = sborderhovercolor
        self.backcolor = sbackcolor
        self.forecolor=forecolor
        self.func_on_click = func_on_click
        self.minScroll=minScroll
        self.maxScroll=maxScroll
        self.curScroll = curScroll
        self.smallScroll=smallScroll
        self.largeScroll=largeScroll

        # Add up and down button
        self.btnUp = Button(pyscreen, text="^", bordercolor=sbordercolor, borderhovercolor=sborderhovercolor,
                            textcolor=forecolor, func_on_click=self.scrollUp)
        self.btnDown = Button(pyscreen, text="v", bordercolor=sbordercolor, borderhovercolor=sborderhovercolor,
                              textcolor=forecolor, func_on_click=self.scrollDown)


    def scrollDown(self,isLargeScroll=False):
        """ Decreases current scroll value. """

        # Check if we have to take a small step or a large step
        if not isLargeScroll:
            self.curScroll=self.curScroll+self.smallScroll
        else:
            self.curScroll = self.curScroll + self.largeScroll
        if self.curScroll>self.maxScroll: self.curScroll=self.maxScroll

        # Send curScroll to parent
        if not self.func_on_click ==None: self.func_on_click(self.curScroll)
        #print("scroll Up: ",self.curScroll)


    def scrollUp(self,isLargeScroll=False):
        """ Inreases current scroll value. """

        # Check if we have to take a small step or a large step
        if not isLargeScroll:
            self.curScroll = self.curScroll - self.smallScroll
        else:
            self.curScroll=self.curScroll - self.largeScroll
        if self.curScroll < self.minScroll: self.curScroll = self.minScroll

        # Send curScroll to parent
        if not self.func_on_click==None: self.func_on_click(self.curScroll)
        #print("scroll Down: ", self.curScroll, isLargeScroll, self.smallScroll)


    def redraw(self):
        """ Redraws ScrollBarV. """

        # If not visible nothing to do.
        if not self.visible: return

        # Position up and down buttons
        self.btnUp.rect= GRect(self.rect.x, self.rect.y, self.rect.width, self.rect.width)
        self.btnDown.rect = GRect(self.rect.x, self.rect.y + self.rect.height - self.rect.width, self.rect.width, self.rect.width)

        # Draw background
        pygame.draw.rect(self.pyscreen, self.backcolor, self.rect.tuple(), 0)

        # Determine scroll area between up and down buttons
        innerRect=self.rect.copy()
        innerRect.y=self.rect.y+self.btnUp.rect.height
        innerRect.height=self.rect.height-self.btnUp.rect.height-self.btnDown.rect.height

        # Determine at what percentage of this area we clicked
        indYrel=(self.curScroll-self.minScroll)/(self.maxScroll-self.minScroll)
        #indY=innerRect.bottom-indYrel*innerRect.height
        indY=innerRect.top+indYrel*innerRect.height

        # Draw indicator at the height we clicked.
        indRect=self.rect.copy()
        indRect.y=indY-1
        indRect.height=3
        pygame.draw.rect(self.pyscreen, self.forecolor, indRect.tuple(), 0)

        # Draw border depending on state of ScrollbarV.
        if self.borderwidth == 1:
            if self.state == self.down or self.state == self.hover:
                pygame.draw.rect(self.pyscreen, self.borderhovercolor, self.rect.tuple(), 1)
            else:
                pygame.draw.rect(self.pyscreen, self.bordercolor, self.rect.tuple(), 1)

        # Call upon up and down buttons to redraw themselves
        self.btnDown.redraw()
        self.btnUp.redraw()


    def handleMouseMove(self, pos):
        """ Updates state of Scroll Area and Up and Down buttons on hover. """
        gpos=GPoint(pos[0],pos[1])
        if gpos.inGRect(self.rect):
            # We are handling this so clear queue for others
            pygame.event.clear()
            self.state=self.hover
        else:
            self.state=self.normal

        # Call upon buttons to check if MouseMove (hover) above them
        self.btnUp.handleMouseMove(pos)
        self.btnDown.handleMouseMove(pos)

    def handleMouseUp(self, pos,button):
        """ Transmits MouseUp to up and down button. """

        #If not left mousebutton then nothing to do
        if not button == 1: return

        # Call upon buttons to check for MouseUp above them
        self.btnUp.handleMouseUp(pos,button)
        self.btnDown.handleMouseUp(pos, button)

    def handleMouseDown(self,pos,button):
        """ Updates state of Scroll Area and Up and Down buttons on mousedown. """

        #If not left mousebutton then nothing to do
        if not button == 1: return

        #Check if in rect
        gpos=GPoint(pos[0],pos[1])
        if not gpos.inGRect(self.rect): return

        # We are handling this so clear queue for others
        pygame.event.clear()

        # Set state if clicked within area
        self.state=self.down

        # Determine scroll area between up and down buttons
        innerRect = self.rect.copy()
        innerRect.y = self.rect.y + self.btnUp.rect.height
        innerRect.height = self.rect.height - self.btnUp.rect.height - self.btnDown.rect.height

        # Check if mouseclick inside scroll area
        if gpos.inGRect(innerRect):
            # Determine at what screen position the scroll indicator is.
            indYrel = (self.curScroll - self.minScroll) / (self.maxScroll - self.minScroll)
            indY = innerRect.top + indYrel * innerRect.height
            # If clicked above indicator we scroll up and vice versa
            if gpos.y > indY: self.scrollDown(True)
            if gpos.y < indY: self.scrollUp(True)

        # Call upon buttons to check for MouseDown above them
        self.btnUp.handleMouseDown(pos, button)
        self.btnDown.handleMouseDown(pos, button)

    def handleKeyDown(self,key,unicode):
        return


########################################################################################################################
## Class ListBox
########################################################################################################################

class ListBox():
    items=[]
    rect = GRect(0, 0, 80, 32)
    margins = GRect(4, 4, 4, 4)
    bordercolor = (128, 128, 128)
    backcolor = defEditorBackground
    textcolor = defEditorForeground
    highbackcolor = defHighSelectBackground
    hightextcolor = defHighSelectForeground
    font=None
    fontname = "Consolas"
    fontsize = 16
    activeItem=-1
    rowheight=0
    spacing=4
    offset=0
    visible=True

    def __init__(self, pyscreen, rect=GRect(100, 40, 80, 80), items=None,fontname=defFontName, fontsize=defFontSize,func_on_click=None):
        """ Saves all values to internal variables. """
        self.pyscreen = pyscreen
        self.rect=rect
        self.items=items
        self.font = pygame.font.SysFont(fontname, fontsize)
        text_width, text_height = self.font.size("M[].j")
        self.rowheight=text_height
        self.items=items
        if not func_on_click==None: self.func_on_click=func_on_click

        # Resize ListBox so the height is a full number of rows
        self.nritems = int(self.rect.height / (self.rowheight + self.spacing))
        self.rect.height=self.nritems*(self.rowheight + self.spacing)

        # Add scrollbar
        self.scrollbarV=ScrollBarV(pyscreen,func_on_click=self.scrollItems)


    def setItems(self, items):
        """ Update items in ListBox """
        self.items=items
        self.offset=0
        self.activeItem=-1


    def items(self):
        """ Return items in ListBox """
        return self.items


    def scrollItems(self,curScroll):
        """ Sets first listitem to show ListBox to curScroll"""
        self.offset=curScroll


    def redraw(self):
        """ Redraws ListBox. """

        # If not visible nothing to do.
        if not self.visible: return

        # Draw background and border
        pygame.draw.rect(self.pyscreen, self.backcolor, self.rect.tuple(), 0)
        pygame.draw.rect(self.pyscreen, self.bordercolor, self.rect.tuple(),1)

        # If no items to display nothing to do.
        if self.items==None: return

        #set Scrollbar so if listbox is moved or listitems are added/removed, the scrollbar is still correct.

        # Resize ListBox so the height is a full number of rows
        self.nritems = int(self.rect.height / (self.rowheight + self.spacing))
        self.rect.height = self.nritems * (self.rowheight + self.spacing)

        # Draw all items beginning with with offset determined by curScroll of scrollbarV
        for row in range(0,self.nritems):
            idx=row+self.offset
            if idx<len(self.items):
                item=self.items[idx]
                rowtop = self.rect.y + self.margins.y + row * (self.rowheight + self.spacing)
                if idx==self.activeItem:
                    pygame.draw.rect(self.pyscreen, self.highbackcolor,(self.rect.x+self.margins.x, rowtop-int(self.spacing/2), self.rect.width-self.margins.x-self.margins.width, self.rowheight), 0)
                    textsurface = self.font.render(item, True, self.hightextcolor)
                else:
                    textsurface = self.font.render(item, True, self.textcolor)
                self.pyscreen.blit(textsurface, (self.rect.x + self.margins.x, self.rect.y + self.margins.y+row*(self.rowheight+self.spacing)),(0,0,self.rect.width,self.rowheight+self.spacing))

        # Position scrollbar and call upon scrollbarV to redraw itself
        scrollRect = self.rect.copy()
        scrollRect.width = self.fontsize
        scrollRect.x = self.rect.right - scrollRect.width
        self.scrollbarV.rect=scrollRect
        self.scrollbarV.maxScroll = len(self.items)-self.nritems
        self.scrollbarV.largeScroll = self.nritems
        self.scrollbarV.visible = True if (len(self.items) > self.nritems) else False
        self.scrollbarV.redraw()


    def activeText(self):
        """ Returns the selected item in ListBox. """
        try:
            return self.items[self.activeItem]
        except:
            print ("Error from ListBox.activeText()")
            return ""


    def handleMouseDown(self,pos,button):
        """ Handles scroll with mousewheel and mousedown on item in ListBox. """

        # Check if we clicked inside the area where the items are displayed
        gpos=GPoint.fromTuple(pos)
        innerRect=self.rect.copy()
        if self.scrollbarV.visible: innerRect.width=innerRect.width-self.scrollbarV.rect.width
        if gpos.inGRect(innerRect):
            # Mousedown on item, store it in activeItem
            if button == 1:
                rely=pos[1]-self.rect.y
                self.activeItem=self.offset+ int((rely-self.margins.y)/(self.rowheight+self.spacing))
                #print ("down on: ", self.activeItem,self.activeText())
            # Mousewheel UP, so scroll up by setting offset (first item to be displayed)
            if button==4: # mousewheel up
                self.offset=self.offset-1
                if self.offset<0: self.offset=0
                self.scrollbarV.curScroll = self.offset # Tell scrollBarV our new position.
            # Mousewheel Down, so scroll down by setting offset (first item to be displayed)
            if button==5:
                self.offset = self.offset + 1
                if self.offset>(len(self.items)-self.nritems): self.offset=len(self.items)-self.nritems
                self.scrollbarV.curScroll = self.offset # Tell scrollBarV our new position.
            # We are handling this so clear queue for others
            pygame.event.clear()
        # Else ask to check if clicked on scrollbarV
        else:
            self.scrollbarV.handleMouseDown(pos,button)


    def handleMouseUp(self,pos,button):
        """ Calls on user function if clicked."""

        # Check if we clicked with left mouse button
        if not button == 1: return

        # Check if we clicked inside the area where the items are displayed
        gpos=GPoint.fromTuple(pos)
        innerRect=self.rect.copy()
        if self.scrollbarV.visible: innerRect.width=innerRect.width-self.scrollbarV.rect.width
        if gpos.inGRect(innerRect):
            # We are handling this so clear queue for others
            pygame.event.clear()
            if not self.func_on_click==None: self.func_on_click(self.activeText())
        else:
            # Else ask to check if clicked on scrollbarV
            self.scrollbarV.handleMouseUp(pos,button)

    def handleMouseMove(self,pos):
        """ Calls upon scrollbarV to handle MouseMove if needed """
        self.scrollbarV.handleMouseMove(pos)
        return

    def handleKeyDown(self,key,unicode):
        return


########################################################################################################################
## Class Combobox
########################################################################################################################

class Combobox():
    items=[]
    rect = GRect(0, 0, 80, 32)
    margins = GRect(4, 4, 4, 4)
    font=None
    fontname = "Consolas"
    fontsize = 16
    activeItem=-1
    rowheight=0
    spacing=4
    offset=0
    visible=True
    text="" #stores text if clicked
    func_on_click=None

    def __init__(self, pyscreen, rect=GRect(100, 40, 80, 80), items=None,defitemnr=0,fontname=defFontName, fontsize=defFontSize,func_on_click=None):
        """ Saves all values to internal variables. """
        self.pyscreen = pyscreen
        self.rect=rect
        self.items=items
        self.font = pygame.font.SysFont(fontname, fontsize)
        text_width, text_height = self.font.size("M[].j")
        self.rowheight=text_height
        self.items=items
        if not func_on_click==None: self.func_on_click=func_on_click

        #Combobox is made up of Label, Button to show Listbox and Listbox itself
        fname=fontname
        fsize=fontsize

        # Calc positions
        labelRect=GRect(rect.left,rect.top,rect.width-rect.height,rect.height)
        buttonRect=GRect(rect.right-rect.height,rect.top,rect.height,rect.height)
        listboxRect=GRect(rect.left,rect.bottom,rect.width,120)
        # Add Label
        defitem=items[defitemnr]
        self.label=Label(pyscreen,rect=labelRect,text=defitem,fontname=fname,fontsize=fsize,autowrap=False)
        self.label.backcolor=defEditorBackground
        self.label.textcolor=defEditorForeground
        self.label.bordercolor=defBorder
        self.label.borderwidt=1
        self.label.drawBorder=True
        labelRect=self.label.rect
        # Label will resize itself in height
        self.label.rect.width=rect.width-self.label.rect.height
        buttonRect.height=self.label.rect.height
        buttonRect.left=self.label.rect.right
        buttonRect.width=self.label.rect.height
        listboxRect.top=labelRect.bottom
        # Add Button
        self.button=Button(pyscreen,rect=buttonRect,text="V",fontname=fname,fontsize=fsize,func_on_click=self.buttonClick)
        # Add Listbox
        self.listbox=ListBox(pyscreen,rect=listboxRect,items=items,fontname=fname,fontsize=fsize,func_on_click=self.listClick)

        # Initially combobox is not expanded / listbox is not visible
        self.listbox.visible=False

    """ 
    def reposControls(self): #called after winrect is moved
        # Recalculates all positions after moving dialog box. 
        rect=self.rect
        #buttons is as wide as height
        labelRect=GRect(rect.left,rect.top,rect.width-rect.height,rect.height)
        buttonRect=GRect(rect.right-rect.height,rect.top,rect.height,rect.height)
        listboxRect=GRect(rect.left,rect.bottom,rect.width,40)
        self.button.rect=buttonRect
        self.label.rect=labelRect
        #todo: listbox below label, but this should depend on room
        self.listbox.rect=listboxRect
    """

    def redraw(self):
        self.label.redraw()
        self.button.redraw()
        self.listbox.redraw()


    def listClick(self,clickedtext):
        print (clickedtext,self.listbox.activeText())
        self.label.setText(clickedtext)
        self.listbox.visible=False
        self.text=clickedtext
        if not self.func_on_click==None: self.func_on_click(clickedtext)

    def buttonClick(self):
        self.listbox.visible= not self.listbox.visible


    def handleMouseUp(self,pos,button):
        """ Passes event to children. """
        if not self.visible: return
        # Pass event to children
        self.listbox.handleMouseUp(pos,button)
        self.button.handleMouseUp(pos,button)
        self.label.handleMouseUp(pos,button)


    def handleMouseDown(self,pos,button):
        """ Passes event to children. """
        if not self.visible: return
        # Pass event to children
        self.listbox.handleMouseDown(pos,button)
        self.button.handleMouseDown(pos,button)
        self.label.handleMouseDown(pos,button)


    def handleMouseMove(self,pos):
        """ Passes event to children. """
        if not self.visible: return
        # Pass event to children
        self.listbox.handleMouseMove(pos)
        self.button.handleMouseMove(pos)
        self.label.handleMouseMove(pos)

    def handleKeyDown(self,key,unicode):
        """ Passes event to children. """
        if not self.visible: return
        # Pass event to children
        self.listbox.handleKeyDown(key,unicode)
        self.button.handleKeyDown(key,unicode)
        self.label.handleKeyDown(key,unicode)

########################################################################################################################
## Class Label
########################################################################################################################

class Label():
    rect=GRect(0, 0, 80, 32)
    margin = GRect(4, 4, 4, 4)
    innerRect=GRect()
    bordercolor = (128, 128, 128)
    backcolor = defFormBackground
    textcolor = defFormForeground
    borderwidth = 1
    autoheight=True
    text = ["text"]
    font=None
    fontname = "Consolas"
    fontsize = 16
    drawBorder=False
    visible=True
    center=False
    autowrap=False
    istransparent=False


    def __init__(self, pyscreen, rect=GRect(0, 0, 80, 32), margin=GRect(4, 4, 4, 4),
                 bordercolor=defBorder, backcolor=defFormBackground, textcolor=defFormForeground,
                 borderwidth=1, drawBorder=False,center=False,istransparent=False,
                 text="text", fontname=defFontName, fontsize=defFontSize, autoheight=True, autowrap=False):
        """ Saves all values to internal variables. """
        self.pyscreen = pyscreen
        self.rect = rect
        self.margin=margin
        self.center=center
        self.bordercolor=bordercolor
        self.backcolor=backcolor
        self.istransparent=istransparent
        self.textcolor=textcolor
        self.borderwidth=borderwidth
        self.autoheight=autoheight
        self.autowrap = autowrap
        self.font = pygame.font.SysFont(fontname, fontsize)
        self.setText(text)
        self.drawBorder=drawBorder

        # Make innerRect (available room for text itself) accounting for margins
        self.innerRect=rect.copy()
        self.innerRect.shrink(self.margin)


    def setText(self,text):
        """ Wraps received text if needed (autowrap=True. """

        # We want to make sure the text fully fits in the TextBox
        self.innerRect = self.rect.copy()
        self.innerRect.shrink(self.margin)

        if self.autowrap:
            # Split sentences on boundaries user inserted a.k.a. newline code '\n\
            lines=text.split("\n")
            # Make room for all the sentences
            newlines=[]
            # For each sentences check if it fits in text area width (innerRect.width)
            for line in lines:
                newline=""
                words=line.split(" ")
                # print ("["+line+"]")
                lastIdx=len(words)-1
                # print("------")
                # Add word for word until it overflows innerRect.width
                for idx,word in enumerate(words):
                    oldline=newline
                    newline=newline+word+" "
                    # Determine width of sentence with new word
                    text_width, text_height = self.font.size(newline)
                    # On overflow, we save current build sentence (oldLine) and begin a new sentence with current word (newLine)
                    if text_width>self.innerRect.width:
                        #todo: check for words which are longer than width, in which case oldline is empty
                        text_width > self.innerRect.width
                        newlines.append(oldline.strip())
                        newline = word + " "
                        # print("|"+ oldline.strip()+ "|")
                # Add newline to newlines array
                newlines.append(newline.strip())
            #print("|" + newline.strip() + "|")
            #print("------")
            #print ("Total result:")
            #print (newlines)
            self.text=newlines
        else:
            #If user doesn't want autowrap we just store his/her new text
            newlines = [text]
            self.text = newlines
            text_width, text_height = self.font.size(text) #needed for self.autoheight

        # If autoheight is set, we recalculate height of label depending on line height and number of sentences
        if self.autoheight:
            self.rect.height=len(self.text)*text_height+self.margin.y+self.margin.height


    def redraw(self):
        """ Redraws Label. """

        # If not visible nothing to do.
        if not self.visible: return

        # Determine area the text can be drawn accounting for margins
        self.innerRect=self.rect.copy()
        self.innerRect.shrink(self.margin)

        # If label is not transparent then we draw background
        if not self.istransparent:
            pygame.draw.rect(self.pyscreen, self.backcolor, self.rect.tuple(), 0)
            if self.drawBorder: pygame.draw.rect(self.pyscreen, self.bordercolor, self.rect.tuple(), self.borderwidth)

        # If user want vertical center we determine the offset (dY) the text should be drawn in the label area
        dummy, lineHeight = self.font.size(self.text[0])
        if self.center:
            dY=int((self.innerRect.height-len(self.text)*lineHeight)/2)
        else: dY=0

        # Draw line by line and center if use set this to True
        for row,line in enumerate(self.text):
            if len(line)>255: line=line[0:255] # really a debug statement
            textsurface = self.font.render(line, True, self.textcolor)
            lineWidth, dummy= self.font.size(line)
            if self.center:
                dX = int((self.innerRect.width - lineWidth)/ 2)
            else: dX=0
            self.pyscreen.blit(textsurface, (self.innerRect.x+dX, self.innerRect.y + dY+row*lineHeight))

    def handleMouseMove(self, pos):
        return
    def handleMouseUp(self, pos,button):
        return
    def handleMouseDown(self,pos,button):
        return
    def handleKeyDown(self,key,unicode):
        return


########################################################################################################################
## Class TextBox
########################################################################################################################

class TextBox():
    rect=GRect(0, 0, 80, 32)
    margin = GRect(4, 4, 4, 4)
    bordercolor = defBorder
    backcolor = defEditorBackground
    textcolor = defEditorForeground
    borderwidth = 1
    text = "text"
    maxlength=10
    font=None
    fontname = defFontName
    fontsize = defFontSize
    editable=True
    cursorActive=False
    cursorChar=0
    drawBorder=True
    visible=True
    allSelected=False

    #Tooltip vars
    toolTipLabel=None
    firstHoverTime = 0
    firstHoverPos=GPoint(0,0)

    # We need constants which dictate what the allowes userinput is
    TEXT = 0
    INT=1
    FLOAT=2
    HEX=3
    inputType=TEXT

    def __init__(self, pyscreen, rect=GRect(0, 0, 80, 32), margin=GRect(4, 4, 4, 4),
                 bordercolor=defBorder, backcolor=defEditorBackground, textcolor=defEditorForeground,
                 borderwidth=1, drawBorder=True,
                 text="text", maxlength=-1, fontname=defFontName, fontsize=defFontSize, editable=True,
                 inputType=TEXT,
                 toolTip="",
                 onEnter=None, linkedData=None):
        """ Saves all values to internal variables. """
        self.pyscreen = pyscreen
        self.rect = rect
        self.margin=margin
        self.bordercolor=bordercolor
        self.backcolor=backcolor
        self.textcolor=textcolor
        self.borderwidth=borderwidth
        self.text = text
        if not maxlength==-1:
            self.maxlength = maxlength
        else:
            self.maxlength = 99
        self.font = pygame.font.SysFont(fontname, fontsize)
        self.editable=editable
        self.inputType=inputType
        self.drawBorder=drawBorder
        self.onEnter=onEnter
        self.linkedData=linkedData

        # We truncate text if larger than allowed maximum length given by user
        if len(self.text)>self.maxlength: self.text=self.text[0:self.maxlength]

        #And that the textbox has enough height to show each letter
        text_width, text_height = self.font.size("M[].j")
        if self.rect.height<(text_height+2*self.margin.y): self.rect.height=text_height+2*self.margin.y

        #And setup tooltip
        # We need to figure out the correct width correct width of tooltip
        if not toolTip=="":
            self.toolTipLabel = Label(pyscreen, rect=GRect(self.rect.right, self.rect.height, 1024, 20),
                                      text=toolTip, drawBorder=True, borderwidth=1, backcolor=defHighEditorBackground,
                                      fontsize=defFontSize - 2,
                                      textcolor=defHighEditorForeground, autowrap=True)
            max_width=0
            for line in toolTip.split("\n"):
                text_width, text_height = self.toolTipLabel.font.size(line)  # needed for self.autoheight
                if text_width>max_width: max_width=text_width
            self.toolTipLabel.rect.width=max_width+self.toolTipLabel.margin.x+self.toolTipLabel.margin.width
            self.toolTipLabel.visible=False


    def setText(self,text):
        """ Truncates text if larger than allowed maximum length given by user. """
        self.text = text
        if len(self.text)>self.maxlength: self.text=self.text[0:self.maxlength]


    def redraw(self):
        """ Redraws TextBox. """

        # If not visible nothing to do.
        if not self.visible: return

        # Draw background and border if needed
        pygame.draw.rect(self.pyscreen, self.backcolor, self.rect.tuple(), 0)
        if self.drawBorder: pygame.draw.rect(self.pyscreen, self.bordercolor, self.rect.tuple(), self.borderwidth)

        # Draw text
        # If all selected we need to draw with hightlighted background
        if self.allSelected:
            textsurface = self.font.render(self.text, True, defHighEditorForeground)
            hrect=GRect(self.rect.x + self.margin.x-1, self.rect.y + self.margin.y, textsurface.get_rect()[2]+1,textsurface.get_rect()[3])
            if self.rect.x+self.margin.x+hrect.width>self.rect.right-1:
                hrect.width=hrect.width-(self.rect.x+self.margin.x+hrect.width-self.rect.right)-1
            pygame.draw.rect(self.pyscreen, defHighEditorBackground, hrect.tuple(), 0)
        # Else with normal background
        else:
            textsurface = self.font.render(self.text, True, self.textcolor)
        # And the text
        self.pyscreen.blit(textsurface, (self.rect.x + self.margin.x, self.rect.y + self.margin.y),(0,0,self.rect.width-2*self.margin.x,self.rect.height-2*self.margin.y))

        # If editing also draw the cursor
        if self.cursorActive:
            text_width, text_height = self.font.size(self.text[0:self.cursorChar])
            if self.rect.x+self.margin.x+text_width<self.rect.x+self.rect.width: # we don't want to put cursor outside box
                pygame.draw.rect(self.pyscreen,
                                 self.textcolor,
                                 (self.rect.x+self.margin.x+text_width,self.rect.y+self.margin.y,2,self.rect.height-2*self.margin.y-1),
                                 0)

    prevClick=0
    def handleMouseUp(self,pos,button):
        """ Set cursor / edit of TextBox """

        # If not left button nothing to do
        if not button == 1: return

        # If not left button nothing to do
        if not self.editable: return

        # Check if clicked within textbox
        gpos=GPoint.fromTuple(pos)
        if gpos.inGRect(self.rect):
            # Register if we doubleclick and if so set allSelected to True (we want to select all the text)
            if (time.time()-self.prevClick)<0.3:
                #print ("Double click")
                self.allSelected=True
            else:
                self.allSelected=False
                #print("Single click")
                self.prevClick = time.time()

            # We are handling this so clear queue for others
            pygame.event.clear()

            # Set cursorActive for redraw and handleKeydown
            self.cursorActive=True

            # determine where we need to put cursor by iterating over each char
            relx=pos[0]-self.rect.x
            rely = pos[1] - self.rect.y
            self.cursorChar=0
            for i in range(0,len(self.text)):
                text_width, text_height = self.font.size(self.text[0:i])
                if relx>(text_width+self.margin.x):
                    self.cursorChar=self.cursorChar+1
        else:
            self.cursorActive = False
            self.allSelected=False


    def handleMouseDown(self,pos,button):
        return


    def handleMouseMove(self,pos):
        return


    def handleToolTips(self,pos):
        """ Returns label control with tooltip if hovered long enough. """
        # if user did not set a tooltip nothing to do
        if self.toolTipLabel==None: return None

        #Check if mouse above control, if not exit
        gpos=GPoint.fromTuple(pos)
        if not gpos.inGRect(self.rect):
            self.firstHoverTime=0
            self.firstHoverPos=GPoint(0,0)
            self.toolTipLabel.visible = False
            return None

        #Check if first time hovering, if so set timer
        if self.firstHoverTime==0:
            self.firstHoverPos=gpos
            self.firstHoverTime=time.time()

        #Check if moved since hovering, if so reset counter and exit
        dif=self.firstHoverPos-gpos
        if math.sqrt(dif.x*dif.x+dif.y*dif.y)>5:
            self.firstHoverPos=GPoint(0,0)
            self.firstHoverTime=0
            self.toolTipLabel.visible = False
            return None

        #Check if hovered enough time and return tooltip
        timeHovered=time.time()-self.firstHoverTime
        if timeHovered>1.5 and not self.toolTipLabel.text=="" :
            self.toolTipLabel.visible=True
            self.toolTipLabel.rect.x = gpos.x
            self.toolTipLabel.rect.y = gpos.y
            #check if tooltip overflow right edge of pyscreen
            if self.toolTipLabel.rect.right>self.pyscreen.get_size()[0]:
                self.toolTipLabel.rect.x=gpos.x-self.toolTipLabel.rect.width
            return self.toolTipLabel


    def handleKeyDown(self,key,unicode):
        """ Handles keypresses and determine which keys are valid for TextBox input type """

        # If not editable nothing to do
        if not self.editable: return

        # Check if textbox was clicked and in editmode
        if self.cursorActive:
            # We are handling this so clear queue for others
            pygame.event.clear()
            # If all is selected each key will clear textbox
            if self.allSelected:
                self.text = ""
                self.allSelected = False
            # Process navigation (left,right) and modify (del, backspace) keys
            if key == K_BACKSPACE:
                if self.cursorChar == 0: return
                self.text = self.text[0:self.cursorChar - 1] + self.text[self.cursorChar:]
                self.cursorChar = self.cursorChar - 1
                if self.cursorChar < 0: self.cursorChar = 0
                return
            if key == K_DELETE:
                if self.cursorChar==len(self.text): return
                self.text = self.text[0:self.cursorChar] + self.text[self.cursorChar + 1:]
                return
            if key == K_LEFT:
                self.cursorChar = self.cursorChar - 1
                if self.cursorChar < 0: self.cursorChar = 0
                return
            if key == K_RIGHT:
                self.cursorChar = self.cursorChar + 1
                if self.cursorChar > len(self.text): self.cursorChar = len(self.text)
                return

            # On enter/return call use function with current text and the (unmodified) metadata we received when initialized
            if key == K_KP_ENTER or key == K_RETURN:
                if not self.onEnter == None: self.onEnter(self, self.text,self.linkedData)
                return# we don't want to add return char (chr 13) to text string

            # Remap keys of numpad to numerical keys
            isNumlockOn=(pygame.key.get_mods() & pygame.KMOD_NUM) ==4096
            #print ("isNumlockOn: ",isNumlockOn)
            if isNumlockOn:
                if key in range(K_KP0,K_KP9+1):
                    key=K_0+(key-K_KP0)
                if key == K_KP_PERIOD: key = K_PERIOD

            # Check for valid input depending on input type the user selected when initialized
            if not self.inputType==self.TEXT and (pygame.key.get_mods() & pygame.KMOD_SHIFT): return #shift (uppercase and specials chars only allowed in text
            if self.inputType==self.INT and key==K_PERIOD: return                                    #float/period not allowed if int
            if self.inputType==self.INT or self.inputType==self.FLOAT:
                if key not in range(K_0,K_COLON) and not key==K_PERIOD: return                           #only numbers/period allowed for int/float
            if self.inputType==self.HEX and (key not in range (K_0,K_9) and key not in range(K_a,K_f)): return
            if self.inputType==self.FLOAT and (key==K_KP_PERIOD or key==K_PERIOD) and "." in self.text:return # only allow one . in a float

            # Process the input which made it through the validation block above
            if len(self.text)<self.maxlength:
                if self.inputType==self.HEX: unicode=unicode.upper() #if hex we want uppercase characters
                self.text=self.text[0:self.cursorChar]+unicode+self.text[self.cursorChar:]
                self.cursorChar=self.cursorChar+1


