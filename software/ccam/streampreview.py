from datetime import datetime, timedelta
import io
import logging

import socketserver
from threading import Condition
from http import server

import picamera

MAX_TIME = 60 # sec

PAGE="""\
<html><head><title>picamera MJPEG streaming demo</title></head>
<body>Trashcam</br>
<img src="stream.mjpg" width="640" height="480" />
</body></html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    timeout = 10

    # def shutdown(self):
    #     print("shutdown")

    def handle_timeout(self):
        pass


class StreamPreview(object):

    def run(self):

        global output

        with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
            output = StreamingOutput()
            camera.start_recording(output, format='mjpeg')

            server = None
            try:
                address = ('', 8000)
                server = StreamingServer(address, StreamingHandler)

                start = datetime.now()

                # https://docs.python.org/2/library/socketserver.html#SocketServer.BaseServer.timeout

                while (datetime.now() - start).total_seconds() < MAX_TIME:
                    server.handle_request()

                print("max time")

            finally:
                # if server is not None:
                #     server.server_close()
                camera.stop_recording()


if __name__ == "__main__":
    preview = StreamPreview()
    preview.run()