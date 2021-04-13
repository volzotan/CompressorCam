#!/usr/bin/env python3

from config import *

from time import sleep
from datetime import datetime, timedelta
from fractions import Fraction
import math
import os
import sys
import shutil
import argparse
import subprocess
import traceback
import logging
from concurrent.futures import ThreadPoolExecutor

import exifread
import picamera

from devices import CompressorCameraController
from uploader import RsyncUploader
from bleadvertisement import advertise

from PIL import Image

"""                      
┌─┐┌─┐┌┬┐┌─┐┬─┐┌─┐┌─┐┌─┐┌─┐┬─┐┌─┐┌─┐┌┬┐
│  │ ││││├─┘├┬┘├┤ └─┐└─┐│ │├┬┘│  ├─┤│││
└─┘└─┘┴ ┴┴  ┴└─└─┘└─┘└─┘└─┘┴└─└─┘┴ ┴┴ ┴

INFO:

Serial Console:

ttyAMA0 is linked to the PL011 UART controller (the good one). The BT module occupies
this by default. If enable_uart=1 in /boot/config.txt is set, ttyS0 (mini UART, the bad one) 
is available and can be used for serial. Better option: either disable BT (dtoverlay=disable-bt)
or move BT to the mini UART (dtoverlay=miniuart-bt) via config.txt.
Buildroot does the latter if --add-miniuart-bt-overlay is set.

more info:
https://www.abelectronics.co.uk/kb/article/1035/raspberry-pi-3--4-and-zero-w-serial-port-usage
https://www.raspberrypi.org/documentation/configuration/uart.md

Camera Module:

The maximum resolution of the V2 camera may require additional GPU memory when 
operating at low framerates (<1fps). Increase gpu_mem in /boot/config.txt if you 
encounter “out of resources” errors when attempting long-exposure captures with 
a V2 module.

The maximum exposure time is currently 6 seconds on the V1 camera module, and 
10 seconds on the V2 camera module. Remember that exposure time is limited by 
framerate, so you need to set an extremely slow framerate before setting 
shutter_speed.

-- from: https://picamera.readthedocs.io/en/release-1.13/fov.html#hardware-limits

PiCamera creates problems when used with python 3.8.1 
(3.8.2 realeased, so not an issue anymore)

-- from: https://github.com/waveform80/picamera/issues/604

To use the Raspberry Pi Camera the extended GPU firmware is required.
Raspbian: start_x=1 in config.txt needs to be set
Buildroot: Hardware Handling -> Firmware -> Extended (but no start_x=1)

PiCamera needs at least 256mb of GPU memory. In config.txt:
gpu_mem_512=256

"""

def read_exif_data(filename):

    log = logging.getLogger()

    with open(filename, 'rb') as f:
        metadata = exifread.process_file(f)

        # for tag in metadata.keys():
        #     if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
        #         print("Key: {}, value {}".format(tag, metadata[tag]))

                    # shutter speed in seconds (e.g. 0.5)

        shutter_speed_val = metadata["EXIF ExposureTime"].values[0]
        if shutter_speed_val.num == 0 or shutter_speed_val.den == 0:
            shutter_speed = 0
        else:
            shutter_speed = float(shutter_speed_val.num) / float(shutter_speed_val.den)

        # ISO (e.g. 100)

        iso = float(metadata["EXIF ISOSpeedRatings"].values[0])

        # Aperture (e.g. 5.6)

        aperture = 8 # default value (may be set for HQ module)
        if "EXIF FNumber" in metadata:
            aperture_val = metadata["EXIF FNumber"].values[0]

            if aperture_val.num == 0 or aperture_val.den == 0:
                log.debug("aperture value is 0")
            else:
                aperture = aperture_val.num / aperture_val.den
        else:
            log.debug("aperture value is missing")

        log.info("Exif exposure time      : {}".format(shutter_speed))
        log.info("Exif aperture           : {}".format(aperture))
        log.info("Exif ISO                : {}".format(iso))

        ev = math.log(aperture / shutter_speed, 2) - math.log(iso/100, 2)

        return ev


