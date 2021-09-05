#!/usr/bin/env python

import support

import json
import sys
import os
import datetime
import subprocess
import logging
import math
from fractions import Fraction

from PIL import Image
import numpy as np

import exifread

try:
    import gi
    gi.require_version('GExiv2', '0.10')
    from gi.repository import GExiv2
except ImportError as e:
    log = logging.getLogger("stacker")
    log.error("Importing Exiv2 failed. No metadata can be written. Error: {}".format(e))


"""
    Stacker loads every image in INPUT_DIRECTORY,
    stacks it and writes output to RESULT_DIRECTORY.

    Do not run with pypy! (Saving image is 30-40s slower)

    =====
    compressor writes EXIF Metadata to generated image file
    * compressor version (or Date or git-commit)
    * datetime of first and last image in series
    * total number of images used
    * total exposure time

    and (should, still TODO) reapply extracted Metadata:
    * camera model
    * GPS Location Data
    * Address Location Data (City, Province-State, Location Code, etc)

    TODO:

    improve metadata reading

"""

PROCESSING_MODE_STACK           = "stack"
PROCESSING_MODE_PEAK            = "peak"
PROCESSING_MODE_SLICE           = "slice"

DEFAULT_APERTURE                = 8.0
EV_OFFSET                       = 26

TIFF_SUPPORT                    = True

NUM_SLICES                      = 24 #*2

try:
    import cv2
except ImportError as e:
    log = logging.getLogger("stacker")
    log.error("Importing cv2 failed. No TIFF support")
    TIFF_SUPPORT = False


class Stopwatch(object):

    def __init__(self):
        pass

    def stop(self, tag):
        pass


