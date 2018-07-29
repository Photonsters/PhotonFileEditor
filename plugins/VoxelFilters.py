import os
# global filename contains full path of opened PhotonFile in PhotonFileEditor
cmd="node plugins/VoxelFilters/dilate -s "+filename+"-d slicer/filled/ -r 4"
print (cmd)
os.system("node plugins/VoxelFilters/dilate -s "+filename+" -d slicer/filled/ -r 4")

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

