@ECHO OFF
ECHO ========

rmdir /Q /S dist
rmdir /Q /S build
rmdir /Q /S __pycache__

pyinstaller --noconfirm -F --windowed goocompressor_win.spec

copy .\dist\Compressor.exe Z:/

PAUSE