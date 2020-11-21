import io
from fractions import Fraction
import threading

from PIL import Image

from flask import current_app, _app_ctx_stack
 
from picamera.array import PiRGBArray
import picamera

class CameraManager(object):

    def __init__(self, app): #**kwargs):

        self.app = app

        if app is not None:
            self.init_app(app)

        self.lock = threading.Lock()
        self.error = None
        self.camera = None

        if self.camera is None:
            self.init_camera()


    def init_app(self, app):
        app.teardown_appcontext(self.teardown)


    def teardown(self, exception):

        print("cameraManager teardown")

        ctx = _app_ctx_stack.top
        if hasattr(ctx, 'picam'):
            pass


    def init_camera(self):

        try:
            print("cameraManager init | {}".format(id(self)))

            self.camera = picamera.PiCamera(sensor_mode=3) 

            # self.camera.exposure_mode = "verylong"
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

            # for (arg, value) in kwargs.items():
            #     setattr(self.camera, arg, value)

            self.camera.start_preview()

        except Exception as e:
            print("initializing camera failed: {}".format(e))
            self.error = e


    def capture_array(self):

        if self.error is not None:
            raise self.error

        self.rawCapture = PiRGBArray(self.camera, size=self.camera.resolution)
        self.camera.capture(self.rawCapture, format="bgr")
        return self.rawCapture.array


    def capture(self):

        if self.camera is None:
            self.init_camera()

        if self.error is not None:
            raise self.error
        
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