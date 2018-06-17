class GPoint():
    __x=0
    __y=0

    def __init__(self,x=0,y=0):
        self.__x = x
        self.__y = y

    @property
    def x(self):return self.__x

    @property
    def y(self):return self.__y

    @x.setter
    def x(self, x):self.__x = x
    @y.setter
    def y(self, y):self.__y = y

    def fromTuple(self,pos):
        return GPoint(pos[0],pos[1])
    @property
    def tuple(self):return (self.x, self.y)

    def __str__(self):return (str(self.x) + " , " + str(self.y) )

    def inGRect(self,GRect):
        return self.x>=GRect.left and self.x<=GRect.right and self.y >= GRect.top and self.y <= GRect.bottom

    def copy(self):
        newG=GPoint(self.x,self.y)
        return newG

    def __add__(self, other): return GPoint(self.x+other.x,self.y+other.y)
    def __sub__(self, other): return GPoint(self.x-other.x,self.y-other.y)
    def __mul__(self, other): return GPoint(self.x * other, self.y * other)
    def __gt__(self, other): return (self.x > other.x and self.y > other.y)
    def __lt__(self, other): return (self.x < other.x and self.y < other.y)
    def __eq__(self, other):
        try:
            print ("comp to gpoints")
            return (self.x == other.x and self.y == other.y)
        except:
            print ("error - compare types")
            return type(self)==type(other)
    def __len__(self, other): return (math.sqrt(self.x^2 + self.y^2))

class GLine():
    x1 = 0
    y1 = 0
    x2 = 0
    y2 = 0

    def __init__(self, x1=0, y1=0, x2=0, y2=0):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
    @property
    def width(self):return self.x2-self.x1
    @property
    def height(self):return self.y2 - self.y1
    @property
    def length(self): return (math.sqrt(self.width + self.height))

    def copy(self):
        newG=GLine(self.x1,self.y1)
        return newG

class GRect():
    __x = 0
    __y = 0
    __width = 0
    __height = 0

    def __init__(self, x=0, y=0, width=0, height=0):
        self.__x = x
        self.__y = y
        self.__width = width
        self.__height = height

    @property
    def x(self):return self.__x
    @property
    def y(self):return self.__y
    @property
    def left(self):return self.__x
    @property
    def top(self):return self.__y
    @property
    def right(self):return self.__x+self.__width
    @property
    def bottom(self):return self.__y+self.__height
    @property
    def width(self):return self.__width
    @property
    def height(self):return self.__height

    @property
    def p1(self):return GPoint(self.left,self.top)
    @property
    def p2(self):return GPoint(self.right,self.top)
    @property
    def p3(self):return GPoint(self.right,self.bottom)
    @property
    def p4(self):return GPoint(self.left,self.bottom)

    @x.setter
    def x(self, x):self.__x = x
    @y.setter
    def y(self, y):self.__y = y
    @left.setter
    def left(self, x):self.__x = x
    @top.setter
    def top(self, y):self.__y = y
    @right.setter
    def right(self,r):self.__width=r-self.x
    @bottom.setter
    def bottom(self,b):self.__width=b-self.y
    @width.setter
    def width(self, w):self.__width = w
    @height.setter
    def height(self, h):self.__height = h
    @p1.setter
    def p1(self, p):
        self.__x = p.x
        self.__y = p.y

    @property
    def topline(self):return GLine(self.x1,self.y1,self.x2,self.y1)
    @property
    def bottomline(self):return GLine(self.x1,self.y2,self.x2,self.y2)
    @property
    def leftline(self):return GLine(self.x1,self.y1,self.x1,self.y2)
    @property
    def rightline(self):return GLine(self.x2,self.y1,self.x2,self.y2)

    def copy(self):
        newG=GRect(self.x,self.y,self.width,self.height)
        return newG

    def move(self,gpos):
        self.x=self.x+gpos.x
        self.y=self.y+gpos.y

    def moveto(self,gpos):
        self.x=gpos.x
        self.y=gpos.y

    def shrink(self,grect):
        self.x=self.x+grect.x
        self.y=self.y+grect.y
        self.width=self.width-grect.x-grect.width
        self.height=self.height-grect.y-grect.height

    def tuple(self):
        return (self.x, self.y, self.width, self.height)

    def __str__(self):
        return (str(self.x) + " , " + str(self.y) + " , " + str(self.width) + " , " + str(self.height))

