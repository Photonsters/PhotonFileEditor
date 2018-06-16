# PhotonFileUtils v0.1

The PhotonFileEditor is a utility to display, make and edit files for the Anycubic Photon printer.

## Installation
It is programmed in Python 3.6 and makes use of the pygame library. 
If you want to test it follow these instructions:
1) install Python from https://www.python.org/downloads/ 
2) install the pygame library: https://www.pygame.org/wiki/GettingStarted
3) download this repository as a zip file and extract
4) you have two options to run PhotonViewer:
   a) from your file explorer run PhotonViewer.py 
   b) go to the commandline and go to the directory where you extracted the zip file and type phyton PhotonViewe.py

In the future (approaching version 1.0), I will make windows executables and a linux package available.

## Implemented functionality
Currently the following functionality is implemented:
1. Viewing all data from a .Photon file, including encapsulated sliced bitmaps, generic info and  meta-info
2. Saving data to a .Photon file, however editing the data is not possible (couple of days)

## Functionality under development
The following functionality will be implemented soon:
1. Editing all numeric data of the Photon File
2. Importing bitmaps (from Povray as png-files) in an exisiting Photon File (which is used as a template)
3. More polished GUI
4. 3D view op bitmap data

## Current screenshot
![Screenshot of PhotonViewer](https://github.com/NardJ/PhotonFileUtils/edit/master/screenshot.jpg "June 16, 2018")


