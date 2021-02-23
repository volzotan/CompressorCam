#!/usr/bin/env python3

import subprocess
import time

BLE_ADVERTISEMENT_PAYLOAD_LENGTH = 31 #26
PREAMBLE = []

def _format_message(data):

   formatted = ""

    for i in range(0, len(data)):

        formatted += "{:02}".format(data[i]) # zero padding

        if i < len(data)-1:
            formatted += " "

    return formatted

def advertise(data):

    call_attach = "hciattach /dev/ttyS0 bcm43xx 921600 noflow -"
    call_up     = "hciconfig hci0 up"
    call_config = "hcitool -i hci0 cmd 0x08 0x0008 {}"
    call_start  = "hciconfig hci0 leadv 3" # advertise as non-connectable service (ADV_NONCONN_IND)
    call_stop   = "hciconfig hci0 noleadv"

    payload = []

    # message.append(0x1E) # ??? Simple Pairing Randomizer

    payload.append(0x02) # length:  2 bytes
    payload.append(0x01) # AD type: flags (0x01)   
    payload.append(0x05) # AD val:  LE Limited Discoverable Mode (0x01) + BR/EDR not supported (0x04)

    payload.append(0x1A) # length:  26 bytes
    payload.append(0xFF) # AD type: Manufacturer Specific Data (0xFF)

    payload += PREAMBLE                     # 4 byte
    payload += data["id"]                   # 4 byte
    payload += data["uptime"]               # 4 byte
    payload += data["images_taken"]         # 2 byte
    payload += data["errors"]               # 2 byte
    payload += data["mode"]                 # 1 byte
    payload += data["free_space"]           # 4 byte
    payload += data["temp"]                 # 2 byte
    payload += data["battery"]              # 1 byte ()

    payload = bytes(payload)
    if len(payload) < BLE_ADVERTISEMENT_PAYLOAD_LENGTH:
        payload = payload + bytes([0x0] * (BLE_ADVERTISEMENT_PAYLOAD_LENGTH-len(payload)))

    call_config = call_config.format(_format_message(payload))

    subprocess.run(call_attach, check=False, shell=True)
    subprocess.run(call_up,     check=False, shell=True)
    subprocess.run(call_config, check=True, shell=True)
    subprocess.run(call_start,  check=True, shell=True)

    time.sleep(10)

    subprocess.run(call_stop)

if __name__ == "__main__":

    data = {}
    data["id"]              = [1, 2, 3, 4]
    data["uptime"]          = [0, 0, 0, 100]
    data["images_taken"]    = [0, 50]
    data["errors"]          = [0, 0]
    data["mode"]            = [1]
    data["free_space"]      = [1, 0, 0, 0]
    data["battery"]         = [128]

    advertise(data)