import pygame
from pygame.locals import *
import math
import GUIhelpers
from GUIhelpers import *

#todo: use new classes GPos en GLine and GRect.shrink to simplify code in Gui elements

defFontName="Verdana"#"None"
defFontSize=16#24
defFormBackground=(232,232,232)
defFormForeground=(0,0,0)
defMenuBackground=defFormBackground
defMenuForeground=(0,0,0)
defHighMenuForeground=(255,255,255)
defHighMenuBackground=(68,123,213)
defEditorBackground=(255,255,255)
defEditorForeground=(0,0,0)
defHighEditorBackground=(68,123,213)
defHighEditorForeground=(255,255,255)
defTitlebarBackground=(215,215,215)
#defButtonBackground=(68,123,213)
defButtonBackground=(205,205,205)
defBorder=(173,173,173)
defBorderHover=defHighMenuBackground


class ImgBox():
    rect=GRect()
    img=None
    hoverimg=None
    hoverActive=False
    action=None
    visible=True
    drawBorder=False

    def __init__(self, pyscreen, filename,filename_hover=None, pos=(0,0),bordercolor=defBorder,borderhovercolor=defBorderHover,drawBorder=False,func_on_click=None):
        self.pyscreen = pyscreen
        self.img=pygame.image.load(filename)
        if not filename_hover==None:
            self.hoverimg = pygame.image.load(filename_hover)
        imgrect=self.img.get_rect()
        self.rect=GRect(imgrect[0],imgrect[1],imgrect[2],imgrect[3])
        self.rect.x=pos[0]
        self.rect.y=pos[1]
        self.bordercolor = bordercolor
        self.borderhovercolor=borderhovercolor
        self.drawBorder=drawBorder
        self.func_on_click=func_on_click
        if func_on_click==None: print ("None")

    def redraw(self):
        if not self.visible: return
        self.pyscreen.blit(self.img,self.rect.tuple())
        if self.hoverActive and not self.hoverimg==None:
            self.pyscreen.blit(self.hoverimg, self.rect.tuple())
        else:
            self.pyscreen.blit(self.img, self.rect.tuple())
        if self.drawBorder:
            if self.hoverActive:
                pygame.draw.rect(self.pyscreen,self.borderhovercolor, self.rect.tuple(), 1)
            else:
                pygame.draw.rect(self.pyscreen, self.bordercolor, self.rect.tuple(), 1)

    def handleMouseMove(self, pos):
        gpos=GPoint(pos[0],pos[1])
        if gpos.inGRect(self.rect):
            self.hoverActive=True
        else:
            self.hoverActive=False

    def handleMouseUp(self, pos,button):
        if not button==1: return
        gpos = GPoint(pos[0], pos[1])
        if gpos.inGRect(self.rect):
            if not self.func_on_click==None:
                self.func_on_click()

    def handleMouseDown(self,pos,button):
        return

    def handleKeyDown(self,key,unicode):
        return

