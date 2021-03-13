#!/usr/bin/env python3

import subprocess
import time
import logging as log

BLE_ADVERTISEMENT_PAYLOAD_LENGTH    = 31
PREAMBLE                            = [0x01, 0x02, 0x03, 0x04]
ADVERTISE_INDEFINITELY              = True

def _format_message(data):

    formatted = ""

    for i in range(0, len(data)):

        formatted += "{}".format(bytes([data[i]]).hex()) # zero padding

        if i < len(data)-1:
            formatted += " "

    return formatted

def _left_pad(value, length):

    if len(value) < length:
        return bytes([0] * (length-len(value)) + value)
    else:
        return bytes(value)

def advertise(data):

    log.debug("preparing BLE advertisement")

    call_attach = "hciattach /dev/ttyS0 bcm43xx 921600 noflow -"
    call_up     = "hciconfig hci0 up"
    call_config = "hcitool -i hci0 cmd 0x08 0x0008 {}"
    call_start  = "hciconfig hci0 leadv 3" # advertise as non-connectable service (ADV_NONCONN_IND)
    call_stop   = "hciconfig hci0 noleadv"

    payload = bytes()

    payload += bytes([0x1E]) # ???

    payload += bytes([0x02]) # length:  2 bytes
    payload += bytes([0x01]) # AD type: flags (0x01)   
    payload += bytes([0x05]) # AD val:  LE Limited Discoverable Mode (0x01) + BR/EDR not supported (0x04)

    payload += bytes([0x1A]) # length:  26 bytes
    payload += bytes([0xFF]) # AD type: Manufacturer Specific Data (0xFF)

    payload += _left_pad(PREAMBLE,                  4)

    if type(data["id"]) is bytes:
        payload += data["id"]
    else:
        payload += bytes([0x00, 0x00, 0x00, 0x00])

    payload += int(data["uptime"]).to_bytes(        4, byteorder="big") 
    payload += data["images_taken"].to_bytes(       2, byteorder="big") 
    payload += data["errors"].to_bytes(             2, byteorder="big") 
    payload += data["mode"].to_bytes(               1, byteorder="big") 
    payload += int(data["free_space"]).to_bytes(    4, byteorder="big") 
    payload += int(data["temp"]).to_bytes(          2, byteorder="big", signed=True) 
    payload += int(data["battery"]).to_bytes(       2, byteorder="big", signed=True)     

    if len(payload) > BLE_ADVERTISEMENT_PAYLOAD_LENGTH:
        raise Exception("payload of length {} exceeds maximum length {}".format(len(payload), BLE_ADVERTISEMENT_PAYLOAD_LENGTH))

    if len(payload) < BLE_ADVERTISEMENT_PAYLOAD_LENGTH:
        print("zero padding message with {} zeros".format(BLE_ADVERTISEMENT_PAYLOAD_LENGTH-len(payload)))
        payload = payload + bytes([0x0] * (BLE_ADVERTISEMENT_PAYLOAD_LENGTH-len(payload)))

    call_config = call_config.format(_format_message(payload))

    # log.debug("raw hcitool command: {}".format(call_config))

    subprocess.run(call_attach, check=False, shell=True)
    subprocess.run(call_up,     check=False, shell=True)
    subprocess.run(call_config, check=True, shell=True)
    subprocess.run(call_start,  check=True, shell=True)

    log.debug("starting BLE advertisement")

    if not ADVERTISE_INDEFINITELY:
        time.sleep(10)
        subprocess.run(call_stop,   check=True, shell=True)
        log.debug("finished BLE advertisement")
    else:
        log.debug("permanent BLE advertisement")


if __name__ == "__main__":

    # random stuff for testing

    data = {}
    data["id"]              = 123456
    data["uptime"]          = 100
    data["images_taken"]    = 50
    data["errors"]          = 0
    data["mode"]            = 1
    data["free_space"]      = 128
    data["temp"]            = -181
    data["battery"]         = 128

    advertise(data)