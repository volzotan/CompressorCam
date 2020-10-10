import serial
# import hid

from datetime import datetime
import time
import os
import subprocess
import re
import serial.tools.list_ports
from threading import Lock
import logging

try:
    import smbus
except ImportError as e:
    pass
    # print("importing smbus failed. Not a raspberry pi platform, i2c will not be available.")

log = logging.getLogger(__name__)


class Controller(object):

    def __init__(self):
        pass

    def turn_camera_on(self, turn_on):
        pass

    def turn_usb_on(self, turn_on):
        pass

    def get_temperature(self):
        pass

    def get_battery_status(self):
        pass

    @staticmethod
    def find_all():
        controller = []

        # controller = controller + YKushXSController.find_all()
        controller = controller + CompressorCameraController.find_all()
        # controller = controller + UsbHubController.find_all()

        return controller

# class YKushXSController(Controller):

#     CMD_ON          = 0x11
#     CMD_OFF         = 0x01
#     CMD_PORT_STATUS = 0x21

#     VENDOR_ID       = 1240
#     PRODUCT_ID      = 61645

#     def __init__(self, serialnumber):
#         self.serialnumber = serialnumber

#     def __repr__(self):
#         return "YKushXSController id: {}".format(self.serialnumber)

#     @staticmethod
#     def find_all():
#         controller = []    

#         for d in hid.enumerate():
#             if d["vendor_id"] == YKushXSController.VENDOR_ID and d["product_id"] == YKushXSController.PRODUCT_ID:
               
#                 if d["serial_number"] is None:
#                     # one reason for that may be that root rights are required to open
#                     # the HID device. create a udev rule for that to enable non-root access 
#                     log.debug("YKushXSController: serial number missing. access rights?")

#                 controller.append(YKushXSController(d["serial_number"]))

#         return controller

#     def turn_usb_on(self, turn_on):
#         if turn_on:
#             self._send_command(self.CMD_ON)
#         else:
#             self._send_command(self.CMD_OFF)

#     def _send_command(self, cmd):
#         h = hid.device()

#         if self.serialnumber is not None and len(self.serialnumber) > 0:
#             h.open(self.VENDOR_ID, self.PRODUCT_ID, self.serialnumber)
#         else:
#             h.open(self.VENDOR_ID, self.PRODUCT_ID)

#         h.set_nonblocking(1)

#         h.write([0, cmd] + [0] * 63)
#         time.sleep(0.05)

#         response = []
#         while True:
#             d = h.read(64)
#             if d:
#                 response.append(d)
#             else:
#                 break

#         h.close()
#         return response

