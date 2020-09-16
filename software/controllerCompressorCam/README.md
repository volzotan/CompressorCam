This is the firmware for the camera controller board. Main job of the board is to turn the Raspberry Pi Zero on and off in predefined intervals.
The microcontroller used for this is the Atmel SAMD21 (the Arduino Zero chip) and as such this hardware is Arduino IDE compatible.

For compiling and flashing, install the Arduino IDE or the Arduino CLI and either compile via IDE or by running `sh compile.sh && sh upload.sh`.

Usage:

Install the Arduino CLI tools and run `install.sh` to download all libraries  
Create a .hex file by running `compile.sh` and upload via `upload.sh` 

When using the Arduino IDE instead of the CLI tools, select Arduino Zero (Native Port) as the board and compile and upload as usual. You may need to install the libraries listed in `install.sh` by using the Library Manager in the IDE.