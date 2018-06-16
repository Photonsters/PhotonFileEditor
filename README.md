# PhotonFileUtils

Currently the PhotonFileEditor is being developed. The PhotonFileEditor is a utility to display, make and edit files for the Anycubic Photon printer.

## Installation
PhotonFileEditor is programmed in Python 3.6 and makes use of the pygame library. 
If you want to test it follow these instructions:
1) install Python from https://www.python.org/downloads/ 
2) install the pygame library: https://www.pygame.org/wiki/GettingStarted
3) download this repository as a zip file and extract
4) you have two options to run PhotonViewer:
   a) from your file explorer run PhotonViewer.py 
   b) go to the commandline and go to the directory where you extracted the zip file and type phyton PhotonViewe.py

In the near future (approaching version 1.0), I will make windows executables and a linux package available.

## How to help with the development
Since I myself do not (yet) have my own Anycubic Photon, there are a few things you could do to help me out with developing this program further:
#### Bugfixing
1) Follow the install guide above and let me know if you encounter any problems.
2) Test PhotonFileEditor with your own (large) Photon files.
3) Check if edited/saved Photon files print as expected on your Photon printer.
4) Let me know of any bugs you find
#### GUI
Until now I have to put much time in the User Interface or its esthetics. Any suggestions are more than welcome.
#### Functionality
If you are missing functionality which is not below, please let me know.


## Implemented functionality
Currently the following functionality is implemented:
1. Viewing all data from a .Photon file, including encapsulated sliced bitmaps, generic info and  meta-info
2. Saving data to a .Photon file, however editing the data is not yet possible (couple of days)
3. Editing all numeric data of the Photon File. Databytes which are internally used (location of bitmaps etc) are shown but readonly.

## Functionality under development
The following functionality will be implemented soon:
1. Importing bitmaps (from Povray as png-files) in an exisiting Photon File (which is used as a template)
2. More polished GUI
3. 3D view of bitmap data

## Current screenshot
![Screenshot of PhotonViewer](https://github.com/NardJ/PhotonFileUtils/blob/master/screenshot.jpg "June 16, 2018")