class CompressorCameraController(Controller):

    CMD_PING            = "K"
    CMD_BATTERY         = "B"
    CMD_UPTIME          = "U"
    CMD_TEMPERATURE     = "T"
    CMD_DEBUG_REGISTER  = "D"
    CMD_NEXT_INVOCATION = "N"

    CMD_ZERO_ON         = "Z 1"
    CMD_ZERO_OFF        = "Z 0"

    CMD_LED             = "L"

    CMD_RED_INTERVAL    = "R"
    CMD_INC_INTERVAL    = "I"

    CMD_SHUTDOWN        = "S"

    STATE_STREAM        = 11

    SERIAL_BAUDRATE     = 9600
    SERIAL_TIMEOUT      = 1.0

    lock = Lock()

    def __init__(self, port):
        self.port = port

    def __repr__(self):
        return "CompressorCameraController at {}".format(self.port) #self.SERIAL_DEVICE)

    @staticmethod
    def find_all():

        controller_list = []
        
        all_ports = list(serial.tools.list_ports.comports())
        log.debug("detecting CompressorCameraController: found {} port(s)".format(len(all_ports)))
        for port in all_ports:
            if "zero" in port[1].lower():
                potential_controller = CompressorCameraController(port[0])
                try:
                    potential_controller.ping()
                    controller_list.append(potential_controller)
                except Exception as e:
                    print(e)

            time.sleep(0.1)

        return controller_list

    @staticmethod
    def find_by_portname(portname):

        potential_controller = CompressorCameraController(portname)
        try:
            potential_controller.ping()
            return potential_controller
        except Exception as e:
            print(e)

        return None

    def ping(self):
        try:
            response = self._send_command(self.CMD_PING)
            return response
        except Exception as e:
            log.error(e)
            raise e

    def get_battery_status(self):
        try:
            response = self._send_command(self.CMD_BATTERY)

            if len(response) < 2:
                raise Exception("response too short [{}]".format(response))

            response = response.split(" ")

            if len(response) != 2:
                raise Exception("response in unexpected format [{}]".format(response))

            return float(response[1])

        except Exception as e:
            log.error(e)
            raise e

    def shutdown(self, delay=None):
        try:
            self._send_command(self.CMD_SHUTDOWN, param=delay)
        except Exception as e:
            log.debug(e)
            raise e

    def turn_zero_on(self, turn_on):
        try:
            if turn_on:
                self._send_command(self.CMD_ZERO_ON)
            else:
                self._send_command(self.CMD_ZERO_OFF)
        except Exception as e:
            log.debug(e)
            raise e

    def get_uptime(self):
        try:
            response = self._send_command(self.CMD_UPTIME)
            return response
        except Exception as e:
            log.debug(e)
            raise e

    def get_temperature(self):
        try:
            response = self._send_command(self.CMD_TEMPERATURE)
            return response
        except Exception as e:
            log.debug(e)
            raise e

    def get_debug_register(self):
        try:
            return self._send_command(self.CMD_DEBUG_REGISTER)
        except Exception as e:
            log.debug(e)
            raise e

    def get_next_invocation(self):
        try:
            return self._send_command(self.CMD_NEXT_INVOCATION)
        except Exception as e:
            log.debug(e)
            raise e

    def set_led(self, r, g, b):
        try:
            return self._send_command(self.CMD_LED, r << 16 | g << 8 | b << 0)
        except Exception as e:
            log.debug(e)
            raise e

    def reduce_interval(self):
        try:
            response = self._send_command(self.CMD_RED_INTERVAL)
            return response
        except Exception as e:
            log.debug(e)
            raise e

    def increase_interval(self):
        try:
            response = self._send_command(self.CMD_INC_INTERVAL)
            return response
        except Exception as e:
            log.debug(e)
            raise e

    def _send_command(self, cmd, param=None):
        response = ""
        ser = None
        lock_acquired = False

        try:
            full_cmd = None
            if param is None:
                full_cmd = cmd
            else:
                full_cmd = "{} {}".format(cmd, param)

            log.debug("[{}] serial send: {}".format(self, full_cmd))

            lock_acquired = self.lock.acquire(timeout=1)

            if not lock_acquired:
                raise AccessException("Lock could not be acquired")

            ser = serial.Serial(self.port, self.SERIAL_BAUDRATE, timeout=self.SERIAL_TIMEOUT, write_timeout=self.SERIAL_TIMEOUT)

            ser.write(bytearray(full_cmd, "utf-8"))
            ser.write(bytearray("\n", "utf-8"))

            response = ser.read(100)
            response = response.decode("utf-8") 

            # remove every non-alphanumeric / non-underscore / non-space / non-decimalpoint character
            response = re.sub("[^a-zA-Z0-9_ .]", '', response)

            log.debug("[{}] serial receive: {}".format(self, response))

            if response is None or len(response) == 0:
                log.debug("[{}] empty response".format(self))
                raise Exception("empty response or timeout")

            if response.startswith("E"):
                log.debug("[{}] serial error: {}".format(self, response))
                raise Exception("serial error: {}".format(response))

            if not response.startswith("K"):
                log.debug("[{}] serial error, non K response: {}".format(self, response))
                raise Exception("serial error, non K response: {}".format(response))

            if len(response) > 1:
                return response[2:]

        except serial.serialutil.SerialException as se:
            log.error("comm failed, SerialException: {}".format(se))
            raise se

        except AccessException as ae:
            log.error("concurrency error: {}".format(ae))
            raise ae

        except Exception as e:
            log.error("comm failed, unknown exception: {}".format(e))
            raise e

        finally:
            if ser is not None:
                ser.close()

            if lock_acquired:
                self.lock.release()


class UsbHubController(Controller):

    CMD = "uhubctl -l {} -a {} -p {}"

    def __init__(self, port, is_data_connection=False):
        self.port = port
    
    def __repr__(self):
        return "UsbHubController at {}:{}".format(self.port[0], self.port[1])

    @staticmethod
    def find_all():
        controller = []

        hubs = []
        ports = []

        hub = None
        
        try: 
            output = subprocess.check_output(["uhubctl"])
            for line in str(output).split("\\n"):
                # print("{}: {}".format("-", line))

                if line.startswith(" "):
                    items = line.split(" ")
                    if len(items) >= 5:

                        # if the camera not running the device will be recognized as "Sony USB Charger"
                        # if running the name is "Sony NUMBER"

                        if "Sony" in line:
                            hubs.append(hub)
                            ports.append(items[3][:-1])

                            controller.append(UsbHubController((hubs[-1], ports[-1]), is_data_connection=True))
                            
                else:
                    if len(line) > 1:
                        hub = line.split(" ")[4]
                    else:
                        hub = None
        except FileNotFoundError as fnfe:
            return []
        except subprocess.CalledProcessError as cpe:
            # log.error(cpe)
            return []

        # for i in range(len(hubs)):
            # print("{} : {}".format(hubs[i], ports[i]))

        return controller

    def turn_usb_on(self, turn_on):
        param = "off"
        if turn_on == True:
            param = "on"

        subprocess.call(self.CMD.format(self.port[0], param, self.port[1]), shell=True)


class AccessException(Exception):
    pass

