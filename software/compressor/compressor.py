#!/usr/bin/env python3

from aligner import Aligner
from stitcher import Stitcher
from stacker import Stacker

import argparse

import os
import sys
import support
import yaml

import cv2
import numpy as np

import config


def print_config():
    pass


def path_check_and_expand(path):
    if not (path.startswith("/") or path.startswith("~")):
        path = os.path.join(BASE_DIR, path)

    if path.startswith("~"):
        path = os.path.expanduser(path)

    return path


def create_if_not_existing(path):
    if not os.path.exists(path):
        print("created directoy: {}".format(path))
        os.makedirs(path)


def abort_if_missing(path):
    if not os.path.exists(path):
        print("dir not found: {}".format(support.Color.BOLD + path + support.Color.END))
        sys.exit(-1)


def get_all_file_names(input_dir):

    if config.EXTENSION is not None:

        file_list = []

        # recursive:
        # for root, dirs, files in os.walk(input_dir):
        #     for f in files:

        counter = 0

        for f in os.listdir(input_dir):

            if f == ".DS_Store":
                counter += 1
                continue

            if not f.lower().endswith(config.EXTENSION):
                counter += 1
                continue

            if os.path.getsize(os.path.join(input_dir, f)) < 100:
                counter += 1
                continue

            file_list.append(f)

        if counter > 0:
            print("skipped {} files during parsing of directory {}".format(counter, input_dir))

        return file_list

    else: # EXTENSION autodetect

        file_list_jpg = []
        file_list_tif = []

        for f in os.listdir(input_dir):
   
            if f.lower().endswith(".jpg"):
                file_list_jpg.append(f)

            if f.lower().endswith(".tif"):
                file_list_tif.append(f)

        print("Extension autodetection: {} JPGs, {} TIFs found.".format(len(file_list_jpg), len(file_list_tif)))

        if (len(file_list_jpg) > 0 and len(file_list_jpg) >= len(file_list_tif)):
            print("Extension autodetection: JPG choosen")
            config.EXTENSION = ".jpg"
            return file_list_jpg

        if (len(file_list_tif) > 0 and len(file_list_tif) >= len(file_list_jpg)):
            print("Extension autodetection: TIF choosen")
            config.EXTENSION = ".tif"
            return file_list_tif

        print("Extension autodetection failed")
    
    return []


def _sort_helper(value):

    # still_123.jpg

    if value.startswith("still_"):
        pos = value.index(".")
        number = value[6:pos]
        return int(number)        
    elif value.startswith("DSCF"):
        pos = value.index(".")
        number = value[4:pos]
        return int(number)
    elif value.startswith("DSC"):
        pos = value.index(".")
        number = value[3:pos]
        return int(number)
    elif value.startswith("DJI_"):
        pos = value.index(".")
        number = value[4:pos]
        return int(number)
    else:
        try:
            filename = os.path.splitext(value)[0]
            return int(filename)
        except ValueError as e:
            return filename


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

parser = argparse.ArgumentParser(description="Stack several image files to create digital long exposure photographies")
parser.add_argument("--align", action="store_true", help="run only the aligner, do not compress")
parser.add_argument("--transform", action="store_true", help="run only the aligner and transform, do not compress")
parser.add_argument("--stitch", action="store_true", help="stitch images for panoramic formats")
args = parser.parse_args()

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

aligner = Aligner()
stitcher = Stitcher()
stacker = Stacker(aligner)
input_images_aligner = []
input_images_stitcher = []
input_images_stacker = []

# transform to absolute paths
BASE_DIR = os.path.dirname(os.path.realpath(__file__))

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

# init aligner

if args.align or args.transform:

    # expand all paths
    for directory in config.DIRS_TO_EXPAND_ALIGNER:
        variable = getattr(config, directory)
        if variable is None:
            print("warning: variable {} empty. not expanded".format(directory))
            continue
        setattr(config, directory, path_check_and_expand(variable))

    for directory in config.DIRS_TO_CREATE_ALIGNER:
        variable = getattr(config, directory)
        create_if_not_existing(variable)

    for directory in config.DIRS_ABORT_IF_MISSING_ALIGNER:
        variable = getattr(config, directory)
        abort_if_missing(variable)

    input_images_aligner = get_all_file_names(config.INPUT_DIR_ALIGNER)

    if config.SORT_IMAGES:
        input_images_aligner = sorted(input_images_aligner, key=_sort_helper)

    if config.REFERENCE_IMAGE is None:
        if len(input_images_aligner) == 0:
            print("aligner: no input images. abort.")
            sys.exit(-1)
        config.REFERENCE_IMAGE = os.path.join(path_check_and_expand(config.INPUT_DIR_ALIGNER), input_images_aligner[0])
        print(config.REFERENCE_IMAGE)
        print("aligner: no reference image specified. defaulting to first image.")

    aligner.REFERENCE_IMAGE                 = config.REFERENCE_IMAGE
    aligner.INPUT_DIR                       = config.INPUT_DIR_ALIGNER
    aligner.OUTPUT_DIR                      = config.OUTPUT_DIR_ALIGNER
    aligner.EXTENSION                       = config.EXTENSION
    aligner.TRANSLATION_DATA                = config.TRANSLATION_DATA
    aligner.RESET_MATRIX_EVERY_LOOP         = config.RESET_MATRIX_EVERY_LOOP
    aligner.DOWNSIZE                        = config.DOWNSIZE
    aligner.DOWNSIZE_FACTOR                 = config.DOWNSIZE_FACTOR
    aligner.JSON_SAVE_INTERVAL              = config.JSON_SAVE_INTERVAL
    aligner.SKIP_TRANSLATION                = config.SKIP_TRANSLATION
    aligner.TRANSFER_METADATA               = config.TRANSFER_METADATA

    aligner.init()

    if args.align:
        aligner.step1(input_images_aligner)

    # aligner.init()

    if args.transform:
        aligner.step2()