class Button():
    #buttonstates
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
        self.pyscreen = pyscreen
        self.text=text
        self.textcolor=textcolor
        self.font = pygame.font.SysFont(fontname, fontsize)
        text_width, text_height = self.font.size(text)
        self.twidth=text_width
        self.theight=text_height

        #if button is image than dimensions are determined by image size
        if not filename == None:
            self.img = pygame.image.load(filename)
            imgrect = self.img.get_rect()
            self.rect=GRect(rect.x,rect.y,imgrect[2],imgrect[3])
        else: #otherwise we listen to the dimensions the user gave us
            self.rect=rect
        if not filename_hover==None:
            self.hoverimg = pygame.image.load(filename_hover)
        if not filename_down==None:
            self.downimg = pygame.image.load(filename_down)


        self.bordercolor = bordercolor
        self.borderhovercolor=borderhovercolor
        self.backcolor=backcolor
        self.func_on_click=func_on_click
        if func_on_click==None: print ("None")

    def redraw(self):
        if not self.visible: return
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


        if not self.text=="":
            textsurface = self.font.render(self.text, True,self.textcolor)
            dx=int(self.rect.width-self.twidth)/2
            dy=int(self.rect.height-self.theight)/2
            if self.state == self.down:  # shift text if down
                dx=dx+self.borderwidth
                dy=dy+self.borderwidth
            self.pyscreen.blit(textsurface, (self.rect.x + dx, self.rect.y+dy))

    def handleMouseMove(self, pos):
        gpos=GPoint(pos[0],pos[1])
        if gpos.inGRect(self.rect):
            self.state=self.hover
        else:
            self.state=self.normal
        #print (self.state)

    def handleMouseUp(self, pos,button):
        if not button == 1: return
        gpos=GPoint(pos[0],pos[1])
        if gpos.inGRect(self.rect):
            self.state=self.normal
            if not self.func_on_click==None:
                self.func_on_click()

    def handleMouseDown(self,pos,button):
        if not button == 1: return
        gpos=GPoint(pos[0],pos[1])
        if gpos.inGRect(self.rect):
            self.state=self.down

    def handleKeyDown(self,key,unicode):
        return

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

    #Fontname None will take default system font
    def __init__(self, pyscreen, location, margins=GRect(4, 4, 4, 4), fontname=defFontName, fontsize=defFontSize, title="unknown"):
        self.pyscreen = pyscreen
        l_x = location[0]
        l_y = location[1]-1
        self.margins=margins
        self.font = pygame.font.SysFont(fontname, fontsize)
        width, height = self.font.size("MinimalText")
        l_width = width + self.margins.x + self.margins.width
        l_height= 1*height++ self.margins.y + self.margins.height
        self.title=title
        self.pos=GRect(l_x,l_y,l_width,l_height)
        self.rowheight = height
        self.items=[]

    def addItem(self,menuitem,func_on_click):
        itemdata = (menuitem,func_on_click)
        self.items.append(itemdata)
        width, height = self.font.size(menuitem)
        if (width+self.margins.x+self.margins.width) >self.pos.width: self.pos.width=width+self.margins.x+self.margins.width
        self.pos.height= len(self.items)*(self.rowheight+self.spacing)+ self.margins.y + self.margins.height-self.spacing # extract 1x spacing at the bottom

    def redraw(self):
        if not self.isVisible:
            self.activeItem=-1 # so on reopening we don have floating cursor
            return
        #print (self.pos)

        #get snapshot of image below menu
        #self.pyscreen.blit(textsurface, (self.rect.x + self.margin.x, self.rect.y + self.margin.y),
        #                       (0, 0, self.rect.width - 2 * self.margin.x, self.rect.height - 2 * self.margin.y))

        #draw background and border
        pygame.draw.rect(self.pyscreen, self.backcolor, self.pos.tuple (), 0)
        pygame.draw.rect(self.pyscreen, self.bordercolor, (self.pos.tuple()), 1)
        #draw item text
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
        if not self.isVisible: return

        if pos[0] > self.pos.x and pos[0] < (self.pos.x+self.pos.width) and \
            pos[1] < (self.pos.y + self.pos.height):
            rely=pos[1]-self.pos.y
            self.activeItem=int((rely-self.margins.y)/(self.rowheight+self.spacing))
        else:
            self.isVisible=False

    def handleMouseDown(self, pos,button):
        return

    def handleMouseUp(self, pos,button):
        if not button == 1: return
        if not self.isVisible: return
        if pos[0] > self.pos.x and pos[0] < (self.pos.x+self.pos.width) and \
           pos[1] > self.pos.y and pos[1] < (self.pos.y + self.pos.height):
            for row, (item, func_on_click) in enumerate(self.items):
                if row == self.activeItem:
                    if not func_on_click==None:
                        func_on_click()

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
        self.pyscreen = pyscreen
        self.font = pygame.font.SysFont(fontname, fontsize)
        self.fontsize=fontsize #store to init menuitems
        self.fontname=fontname  #store to init menuitems
        dummy, height = self.font.size("gFile")
        #todo: the bar height does not take height of q/g/j wel enough in account
        height=int(height*0.5) # we take in account that g/q/j can be drawn lower
        if (height + self.margins.y + self.margins.height) > self.height: self.height = height + self.margins.y + self.margins.height

    def addMenu(self, menutitle,shortcutChar):
        #get left pos
        prevIdx=len(self.menus)-1
        if prevIdx==-1:
            x=self.margins.x
        else:
            prevTitle = self.menus[prevIdx]["title"]
            prevLeft =self.menus[prevIdx]["left"]
            prevWidth, height = self.font.size(prevTitle)
            if prevWidth<self.minwidth: prevWidth=self.minwidth
            x= prevLeft+prevWidth+ self.spacing
        scNr=0

        #get width
        width, height = self.font.size(menutitle)
        width=width+self.spacing

        #get nr of shortcutchar
        for idx,ch in enumerate(menutitle):
            if ch==shortcutChar:
                scNr=idx
        #print (scNr)

        #make menulist
        loc=(x,self.height+self.margins.x+self.margins.height+1)
        menulist=MenuList(pyscreen=self.pyscreen,location=loc, fontname = self.fontname, fontsize = self.fontsize, title=menutitle)

        #store all
        menudata={"title":menutitle,"left":x,"width":width,"scChar":scNr, "menulist":menulist}
        self.menus.append(menudata)

    def addItem(self, menutitle, menuitem, func_on_click):
        for menu in self.menus:
            if menu["title"]==menutitle:
                menulist=menu["menulist"]
                menulist.addItem(menuitem,func_on_click)

    def handleMouseDown(self, pos,button):
        if not button == 1: return
        if pos[1]>(self.height+self.margins.y+self.margins.height): return
        for menu in self.menus:
            if pos[0]>menu["left"] and pos[0]<(menu["left"]+menu["width"]):
                self.activeMenu=menu
                menulist=menu["menulist"]
                menulist.isVisible=True
            else:
                menulist = menu["menulist"]
                menulist.isVisible = False
        for menu in self.menus:
            menu["menulist"].handleMouseDown(pos,button)

    def handleMouseUp(self, pos,button):
        if not button == 1: return
        self.activeMenu=None
        for menu in self.menus:
            menu["menulist"].handleMouseUp(pos,button)

    def handleMouseMove(self, pos):
        for menu in self.menus:
            menu["menulist"].handleMouseMove(pos)

    def openMenu(self,menutitle):
        for idx,(title, shortcutChar, items, state) in enumerate(self.menus):
            if title == menutitle:
                self.menus[idx][3]= True
            else:
                self.menus[idx][3] = False

    def redraw(self):
        if not self.isVisible: return
        w, dummy = pygame.display.get_surface().get_size()
        #draw menubar
        h=self.height+self.margins.y+self.margins.height
        pygame.draw.rect(self.pyscreen, self.backcolor, (0,0,w,h), 0)
        pygame.draw.rect(self.pyscreen, self.bordercolor , (0, h, w, 1),1)

        #self.pyscreen.blit(textsurface, (self.rect.x + self.margin.x, self.rect.y + self.margin.y),
        #                       (0, 0, self.rect.width - 2 * self.margin.x, self.rect.height - 2 * self.margin.y))

        for menudata in self.menus:
            menuleft = menudata["left"]
            menuwidth = menudata["width"]
            if menudata==self.activeMenu:
                pygame.draw.rect(self.pyscreen, self.highbackcolor, (menuleft-self.spacing, 0,menuwidth+self.spacing, h), 0)
                localtextcolor=defHighMenuForeground
            else:
                localtextcolor=defMenuForeground

            scNr=menudata["scChar"]
            preStr=menudata["title"][:scNr]
            scStr=menudata["title"][scNr:scNr+1]
            postStr = menudata["title"][scNr + 1:]
            #print (scNr,preStr,scStr,postStr)
            wPre, dummy = self.font.size(preStr)
            wSc, dummy = self.font.size(scStr)
            wPost, dummy = self.font.size(postStr)

            self.font.set_underline(False)
            textsurface = self.font.render(preStr, True, localtextcolor)
            self.pyscreen.blit(textsurface, (menuleft , self.margins.y))

            self.font.set_underline(True)
            textsurface = self.font.render(scStr,True, localtextcolor)
            self.pyscreen.blit(textsurface, (menuleft +wPre, self.margins.y))

            self.font.set_underline(False)
            textsurface = self.font.render(postStr, True, localtextcolor)
            self.pyscreen.blit(textsurface, (menuleft +wPre+wSc, self.margins.y))

            menudata["menulist"].redraw()


