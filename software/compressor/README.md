Gooey provides a GUI for the `stacker.py` script. Run `python3 goocompressor.py` to start the application.

# Requirements:

    pip install -r requirements.txt

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

    brew install libffi
    pip install pygobject

If libffi.h can not be found, it may be necessary to set the path manually.

Run `brew info libffi` to get the location of the files (in my case):

    
    For compilers to find libffi you may need to set:
        export LDFLAGS="-L/usr/local/opt/libffi/lib"
        export CPPFLAGS="-I/usr/local/opt/libffi/include"

and run the export commands before installing pygobject via pip.

## Gooey Debugging

pyinstaller and gooey may behave weird sometimes and make debugging a hassle.  
To actually get an exception, build the .app bundle, cd to dist and run the application manually via  
`./Compressor.app/Contents/MacOS/Compressor`