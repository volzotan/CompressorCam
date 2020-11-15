---
title: Buyers Guide
permalink: buyers_guide
---

There are a few things you need to have or buy separately to complete the camera kit:

  * Raspberry Pi Zero W (without headers)
  * Raspberry Pi Zero HQ camera module
  * C or CS-Mount Lens (more info below)
  * two 18650 Lithium-Ion batteries (and a charger)
  * metric allen-keys (sizes: 1.5/2/2.5)
  * a tripod or zip ties

### Raspberry Pi Zero W 

There are three versions of the Raspberry Pi Zero:
  * Zero (no W, no WH) has no wifi-module, does not work
  * Zero WH, has already pre-soldered headers (the 40 pins) and thus our circuit board does not fit
  * Zero W has a wifi-module and no headers (empty holes). **That's the one we need.**

Where to buy:  
You can find a list of [recommended resellers](https://www.raspberrypi.org/products/raspberry-pi-zero-w/) on the Raspberry Pi Foundation homepage. Direct links to the correct model are down below.

### Raspberry Pi Zero HQ camera module

There are no different models or distinctions.

Where to buy:  
Same shop as the Pi Zero.

### C-Mount or CS-Mount Lens

The Rasberry Pi Camera Module does support C and CS-Mount lenses. Any non-motorized lens will work as long as it fits the enclosure. The physical length of the lens (not the focal length, but how long the barrel of the lens actually is) should not exceed 35mm. The official 6mm wide-angle sold alongside the Camera Module is quite large but does fit nicely. If you are not sure which lens to buy, the 6mm is not a bad option (it is not very wide-angle, though).

I did a comparison of several wide angle lenses [here](http://volzo.de/posts/raspberry-wide-angle-lenses). I recommend purchasing the unbranded 3.2mm wide angle lens for really wide shots (what you usually want for solargraphy). However, buying the official 6mm lens is not a bad choice either.

One option is to order from shops like B and H ([link](https://www.bhphotovideo.com/c/product/1447550-REG/marshall_electronics_cs_3_2_12mp_12mp_4k_uhd_3_2mm_fixed.html)) that may ship internationally or directly from Aliexpress ([link](https://aliexpress.com/item/32999824737.html?spm=a2g0s.9042311.0.0.6c7e4c4dntGzch)).

### 18650 batteries

Lithium-Ion batteries have some international shipping restrictions, that's why it's a good idea to buy them domestically. When buying batteries you need to check for two criteria:

  * The same size of batteries (18650) is available with different chemistries. Most common are `Lithium-Ion` cells (Li-Ion, sometimes falsely referred to as Lithium-Polymer/LiPo, too) and Li-Ion is what we need. If a battery is labelled as `LiFePo` the cell is using a different chemistry with different voltages when fully charged/empty and the controller board will not be able to correctly shut down if the battery is depleted.
  * Some batteries are slightly more expensive and come with a protection circuit (labelled as protected). This protection circuit sits on top of the batteries positive pole and makes the battery slightly longer so it may not fit the holder. Avoid these batteries.

I use Sanyo/Panasonic NCR18650GA cells, however, any unprotected Li-Ion battery will work fine.

### 18650 charger

Any 18650 charger will work fine. I use the Xtar VC4 because that's running on USB power and is very convenient.

### Allen Keys

Any allen key will work fine as long as they have metric dimensions. Make sure that the smallest required size (1.5mm) is included, too. What I use and recommend is the [Wera Hex Key set](https://www-de.wera.de/en/great-tools/l-keys-in-a-two-component-clip/).

### Tripod or Zip Ties

Use whatever you have handy. If you want to zip tie the enclosure to a pole, I recommend zip ties with a width of 4.5-5mm to fit the nudges on the enclosure. That holds very tight and works well.

## Country-specific link lists:

### United Kingdom

| Item                            | Shop      | Link  |
|:--------------------------------|:----------|-------|
| Raspberry Pi Zero W             | Pimoroni  | <https://shop.pimoroni.com/products/raspberry-pi-zero-w> |
| Raspberry Pi Camera Module HQ   | Pimoroni  | <https://shop.pimoroni.com/products/raspberry-pi-high-quality-camera> |
| Allen key set                   | Pimoroni  | <https://shop.pimoroni.com/products/allen-key-set> |
| 18650 battery                   | Pimoroni  | <https://shop.pimoroni.com/products/18650-lithium-cell> |
| 18650 charger                   | Amazon    | <https://www.amazon.co.uk/~/dp/B07DNG1MSQ/> |
| Lens [3.2mm]                    | AliExpress | <https://aliexpress.com/item/32999824737.html> |


### United States of America

| Item                            | Shop      | Link  |
|:--------------------------------|:----------|-------|
| Raspberry Pi Zero W             | Sparkfun  | <https://www.sparkfun.com/products/14277> |
| Raspberry Pi Camera Module HQ   | Sparkfun  | <https://www.sparkfun.com/products/16760> |
| Allen key set<sup>[1](#myfootnote1)</sup> | Sparkfun  | <https://www.sparkfun.com/products/14223> |
| 18650 battery                   | Sparkfun  | <https://www.sparkfun.com/products/12895> |
| 18650 charger                   | Amazon    | <https://www.amazon.com/~/dp/B010J9GE5G> |
| Lens [3.2mm]                    | AliExpress | <https://aliexpress.com/item/32999824737.html> |

<a name="footnote-pay-less">1</a>: There are other places where you may pay significantly less for Allen keys

### Addtional countries?

Let me know.