# init stitcher

if args.stitch:

    stitcher.INPUT_DIR                      = config.INPUT_DIR_STITCHER
    stitcher.OUTPUT_DIR                     = config.OUTPUT_DIR_STITCHER

    input_images_stitcher = [["stitcher_test/1.jpg", "stitcher_test/2.jpg"]]

    stitcher.init()
    stitcher.run(input_images_stitcher)

# init stacker

if not args.align and not args.transform and not args.stitch:

    # expand all paths
    for directory in config.DIRS_TO_EXPAND_STACKER:
        variable = getattr(config, directory)
        if variable is None:
            print("warning: variable {} empty. not expanded".format(directory))
            continue
        setattr(config, directory, path_check_and_expand(variable))

    for directory in config.DIRS_TO_CREATE_STACKER:
        variable = getattr(config, directory)
        create_if_not_existing(variable)

    for directory in config.DIRS_ABORT_IF_MISSING_STACKER:
        variable = getattr(config, directory)
        abort_if_missing(variable)

    input_images_stacker = get_all_file_names(config.INPUT_DIR_STACKER)

    # min size

    num_skipped = 0
    input_images_stacker_nonempty = []
    for img in input_images_stacker:
        if os.path.getsize(os.path.join(config.INPUT_DIR_STACKER, img)) < 100:
            num_skipped += 1
        else:
            input_images_stacker_nonempty.append(img)
    input_images_stacker = input_images_stacker_nonempty
    print("skipped {} images smaller than 100 bytes".format(num_skipped))

    # missing second image

    num_skipped = 0
    input_images_stacker_nonempty = []
    for img in input_images_stacker:
        if img.lower().endswith("_2.jpg") or img.lower().endswith("_2.tif"):
            num_skipped += 1
        else:
            input_images_stacker_nonempty.append(img)
    input_images_stacker = input_images_stacker_nonempty
    print("skipped {} peaking images (suffix _2.EXTENSION)".format(num_skipped))

    # min brightness

    # if config.MIN_BRIGHTNESS_THRESHOLD is not None:
    #     num_skipped = 0
    #     input_images_stacker_nonempty = []
    #     for img in input_images_stacker:

    #         im = cv2.imread(os.path.join(config.INPUT_DIR_STACKER, img), cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH) 
            
    #         # value = np.max(im) # brightest pixel
    #         value = im.mean() # average brightness

    #         if value < config.MIN_BRIGHTNESS_THRESHOLD:
    #             num_skipped += 1
    #         else:
    #             input_images_stacker_nonempty.append(img)

    #         # print("{} - {}".format(img, im.mean()))
    #         # exit()

    #     input_images_stacker = input_images_stacker_nonempty
    #     print("skipped {} images darker than {}".format(num_skipped, config.MIN_BRIGHTNESS_THRESHOLD))

    # sort

    if config.SORT_IMAGES:
        input_images_stacker = sorted(input_images_stacker, key=_sort_helper)

    # debug file sorting: 
    # print(*input_images_stacker, sep="\n")
    # exit()

    stacker.NAMING_PREFIX               = config.NAMING_PREFIX
    stacker.INPUT_DIRECTORY             = config.INPUT_DIR_STACKER
    stacker.RESULT_DIRECTORY            = config.OUTPUT_DIR_STACKER

    if config.FIXED_OUTPUT_NAME.endswith(config.EXTENSION):
        stacker.FIXED_OUTPUT_NAME       = config.FIXED_OUTPUT_NAME
    else:
        stacker.FIXED_OUTPUT_NAME       = config.FIXED_OUTPUT_NAME + config.EXTENSION

    stacker.BASE_DIR                    = BASE_DIR
    stacker.EXTENSION                   = config.EXTENSION
    stacker.PICKLE_NAME                 = config.PICKLE_NAME

    stacker.ALIGN                       = config.ALIGN

    if config.ALIGN:
        aligner.TRANSLATION_DATA        = config.TRANSLATION_DATA

    stacker.MIN_BRIGHTNESS_THRESHOLD    = config.MIN_BRIGHTNESS_THRESHOLD

    stacker.DISPLAY_CURVE               = config.DISPLAY_CURVE
    stacker.APPLY_CURVE                 = config.APPLY_CURVE

    stacker.DISPLAY_PEAKING             = config.DISPLAY_PEAKING
    stacker.APPLY_PEAKING               = config.APPLY_PEAKING
    stacker.PEAKING_STRATEGY            = config.PEAKING_STRATEGY
    stacker.PEAKING_FROM_2ND_IMAGE      = config.PEAKING_FROM_2ND_IMAGE 
    stacker.PEAKING_IMAGE_THRESHOLD     = config.PEAKING_IMAGE_THRESHOLD
    stacker.PEAKING_BLEND               = config.PEAKING_BLEND
    stacker.PEAKING_PIXEL_THRESHOLD     = config.PEAKING_PIXEL_THRESHOLD
    stacker.PEAKING_MUL_FACTOR          = config.PEAKING_MUL_FACTOR

    stacker.WRITE_METADATA              = config.WRITE_METADATA

    stacker.SAVE_INTERVAL               = config.SAVE_INTERVAL
    stacker.INTERMEDIATE_SAVE_FORCE_JPEG = config.INTERMEDIATE_SAVE_FORCE_JPEG
    stacker.PICKLE_INTERVAL             = config.PICKLE_INTERVAL

    stacker.post_init()
    stacker.print_config()
    stacker.run(input_images_stacker)
