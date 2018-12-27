# PhotonFileEditor

The PhotonFileEditor is a utility to display, make and edit files for the Anycubic Photon printer. The current version is beta. This means that you may encounter bugs. __Some bugs can potentially harm your printer__, imagine for instance a buggy photonfile which tells your printer to move down instead of up after printing a layer!

PhotonFileEditor is programmed in Python 3.6 and uses one mandatory library, pygame, and two optional libraries (numpy and pyOpenGL).
 
 ---
  
## Installation
You can run PhotonFileEditor in Windows, OSX and Linux.

All the releases can be found at https://github.com/Photonsters/PhotonFileEditor/releases 

For Windows an easy install package is available. For Linux and OSX you have to install python and some libraries.

### Windows:
- Download the MSI file and run it.
- If you want to run the latest version check the step-by-step in issue [#24](https://github.com/Photonsters/PhotonFileEditor/issues/24)

### OSX/Linux:
0) Download the source code in zip or tar.gz.
1) Install Python **3** from https://www.python.org/downloads/  
__or__ install Anaconda 3.6 https://www.anaconda.com/download/ 
2) Check the python version is above 3 by typing in the command line 'python --version'
3) Install the pygame library (https://www.pygame.org/wiki/GettingStarted) by 
   * opening a dos prompt/linux terminal  
   __or__ if using Anaconda use the windows start menu, type/find 'anaconda' and run the anaconda prompt
   * type 'python -m pip install -U pygame --user'  to install the required library
4) Recommended: with numpy installed a number of actions will be a lot faster, like importing and exporting of images and also updating the layer image when navigating.(Anaconda installations already comes with Numpy 1.14.3 installed, however better to be safe than sorry, so...)
   * type 'python -m pip install -U numpy --user'
5) Optional: with opengl installed you can (in a future release) view and slice STL files.
   * python -m pip install PyOpenGL
6) Download this repository as a zip file and extract
7) You have two options to run PhotonFileEditor:
   * from your file explorer find and run PhotonEditor.py 
   * from a dos prompt/linux terminal, navigate to the directory where you extracted the zip file and type 'phyton PhotonEditor.py'

**Attention: PhotonFileEditor will not work with Python 2! [Read Issue #3](https://github.com/NardJ/PhotonFileUtils/issues/3)** 

---

## How to help with the development
There are a few things you could do to help me out with developing this program further:

#### Programming
The core programming team currently only consists of 1 programmer (me). Some extra hands are needed to make some faster progress. Please let me (GitHub alias NardJ) know. 

#### Bugfixing
1) Test PhotonFileEditor with your own (large) Photon files.
3) Check if edited/saved Photon files print as expected on your Photon printer.
3) Let me know of any bugs you find by posting a issue [here](https://github.com/Photonsters/PhotonFileEditor/issues)

#### GUI
The User Interface and its esthetics always could benefit from further improvements. Any suggestions are more than welcome!

#### Functionality
If you are missing functionality which is not mentioned below, please let me know [here](https://github.com/Photonsters/PhotonFileEditor/issues/).

Since this is very much an alpha version (or rather an alpha *of* an alpha version), all suggestions of any kind are more than welcome!

---

## Implemented functionality
Currently the following functionality is implemented:
1. Viewing all data from a .Photon file, including encapsulated sliced bitmaps, generic info, meta-info and preview images/thumbnails.
2. Editing all numeric data of the Photon File. Data-bytes which are internally used (location of bitmaps etc) are shown but readonly.
3. Basic editing of individual layer images and multiple layers at once.
4. Delete/Duplicate/Copy Layers
5. Exporting all images
6. Importing bitmaps (.e.g. from Povray as png-files) in an exisiting Photon File (which is thus used as a template)
7. Undo before mentioned actions Delete/Duplicate/Copy.
8. Apply new resin settings to the photon file
9. Starting fresh with a new .Photon file
10. Saving to a .Photon file.

---

## Functionality under development
The following functionality will be implemented soon:
1. Improved layer editing
2. Slicing STL's to layer images
3. 3D view of bitmap data
4. Improved GUI

---

## Current screenshot
### Basic settings view 
![image](https://user-images.githubusercontent.com/11459480/43247680-b7f1c86c-90b5-11e8-866b-9d33bb9e8b77.png)
### Advanced settings view 
![image](https://user-images.githubusercontent.com/11459480/43339054-8786d568-91d8-11e8-9d3e-04f9704f2222.png)
### Layer editing 
![image](https://user-images.githubusercontent.com/11459480/43247903-68160b40-90b6-11e8-9eb8-82f383970911.png)


 
