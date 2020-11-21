#!/usr/bin/env python3

# from aligner import Aligner
# from stitcher import Stitcher
import stacker
import config

# import argparse
from gooey import Gooey, GooeyParser, local_resource_path

import os
import sys
import support
import yaml

import logging as log

from multiprocessing import freeze_support


VERSION = "1.0.0"


def blockstring_to_string(s):

    # s = s.replace("\n", "")
    # s = s.replace("\r", "")
    # return s

    return " ".join(s.split())


def create_if_not_existing(path):
    if not os.path.exists(path):
        log.debug("created directoy: {}".format(path))
        os.makedirs(path)


def abort_if_missing(path):
    if not os.path.exists(path):
        log.error("dir not found: {}".format(support.Color.BOLD + path + support.Color.END))
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
            log.debug("skipped {} files during parsing of directory {}".format(counter, input_dir))

        return file_list

    else: # EXTENSION autodetect

        file_list_jpg = []
        file_list_tif = []

        for f in os.listdir(input_dir):
   
            if f.lower().endswith(".jpg"):
                file_list_jpg.append(f)

            if f.lower().endswith(".tif"):
                file_list_tif.append(f)

        log.debug("Extension autodetection: {} JPGs, {} TIFs found.".format(len(file_list_jpg), len(file_list_tif)))

        if (len(file_list_jpg) > 0 and len(file_list_jpg) >= len(file_list_tif)):
            log.debug("Extension autodetection: JPG choosen")
            config.EXTENSION = ".jpg"
            return file_list_jpg

        if (len(file_list_tif) > 0 and len(file_list_tif) >= len(file_list_jpg)):
            log.debug("Extension autodetection: TIF choosen")
            config.EXTENSION = ".tif"
            return file_list_tif

        log.warning("Extension autodetection failed")
    
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

gooey_options = {
    "program_name":         "Compressor",
    "description":          "Merge images to create digital long exposure photographies",
    "required_cols":        1,
    "show_stop_warning":    False,
    "image_dir":            local_resource_path("icons"),
    "progress_regex":       r"processing image[\ ]*(?P<current>\d+) \/[\ ]*(?P<total>\d+)",
    "progress_expr":        "current / total * 100",
    "menu":                 [{  'name': 'File', 
                                'items': [{
                                    'type': 'AboutDialog',
                                    'menuTitle': 'About',
                                    'name': 'Compressor',
                                    'description': 'Merge images to create digital long exposure photographies',
                                    'version': VERSION,
                                    'website': 'https://github.com/volzotan/CompressorCam',
                                    'developer': 'https://digitalsolargraphy.com/'
                                }]
                            }]
}

