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

        controller = controller + YKushXSController.find_all()
        controller = controller + TimeboxController.find_all()
        # controller = controller + UsbHubController.find_all()
        # controller = controller + UsbDirectController.find_all()

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

class TimeboxController(Controller):

    CMD_PING            = "K"
    CMD_BATTERY         = "B"
    CMD_UPTIME          = "U"
    CMD_TEMPERATURE     = "T"
    CMD_DEBUG_REGISTER  = "D"
    CMD_NEXT_INVOCATION = "N"

    CMD_CAM_ON          = "C 1"
    CMD_CAM_OFF         = "C 0"
    CMD_USB1_ON         = "X 1"
    CMD_USB1_OFF        = "X 0"
    CMD_USB2_ON         = "Y 1"
    CMD_USB2_OFF        = "Y 0"
    CMD_ZERO_ON         = "Z 1"
    CMD_ZERO_OFF        = "Z 0"

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
        return "TimeboxController at {}".format(self.port) #self.SERIAL_DEVICE)

    @staticmethod
    def find_all():

        controller_list = []
        
        all_ports = list(serial.tools.list_ports.comports())
        log.debug("detecting TimeboxController: found {} ports".format(len(all_ports)))
        for port in all_ports:
            if "zero" in port[1].lower():
                potential_controller = TimeboxController(port[0])
                try:
                    potential_controller.ping()
                    controller_list.append(potential_controller)
                except Exception as e:
                    print(e)

            time.sleep(0.1)

        return controller_list

    @staticmethod
    def find_by_portname(portname):

        potential_controller = TimeboxController(portname)
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

    def turn_camera_on(self, turn_on):
        try:
            if turn_on:
                self._send_command(self.CMD_CAM_ON)
            else:
                self._send_command(self.CMD_CAM_OFF)
        except Exception as e:
            log.debug(e)
            raise e

    def turn_usb_on(self, turn_on, usb_device=1):
        try:
            if turn_on:
                if usb_device == 1:
                    self._send_command(self.CMD_USB1_ON)
                elif usb_device == 2:
                    self._send_command(self.CMD_USB2_ON)
                else:
                    raise Exception("unknown usb device: {}".format(usb_device))
            else:
                if usb_device == 1:
                    self._send_command(self.CMD_USB1_OFF)
                elif usb_device == 2:
                    self._send_command(self.CMD_USB2_OFF)
                else:
                    raise Exception("unknown usb device: {}".format(usb_device))
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


# class UsbDirectController(Controller):

#     CMD_PING    = "K"
#     CMD_BATTERY = "B"
#     # CMD_STATUS  = "status"
#     CMD_ON      = "C 1"
#     CMD_OFF     = "C 0"
#     CMD_TEMP    = "T"

#     SERIAL_BAUDRATE = 9600
#     SERIAL_TIMEOUT = 1.0

#     def __init__(self, port):
#         self.port = port

#     def __repr__(self):
#         return "UsbDirectController at {}".format(self.port)

#     @staticmethod
#     def find_all():
#         controller = []
        
#         all_ports = list(serial.tools.list_ports.comports())
#         log.debug("detecting UsbDirectController: found {} ports".format(len(all_ports)))
#         for port in all_ports:
#             if "zero" in port[1].lower():
#                 potential_controller = UsbDirectController(port[0])
#                 try:
#                     potential_controller.ping()
#                     controller.append(potential_controller)
#                 except Exception as e:
#                     print(e)

#             time.sleep(0.1)

#         return controller

#     def ping(self):
#         try:
#             self._send_command(self.CMD_PING)
#         except Exception as e:
#             log.error(e)
#             raise e

#     def turn_camera_on(self, turn_on):
#         try:
#             if turn_on:
#                 self._send_command(self.CMD_ON)
#             else:
#                 self._send_command(self.CMD_OFF)
#         except Exception as e:
#             log.error(e)
#             return None

#     def get_status(self):
#         # try:
#         #     response = self._send_command(self.CMD_STATUS)
#         #     # print(response)
#         # except Exception as e:
#         #     print(e)
#         #     return None

#         return None

#     def get_battery_status(self):
#         try:
#             response = self._send_command(self.CMD_BATTERY)

#             if len(response) < 2:
#                 raise Exception("response too short [{}]".format(response))

#             response = response.split(" ")

#             if len(response) != 2:
#                 raise Exception("response in unexpected format [{}]".format(response))