def print_exposure_settings(camera):

    STATEMENT = "{:25s}: {}"

    print(STATEMENT.format("Shutter speed (0=auto)", camera.shutter_speed))
    print(STATEMENT.format("ISO", camera.iso))
    print(STATEMENT.format("Analog gain", camera.analog_gain))
    print(STATEMENT.format("Digital gain", camera.digital_gain))
    print(STATEMENT.format("Exp speed", camera.exposure_speed))
    print(STATEMENT.format("Exp mode", camera.exposure_mode))
    print(STATEMENT.format("Exp compensation", camera.exposure_compensation))
    print(STATEMENT.format("Meter mode", camera.meter_mode))
    print(STATEMENT.format("Framerate", camera.framerate))
    print(STATEMENT.format("brightness", camera.brightness))
    print(STATEMENT.format("Awb mode", camera.awb_mode))
    print(STATEMENT.format("Drc strength", camera.drc_strength))
    print(STATEMENT.format("Brightness meter mode", camera.meter_mode))
    print(STATEMENT.format("Resolution", camera.resolution))

    print("--- --- ---")


def log_capture_info(camera, filename):

    log.info("{:24s}: {}".format("filename", filename))

    log.info("{:24s}: {}".format("shutter speed", camera.shutter_speed)) # microseconds
    log.info("{:24s}: {:.10}".format("exposure speed", camera.exposure_speed/(1000*1000)))

    log.info("{:24s}: {}".format("iso", camera.iso))
    log.info("{:24s}: {:4.2f}".format("analog gain", float(camera.analog_gain)))
    log.info("{:24s}: {:4.2f}".format("digital gain", float(camera.digital_gain)))

    awb_gains = camera.awb_gains
    log.info("{:24s}: {} {:4.2f} | {:4.2f}".format("awb", camera.awb_mode, float(awb_gains[0]), float(awb_gains[1])))


def get_uptime():    

    uptime = None

    try:
        f = open('/proc/uptime','r')
        for line in f:
            uptime = float(line.split(" ")[0])
        f.close()
    except Exception as e:
        log.warn("reading uptime failed: {}".format(e))

    return uptime


def get_serial():

    serial = None

    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:6]=='Serial':
                serial = line[10:26]
        f.close()
    except Exception as e:
        log.warn("reading serial failed: {}".format(e))

    return serial


def calculate_brightness(filename):

    with Image.open(filename) as image:
        greyscale_image = image.convert('L')
        histogram = greyscale_image.histogram()
        pixels = sum(histogram)
        brightness = scale = len(histogram)

        for index in range(0, scale):
            ratio = histogram[index] / pixels
            brightness += ratio * (-scale + index)

        return 1 if brightness == 255 else brightness / scale


# all extensions are checked for duplicate filenames, first extension 
# is returned as file name candidate
def get_filename(extensions, prefix=None): # returns(path, filename.ext)

    if not type(extensions) is list:
        extensions = [extensions]

    for i in range(0, len(extensions)):
        if extensions[i] == "jpeg":
            extensions[i] = "jpg"

    for i in range(0, 100000):

        filename_base = "{}_{:06d}.".format(OUTPUT_FILENAME, i)
        if not prefix is None:
            filename_base = prefix + filename_base
        duplicate_found = False

        for extension in extensions:
            filename = filename_base + extension
            if os.path.exists(os.path.join(OUTPUT_DIR_1, filename)):
                duplicate_found = True
                break

        if not duplicate_found:
            return (OUTPUT_DIR_1, filename_base + extensions[0], i)

    raise Exception("no filenames left!")


