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

**The camera is not in maintenance mode**

If the LED is not constantly blue, the camera did not start in maintenance mode.
Switch of the camera with the on/off-switch and switch it back on. The status LED is blinking white for 10s, during these 10s push the button next to the LED once. The LED will stop blinking white and instead blink blue. After at most 30s the LED should change to a permanent blue and the camera has booted and created a Wifi-network.

**You are not connected to the correct Wifi-network**

Make sure that the camera did start in maintenance mode (LED is constantly blue, not blinking) and you are connected to the ComressorCamera Wifi-network. I recommend to do this with a computer, not a tablet or a phone. Modern Android and iOS versions are not happy about wireless networks that are not connected to the internet and may complain or refuse to connect altogether.