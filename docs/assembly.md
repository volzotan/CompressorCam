---
title: Assembly
---

Steps:

  * [Materials](#materials)
  * [Disassemble the Camera Module](#disassembly)
  * [Join the Camera Module and the Electronics](#join)
  * Focus the Lens
  * Finish the Assembly
  * Close the Enclosure and Take Images
  * Copy the data
  * Postprocessing

One word of caution though: This is a very low volume DIY kit of 3D-printed parts, not industrial-grade perfect consumer goods. However, I did my best to make assembly as easy and reliable as possible, if you encounter issues, let me know and I help you out.

### <a name="materials"></a>Materials

Make sure you've got all necessary parts:

Part of the kit:

  * the CompressorCamera-board to control your pi
  * ND64 neutral density filter
  * 3d-printed enclosure
  * Raspberry Pi Zero camera cable
  * 18650 battery holder for 2 batteries
  * Micro-SD card (pre-loaded with the software)
  * all required fasteners and spares

Whats you need to buy separately:

  * Raspberry Pi Zero W (without headers)
  * Raspberry Pi Zero HQ camera module
  * C or CS-Mount Lens (see lens size for more info)
  * two 18650 Lithium-Ion batteries (and a charger)
  * metric Allen-keys (sizes: 1.5/2/2.5mm)
  * a tripod or zip ties

See the [buyers guide]({% link buyersguide.md %}) for recommendations.

In your Camera Kit should be the following parts:

    Top and bottom of your 3d-printed weatherproof enclosure (gray)
    Insert of enclosure (black)
    Bag of 3d-printed connection parts (black)
    Bag of screws and nuts
    ND64 neutral-density filter (58mm diameter)
    Orange camera connection cable
    The circuit board (green)
    Battery holder (black)
    Micro SD-card incl. SD-Adapter

Please make sure that everything is present and looks fine.


### <a name="disassemble"></a>Disassemble the Camera Module

Let's start with the assembly by preparing the camera module. Get the camera module and open the packaging. Sometimes there may be a flat white cable attached to the camera, sometimes the cable can be found in the packaging. The white cable does not fit the Raspberry Pi Zero so we need to remove it in case it is attached.
Additionally you will find a tiny flat-head screwdriver in a paper pouch. Keep the screwdriver, you'll need it to tighten a screw after focussing.

A word of caution beforehand: be careful, excessive force may break the connector.

Put your fingernails on the tiny plastic nudges of the connector and push the plastic bar gently towards the cable. You will be able to move it about a millimeter. Afterwards the cable is not secured anymore and can be pulled from the connector.

Second step: grab the orange camera cable and align it as shown in the photo. Wide end facing the camera, exposed metal side facing towards the circuit board. Push the cable in the connector (about 2mm) and hold it with two fingers while you secure the connector again.

Third step: remove the tripod mount. For this you will need an Allen key of size 1.5mm. Unscrew both screws left and right and remove the metal part with the threaded hole. Keep the screws and the mount in case you want to use the camera module in a different way in the future. The camera module now needs to be screwed to the corresponding 3d-printed plastic part.

A word of caution again: the plastic part is manufactured with a 3d-printer. Excessive force while tightening the screws will break the plastic. Always use enough torque so that the screw sits nicely, but never use more force than you would be able to apply with two fingers on the screwdriver.

Put a nut in each of the three holes shown in the photo. Often using the screwdriver makes it easier to push the nut in the hole (the nut doesn't need to touch the bottom of the hole, this happens during fastening).

Push the metal ring of the camera module through the plastic (take care, that might be a tight fit) and screw it down using the three 10mm long screws with the flat head. (2mm Allen key needed).

Last step: attach the lens. Grab your lens and remove the rear cap from the lens and the front cap from the camera module. If you have a CS-mount lens such as the official 6mm wide-angle, the adapter ring needs to be removed. Screw the lens in and you're done (for now).

### <a name="join"></a>Join the Camera Module and the Electronics

### Copy the data

After a day or two, grab your camera again and open the enclosure. Make sure that the LED (see image) is not on before moving the switch to off and remove the SD-card.

If you use Windows or MacOS the SD-card will show two partitions. One rather small one which you can ignore and a second one called CCSTORAGE. If you are using Linux, you will see a third ext4-formatted partition which contains the operating system, but you can ignore that.

On the CCSTORAGE partition you will find four folders and a text file that contains the log-output of the camera. Copy the images in the four folders to your computer. Have a look at the `captures_regular` folder and see if you may need to delete the first or last few images.

### Postprocess

Download the compressor software for Windows or MacOS. Start the application and select the first folder (`capture_regular`) as input. Set the processing mode to `stack` and hit start. The compressor software will now combine all correctly exposed images and compute based on the metadata a long exposure image. If you did not select a specific output directory, the output will be stored in `captures_regular_stacked`.

Repeat this with the other three directories but set the processing mode to `peak`.

Merge the images in your preferred software such as Photoshop or Gimp. What usually works well is to use the long exposure image as the base layer and the peaked images in either `Lighten` or `Screen` blend mode. 

### Additional info:

#### Never flip the batteries!
I assume it is not necessary to state this, but I will do it nevertheless: never place the batteries in the holder reversed! Never confuse the battery holder cables! Never use a conductive screwdriver to remove the batteries from the holder! You are using 18650 Lithium-Ion cells. Reverse polarity will destroy the electronics instantly. Short-circuiting the batteries itself will release enough energy to get glowing red metal in a matter of seconds. Cells will be impossible to touch and may explode. Do not discharge the batteries below 3V per battery. 

#### Do not leave the batteries in the camera over an extended amount of time
Even when the switch is set to off the circuit will draw an incredibly tiny but constant amount of power. Remove the batteries when not using the camera for several weeks and recharge them before the next usage.