class Stack(object):

    NAMING_PREFIX                   = ""
    INPUT_DIRECTORY                 = "images"
    RESULT_DIRECTORY                = "stack_" + NAMING_PREFIX
    FIXED_OUTPUT_NAME               = None
    DIMENSIONS                      = None # (length, width)
    EXTENSION                       = ".tif"

    BASE_DIR                        = None

    # Image proc mode (stack / peak)
    PROCESSING_MODE                 = PROCESSING_MODE_STACK

    # Align
    ALIGN                           = False
    USE_CORRECTED_TRANSLATION_DATA  = False

    MIN_BRIGHTNESS_THRESHOLD        = 100

    # Curve
    DISPLAY_CURVE                   = False
    APPLY_CURVE                     = False

    WRITE_METADATA                  = True
    SAVE_INTERVAL                   = 15

    DEBUG                           = False

    # misc

    EXIF_DATE_FORMAT                = '%Y:%m:%d %H:%M:%S'
    VERSION_NUMBER                  = None

    # debug options

    CLIPPING_VALUE                  = -1

    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

    def __init__(self, aligner):

        self.aligner                            = aligner

        self.counter                            = 0
        self.processed                          = 0

        self.input_images                       = []
        self.stacked_images                     = []

        self.weighted_average_divider           = 0

        self.stopwatch                          = {
            "load_image": 0,
            "transform_image": 0,
            "convert_to_array": 0,
            "stacking": 0,
            "write_image": 0
        }

        self.tresor                             = None

        # initialize log

        self.log = logging.getLogger("stacker")
        self.log.debug("init")


    """
    After the class variables have been overwritten with the config from the compressor.py script,
    some default values may need to be calculated.
    """
    def post_init(self):

        if self.CLIPPING_VALUE < 0 and self.EXTENSION == ".jpg":
            self.CLIPPING_VALUE = 2**8 - 1
        if self.CLIPPING_VALUE < 0 and self.EXTENSION == ".tif":
            self.CLIPPING_VALUE = 2**16 - 1

        if self.WRITE_METADATA:
            if "GExiv2" not in sys.modules:
                self.log.error("Importing Exiv2 failed. No metadata can be written")
                self.WRITE_METADATA = False

        # TODO: is ignored right now
        # self.PEAKING_THRESHOLD = int(self.CLIPPING_VALUE * self.PEAKING_PIXEL_THRESHOLD) # peaking includes pixel above 95% brightness

    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

    def print_config(self):

        config = [
            ("proc mode:        {}", str(self.PROCESSING_MODE)),
            (" ", " "),
            ("directories:", ""),
            ("   input:         {}", self.INPUT_DIRECTORY),
            ("   output:        {}", self.RESULT_DIRECTORY),
            ("   prefix:        {}", self.NAMING_PREFIX),
            ("extension:        {}", self.EXTENSION),
            (" ", " "),
            ("modifications:", ""),
            ("   align:         {}", str(self.ALIGN)),
            ("   curve:         {}", str(self.APPLY_CURVE)),
            (" ", " "),
            ("save interval:    {}", str(self.SAVE_INTERVAL))
        ]

        self.log.debug("CONFIG:")
        for line in config:
            if len(line) > 1:
                self.log.debug(line[0].format(line[1]))
            else:
                self.log.debug(line)

        self.log.debug("---------------------------------------")


    def save(self, fixed_name=None, force_jpeg=False):

        filename = None

        if fixed_name is None:
            # {0:0Nd}{1} where N is used to pad to the length of the highest number of images (eg. 001 for 256 images)
            # pattern = str("{0:0") + str(len(str(len(self.input_images)))) + str("d}{1}")

            pattern = "{0:06d}{1}"
            filename = pattern.format(self.counter, self.EXTENSION)

            if force_jpeg:
                filename = str(self.counter) + ".jpg"

            if len(self.NAMING_PREFIX) > 0:
                filename = self.NAMING_PREFIX + "_" + filename
        else:
            filename = fixed_name

        filepath = os.path.join(self.RESULT_DIRECTORY, filename)

        t = self.tresor.copy()

        overflow_perc = np.amax(t) / (np.iinfo(np.uint64).max / 100.0)
        if overflow_perc > 70:
            self.log.warning("tresor overflow status: {}%".format(round(overflow_perc, 2)))

        if self.APPLY_CURVE:
            if self.weighted_average_divider > 0:
                t = t / (self.weighted_average_divider)
        else:
            if self.counter > 0:
                t = t / (self.counter)

        # convert to uint16 for saving, 0.5s faster than usage of t.astype(np.uint16)
        if self.EXTENSION == ".tif":
            s = np.asarray(t, np.uint16)
        else:
            s = np.asarray(t, np.uint8)

        self.log.debug("writing file: {}".format(filepath))

        if filename.endswith(".tif"):
            # taken from: https://blog.itsayellow.com/technical/saving-16-bit-tiff-images-with-pillow-in-python
            # size = (s.shape[1], s.shape[0])
            # img_out = Image.new('I;16', size)
            # outpil = s.astype(s.dtype.newbyteorder("<")).tobytes()
            # img_out.frombytes(outpil)
            # img_out.save(filepath)

            # tiff.imwrite(filepath, s)

            # Fast and easy way with OpenCV
            cv2.imwrite(filepath, s)
        else:
            # PIL does not support 16bit data directly
            # However, fromarray works fine for JPEGs
            Image.fromarray(s).save(filepath)

        if self.WRITE_METADATA:
            self.write_metadata(filepath, self.metadata)

        return filepath


    def read_metadata(self, images):
        info = {}

        # exposure time
        earliest_image  = None
        latest_image    = None

        for image in images:
   
            with open(os.path.join(self.INPUT_DIRECTORY, image), 'rb') as f:
                metadata = exifread.process_file(f)

                timetaken = self._get_exif_capturetime(metadata)

                if earliest_image is None or earliest_image[1] > timetaken:
                    earliest_image = (image, timetaken)

                if latest_image is None or latest_image[1] < timetaken:
                    latest_image = (image, timetaken)

        if earliest_image is not None and latest_image is not None:
            info["exposure_time"] = (latest_image[1] - earliest_image[1]).total_seconds()
        else: 
            info["exposure_time"] = 0
            self.log.warning("exposure_time could not be computed")

        with open(os.path.join(self.INPUT_DIRECTORY, images[0]), 'rb') as f:
            metadata = exifread.process_file(f)

            # capture date
            if latest_image is not None:
                info["capture_date"] = latest_image[1]
            else:
                info["capture_date"] = datetime.datetime.now()
                self.log.warning("exposure_time could not be computed")

            # number of images
            info["exposure_count"] = len(images)

            # focal length
            value = metadata["EXIF FocalLength"].values[0]
            info["focal_length"] = value.num / value.den
            if info["focal_length"] < 0:
                self.log.warning("EXIF: focal length missing")
                info["focal_length"] = None

            # compressor version
            try:
                info["version"] = subprocess.check_output(["git", "describe", "--always"], cwd=self.BASE_DIR)
                info["version"] = info["version"].decode("utf-8")
                if info["version"][-1] == "\n":
                    info["version"] = info["version"][:-1]
            except Exception as e:
                self.log.warning("compressor version not available. Error: {}".format(str(e)))
                if VERSION_NUMBER is None:
                    info["version"] = "not-available"
                else:
                    info["version"] = "{:5.2f}".format(VERSION_NUMBER)

            # compressing date
            info["compressing_date"] = datetime.datetime.now()

            return info


    def write_metadata(self, filepath, info):

        metadata = GExiv2.Metadata()
        metadata.open_path(filepath)

        compressor_name = "compressor v[{}]".format(info["version"])

        # Exif.Image.ProcessingSoftware is overwritten by Lightroom when the final export is done
        key = "Exif.Image.ProcessingSoftware";  metadata.set_tag_string(key, compressor_name)
        key = "Exif.Image.Software";            metadata.set_tag_string(key, compressor_name)

        try:
            key = "Exif.Image.ExposureTime";    metadata.set_exif_tag_rational(key, info["exposure_time"], 1)
        except Exception as e:
            key = "Exif.Image.ExposureTime";    metadata.set_exif_tag_rational(key, info["exposure_time"])
        key = "Exif.Image.ImageNumber";         metadata.set_tag_long(key, info["exposure_count"])
        key = "Exif.Image.DateTimeOriginal";    metadata.set_tag_string(key, info["capture_date"].strftime(self.EXIF_DATE_FORMAT))
        key = "Exif.Image.DateTime";            metadata.set_tag_string(key, info["compressing_date"].strftime(self.EXIF_DATE_FORMAT))

        if info["focal_length"] is not None:
            try:
                key = "Exif.Image.FocalLength"; metadata.set_exif_tag_rational(key, info["focal_length"])
            except Exception as e:
                key = "Exif.Image.FocalLength"; metadata.set_exif_tag_rational(key, info["focal_length"], 1)
        # TODO GPS Location

        metadata.save_file(filepath)
        self.log.debug("metadata written to {}".format(filepath))


    def _intensity(self, shutter, aperture, iso):

        # homebrew scene brightness metric (rather use EV with offset)
        # limits in this calculations:
        # min shutter is 1/4000th second

        # min aperture is 22
        # apertures: 22  16  11   8 5.6   4 2.8 2.0 1.4   1
        #            10   9   8   7   6   5   4   3   2   1  
        # log-value: 4.4               ...                0

        # min iso is 100

        shutter_repr    = math.log(shutter, 2) + 13 # offset = 13 to accomodate shutter values down to 1/4000th second
        iso_repr        = math.log(iso/100.0, 2) + 1  # offset = 1, iso 100 -> 1, not 0

        if aperture is not None:
            aperture_repr = np.interp(math.log(aperture, 2), [0, 4.5], [10, 1])
        else:
            aperture_repr = 1

        return shutter_repr + aperture_repr + iso_repr


    def _exposure_value(self, shutter, aperture, iso):
        
        ev = math.log(aperture / shutter, 2) - math.log(iso/100, 2)

        # self.log.error("EV: {:5.2f}".format(ev))

        ev += EV_OFFSET

        if ev < 1:
            self.log.warning("EV value below zero ({}). offset to low.".format(ev))

        return ev

    def _get_exif_capturetime(self, metadata):

        capturetime = None
        if "EXIF DateTimeOriginal" in metadata.keys():
            capturetime = metadata["EXIF DateTimeOriginal"].values
        elif "Image DateTime" in metadata.keys():
            capturetime = metadata["Image DateTime"].values
        elif "ModifyDate" in metadata.keys():
            capturetime = metadata["Image ModifyDate"].values
        else:
            raise Exception("time exif data missing. no brightness curve can be calculated") 
                
        capturetime = datetime.datetime.strptime(capturetime, self.EXIF_DATE_FORMAT)  
        return capturetime 


    def calculate_brightness_curve(self, images):
        values = []

        for image in images:

            with open(os.path.join(self.INPUT_DIRECTORY, image), "rb") as f:
                metadata = exifread.process_file(f)

                try:
                    shutter = metadata["EXIF ExposureTime"].values
                    if type(shutter) is list and type(shutter[0]) is exifread.utils.Ratio:
                        shutter = shutter[0].num / shutter[0].den
                    elif shutter[0] == 0 and shutter[1] == 0:
                        raise Exception("Shutter is 0/0")
                    else:
                        shutter = float(shutter)
                except Exception as e:
                    self.log.error("EXIF data missing for image: {} (error: {})".format(image, e))
                    import traceback
                    self.log.error(traceback.format_exc())
                    sys.exit(-1)

                iso = metadata["EXIF ISOSpeedRatings"].values[0]
                if iso is not None:
                    iso = int(iso)
                else:
                    iso = 100 

                capturetime = self._get_exif_capturetime(metadata)

                aperture = None
                if "EXIF FocalLength" in metadata.keys():
                    aperture = metadata["EXIF FocalLength"].values
                if type(aperture) is list:
                    if type(aperture[0]) is exifread.utils.Ratio:
                        aperture = aperture[0].num / aperture[0].den
                    else: 
                        aperture = aperture[0] / aperture[1]
                elif aperture is None or aperture < 0:
                    # no aperture tag set, probably an lens adapter was used. assume fixed aperture.
                    aperture = DEFAULT_APERTURE
                else:
                    self.log.warning("unexpected EXIF value for aperture: {}".format(aperture))
                    aperture = DEFAULT_APERTURE

                # values.append((image, capturetime, self._intensity(shutter, aperture, iso), self._luminosity(image)))
                values.append((image, capturetime, self._exposure_value(shutter, aperture, iso)))

                # self.log.debug("{} | {} || {}".format(
                #     self._exposure_value(shutter, aperture, iso), 
                #     self._intensity(shutter, aperture, iso), 
                #     self._exposure_value(shutter, aperture, iso)-self._intensity(shutter, aperture, iso))
                # )

        # normalize
        intensities = [x[2] for x in values]

        min_intensity = min(intensities)
        max_intensity = max(intensities)

        curve = []

        for i in range(0, len(values)):
            # range 0 to 1, because we have to invert the camera values to derive the brightness
            # value of the camera environment

            image_name                  = values[i][0]
            time                        = values[i][1]
            relative_brightness_value   = np.interp(values[i][2], [min_intensity, max_intensity], [0, 1])
            # inverted_absolute_value     = np.interp(values[i][2], [min_intensity, max_intensity], [max_intensity, min_intensity])
            # luminosity_value            = values[i][3]

            # right now the inverted absolute brightness, which is used for the weighted curve calculation,
            # is quite a large number. Usually around 20. (but every image is multiplied with it's respective value,
            # resulting in enormous numbers in the tresor matrix)
            #
            # better: value - min_brightness + 1 (result should never actually be zero)

            # inverted_absolute_value = inverted_absolute_value - min_brightness + 1

            # print(inverted_absolute_value)

            curve.append({
                "image_name": image_name, 
                "time": time, 
                "EV": values[i][2],                                 # measure how much light the camera needed (exposure value, lower means darker)
                "relative_brightness": relative_brightness_value,   # relative brightness (0: darkest scene, 1: brightest scene)
                "absolute_brightness": 2**values[i][2]              # absolute brightness (min: darkest scene, max: brightest scene)
            })

        absolute_brightnesses = [x["absolute_brightness"] for x in curve]
        self.curve_avg = sum(absolute_brightnesses) / float(len(absolute_brightnesses))

        return curve


    def display_curve(self, curve):
        
        import matplotlib.pyplot as plt

        dates = [i["time"] for i in curve]
        values_exif = [i["absolute_brightness"] for i in curve]
        values_luminosity = [i["EV"] for i in curve]

        # print(values_exif)

        plt.plot(dates, values_exif)
        plt.plot(dates, values_luminosity)
        # plt.plot(dates, values_luminosity)
        plt.savefig(os.path.join(self.RESULT_DIRECTORY, "curveplot.png"))
        # plt.show()


    def _load_image(self, filename, directory=None):
        # read input as 16bit color TIFF or plain JPG in 8bit
        if directory is not None:
            image_path = os.path.join(directory, filename)
        else:
            image_path = filename

        # no faster method found for TIF images than openCVs imread (tested: PIL, imageio, libtiff)
        # Problem: PIL/pillow does not support RGB-16bit data (16bit grayscales work)

        if filename.lower().endswith(".tif") or filename.lower().endswith(".tiff"):

            if not TIFF_SUPPORT:
                log.error("No TIFF support (openCV not found). Exit.")
                sys.exit(-1)

            return cv2.imread(image_path, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH) 
            # return tiff.imread(image_path)

        else: # assume JPEG

            # Note: if we use openCV to read the image we either need to write it with openCV as well or change the channel order
            # return cv2.imread(image_path, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH) 

            return np.asarray(Image.open(image_path))


    def stop_time(self, msg=None):
        seconds = (datetime.datetime.now() - self.timer).total_seconds()
        if msg is not None:
            if seconds >= 0.1:
                self.log.debug(msg.format(seconds, "s"))  
            else: # milliseconds
                self.log.debug(msg.format(seconds * 1000, "ms"))  

        self.timer = datetime.datetime.now()

        return seconds


    def reset_timer(self):
        self.timer = datetime.datetime.now()


    # def _plot(self, mat):
    #     # plot a numpy array with matplotlib
    #     plt.imshow(cv2.bitwise_not(cv2.cvtColor(np.asarray(mat, np.uint16), cv2.COLOR_RGB2BGR)), interpolation="nearest")
    #     plt.show()


    def print_info(self):

        # time calculations

        timeperimage = 0
        for key in self.stopwatch:
            timeperimage += self.stopwatch[key]
        timeperimage -= self.stopwatch["write_image"]
        timeperimage /= self.counter

        images_remaining = (self.LIMIT - self.counter) 
        est_remaining = images_remaining * timeperimage + ( (images_remaining/self.SAVE_INTERVAL) * (self.stopwatch["write_image"]/self.counter) )

        save_time = self.stopwatch["write_image"]/(self.counter/self.SAVE_INTERVAL)

        status =  "saved. counter: {:3d} | ".format(         self.counter) 
        status += "time total: {:.1f} | ".format(            (datetime.datetime.now()-self.starttime).total_seconds())
        status += "saving image: {:.1f} | ".format(          save_time) 
        status += "time per image: {:.1f} | ".format(        timeperimage)
        status += "est. remaining: {:.1f} || ".format(       est_remaining)
        status += support.Converter().humanReadableSeconds(  est_remaining)
        
        text =  "load_image: {load_image:.3f} | "
        text += "transform_image: {transform_image:.3f} | "
        text += "convert_to_array: {convert_to_array:.3f} | "
        text += "stacking: {stacking:.3f} | "
        text += "write_image: {write_image:.3f}"

        stopwatch_avg = self.stopwatch.copy()
        for key in stopwatch_avg:
            stopwatch_avg[key] /= self.counter
        # stopwatch_avg["write_image"] *= self.counter
        # stopwatch_avg["write_image"] /= int(self.counter/self.SAVE_INTERVAL)

        # print(status + "\n" + text.format(**stopwatch_avg), end="\r")

        self.log.info("processing image {:5d} / {:5d} ({:5.2f}%) | est. remaining: {}".format(
            self.counter, 
            len(self.input_images), 
            (self.counter/len(self.input_images)) * 100,
            support.Converter().humanReadableSeconds(est_remaining)
        ))

        for h in self.log.handlers:
            h.flush()

        # print(self.stopwatch)

    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

    def process(self, f):

        self.counter += 1
        if f in self.stacked_images:
            return

        im = self._load_image(f, directory=self.INPUT_DIRECTORY)
        self.stopwatch["load_image"] += self.stop_time()

        skip_processing = False

        # check if the image is too dark to care
        if self.PROCESSING_MODE == PROCESSING_MODE_STACK and self.MIN_BRIGHTNESS_THRESHOLD is not None:
                
            # value = np.max(im) # brightest pixel
            value = im.mean() # average brightness

            if value < self.MIN_BRIGHTNESS_THRESHOLD:
                self.log.debug("skipping image: {} (brightness below threshold)".format(f))
                skip_processing = True

        if not skip_processing:

            if self.ALIGN:
                # translation_data[f] = ( matrix, (computed_x, computed_y), (corrected_x, corrected_y) ) 

                warp_matrix_key = None
                for key in self.translation_data.keys():
                    if key.lower() <= f.lower():
                        warp_matrix_key = key
                    else:
                        break

                # if f not in self.translation_data:
                if warp_matrix_key is None:
                    self.log.warning("not aligned: translation data missing for {}".format(f))
                else:

                    matrix = np.matrix(self.translation_data[warp_matrix_key][0])

                    sum_abs_trans = abs(matrix[0, 2]) + abs(matrix[1, 2])
                    if sum_abs_trans > 100:
                        self.log.warning("\n   image {} not aligned: values too big: {:.2f}".format(f, sum_abs_trans))
                    else:
                        im = self.aligner.transform(im, matrix, im.shape)
                        self.stopwatch["transform_image"] += self.stop_time()

            # data = np.array(im, np.int) # 100ms slower per image
            data = np.uint64(np.asarray(im, np.uint64))
            self.stopwatch["convert_to_array"] += self.stop_time()

            if self.PROCESSING_MODE == PROCESSING_MODE_STACK:

                if self.APPLY_CURVE:
                    multiplier = self.curve[self.counter-1]["absolute_brightness"]
                    data = data * multiplier
                    self.weighted_average_divider += multiplier

                self.tresor = np.add(self.tresor, data)

            elif self.PROCESSING_MODE == PROCESSING_MODE_PEAK:

                brighter_mask = self.tresor < data 
                min_brightness_mask = data > 10 #120
                min_brightness_mask = np.any(min_brightness_mask, axis=2, keepdims=True)
                brighter_mask = np.logical_and(brighter_mask, min_brightness_mask)
                self.tresor[brighter_mask] = data[brighter_mask]

            elif self.PROCESSING_MODE == PROCESSING_MODE_SLICE:

                ind = self.input_images.index(f)
                num_images = len(self.input_images)
                # slice_width = max(1, int(num_images/self.DIMENSIONS[1]))
                # start = ind * slice_width
                # end = min(self.DIMENSIONS[1], start + slice_width)

                pixels_per_slice = math.floor(self.DIMENSIONS[1] / NUM_SLICES)
                images_per_slice = math.ceil(num_images / NUM_SLICES)  

                self.tresor2 = np.add(self.tresor2, data)

                if (ind+1) % images_per_slice == 0:

                    number_slice = int(ind / images_per_slice)
                    start = number_slice * pixels_per_slice
                    end = start + pixels_per_slice

                    self.tresor[:,start:end] = self.tresor2[:,start:end]/images_per_slice
                    self.tresor2.fill(0)

                    # print("num {} ind {} img {} px {} start {} end {}".format(number_slice, ind, images_per_slice, pixels_per_slice, start, end))

                elif ind == num_images-1:
                    end = self.DIMENSIONS[1]-1
                    start = end - pixels_per_slice+1
                    self.tresor[:,start:end] = self.tresor2[:,start:end]/((ind % images_per_slice) + 1)
                    self.tresor2.fill(0)

                    # print("ind {} img {} px {} start {} end {}".format(ind, images_per_slice, pixels_per_slice, start, end))              

            else:   
                self.log.error("unknown PROCESSING_MODE: {}".format(self.PROCESSING_MODE))
                exit(-1)

            self.stopwatch["stacking"] += self.stop_time()

        self.stacked_images.append(f)

        if self.SAVE_INTERVAL > 0 and self.counter % self.SAVE_INTERVAL == 0:
            self.save(force_jpeg=self.INTERMEDIATE_SAVE_FORCE_JPEG)

        self.stopwatch["write_image"] += self.stop_time()

        self.print_info()

        # print("counter: {0:.0f}/{1:.0f}".format(self.counter, len(self.input_images)), end="\r")


    def run(self, inp_imgs):

        self.input_images = inp_imgs

        # self.input_images = self.input_images[:720]

        self.starttime = datetime.datetime.now()
        self.timer = datetime.datetime.now()

        self.LIMIT = len(self.input_images)

        if self.LIMIT <= 0:
            self.log.error("no images found. exit.")
            sys.exit(-1)

        self.stop_time("searching for files: {0:.3f}{1}")
        self.log.info("number of images: {}".format(self.LIMIT))

        if self.WRITE_METADATA:
            self.metadata = self.read_metadata(self.input_images)

        if self.DIMENSIONS is None:
            # cv2.imread(os.path.join(self.INPUT_DIRECTORY, self.input_images[0])).shape
            shape = self._load_image(self.input_images[0], directory=self.INPUT_DIRECTORY).shape
            self.DIMENSIONS = (shape[1], shape[0])

        self.tresor = np.zeros((self.DIMENSIONS[1], self.DIMENSIONS[0], 3), dtype=np.uint64)

        if self.PROCESSING_MODE == PROCESSING_MODE_SLICE:
            if len(self.input_images) < NUM_SLICES:
                self.log.error("too few images for processing mode SLICE (only {} images but {} slices)".format(len(self.input_images), NUM_SLICES))
                exit(-1)

            self.tresor2 = np.zeros((self.DIMENSIONS[1], self.DIMENSIONS[0], 3), dtype=np.uint64)            
        
        self.stop_time("initialization: {0:.3f}{1}")

        # Curve
        if self.DISPLAY_CURVE or self.APPLY_CURVE:
            self.curve = self.calculate_brightness_curve(self.input_images)
            
            # for item in self.curve:
            #     print(item)

            # sys.exit(0)
            self.stop_time("compute brightness curve: {0:.3f}{1}")

        if self.DISPLAY_CURVE:
            self.display_curve(self.curve)

        if self.ALIGN:
            self.log.debug("translation data: {}".format(self.aligner.TRANSLATION_DATA))
            self.translation_data = json.load(open(self.aligner.TRANSLATION_DATA, "r"))

        # for item in self.curve:
        #     print("{0:20s} | brightness: {1:>3.1f} | luminosity: {2:>3.1f}".format(item["image_name"], item["brightness"], item["luminosity"]))

        # sys.exit(0)

        # print(*self.input_images[0:10], sep="\n")

        for f in self.input_images:
            try:
                self.process(f)
            except Exception as e:
                self.log.error("ERROR in image: {}".format(f))
                raise(e)

        filepath = self.save(fixed_name=self.FIXED_OUTPUT_NAME)

        self.log.info("finished. time total: {}".format(datetime.datetime.now() - self.starttime))
        sys.exit(0)