#             return float(response[1])

#         except Exception as e:
#             log.error(e)
#             raise e

#     def get_temperature(self):
#         try:
#             response = self._send_command(self.CMD_TEMP)

#             if response is None: # error
#                 return None

#             if response is "null": # controller has no sensor
#                 return None

#             return float(response)
#         except Exception as e:
#             log.error(e)
#             return None

#     def get_uptime(self):
#         try:
#             response = self._send_command(self.CMD_UPTIME)
#             return response
#         except Exception as e:
#             log.error(e)
#             raise e

#     def _send_command(self, cmd):
#         response = ""
#         ser = None

#         try:
#             log.debug("[{}] serial send: {}".format(self, cmd))

#             ser = serial.Serial(self.port, self.SERIAL_BAUDRATE, timeout=self.SERIAL_TIMEOUT)

#             ser.write(bytearray(cmd, "utf-8"))
#             ser.write(bytearray("\n", "utf-8"))

#             response = ser.read(100)
#             response = response.decode("utf-8") 

#             # remove every non-alphanumeric / non-underscore / non-space / non-decimalpoint character
#             response = re.sub("[^a-zA-Z0-9_ .]", '', response)

#             log.debug("[{}] serial receive: {}".format(self, response))

#             if response is None or len(response) == 0:
#                 log.debug("[{}] empty response".format(self))
#                 raise Exception("empty response")

#             if response.startswith("E"):
#                 log.debug("[{}] serial error: {}".format(self, response))
#                 raise Exception("serial error: {}".format(response))

#             if not response.startswith("K"):
#                 log.debug("[{}] serial error, non K response: {}".format(self, response))
#                 raise Exception("serial error, non K response: {}".format(response))

#             if len(response) > 1:
#                 return response[2:]

#         except serial.serialutil.SerialException as se:
#             log.error("comm failed, SerialException: {}".format(se))
#             raise se

#         except Exception as e:
#             log.error("comm failed, unknown exception: {}".format(e))
#             raise e

#         finally:
#             if ser is not None:
#                 ser.close()


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


