import sys
from cx_Freeze import setup, Executable

# https://stackoverflow.com/questions/15734703/use-cx-freeze-to-create-an-msi-that-adds-a-shortcut-to-the-desktop
# http://msdn.microsoft.com/en-us/library/windows/desktop/aa371847(v=vs.85).aspx
shortcut_table = [
    ("DesktopShortcut",								# Shortcut
     "DesktopFolder",								# Directory_
     "Photon File Editor",							# Name
     "TARGETDIR",									# Component_
     "[TARGETDIR]PhotonEditor.exe",					# Target
     None,											# Arguments
     None,											# Description
     None,											# Hotkey
     "C:\Program Files (x86)\PhotonFileEditor\photonsters.ico",					# Icon
     None,											# IconIndex
     None,											# ShowCmd
     'TARGETDIR'               						# WkDir
     )
    ]

# Now create the table dictionary
msi_data = {"Shortcut": shortcut_table}

# Change some default MSI options and specify the use of the above defined tables
bdist_msi_options = {'data': msi_data}

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os"],"excludes": ["tkinter"],"include_files": [""], "include_msvcr" : True}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "PhotonFileEditor",
        version = "0.1",
        description = "Photon Files Editor",
        options = {"build_exe": build_exe_options,"bdist_msi": bdist_msi_options},
        executables = [Executable("PhotonEditor.py", base=base,)])


#just build	 	python setup.py build --build-base=../
#installer		python setup.py build --build-base=../ bdist_msi