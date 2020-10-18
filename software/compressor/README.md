# Requirements:

# Ubuntu:

sudo apt-get install python-dev python-pyexiv2
sudo apt-get install python3-gi
sudo apt-get install gir1.2-gexiv2-0.10

sudo pip3 install pillow
sudo pip3 install scipy
sudo pip3 install matplotlib
sudo pip3 install pyyaml

build the newest opencv3, not the one from the distribution repository (probably opencv2) (old info, still relevant?)

### unlisted opencv3 dependencies:

sudo apt-get install libqt4-core libqt4-dev libqt4-gui qt4-dev-tools

# OSX

## EXIF related:

brew install pygobject3

    in case pygobject can not be found (AttributeError: module 'gi' has no attribute 'require_version'), 
    install pygobject via pip (requirements need to be installed separately):

    pip install pygobject

## Gooey Debugging

pyinstaller and gooey may behave weird sometimes and make debugging a hassle.  
To actually get an exception, build the .app bundle, cd to dist and run the application manually via  
`./Compressor.app/Contents/MacOS/Compressor`