@Gooey(**gooey_options)
def main():

    # parser = argparse.ArgumentParser(description="Stack images to create digital long exposure photographies")
    parser = GooeyParser()

    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="detailed output messages"
    )

    # subs = parser.add_subparsers(help='commands', dest='command')

    # stack_parser = subs.add_parser("stack", help="compress correctly exposed images for a single long exposure image")
    # peak_parser = subs.add_parser("peak", help="peak underexposed images for a single long sun-arc image")

    # stack_parser.add_argument(
    #     "input-dir", 
    #     widget="DirChooser",
    #     help="directory containing all input images"
    # )

    # stack_parser.add_argument(
    #     "output-dir", 
    #     widget="DirChooser",
    #     help="output directory for results"
    # )
   
    # peak_parser.add_argument(
    #     "input-dir", 
    #     widget="DirChooser",
    #     help="directory containing all input images"
    # )

    # peak_parser.add_argument(
    #     "output-dir", 
    #     widget="DirChooser",
    #     help="output directory for results"
    # )
   
    parser.add_argument(
        "processingmode",
        default=stacker.PROCESSING_MODE_STACK,
        choices=[stacker.PROCESSING_MODE_STACK, stacker.PROCESSING_MODE_PEAK], 
        help=blockstring_to_string("""
        '{}' blends several correctly exposed images to a single long exposure image. 
        '{}' blends several underexposed images to a peaked image showing the burned parts.
        """.format(stacker.PROCESSING_MODE_STACK, stacker.PROCESSING_MODE_PEAK))
    )

    parser.add_argument(
        "inputdir", 
        default=".",
        widget="DirChooser",
        help="input directory containing all images for processing"
    )

    parser.add_argument(
        "--outputdir", 
        widget="DirChooser",
        help="output directory for results"
    )

    args = parser.parse_args()

    # initialize logger

    logger = log.getLogger() 
    logger.setLevel(log.DEBUG)

    log.basicConfig(level=log.DEBUG)
    #                     format="%(asctime)s | %(levelname)-7s | %(message)s",
    #                     datefmt='%m-%d %H:%M',
    # )

    # formatter = log.Formatter("%(asctime)s | %(levelname)-7s | %(message)s")
    # consoleHandler = log.StreamHandler()
    # consoleHandler.setLevel(log.DEBUG)
    # consoleHandler.setFormatter(formatter)
    # logger.addHandler(consoleHandler)

    # subloggers
    ezdxf_logger = log.getLogger("exifread").setLevel(log.WARN)
    ezdxf_logger = log.getLogger("PIL").setLevel(log.WARN)

    root = log.getLogger()
    root_handler = root.handlers[0]
    formatter = log.Formatter("%(asctime)s | %(name)-10s | %(levelname)-7s | %(message)s")
    root_handler.setFormatter(formatter)

    # ---

    stack = stacker.Stack(None)
    input_images_stack = []

    # transform to absolute paths
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))

    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

    if args.outputdir is None:
        if args.processingmode == stacker.PROCESSING_MODE_STACK:
            args.outputdir = args.inputdir + "_stacked"
        elif args.processingmode == stacker.PROCESSING_MODE_PEAK:
            args.outputdir = args.inputdir + "_peaked"
        else:
            args.outputdir = args.inputdir + "_undefined" 

    for directory in [args.inputdir]:
        abort_if_missing(directory)

    for directory in [args.outputdir]:
        create_if_not_existing(directory)

    input_images_stack = get_all_file_names(args.inputdir)

    # min size

    num_skipped = 0
    input_images_stack_nonempty = []
    for img in input_images_stack:
        if os.path.getsize(os.path.join(args.inputdir, img)) < 100:
            num_skipped += 1
        else:
            input_images_stack_nonempty.append(img)
    input_images_stack = input_images_stack_nonempty
    log.info("skipped {} images smaller than 100 bytes".format(num_skipped))

    # missing second image

    # num_skipped = 0
    # input_images_stack_nonempty = []
    # for img in input_images_stack:
    #     if img.lower().endswith("_2.jpg") or img.lower().endswith("_2.tif"):
    #         num_skipped += 1
    #     else:
    #         input_images_stack_nonempty.append(img)
    # input_images_stack = input_images_stack_nonempty
    # print("skipped {} peaking images (suffix _2.EXTENSION)".format(num_skipped))

    # min brightness

    # if config.MIN_BRIGHTNESS_THRESHOLD is not None:
    #     num_skipped = 0
    #     input_images_stack_nonempty = []
    #     for img in input_images_stack:

    #         im = cv2.imread(os.path.join(config.INPUT_DIR_STACKER, img), cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH) 
            
    #         # value = np.max(im) # brightest pixel
    #         value = im.mean() # average brightness

    #         if value < config.MIN_BRIGHTNESS_THRESHOLD:
    #             num_skipped += 1
    #         else:
    #             input_images_stack_nonempty.append(img)

    #         # print("{} - {}".format(img, im.mean()))
    #         # exit()

    #     input_images_stack = input_images_stack_nonempty
    #     print("skipped {} images darker than {}".format(num_skipped, config.MIN_BRIGHTNESS_THRESHOLD))

    if len(input_images_stack) == 0:
        log.error("no input images found. exiting...")
        exit(0)

    # sort

    if config.SORT_IMAGES:
        input_images_stack = sorted(input_images_stack, key=_sort_helper)

    # config file loading

    stack.NAMING_PREFIX                 = config.NAMING_PREFIX
    stack.INPUT_DIRECTORY               = args.inputdir
    stack.RESULT_DIRECTORY              = args.outputdir

    if config.FIXED_OUTPUT_NAME.endswith(config.EXTENSION):
        stack.FIXED_OUTPUT_NAME         = config.FIXED_OUTPUT_NAME
    else:
        stack.FIXED_OUTPUT_NAME         = config.FIXED_OUTPUT_NAME + config.EXTENSION

    stack.BASE_DIR                      = BASE_DIR
    stack.EXTENSION                     = config.EXTENSION

    stack.PROCESSING_MODE               = args.processingmode

    stack.ALIGN                         = config.ALIGN
    if config.ALIGN:
        aligner.TRANSLATION_DATA        = config.TRANSLATION_DATA

    stack.MIN_BRIGHTNESS_THRESHOLD      = config.MIN_BRIGHTNESS_THRESHOLD

    stack.DISPLAY_CURVE                 = config.DISPLAY_CURVE
    stack.APPLY_CURVE                   = config.APPLY_CURVE

    stack.WRITE_METADATA                = config.WRITE_METADATA

    stack.SAVE_INTERVAL                 = config.SAVE_INTERVAL
    stack.INTERMEDIATE_SAVE_FORCE_JPEG  = config.INTERMEDIATE_SAVE_FORCE_JPEG

    stack.post_init()
    stack.print_config()
    stack.run(input_images_stack)

if __name__ == "__main__":

    # fix: https://github.com/pyinstaller/pyinstaller/issues/3907
    freeze_support()

    main()
