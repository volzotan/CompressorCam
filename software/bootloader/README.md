the controller board is using an Atmel SAMD21, that's the Arduino Zero chip. When soldering the board yourself you need to flash the Arduino bootloader before you can upload the firmware. A J-Link programmer and Adafruits Adalink software is recommended (in order to avoid Atmel Studio at all cost...).

run `sh install.sh` to clone Adalink

run `sh flash_bootoader.sh` to wipe the memory of the SAMD21 and copy the bootloader 