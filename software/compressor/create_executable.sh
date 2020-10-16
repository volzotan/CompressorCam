#!/bin/sh

rm -rf dist
rm -rf build
rm -rf __pycache__

pyinstaller --windowed --noconfirm -F goocompressor_osx.spec
# chmod +x dist/Compressor.app

# pyinstaller --noconfirm -F --windowed goocompressor_win.spec