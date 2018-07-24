# PhotonFileEditor

The PhotonFileEditor is a utility to display, make and edit files for the Anycubic Photon printer. The current version is beta. This means that you may encounter bugs. __Some bugs can potentially harm your printer__, imagine for instance a buggy photonfile which tells your printer to move down instead of up after printing a layer!
 
 ---
  
## Installation
PhotonFileEditor is programmed in Python 3.6 and only one external library, pygame, is required but numpy and pyOpenGL are also recommended. 
If you want to test it follow these instructions:
1) Install Python **3** from https://www.python.org/downloads/  
__or__ install Anaconda 3.6 https://www.anaconda.com/download/ 
2) Check the python version is above 3 by typing in the command line 'python --version'
3) Install the pygame library (https://www.pygame.org/wiki/GettingStarted) by 
   * opening a dos prompt/linux terminal  
   __or__ if using Anaconda use the windows start menu, type/find 'anaconda' and run the anaconda prompt
   * type 'python -m pip install -U pygame --user'  to install the required library
4) Recommended: with numpy installed a number of actions will be a lot faster, like importing and exporting of images and also updating the layer image when navigating.(Anaconda installations already comes with Numpy 1.14.3 installed, however better to be safe than sorry, so...)
   * type 'python -m pip install -U numpy --user'
5) Recommended: with opengl installed you can view and slice STL files.
   * python -m pip install PyOpenGL
6) Download this repository as a zip file and extract
7) You have two options to run PhotonFileEditor:
   * from your file explorer find and run PhotonEditor.py 
   * from a dos prompt/linux terminal, navigate to the directory where you extracted the zip file and type 'phyton PhotonEditor.py'

**Attention: PhotonFileEditor will not work with Python 2! [Read Issue #3](https://github.com/NardJ/PhotonFileUtils/issues/3)** 

In the near future (approaching version 1.0), I will make a windows executables and a linux package available..

---

## How to help with the development
Since I myself do not (yet) have my own Anycubic Photon, there are a few things you could do to help me out with developing this program further:

#### Bugfixing
1) Follow the install guide above and let me know if you encounter any problems.
2) Test PhotonFileEditor with your own (large) Photon files.
3) Check if edited/saved Photon files print as expected on your Photon printer.
4) Let me know of any bugs you find by filing a issue [here](https://github.com/NardJ/PhotonFileUtils/issues/)

#### GUI
Until now I have not put much time in the User Interface or its esthetics. Any suggestions are more than welcome.

#### Functionality
If you are missing functionality which is not mentioned below, please let me know [here](https://github.com/NardJ/PhotonFileUtils/issues/).

Since this is very much an alpha version (or rather an alpha *of* an alpha version), all suggestions of any kind are more than welcome!

---

## Implemented functionality
Currently the following functionality is implemented:
1. Viewing all data from a .Photon file, including encapsulated sliced bitmaps, generic info, meta-info and preview images/thumbnails.
2. Editing all numeric data of the Photon File. Data-bytes which are internally used (location of bitmaps etc) are shown but readonly.
3. Exporting all images
4. Importing bitmaps (.e.g. from Povray as png-files) in an exisiting Photon File (which is thus used as a template)
5. Delete/Duplicate/Copy Layers
6. Undo before mentioned actions
7. Apply new resin settings to the photon file
8. Starting fresh with a new .Photon file
9. Saving to a .Photon file.

---

## Functionality under development
The following functionality will be implemented soon:
1. Improved GUI
2. 3D view of bitmap data

---

## Current screenshot
![image](https://user-images.githubusercontent.com/11459480/41983949-b2a3c7b2-7a2f-11e8-9168-6176c4a9b16b.png)

---

## Previous screenshots
![image](https://user-images.githubusercontent.com/11083514/41735866-babb511a-7582-11e8-8e4e-37a96751b097.png)
![image](https://user-images.githubusercontent.com/11083514/41695957-74c0e4f0-7509-11e8-9be5-382ac51c9fe2.png)
 
