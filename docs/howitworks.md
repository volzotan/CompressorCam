---
title: How it works
imgdir: howitworks
permalink: howitworks/
---

# Theory

### The problem: 

It's easy to create digital long exposures. Reduce the sensors' exposure to light and let it run for a few seconds. If you want to go longer you will realize that after a few seconds it will get horribly noisy. The next step up in the game is taking many single exposures and averaging them. This way an arbitarily long exposure can be simulated quite well in software. When using a weighted average based on exposure value from the single images, even day long exposures are possible. Nice! Except that won't work for solargraphy images. While the sun burns into the film and marks it permanently, the extremly bright spot/streak of the sun is averaged away and won't be visible in the digital ultra long exposure. Darn...


24 hour digital long exposure:

<div style="width: 460px; margin: 0 auto;">
    <video autoplay loop muted playsinline>
        <source src="{{ site.baseurl }}/assets/{{ page.imgdir }}/herderplatz_raw.webm" type="video/webm">
    </video>
    <video autoplay loop muted playsinline>
        <source src="{{ site.baseurl }}/assets/{{ page.imgdir }}/herderplatz_stacked.webm" type="video/webm">
    </video>
</div>


result:

![Only averaging]( {{ site.baseurl }}/assets/{{ page.imgdir }}/herderplatz_only_averaging.jpg ){:.enable_lightbox}

So, how can we solve this problem? While taking single exposures we need to keep track of the spots of the film that would be "burned" or [solarized](https://en.wikipedia.org/wiki/Solarization_(photography)). For every image we take (with the correct exposure) we take another image right away with the least amount of light possible hitting the sensor. We assume that every bit of light that would have hit the sensor in our second, much darker exposure would have been sufficiently bright to permanently mark the film.

Lets take a step back for a moment and talk about EV or [Exposure Value](https://en.wikipedia.org/wiki/Exposure_value). A correctly exposed image done at 1s with f/1.0 and ISO 100 has an EV of 0. Half a second with the same aperture and ISO settings is EV 1, quarter of a second EV 2, ...
So Wikipedia lists a scene with a cloudy or overcast sky at about EV 13, a cloud-free full sunlight moment at EV 16.
A standard (DSLR/mirrorless) camera reaches about 1/4000th of a second exposure time, most lenses f/22 and the lowest ISO setting is either 25, 50 or 100. 1/4000s @ f/22 and ISO 100 is equal to EV 20 to 22.
So we can use EV as a way to describe the amount of brightness in a scene (if we would expose it correctly) and -- at the same time -- as a measure of whats the maximum amount of brightness a camera can handle without overexposing. Basically how many photons are hitting the camera and how many photons can the camera successfully block during exposure.
Whats the EV value to (reliably) determine which parts of the film would have been permanently marked? Generally, as a rule of thumb: the clearer the sky, the less clouds, the less haze, the less particles and water droplets in the atmosphere that reflect light, the lower the max EV value of the camera may be. 
So, can a camera at 1/4000s with aperture 22 and ISO 100 capture so _few_ photons that we can assume that a certain part of the image is extremly bright: sometimes. Every piece of cloud that gets backlit by the sun gets incredibly bright and if the camera is not able to step down/reduce the brightness sufficiently it's impossible to reliably determine if this spot would have been bright enough to leave a mark (spoiler, it wouldn't, but it's impossible then to differentiate between a bright cloud and an unblocked view of the sun.)
To step down to EV 20 suffices only for very clear days, if unknown conditions are to be expected (nearly always in europe sadly), then at least 24 is required in my experience.

However, there is an easy way to move the window of min/max possibly capturable EV values by the camera: a neutral-density filter. That reduces the amount of light that hits the sensor considerably, so the camera won't be able to capture images in the dusk or dawn or the night, but that's not a problem in our case since these images wouldn't be relevant for a multi-day long exposure anyway (compared to the bright daytime their impact on the overall image is negligible). When using a ND64 filter (64 or 2 to the power of 6) it takes away about 6 EV (ND filters are never precise) and thus gives us 26 as the max EV value. How does that look?

Correctly exposed image (EV: 11)
![ND filter comparison]( {{ site.baseurl }}/assets/{{ page.imgdir }}/captures_1_cap_000750_ev_11.24.jpg ){:.enable_lightbox}

Slightly darker (EV: 14)
![ND filter comparison]( {{ site.baseurl }}/assets/{{ page.imgdir }}/captures_4_cap_000750_ev_14.76.jpg ){:.enable_lightbox}

Close to what most DSLRs achieve out of the box (EV: 19)
![ND filter comparison]( {{ site.baseurl }}/assets/{{ page.imgdir }}/captures_3_cap_000750_ev_18.77.jpg ){:.enable_lightbox}

Aaaand here we go (EV: 26)
![ND filter comparison]( {{ site.baseurl }}/assets/{{ page.imgdir }}/captures_2_cap_000750_ev_25.76.jpg ){:.enable_lightbox}

Does that suffice: I would say, yes.


# Software

So, how to process this? Take a correctly exposed photo every X seconds and a second photo at EV 26 right away too. From all the first photos the long exposure image is calculated by doing a weighted average based on metadata. We can calculate the EV value from the EXIF data of the image, apply an offset to the value and use 2 to the power of the offsetted EV value as our weight for averaging pixel values.  
For the set of second images we can't do that, we would average out all burned image sections/pixels. There we just overlay every image and keep the brightest pixels of all images.


<div style="width: 480px; margin: 0 auto;">
    <video autoplay loop muted playsinline>
        <source src="{{ site.baseurl }}/assets/{{ page.imgdir }}/capture_1.webm" type="video/webm">
    </video>
    <video autoplay loop muted playsinline>
        <source src="{{ site.baseurl }}/assets/{{ page.imgdir }}/capture_3_peaked.webm" type="video/webm">
    </video>
</div>

Afterwards we take the long exposure image and burn all the bright pixels with the data from our sun overlay:

![Weimarhallenpark]( {{ site.baseurl }}/assets/{{ page.imgdir }}/weimarhallenpark.jpg ){:.enable_lightbox}

Terrific! But how many images are required and how fast do we need to take them?  
Interval duration depends on the focal length (the wider the image, the smaller the sun, the longer the time in between images may last). In my case for a wide angle image (about 24mm) 60s seem to be the minium and 45s would be preferrable. If the interval exceeds 60s the arc of the sun is reduced to overlaying circles and finally just something like a string of pearls. One way to cheat is by applying a bit of gaussian smooting on the sun overlay image to help break up the hard edges and smooth out the sun circles.  

90 second interval:
![artifacts]( {{ site.baseurl }}/assets/{{ page.imgdir }}/sun_arc_artifacts.png ){:.enable_lightbox}  
(gaps are caused by a partially clouded sky which blocked the sun)

The number of images for the long exposure depends on the amount of movement but a number of 60 to 90 images works well even for tiny details.