def run_subprocess(cmd):

    # combine STDERR and STDOUT to STDOUT
    subp = subprocess.run(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = subp.stdout.decode("utf-8")

    if output[-1] == "\n":
        output = output[:-1]

    return output


def global_except_hook(exctype, value, tb):
    
    log = logging.getLogger()

    log.error("global error: {} | {}".format(exctype, value))

    logging.shutdown()

    subprocess.call(["sync"])
    sleep(1.0)

    print("sync called. traceback:")
    traceback.print_tb(tb)

    exit()

    # sys.__excepthook__(exctype, value, traceback)


def trigger():

    image_info = []

    # starts hidden preview for 3A automatically
    camera = picamera.PiCamera(sensor_mode=SENSOR_MODE) 

    # sensor modes:
    # MODE  : SETTING           : CAMERA 
    # 0     : automatic         : all
    # 2     : 1    <  fps <= 15 : v1
    # 3     : 1/6  <= fps <= 1  : v1   
    # 2     : 1/10 <= fps <= 15 : v2
    # 3     : 1/10 <= fps <= 15 : v2
    # 2     : 0.1-50fps         : HQ (2x2 binned = half resolution)
    # 3     : 0.005-10fps       : HQ

    camera.exposure_mode = "verylong"
    
    camera.meter_mode = "average"
    camera.exposure_compensation = EXPOSURE_COMPENSATION
    # camera.iso = 400

    resolutions = {}
    resolutions["HQ"] = [[4056, 3040], Fraction(1, 2)]
    resolutions["V2"] = [[3280, 2464], Fraction(1, 2)]
    resolutions["V1"] = [[2592, 1944], Fraction(1, 2)]

    for key in resolutions.keys():
        try:
            camera.resolution = resolutions[key][0]
            camera.framerate = resolutions[key][1]
            log.debug("camera resolution set to [{}]: {}".format(key, resolutions[key][0]))
            break
        except picamera.exc.PiCameraValueError as e:
            log.warning("failing setting camera resolution for {}, attempting fallback".format(key))

    # give the 3A algorithms some time for warmup
    sleep(1)

    log.debug("------ exposure 1 ------")

    prefix = None
    if USE_TIMESTAMP_PREFIX:
        prefix = "{}_".format(int(datetime.now().timestamp()))

    filename_path, filename, filename_iteration = get_filename([IMAGE_FORMAT, "jpg.gz", "jpeg.gz"], prefix=prefix)
    full_filename = os.path.join(filename_path, filename)

    capture_raw = WRITE_RAW
    if WRITE_RAW and MODULO_RAW is not None:
        if filename_iteration % MODULO_RAW == 0:
            capture_raw = True
        else:
            capture_raw = False

    camera.capture(full_filename, format=IMAGE_FORMAT, bayer=capture_raw)
    
    # log_capture_info(camera, full_filename)
    # print_exposure_settings(camera)
    
    log_capture_info(camera, full_filename)
    first_exposure_ev = read_exif_data(full_filename)
    future_brightness_1 = pool.submit(calculate_brightness, (full_filename))
    image_info.append([full_filename, first_exposure_ev, filename_iteration, future_brightness_1])

    log.info("brightness              : {:.2f} EV".format(first_exposure_ev))
    log.info("contains raw data       : {}".format(capture_raw))
    # if ND_FILTER is not None:
    #     log.info("brightness (incl ND): {:.2f} EV".format(first_exposure_ev+ND_FILTER))
    # print_exposure_settings(camera)

    log.debug("------ exposure 2 ------")

    # increase framerate, otherwise capture will block even on short exposures 
    # for several seconds (sensor mode 3 supports framerates of up to 15fps)
    # (>=16fps will result in 0-value images))
    camera.framerate = Fraction(10, 1)
    camera.exposure_compensation = 0

    # set a fixed AWB mode since 'auto' will fail on very dark exposures, resulting
    # in too cold white-balance settings (blue-greenish flickering in the sun streakes)
    camera.awb_mode = "sunlight"
    # camera.awb_mode = "off"
    # camera.awb_gains = (1.5, 0.9)

    # before actually disabling exposure mode (and thus disabling automatic gain control)
    # set ISO to a low value. AGC will reduce analog and digital gain and afterwards we 
    # can set the exposure mode to off. If that's not done the first (quite dark) exposure
    # through the filter will nudge the AGC to increase the gain and our (mostly black) 2nd
    # and 3rd exposures will be extremly noisy (and thus will result in jpegs with high 
    # filesizes)
    camera.iso = SECOND_EXPOSURE_ISO
    sleep(0.5)
    camera.exposure_mode = "off"
    camera.shutter_speed = SECOND_EXPOSURE_SHUTTER_SPEED

    sleep(0.5)

    full_filename_2 = os.path.join(OUTPUT_DIR_2, filename) #[:-4] + "_2" + ".jpg")
    camera.capture(full_filename_2, format=IMAGE_FORMAT)
    log_capture_info(camera, full_filename_2)

    future_brightness_2 = pool.submit(calculate_brightness, (full_filename_2))
    image_info.append([full_filename_2, None, filename_iteration, future_brightness_2])

    # read_exif_data(full_filename_2)
    # print_exposure_settings(camera)

    log.debug("------ exposure 3 ------")

    camera.shutter_speed = THIRD_EXPOSURE_SHUTTER_SPEED

    sleep(0.5)

    full_filename_3 = os.path.join(OUTPUT_DIR_3, filename)
    camera.capture(full_filename_3, format=IMAGE_FORMAT)
    log_capture_info(camera, full_filename_3)

    image_info.append([full_filename_3, None, filename_iteration])

    log.debug("------ exposure 4 ------")

    camera.shutter_speed = FOURTH_EXPOSURE_SHUTTER_SPEED

    sleep(0.5)

    full_filename_4 = os.path.join(OUTPUT_DIR_4, filename)
    camera.capture(full_filename_4, format=IMAGE_FORMAT)
    log_capture_info(camera, full_filename_4)

    image_info.append([full_filename_4, None, filename_iteration])

    # log.debug("------ exposure 5 ------")

    # camera.framerate = Fraction(1, 2)
    # camera.exposure_mode = "auto" #"verylong" # "auto"
    # camera.shutter_speed = FIFTH_EXPOSURE_SHUTTER_SPEED
    # camera.iso = 200

    # sleep(0.1)

    # full_filename_5 = os.path.join(OUTPUT_DIR_5, filename[1])
    # camera.capture(full_filename_5, format=IMAGE_FORMAT)
    # log_capture_info(camera, full_filename_5)

    # image_info.append([full_filename_5, None])

    log.debug("------    done    ------")

    camera.close()
    return image_info


if __name__ == "__main__":

    # we need to use timestamp milliseconds because we may change system time later
    start_global = datetime.now().timestamp()

    # ---------------------------------------------------------------------------------------

    # create logger
    log = logging.getLogger() #"oneshot")
    log.setLevel(logging.DEBUG)

    # subloggers
    exifread_logger = logging.getLogger("exifread").setLevel(logging.INFO)
    pil_logger = logging.getLogger("PIL").setLevel(logging.INFO) # PIL.TiffImagePlugin
    devices_logger = logging.getLogger("devices").setLevel(logging.INFO)

    # create formatter
    formatter = logging.Formatter("%(asctime)s | %(name)-7s | %(levelname)-7s | %(message)s")
    # formatter = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s")

    # console handler and set level to debug
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.DEBUG)
    consoleHandler.setFormatter(formatter)
    log.addHandler(consoleHandler)

    fileHandlerDebug = logging.FileHandler(LOG_FILE, mode="a", encoding="UTF-8")
    fileHandlerDebug.setLevel(logging.DEBUG)
    fileHandlerDebug.setFormatter(formatter)
    log.addHandler(fileHandlerDebug)

    sys.excepthook = global_except_hook

    # log.info(subprocess.check_output(["cat", "/proc/uptime"]))

    # ---------------------------------------------------------------------------------------

    # tvservice off

    # calling tvservice may freeze in newest buildroot

    if DISABLE_HDMI:
        try:
            subprocess.run(["tvservice", "-o"], timeout=1)    
        except Exception as e:
            log.info("disabling tvservice error: {}".format(e))

    # ---------------------------------------------------------------------------------------

    log.info("------------------------------------------")
    log.info(" ┌─┐┌─┐┌┬┐┌─┐┬─┐┌─┐┌─┐┌─┐┌─┐┬─┐┌─┐┌─┐┌┬┐  ")
    log.info(" │  │ ││││├─┘├┬┘├┤ └─┐└─┐│ │├┬┘│  ├─┤│││  ")
    log.info(" └─┘└─┘┴ ┴┴  ┴└─└─┘└─┘└─┘└─┘┴└─└─┘┴ ┴┴ ┴  ")
    log.info("------------------------------------------")

    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--persistent-mode", type=bool, default=False, help="")
    ap.add_argument("-s", "--stream-mode", type=bool, default=False, help="")
    args = vars(ap.parse_args())

    # log.info("ND FILTER       : {} stops".format(ND_FILTER))
    log.info("PERSISTENT MODE   : {}".format(args["persistent_mode"]))
    log.info("STREAM MODE       : {}".format(args["stream_mode"]))
    log.info(" ")
    log.info("WRITE RAW         : {}".format(WRITE_RAW))
    log.info("MODULO RAW        : {}".format(MODULO_RAW))
    log.info("EVEN ODD DELETION : {}".format(EVEN_ODD_DELETION_CAPTURE_1))
    log.info("BLUETOOTH ADV.    : {}".format(SEND_BLE_ADVERTISEMENT))

    log.info("------------------------------------------")

    image_info = None
    pool = ThreadPoolExecutor(3)

    # status data
    status_images_taken         = None
    status_free_space_mb        = None
    status_temp_pi              = None
    status_temp_controller      = None
    status_interval_mode        = None
    status_battery_volt         = None
    status_battery_perc         = None

    try:
        controller = CompressorCameraController.find_by_portname(SERIAL_PORT)
        
        if controller is not None:

            log.debug("controller found: {}".format(controller))

            millis  = int(controller.get_uptime()) # 1008343
            secs    = int(millis/1000)

            subprocess.run(["date", "-s", "@{}".format(secs)], check=True)

            seconds = math.floor(float(millis) / 1000.0)
            minutes = math.floor(seconds / 60.0)
            hours   = math.floor(minutes / 60.0)
            days    = math.floor(hours / 24.0)

            msg = "{:.0f} sec".format(seconds % 60)
            if minutes >= 1:
                msg = "{:.0f} min, ".format(minutes % 60) + msg
            if hours >= 1:
                msg = "{:.0f} h, ".format(hours % 24) + msg
            if days >= 1:
                msg = "{:.0f} d, ".format(days) + msg

            log.info("running for: " + msg)

            start_global += millis/1000.0

            d = datetime.fromtimestamp(secs)
            log.debug("setting system time to {}".format(d.strftime('%Y-%m-%d %H:%M:%S')))
        else:
            log.warning("setting system time failed, no controller found")
    except Exception as e:
        log.error("setting system time failed: {}".format(e))

    # checking for directories

    if CHECK_IF_MOUNTED and not os.path.ismount(BASE_DIR):
        log.error("mounting {} failed. exit!".format(BASE_DIR))
        controller.set_led(10, 0, 10)
        exit(1)

    for directory_name in [OUTPUT_DIR_1, OUTPUT_DIR_2, OUTPUT_DIR_3, OUTPUT_DIR_4]:
        try: 
            os.makedirs(directory_name)
            log.debug("created dir: {}".format(directory_name))
        except FileExistsError as e:
            pass

    # checking for actions

    try:
        if controller is not None:
            status = controller.ping()
            try:
                status = int(status)

                # status may be None with older controller firmware versions

                if status == CompressorCameraController.STATE_STREAM:

                    log.info("entering mode STREAM")
                    
                    # subprocess.run(["sh", "start_stream.sh"], shell=True, check=True)
                    # subprocess.run(["sh", "start_server.sh"], shell=True, check=True)

                    total_space_mb = shutil.disk_usage(OUTPUT_DIR_1).total / (1024 * 1024)
                    if total_space_mb < 100:
                        log.debug("total space on {:5.2f} below 100MB. initiating resize_fs.sh".format(total_space_mb))

                        log.debug("logging shutdown")
                        logging.shutdown()

                        subprocess.run(["sh", "/root/resize_fs.sh"], check=True)

                        sleep(3)
                        exit(0)

                    proc = subprocess.run(["ifup", "wlan0"], check=True, capture_output=True)
                    log.debug(proc)

                    # it takes a few seconds till the interface is available
                    # otherwise gunicorn will refuse to start
                    sleep(5)

                    controller.set_led(0, 0, 10)
        
                    pid = subprocess.Popen(["sh", "start_server.sh"]) #, close_fds=True)

                    log.debug("logging shutdown")
                    logging.shutdown()

                    sleep(1)
                    exit(0)

                elif status == CompressorCameraController.STATE_UPLOAD:

                    log.info("entering mode UPLOAD")

                    try:
                        uploader = RsyncUploader(
                            [OUTPUT_DIR_1, OUTPUT_DIR_2, OUTPUT_DIR_3, OUTPUT_DIR_4],
                            UPLOAD_DIR)

                        uploader.run()

                    except Exception as e:
                        log.e("failed upload: {}".format(e))

            except Exception as e:
                log.error("parsing controller status failed: {}".format(e))
        else:
            log.warning("checking for controller actions failed, no controller found")
    except Exception as e:
        log.error("running controller actions failed: {}".format(e))

    # all good: check free space and start capturing

    try:
        status_free_space_mb = shutil.disk_usage(OUTPUT_DIR_1).free / (1024 * 1024)
        if status_free_space_mb < MIN_FREE_SPACE:
            log.error("NO SPACE LEFT ON DEVICE (directory: {}, free space: {:.2f}, min free space: {:.2f}".format(OUTPUT_DIR_1, status_free_space_mb, MIN_FREE_SPACE))
            # TODO: red LED on controller
            raise Exception("no space left on device")
        else:
            log.debug("free space in {}: {:.2f}mb".format(OUTPUT_DIR_1, status_free_space_mb))

        if args["stream_mode"]:
            preview = StreamPreview()
            preview.run()

        if args["persistent_mode"]:
            log.info("PERSISTENT MODE")
            for i in range(0, MAX_ITERATIONS):
                log.info("iteration: {}/{}".format(i, MAX_ITERATIONS))
                next_trigger = datetime.now() + timedelta(seconds=INTERVAL)
                
                trigger()
                
                remaining_time = next_trigger-datetime.now()
                log.debug("sleep time till trigger: {}".format(remaining_time.total_seconds()))
                sleep(remaining_time.total_seconds())
        else:
            image_info = trigger()

        log.info("------------------------")

    except Exception as e:
        log.error("error: [{}] {}".format(type(e), e))

    # ---------------------------------------------------------------------------------------

    start = datetime.now()
    subprocess.call(["sync"])
    diff = (datetime.now() - start).total_seconds()
    log.debug("sync done. took         : {:.3f} sec".format(diff))

    try: 
        temp_str = str(subprocess.check_output(["vcgencmd", "measure_temp"]))
        status_temp_pi = float(temp_str[temp_str.index("=")+1:temp_str.index("'")])
    except Exception as e:
        log.warn("reading pi temperature failed: {}".format(e))
    log.info("temperature [pi]        : {:.2f}".format(status_temp_pi))

    # BLE advertisement

    if SEND_BLE_ADVERTISEMENT:

        data = {}

        data["id"] = get_serial()
        # get last 8 chars (is equal to 4 bytes)
        if data["id"] is not None and len(data["id"]) > 8:
            data["id"] = bytes.fromhex(data["id"][-8:])

        data["uptime"] = datetime.now().timestamp()

        _, _, filename_iteration = get_filename([IMAGE_FORMAT, "jpg.gz", "jpeg.gz"]) # TODO: does not work with filename prefixes. Rather just count all files in the directory
        data["images_taken"] = int(filename_iteration)

        data["errors"] = 0  # 2 byte # TODO
        data["mode"] = 0    # 1 byte # TODO

        data["free_space"] = status_free_space_mb

        data["temp"] = -127
        if controller is not None:
            if status_temp_controller is None:     
                status_temp_controller = float(controller.get_temperature())
              
            data["temp"] = int(status_temp_controller)

        data["battery"] = -127
        if controller is not None:
            if status_battery_perc is None:  
                status_battery_perc = controller.get_battery_status()
        
            data["battery"] = status_battery_perc

        _ = pool.submit(advertise, (data))
        # advertise(data)


    # get EV of last (primary) image and reduce if brighter than threshold
    # 
    # option A: use EXIF data to compute EV
    #  problem: if a ND1000 filter is used, only very bright scenes do increase
    #           the shutter speed above minimum (and thus change the computed EV)
    #
    # option B: calculate brightness (or non-zero pixels) of capture_2 or _3
    #  problem: requires 2-3s per image! (total time with option B from powerup
    #           to request-for-shutdown is 37s)
    #           solved: just do it in another thread
    #
    # option C: get the brightest pixel in capture_2
    #           if > than threshold, sun must be present
    #  problem: works well for increase interval, but how to know when to reduce?
    #           slow (seems to take about 8s??)

    brightness_1 = None
    brightness_2 = None

    try:
        if image_info is not None and len(image_info) > 0:

            # option B:

            if CHECK_FOR_INTERVAL_REDUCE:
                filename_capture_1 = image_info[0][0]
                future_brightness_1 = image_info[0][3]

                # brightness_1 = calculate_brightness(filename_capture_1)
                brightness_1 = future_brightness_1.result(timeout=8)

                log.info("brightness of capture_1 : {:8.6f}".format(brightness_1))

            if CHECK_FOR_INTERVAL_INCREASE:
                filename_capture_2 = image_info[1][0]
                future_brightness_2 = image_info[1][3]

                # brightness_2 = calculate_brightness(filename_capture_2)
                brightness_2 = future_brightness_2.result(timeout=8)

                log.info("brightness of capture_2 : {:8.6f}".format(brightness_2))

    except Exception as e:
        log.error("increasing/reducing interval failed: {}".format(e))

    if COMPRESS_CAPTURE_1:
        try:
            timer_compression = datetime.now()
            # subprocess.run(["tar", "-czvf", filename_capture_1 + ".tar.gz", filename_capture_1], check=True)
            # subprocess.run(["rm", filename_capture_1], check=True)            
            subprocess.run(["gzip", "-1", "-f", filename_capture_1], check=True)
            diff = datetime.now() - timer_compression
            log.debug("compressing capture_1 image took: {:.2f}s".format(diff.total_seconds()))
        except Exception as e:
            log.error("compressing capture_1 image failed: {}".format(e))

    if EVEN_ODD_DELETION_CAPTURE_1:
        iteration = image_info[0][2]
        filename_capture_1 = image_info[0][0]
        if iteration % 2 == 1:
            os.remove(filename_capture_1)
            log.info("EVEN_ODD_DELETION_CAPTURE_1 deleted: {}".format(filename_capture_1))
            # create empty file so the filename won't be available on next iteration
            open(filename_capture_1, 'a').close() 

    if SHUTDOWN_ON_COMPLETE:

        if controller is not None:
            try:

                status_battery_perc = controller.get_battery_status()

                log.info("battery                 : {}".format(status_battery_perc))
                # log.info("temperature [controller]: {}".format(controller.get_temperature()))
                log.info("debug register          : {}".format(controller.get_debug_register()))
                log.info("next invocation         : {}".format(controller.get_next_invocation()))

                if brightness_2 is not None and brightness_2 >= INCREASE_INTERVAL_ABOVE:

                    # take images faster

                    log.debug("request interval increase (brightness: {:.6f} > {})".format(
                        brightness_2, INCREASE_INTERVAL_ABOVE))
                    controller.increase_interval()

                    status_interval_mode = "INC"

                elif brightness_1 is not None and brightness_1 < REDUCE_INTERVAL_BELOW:

                    # take images slower

                    log.debug("request interval reduction (brightness: {:.6f} < {})".format(
                        brightness_1, REDUCE_INTERVAL_BELOW))
                    controller.reduce_interval()

                    status_interval_mode = "DEC"

                else:

                    status_interval_mode = "NRM"

                # ---  STATUS timestamp|images_taken|free_space|temp_pi|temp_controller|interval_mode|battery_volt|battery_percentage
                
                status_data = {}

                status_data["timestamp"]            = int(datetime.now().timestamp())

                if status_images_taken is None:
                    _, _, filename_iteration        = get_filename([IMAGE_FORMAT, "jpg.gz", "jpeg.gz"]) # TODO: count files in dir
                    status_images_taken             = int(filename_iteration)
                status_data["images_taken"]         = status_images_taken

                status_data["free_space"]           = "_"
                if status_free_space_mb is not None:
                    status_data["free_space"]       = "{:5.2f}".format(status_free_space_mb)

                status_data["temp_pi"]              = "_"
                if status_temp_pi is not None:
                    status_data["temp_pi"]          = "{:5.2f}".format(status_temp_pi)

                status_data["temp_controller"]      = "_"
                if status_temp_controller is not None:
                    status_data["temp_controller"]  = "{:5.2f}".format(status_temp_controller)

                status_data["interval_mode"]        = "_"
                if status_interval_mode is not None:
                    status_data["interval_mode"]    = status_interval_mode

                status_data["battery_volt"]         = "_"
                if status_battery_volt is not None:
                    status_data["battery_volt"]     = "{:5.2f}".format(status_battery_volt)

                status_data["battery_percentage"]   = "_"
                if status_battery_perc is not None:
                    status_data["battery_percentage"] = "{:5.2f}".format(status_battery_perc)

                log.info("STATUS {timestamp}|{images_taken}|{free_space}|{temp_pi}|{temp_controller}|{interval_mode}|{battery_volt}|{battery_percentage}".format(**status_data))

                # ---

                controller.shutdown(delay=15000)

                log.debug("shutdown command sent")
                log.info("POWEROFF")

                uptime = get_uptime()
                if uptime is not None:
                    log.info("uptime                  : {:.3f} sec".format(uptime))
                
                log.debug("logging shutdown")
                logging.shutdown()

                subprocess.call(["sync"])
                # subprocess.call(["umount {}".format(BASE_DIR)])
                
                # important, damage to filesystem: 
                # wait a few sec before poweroff!
                sleep(4)

                subprocess.call(["poweroff"])

                # note: exit() won't be performed as long as 
                # ThreadPoolExecutor still has running threads
                exit()

            except Exception as e:
                log.error("poweroff failed: {}".format(e))
        else:
            log.error("poweroff failed: {}".format("no controller found"))

    log.debug("logging shutdown")
    logging.shutdown()

    start = datetime.now()
    subprocess.call(["sync"])
    diff = (datetime.now() - start).total_seconds()
    print("sync done. took: {:.3f} sec".format(diff))

    print("------------------------")

    uptime = get_uptime()
    if uptime is not None:
        log.info("uptime                  : {:.3f} sec".format(uptime))

    diff = datetime.now().timestamp() - start_global
    print("total runtime           : {:.3f} sec".format(diff))

    sleep(1.0)

