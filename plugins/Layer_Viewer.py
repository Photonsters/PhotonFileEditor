import subprocess

#os.chdir("plugins/photonfileviewer-1.0")
#print (os.getcwd())
#filepath=os.getcwd() +"/plugins/photonfileviewer-1.0/PhotonFileCheck.jar"
#args="-jar "+filepath
#arg1="-jar"
#arg2="plugins/photonfileviewer-1.0/PhotonFileCheck.jar"
#print (arg1,arg2)
#cmd=['java', arg1,arg2]
#subprocess.call(cmd, shell=True)
#subprocess.call("java -jar plugins/photonfileviewer-1.0/PhotonFileCheck.jar")
#subprocess.call(["java", "-jar PhotonFileCheck.jar"])
#subprocess.call("echo Hello World", shell=True) 

import os
class start:
    def __init__(self):
        os.system("java -jar /home/nard/PhotonFileUtils-OpenGL/plugins/photonfileviewer-1.0/PhotonFileCheck.jar")
        ret="Nard"
