---
title: Troubleshooting Guide
imgdir: troubleshooting
assemblyimgdir: assembly
permalink: troubleshooting/
---

### When starting in maintenance mode the LED keeps blinking blue

Possible problems:

**The spring-loaded connection pins are not making contact properly.**

Make sure that everything sits nice and tight and the 4 screws that connect the boards are not loose (However, be careful not to overtighten them. It just needs to be firm). If everything is correct you see the small green LED on the edge of the Raspberry Pi Zero flickering while the main LED is blinking blue.

![Pi Zero camera assembly]( {{ site.baseurl }}/assets/{{ page.assemblyimgdir }}/2054.jpg ){:.enable_lightbox}

<!-- (should look like this: http://digitalsolargraphy.com/assets/assembly/pi_act_led.jpg ) -->

**The SD-card is not inserted correctly.**

Make sure that the contacts of the SD-card are facing down, the SD-card is fully inserted and it did no wiggle itself loose.

### It is not possible to open the compressor.camera website

Possible problems:

**You are not connected to the correct Wifi-network**

Make sure that the camera did start in maintenance mode (LED is constantly blue, not blinking) and you are connected to the ComressorCamera Wifi-network. I recommend to do this with a computer, not a tablet or a phone. Modern Android and iOS versions are not happy about wireless networks that are not connected to the internet and may complain or refuse to connect altogether.