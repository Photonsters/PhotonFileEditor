# PhotonFileUtils

Currently the PhotonFileEditor is being developed. The PhotonFileEditor is a utility to display, make and edit files for the Anycubic Photon printer.

## Installation
PhotonFileEditor is programmed in Python 3.6 and makes use of only one external library:pygame. 
If you want to test it follow these instructions:
1) install Python **3** from https://www.python.org/downloads/  
__or__ install Anaconda 3.6 https://www.anaconda.com/download/ 
2) install the pygame library (https://www.pygame.org/wiki/GettingStarted) by 
   * opening a dos prompt/linux terminal  
   __or__ if using Anaconda use the windows start menu, type/find 'anaconda' and run the anaconda prompt
   * type 'python -m pip install -U pygame --user'  to install the required library
3) download this repository as a zip file and extract
4) you have two options to run PhotonFileEditor:
   * from your file explorer find and run PhotonEditor.py 
   * from a dos prompt/linux terminal, navigate to the directory where you extracted the zip file and type 'phyton PhotonEditor.py'

**Attention: PhotonFileEditor will __not__ work with Python 2 !**

In the near future (approaching version 1.0), I will make a windows executables and a linux package available..

## How to help with the development
Since I myself do not (yet) have my own Anycubic Photon, there are a few things you could do to help me out with developing this program further:
#### Bugfixing
1) Follow the install guide above and let me know if you encounter any problems.
2) Test PhotonFileEditor with your own (large) Photon files.
3) Check if edited/saved Photon files print as expected on your Photon printer.
4) Let me know of any bugs you find
#### GUI
Until now I have not put much time in the User Interface or its esthetics. Any suggestions are more than welcome.
#### Functionality
If you are missing functionality which is not mentioned below, please let me know.

Since this is very much an alpha version (or rather an alpha *of* an alpha version), all suggestions of any kind are more than welcome!

## Implemented functionality
Currently the following functionality is implemented:
1. Viewing all data from a .Photon file, including encapsulated sliced bitmaps, generic info, meta-info and preview images/thumbnails.
2. Saving data to a .Photon file, however editing the data is not yet possible (couple of days)
3. Editing all numeric data of the Photon File. Databytes which are internally used (location of bitmaps etc) are shown but readonly.
4. Not yet tested - Importing bitmaps (from Povray as png-files) in an exisiting Photon File (which is used as a template)

## Functionality under development
The following functionality will be implemented soon:
1. More polished GUI
2. 3D view of bitmap data

## Current screenshot
![Screenshot of PhotonViewer](https://github.com/NardJ/PhotonFileUtils/blob/master/Screenshot1.png "June 18, 2018")

![Screenshot of PhotonViewer](https://github.com/NardJ/PhotonFileUtils/blob/master/Screenshot2.png "June 18, 2018")


