from flask import Flask, Response
from flask import render_template, redirect, url_for, make_response, request

from picamera.array import PiRGBArray
import picamera

from fractions import Fraction

import cv2
import numpy as np

import threading
import time
import datetime
import io

CROP_SIZE = [1280, 720]

CMD_SHUTDOWN        = "shutdown"
CMD_STREAM_START    = "stream_start"
CMD_STREAM_STOP     = "stream_stop"
CMD_FOCUS_START     = "focus_start"
CMD_FOCUS_STOP      = "focus_stop"

app = Flask(__name__)

class CameraManager(object):

    def __init__(self, **kwargs):

        self.camera = picamera.PiCamera(sensor_mode=3) 

        self.camera.exposure_mode = "verylong"
        self.camera.meter_mode = "average"

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

    def capture(self):

        self.rawCapture = PiRGBArray(self.camera, size=self.camera.resolution)
        self.camera.capture(self.rawCapture, format="bgr")
        return self.rawCapture.array

    def stop(self):
        self.camera.close()


@app.route("/")
def root():
    return redirect(url_for("overview"))


@app.route("/overview")
def overview():

    data = {
        "total_space"       : 0,
        "available_space"   : 0,
    }

    return render_template("overview.html", data=data)


@app.route("/command/<cmd>")
def command(cmd):

    if cmd is CMD_SHUTDOWN:
        subprocess.call("shutdown")
    elif cmd is CMD_STREAM_START:
        subprocess.call("sh ../start_stream.sh")
    elif cmd is CMD_STREAM_STOP:
        pass
    else:
        return "unknown command. Available commands: {}".format(ALL_COMMANDS)

    return("...")


@app.route("/stream")
def stream():
    return render_template("stream.html")

@app.route("/focus")
def focus():
    return render_template("focus.html")

def process_image(cameraManager, peak=None, crop=None, resize=None):

    with lock:

        # cameraManager = CameraManager()
        # frame = cameraManager.capture()
        # cameraManager.stop()

        frame = cameraManager.capture()

        if crop is not None:
            frame = frame[
                int(frame.shape[1]/2 - crop[1]/2) : int(frame.shape[1]/2 + crop[1]/2), 
                int(frame.shape[0]/2 - crop[0]/2) : int(frame.shape[0]/2 + crop[0]/2) 
            ]

        frame = frame.copy()

        if peak is not None:

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 120, 140)

            kernel = np.ones((3, 3), np.uint8)
            dilation = cv2.dilate(edges, kernel, iterations=1)

            frame[dilation > 0, :] = [0, 0, 255]

        if resize is not None:
            pass

        flag, encodedImage = cv2.imencode(".jpg", frame)

        if not flag:
            return None

        return bytearray(encodedImage)

@app.route("/video_feed")
def video_feed():

    peak = request.args.get("peak", False)
    crop = request.args.get("crop", False)
    resize = request.args.get("resize", False)

    response = make_response(process_image(cameraManager, peak=peak, crop=CROP_SIZE))
    response.headers.set("Content-Type", "image/jpeg")

    return response

cameraManager = CameraManager()
lock = threading.Lock()

if __name__ == '__main__':

    app.run(host="0.0.0.0", port=5000, debug=True,
        threaded=True, use_reloader=False)
