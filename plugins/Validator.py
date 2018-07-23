import os
# global filename contains full path of opened PhotonFile in PhotonFileEditor
os.system("java -jar /home/nard/PhotonFileUtils-OpenGL/plugins/PhotonFileValidator/PhotonFileValidator.jar "+filename)

"""
# Some extra code, maybe needed in future releases
import platform

print ("test:")

if platform.system()=="Linux":
    # use 'which java' to find path
    print ("Running Linux")

if platform.system()=="Darwin": #Mac
    None 

if platform.system()=="Windows":
    None 
"""

#Always have the return variable set!
ret = "Succes"

