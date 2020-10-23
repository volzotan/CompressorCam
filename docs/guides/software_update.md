---
title: Software Update
imgdir: guides
---

The latest version of the software can always be found on the [github page](https://github.com/volzotan/CompressorCam/releases).

The Compressor Camera requires three distinct parts of software:

### The Compressor application

This is the Compressor software used for postprocessing the images. Use Compressor.exe for Windows 10 and the Compressor.app.zip archive for MacOS (unzipping required beforehand). No installation necessary. Just run the application.

### Zeroroot 

![Balena Etcher]( {{ site.baseurl }}/assets/{{ page.imgdir }}/balena_etcher_screenshot.png ){:.enable_lightbox}

The operating system of the Raspberry Pi Zero Linux computer (zeroroot_v1.0.0.img). To update this you need to overwrite the SD-card with the supplied image. I recommend the [BalenaEtcher](https://www.balena.io/etcher/) program for this, that's rather quick and convenient. Remove the SD-card from the Pi Zero board, and connect it to your computer. Open the Balena Etcher, select the downloaded image and the SD-card you just inserted. Flashing will take a minute or two. Afterwards you need to start the camera once in maintenance mode (hitting the button while booting).
The LED will blink blue for one or two minutes. If the LED stops blinking and remains blue, the update is done and you can switch the camera off.

**Overwriting the SD-card will erase all data! Copy your images beforehand.**

### CompressorCameraController

That's the firmware on the CompressorCameraBoard, managing the power supply, controlling the Linux board, etc. Hopefully you will never need to update this. 