class ListBox():
    items=[]
    rect = GRect(0, 0, 80, 32)
    margins = GRect(4, 4, 4, 4)
    bordercolor = (128, 128, 128)
    backcolor = defEditorBackground
    textcolor = defEditorForeground
    highbackcolor = defHighEditorBackground
    hightextcolor = defHighEditorForeground
    font=None
    fontname = "Consolas"
    fontsize = 16
    activeItem=-1
    rowheight=0
    spacing=4
    offset=0
    visible=True

    def __init__(self, pyscreen, rect=GRect(100, 40, 80, 80), items=None,fontname=defFontName, fontsize=defFontSize,func_on_click=None):
        self.pyscreen = pyscreen
        self.rect=rect
        self.items=items
        self.font = pygame.font.SysFont(fontname, fontsize)
        text_width, text_height = self.font.size("M[].j")
        self.rowheight=text_height
        self.items=items
        #resize list so the height is number of rows
        self.nritems = int(self.rect.height / (self.rowheight + self.spacing))
        self.rect.height=self.nritems*(self.rowheight + self.spacing)
        if not func_on_click==None:
            self.func_on_click=func_on_click

    def setItems(self, items):
        self.items=items

    def items(self):
        return self.items

    def redraw(self):
        if not self.visible: return
        pygame.draw.rect(self.pyscreen, self.backcolor, self.rect.tuple(), 0)
        pygame.draw.rect(self.pyscreen, self.bordercolor, self.rect.tuple(),1)

        self.nritems = int(self.rect.height / (self.rowheight + self.spacing))
        #print (self.activeItem)

        if self.items==None: return
        for row in range(0,self.nritems):
            idx=row+self.offset
            if idx<len(self.items):
                item=self.items[idx]
                rowtop = self.rect.y + self.margins.y + row * (self.rowheight + self.spacing)
                if row==self.activeItem:
                    pygame.draw.rect(self.pyscreen, self.highbackcolor,(self.rect.x+self.margins.x, rowtop-int(self.spacing/2), self.rect.width-self.margins.x-self.margins.width, self.rowheight), 0)
                    textsurface = self.font.render(item, True, self.hightextcolor)
                else:
                    textsurface = self.font.render(item, True, self.textcolor)
                self.pyscreen.blit(textsurface, (self.rect.x + self.margins.x, self.rect.y + self.margins.y+row*(self.rowheight+self.spacing)))

    def handleMouseMove(self,pos):
        return

    def activeText(self):
        try:
            return self.items[self.activeItem+self.offset]
        except:
            print ("Error from ListBox.activeText()")
            return ""

    def handleMouseDown(self,pos,button):
        if pos[0] > self.rect.x and pos[0] < (self.rect.x + self.rect.width) and \
                pos[1] < (self.rect.y + self.rect.height):
            if button == 1:
                rely=pos[1]-self.rect.y
                self.activeItem=int((rely-self.margins.y)/(self.rowheight+self.spacing))
                #print ("down on: ", self.activeItem,self.activeText())
            if button==4: # mousewheel up
                self.offset=self.offset-1
                if self.offset<0: self.offset=0
            if button==5:
                self.offset = self.offset + 1
                if self.offset>(len(self.items)-self.nritems): self.offset=len(self.items)-self.nritems

    def handleMouseUp(self,pos,button):
        if pos[0] > self.rect.x and pos[0] < (self.rect.x + self.rect.width) and \
                pos[1] < (self.rect.y + self.rect.height):
            if button == 1:
                if not self.func_on_click==None:
                    #print ("send:", self.activeItem,self.activeText())
                    self.func_on_click(self.activeText())

    def handleKeyDown(self,key,unicode):
        return

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

    def __init__(self, pyscreen, rect=GRect(0, 0, 80, 32), margin=GRect(4, 4, 4, 4),
                 bordercolor=defBorder, backcolor=defFormBackground, textcolor=defFormForeground,
                 borderwidth=1, drawBorder=False,center=False,
                 text="text", fontname=defFontName, fontsize=defFontSize, autoheight=True):
        self.pyscreen = pyscreen
        self.rect = rect
        self.margin=margin
        self.innerRect=rect.copy()
        self.innerRect.shrink(self.margin)
        self.center=center
        self.bordercolor=bordercolor
        self.backcolor=backcolor
        self.textcolor=textcolor
        self.borderwidth=borderwidth
        self.autoheight=autoheight
        self.font = pygame.font.SysFont(fontname, fontsize)
        self.setText(text)
        self.drawBorder=drawBorder

        # We want to make sure the text fully fits in the TextBox
        text_width, text_height = self.font.size("M[].j")
        #And that the textbox has enough height to show each letter
        if self.rect.height<(text_height+2*self.margin.y): self.rect.height=text_height+2*self.margin.y

    def setText(self,text):
        # We want to make sure the text fully fits in the TextBox
        self.text = text
        self.innerRect = self.rect.copy()
        self.innerRect.shrink(self.margin)

        lines=text.split("\n")
        newlines=[]
        for line in lines:
            newline=""
            words=line.split(" ")
        #    print ("["+line+"]")
            lastIdx=len(words)-1
        #    print("------")
            for idx,word in enumerate(words):
                oldline=newline
                newline=newline+word+" "
                text_width, text_height = self.font.size(newline)
                if text_width>self.innerRect.width:
                    #todo: check for words which are longer than width, in which case oldline is empty
                    text_width > self.innerRect.width
                    newlines.append(oldline.strip())
                    newline = word + " "
        #            print("|"+ oldline.strip()+ "|")
            newlines.append(newline.strip())
        #    print("|" + newline.strip() + "|")
        #print("------")
        #print ("Total result:")
        #print (newlines)
        self.text=newlines
        if self.autoheight:
            self.rect.height=len(newlines)*text_height+self.margin.y+self.margin.height

    def show(self):
        self.waiting=True
        self.waitforuser()

    def redraw(self):
        if not self.visible: return
        pygame.draw.rect(self.pyscreen, self.backcolor, self.rect.tuple(), 0)
        if self.drawBorder: pygame.draw.rect(self.pyscreen, self.bordercolor, self.rect.tuple(), self.borderwidth)
        dummy, lineHeight = self.font.size(self.text[0])
        if self.center:
            dY=int((self.innerRect.height-len(self.text)*lineHeight)/2)
        else: dY=0
        for row,line in enumerate(self.text):
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

    TEXT = 0
    INT=1
    FLOAT=2
    HEX=3
    inputType=TEXT

    def __init__(self, pyscreen, rect=GRect(0, 0, 80, 32), margin=GRect(4, 4, 4, 4),
                 bordercolor=defBorder, backcolor=defEditorBackground, textcolor=defEditorForeground,
                 borderwidth=1, drawBorder=True,
                 text="text", maxlength=-1, fontname=defFontName, fontsize=defFontSize, editable=True,
                 inputType=TEXT, onEnter=None, linkedData=None):
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

        # We want to make sure the text fully fits in the TextBox
        text_width, text_height = self.font.size("M[].j")
        if len(self.text)>self.maxlength: self.text=self.text[0:self.maxlength]
        #And that the textbox has enough height to show each letter
        if self.rect.height<(text_height+2*self.margin.y): self.rect.height=text_height+2*self.margin.y

    def setText(self,text):
        # We want to make sure the text fully fits in the TextBox
        text_width, text_height = self.font.size("M[].j")
        self.text = text
        if len(self.text)>self.maxlength: self.text=self.text[0:self.maxlength]

    def redraw(self):
        if not self.visible: return
        textsurface = self.font.render(self.text, True, self.textcolor)
        pygame.draw.rect(self.pyscreen, self.backcolor, self.rect.tuple(), 0)
        if self.drawBorder: pygame.draw.rect(self.pyscreen, self.bordercolor, self.rect.tuple(), self.borderwidth)
        self.pyscreen.blit(textsurface, (self.rect.x + self.margin.x, self.rect.y + self.margin.y),(0,0,self.rect.width-2*self.margin.x,self.rect.height-2*self.margin.y))
        if self.cursorActive:
            text_width, text_height = self.font.size(self.text[0:self.cursorChar])
            if self.rect.x+self.margin.x+text_width<self.rect.x+self.rect.width: # we don't want to put cursor outside box
                pygame.draw.rect(self.pyscreen,
                                 self.textcolor,
                                 (self.rect.x+self.margin.x+text_width,self.rect.y+self.margin.y,2,self.rect.height-2*self.margin.y-1),
                                 0)


    def handleMouseMove(self,pos):
        return

    def handleMouseUp(self,pos,button):
        if not button == 1: return
        if not self.editable: return
        if pos[0]>self.rect.x and pos[0]<(self.rect.x+self.rect.width) and \
            pos[1] > self.rect.y and pos[1] < (self.rect.y + self.rect.height):
            self.cursorActive=True

            relx=pos[0]-self.rect.x
            rely = pos[1] - self.rect.y
            self.cursorChar=0
            for i in range(0,len(self.text)):
                text_width, text_height = self.font.size(self.text[0:i])
                if relx>(text_width+self.margin.x):
                    self.cursorChar=self.cursorChar+1
        else:
            self.cursorActive = False

    def handleMouseDown(self,pos,button):
        if not button == 1: return
        return

    def handleKeyDown(self,key,unicode):
        if not self.editable: return
        if self.cursorActive:
            # process navigation
            if key == K_BACKSPACE:
                self.text = self.text[0:self.cursorChar - 1] + self.text[self.cursorChar:]
                self.cursorChar = self.cursorChar - 1
                if self.cursorChar < 0: self.cursorChar = 0
                return
            if key == K_DELETE:
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
            # exit/validate
            if key == K_KP_ENTER or key == K_RETURN:
                if not self.onEnter == None: self.onEnter(self, self.text,self.linkedData)

            #check for valid input
            if not self.inputType==self.TEXT and (pygame.key.get_mods() & pygame.KMOD_SHIFT): return #shift (uppercase and specials chars only allowed in text
            if self.inputType==self.INT and key==K_PERIOD: return                                    #float/period not allowed if int
            if self.inputType==self.INT or self.inputType==self.FLOAT:
                if key not in range(K_0,K_COLON) and not key==K_PERIOD: return                           #only numbers/period allowed for int/float
            if self.inputType==self.HEX and (key not in range (K_0,K_9) and key not in range(K_a,K_f)): return
            if self.inputType==self.FLOAT and (key==K_KP_PERIOD or key==K_PERIOD) and "." in self.text:return # only allow one . in a float

            #process input
            if len(self.text)<self.maxlength:
                if self.inputType==self.HEX: unicode=unicode.upper() #if hex we want uppercase characters
                self.text=self.text[0:self.cursorChar]+unicode+self.text[self.cursorChar:]
                self.cursorChar=self.cursorChar+1