class RTC():

    DS_REG_SECONDS = 0x00
    DS_REG_MINUTES = 0x01
    DS_REG_HOURS   = 0x02
    DS_REG_DOW     = 0x03
    DS_REG_DAY     = 0x04
    DS_REG_MONTH   = 0x05
    DS_REG_YEAR    = 0x06
    DS_REG_CONTROL = 0x07

    def _bcd_to_int(self, x):
        # Decode 2x4 bit BCD to byte value
        return int((x//16)*10 + x%16)


    def _int_to_bcd(self, x):
        # Encode byte value to BCD
        return int((x//10)*16 + x%10)

    def __init__(self, twi=1, addr=0x68):
        self._bus = smbus.SMBus(twi)
        self._addr = addr

        # check if device is responding
        self.read_temperature()


    def _read_seconds(self):
        return _bcd_to_int(self._bus.read_byte_data(self._addr, self.DS_REG_SECONDS))


    def _read_minutes(self):
        return _bcd_to_int(self._bus.read_byte_data(self._addr, self.DS_REG_MINUTES))


    def _read_hours(self):
        d = self._bus.read_byte_data(self._addr, self.DS_REG_HOURS)
        if (d == 0x64):    # 12h
            if ((d & 0b00100000) > 0):
                # 24h
                return _bcd_to_int(d & 0x3F) + 12
        return _bcd_to_int(d & 0x3F)


    def _read_dow(self):
        return self._bcd_to_int(self._bus.read_byte_data(self._addr, self.DS_REG_DOW))


    def _read_day(self):
        return self._bcd_to_int(self._bus.read_byte_data(self._addr, self.DS_REG_DAY))


    def _read_month(self):
        return self._bcd_to_int(self._bus.read_byte_data(self._addr, self.DS_REG_MONTH))


    def _read_year(self):
        return self._bcd_to_int(self._bus.read_byte_data(self._addr, self.DS_REG_YEAR))


    def read_all(self):
        return (self._read_year(), self._read_month(), self._read_day(),
               self._read_dow(), self._read_hours(), self._read_minutes(),
               self._read_seconds())


    def read_temperature(self):
        temp_msb = self._bus.read_byte_data(self._addr, 0x11)
        temp_lsb = self._bus.read_byte_data(self._addr, 0x12)
        temp = ((temp_msb << 2) + (temp_lsb >> 6)) / 4.0

        # zweierkomplement. negativ?

        return temp


    def read_str(self, century=20):
        # returns string in YYYY-DD-MM HH:MM:SS
        return '%04d-%02d-%02d %02d:%02d:%02d' % (century*100 + self._read_year(),
               self._read_month(), self._read_day(), self._read_hours(),
               self._read_minutes(), self._read_seconds())


    def read_datetime(self, century=20, tzinfo=None):
        # returns datetime.datetime object
        return datetime(century*100 + self._read_year(),
               self._read_month(), self._read_day(), self._read_hours(),
               self._read_minutes(), self._read_seconds(), 0, tzinfo=tzinfo)


    def set_clock(self, century=20):
        # parses string in format 'MMDDhhmmYYss' from RTC 
        # and sets system date with date command
        cmd = 'sudo date %02d%02d%02d%02d%04d.%02d' % (self._read_month(),
              self._read_day(), self._read_hours(), self._read_minutes(),
              century*100 + self._read_year(), self._read_seconds())
        os.system(cmd)


    def write_all(self, seconds=None, minutes=None, hours=None, dow=None,
                  day=None, month=None, year=None):

        # resets date and time values in the RTC (all non None values)

        if seconds is not None:
            if seconds < 0 or seconds > 59:
                raise ValueError('Seconds out of range [0-59].')
            self._bus.write_byte_data(self._addr, self.DS_REG_SECONDS, self._int_to_bcd(seconds))

        if minutes is not None:
            if minutes < 0 or minutes > 59:
                raise ValueError('Minutes out of range [0-59].')
            self._bus.write_byte_data(self._addr, self.DS_REG_MINUTES,self._int_to_bcd(minutes))

        if hours is not None:
            if hours < 0 or hours > 23:
                raise ValueError('Hours out of range [0-23].')
            self._bus.write_byte_data(self._addr, self.DS_REG_HOURS, self._int_to_bcd(hours))

        if year is not None:
            if year < 0 or year > 99:
                raise ValueError('Year out of range [0-99].')
            self._bus.write_byte_data(self._addr, self.DS_REG_YEAR, self._int_to_bcd(year))

        if month is not None:
            if month < 1 or month > 12:
                raise ValueError('Month out of range [1-12].')
            self._bus.write_byte_data(self._addr, self.DS_REG_MONTH, self._int_to_bcd(month))

        if day is not None:
            if day < 1 or day > 31:
                raise ValueError('Day out of range [1-31].')
            self._bus.write_byte_data(self._addr, self.DS_REG_DAY, self._int_to_bcd(day))

        if dow is not None:
            if dow < 1 or dow > 7:
                raise ValueError('DOW out of range [1-7].')
            self._bus.write_byte_data(self._addr, self.DS_REG_DOW, self._int_to_bcd(dow))


    def write_datetime(self, dto):

        # sets RTCs internal date and time from datetime.datetime object
        # isoweekday() is: Monday = 1, Tuesday = 2, ..., Sunday = 7;
        # RTC needs: Sunday = 1, Monday = 2, ..., Saturday = 7
        wd = dto.isoweekday() + 1 # 1..7 -> 2..8
        if wd == 8:               # Sunday
            wd = 1
        self.write_all(dto.second, dto.minute, dto.hour, wd,
                       dto.day, dto.month, dto.year % 100)


    def write_now(self):
        # same as write_datetime(datetime.datetime.now())
        self.write_datetime(datetime.now())


# if __name__ == "__main__":
#     print "Test DS1307/DS3231"
#     starttime = datetime.now()
#     print "Programstart um: "+ starttime.strftime("%Y.%m.%d %H:%M:%S")

#     ds1307 = RTC(1, 0x68)
#     print "Setze DS1307 auf Daten der internen Uhr"
#     ds1307.write_now()
#     print "DS1307 auslesen: " + ds1307.read_str()

#     # Setze interne Uhr
# #    ds1307.set_clock()

#     while True:
#         currenttime = datetime.now()
#         rtctime = ds1307.read_datetime()
#         print "\nInterne Uhr:   " + currenttime.strftime("%Y-%m-%d %H:%M:%S")
#         print "DS1307/DS3231: " + rtctime.strftime("%Y-%m-%d %H:%M:%S")
#         time.sleep(2.0)
