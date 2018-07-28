# This script is working but needs a major overhaulling
# Check https://github.com/makewitharduino/Scratio/blob/master/setup.py for inspiration
# X3msnake 180726
#
################################
#
#just build	 			python winsetup.py build -b ..\							#Builds on the folder above
#build installer		python winsetup.py build -b ..\  bdist_msi -d ..\		#Builds on the folder above
#
################################

import os
import sys
from cx_Freeze import setup, Executable
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import OpenGL.arrays.numpymodule
import numpy
import OpenGL.platform.win32
import OpenGL.arrays.ctypesarrays
import OpenGL.arrays.ctypesparameters
import OpenGL.arrays.ctypespointers
import OpenGL.arrays.lists
import OpenGL.arrays.nones
import OpenGL.arrays.numbers
import OpenGL.arrays.strings
import OpenGL.platform.win32
import OpenGL.raw.GL
import OpenGL.GL
import OpenGL.GLU
import OpenGL.GLUT
#import dummy.Process
#import email.Generator
#import email.Iterators


shortcut_table = [
    ("DesktopShortcut",												# Shortcut
     "DesktopFolder",												# Directory_
     "PhotonFileEditor",											# Name
     "TARGETDIR",													# Component_
     "[TARGETDIR]\PhotonEditor.exe",								# Target
     None,															# Arguments
     None,															# Description
     None,															# Hotkey
     "",															# Icon
     0,																# IconIndex
     None,															# ShowCmd
     "TARGETDIR",              										# WkDir
     )
    ]

	
# Now create the table dictionary
msi_data = {"Shortcut": shortcut_table}

# Change some default MSI options and specify the use of the above defined tables
bdist_msi_options = {'data': msi_data}

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os", "OpenGL", "numpy"],"include_files": [""], "include_msvcr" : True}

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"
	
if 'bdist_msi' in sys.argv:
    sys.argv += ['--initial-target-dir', 'c:\PhotonFileEditor']
	
setup(  name = "PhotonFileEditor",
        version = "0.1",
		author= "Photonsters",
		url="https://github.com/Photonsters",
        description = "Photon File Editor",
        options = {"build_exe": build_exe_options,"bdist_msi": bdist_msi_options},
        executables = [Executable(script="PhotonEditor.py", base=base,icon="PhotonEditor.ico",)]
	 )



