from flask import Flask, Response
from flask import render_template, redirect, url_for, make_response, request

import subprocess
import threading
import time
import datetime
import io
import shutil
import psutil

from picamera.array import PiRGBArray
import picamera

from PIL import Image
from fractions import Fraction

CROP_SIZE = [1280, 720]
BASE_DIR = "/media/storage"

IMAGE_DIR = "/media/storage"

CMD_SHUTDOWN        = "shutdown"
CMD_REBOOT          = "reboot"
CMD_RESIZEFS        = "resizefs"
CMD_STREAM_START    = "stream_start"
CMD_STREAM_STOP     = "stream_stop"
CMD_FOCUS_START     = "focus_start"
CMD_FOCUS_STOP      = "focus_stop"

LOCK_TIMEOUT        = 5

app = Flask(__name__)

lock = threading.Lock()

class CameraManager(object):

    def __init__(self, **kwargs):

        self.error = None

        try:

            self.camera = picamera.PiCamera(sensor_mode=3) 

            self.camera.exposure_mode = "verylong"
            self.camera.meter_mode = "average"

            self.stream = io.BytesIO()

            resolutions = {}
            resolutions["HQ"] = [[4056, 3040], Fraction(1, 2)]
            resolutions["V2"] = [[3280, 2464], Fraction(1, 2)]
            resolutions["V1"] = [[2592, 1944], Fraction(1, 2)]

            for key in resolutions.keys():
                try:
                    self.camera.resolution = resolutions[key][0]
                    self.camera.framerate = resolutions[key][1]
                    break
                except picamera.exc.PiCameraValueError as e:
                    pass

            for (arg, value) in kwargs.items():
                setattr(self.camera, arg, value)

            self.camera.start_preview()

        except Exception as e:
            print("initializing camera failed: {}".format(e))
            self.error = e

    def capture_array(self):

        if self.error is not None:
            raise e

        self.rawCapture = PiRGBArray(self.camera, size=self.camera.resolution)
        self.camera.capture(self.rawCapture, format="bgr")
        return self.rawCapture.array

    def capture(self):

        if self.error is not None:
            raise e
        
        self.stream.seek(0)
        self.stream.truncate()
        
        self.camera.capture(self.stream, format='jpeg')

        # "Rewind" the stream to the beginning so we can read its content
        self.stream.seek(0)
        image = Image.open(self.stream)

        return image

    def stop(self):
        if self.camera is None:
            return

        self.camera.close()
        self.camera = None


@app.route("/")
def root():
    return redirect(url_for("overview"))


@app.route("/overview")
def overview():

    data = {
        "total_space"       : None,
        "available_space"   : None,
        "uptime"            : None,
        "temperature_cpu"   : None,
        # "camera_status"     : "connected"
        # "temperature_ext"   : None,
        # "battery_volt"      : None,
        # "battery_perc"      : None, 
        # "controller_version": None,
    }

    try:
        total, used, free = shutil.disk_usage(BASE_DIR)
        data["total_space"] = "{:5.2f} GB".format(total / (2**30))
        data["available_space"] = "{:5.2f} GB".format(free / (2**30))
    except Exception as e:
        print("getting disk space failed: {}".format(e))

    data["uptime"] = "{:7.0f}s".format(time.time() - psutil.boot_time())

    # if cameraManager.error is not None:
    #     data["camera_status"] = "failure (probably not connected)"

    try:
        temp_str = str(subprocess.check_output(["vcgencmd", "measure_temp"]))
        temp = float(temp_str[temp_str.index("=")+1:temp_str.index("'")])
        data["temperature_cpu"] = temp
    except Exception as e:
        print("reading temperature failed: {}".format(e))

    return render_template("overview.html", data=data)


@app.route("/settings")
def settings():

    data = {}

    import importlib.util
    spec = importlib.util.spec_from_file_location("config", "config.py")
    conf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(conf)
    conf_dict = vars(conf)

    for key in conf_dict.keys():

        if key.startswith("__") and key.endswith("__"):
            continue

        data[key] = conf_dict[key]

    return render_template("settings.html", data=data)


@app.route("/command/<cmd>")
def command(cmd):

    if cmd.lower() == CMD_SHUTDOWN:
        subprocess.run(["shutdown"])
    elif cmd == CMD_REBOOT:
        subprocess.run(["reboot"])
    elif cmd == CMD_RESIZEFS:
        subprocess.run(["sh", "/root/resize_fs.sh"])
        return("the file system will be resized. This may take a minute. The camera will restart.")
        # return redirect(url_for("/overview", messages=messages))
    elif cmd == CMD_STREAM_START:
        subprocess.run(["sh", "../start_stream.sh"])
    elif cmd == CMD_STREAM_STOP:
        pass
    else:
        return "unknown command {}".format(cmd)

    return("command executed.")


@app.route("/stream")
def stream():
    return render_template("stream.html")

@app.route("/focus")
def focus():
    return render_template("focus.html")

@app.route("/preview")
def preview():
    return render_template("preview.html")

def process_image_cv2(cameraManager, peak=None, crop=None, resize=None):

    with lock:

        if cameraManager is None:
            cameraManager = CameraManager()
            time.sleep(0.1)
            frame = cameraManager.capture_array()
            cameraManager.stop()
        else:
            frame = cameraManager.capture_array()

        if crop is not None:
            frame = frame[
                int(frame.shape[1]/2 - crop[1]/2) : int(frame.shape[1]/2 + crop[1]/2), 
                int(frame.shape[0]/2 - crop[0]/2) : int(frame.shape[0]/2 + crop[0]/2) 
            ]

        frame = frame.copy()

        if peak is not None:

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 160, 200)

            kernel = np.ones((3, 3), np.uint8)
            dilation = cv2.dilate(edges, kernel, iterations=1)

            frame[dilation > 0, :] = [0, 0, 255]

        if resize is not None:
            pass

        flag, encodedImage = cv2.imencode(".jpg", frame)

        if not flag:
            return None

        return bytearray(encodedImage)


def process_image(peak=None, crop=None, resize=None):

    cameraManager = None

    try:

        lock.acquire(timeout=LOCK_TIMEOUT)

        cameraManager = CameraManager()

        if cameraManager is None:
            cameraManager = CameraManager()
            time.sleep(0.1)
            img = cameraManager.capture()
            cameraManager.stop()
        else:
            img = cameraManager.capture()

        if crop is not None:
            img = img.crop((
                int(img.size[0]/2 - crop[0]/2), int(img.size[1]/2 - crop[1]/2), 
                int(img.size[0]/2 + crop[0]/2), int(img.size[1]/2 + crop[1]/2) 
            ))

        if resize is not None:
            factor = resize / img.size[0]
            new_size = [img.size[0] * factor, img.size[1] * factor]
            img.thumbnail(new_size, Image.ANTIALIAS)

        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format="JPEG")
        imgByteArr = imgByteArr.getvalue()
        return bytearray(imgByteArr)

    except Exception as e:
        print("processing failed: {}".format(e))

    finally:
        if cameraManager is not None:
            cameraManager.stop()

        lock.release()

@app.route("/video_feed")
def video_feed():

    peak = request.args.get("peak", None)
    crop = request.args.get("crop", None)
    resize = request.args.get("resize", None)

    if crop is not None:
        crop = CROP_SIZE

    if resize is not None:
        resize = int(resize)

    response = make_response(process_image(peak=peak, crop=crop, resize=resize))
    response.headers.set("Content-Type", "image/jpeg")

    return response

# if __name__ == '__main__':

#     app.run(host="0.0.0.0", port=5000, debug=True,
#         threaded=True, use_reloader=False)
