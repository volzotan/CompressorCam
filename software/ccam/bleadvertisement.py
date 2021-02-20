#!/usr/bin/env python3

import subprocess
import time

BLE_ADVERTISEMENT_PAYLOAD_LENGTH = 26

def advertise():

    call_attach = "hciattach /dev/ttyS0 bcm43xx 921600 noflow -"
    call_up     = "hciconfig hci0 up"
    call_config = "hcitool -i hci0 cmd 0x08 0x0008 1e 02 01 05 1a ff {}"
    call_start  = "hciconfig hci0 leadv 3" # advertise as non-connectable service
    call_stop   = "hciconfig hci0 noleadv"

    data = bytes([(0x00), (0x01), (0x1A), (25)])

    if len(data) < BLE_ADVERTISEMENT_PAYLOAD_LENGTH:
        data = data + bytes([0x0] * (BLE_ADVERTISEMENT_PAYLOAD_LENGTH-len(data)))

    data_formatted = ""

    for i in range(0, len(data)):

        data_formatted += "{:02}".format(data[i]) # zero padding

        if i < len(data)-1:
            data_formatted += " "

    call_config = call_config.format(data_formatted)

    subprocess.run(call_attach, check=False, shell=True)
    subprocess.run(call_up,     check=False, shell=True)
    subprocess.run(call_config, check=True, shell=True)
    subprocess.run(call_start,  check=True, shell=True)

    time.sleep(10)

    subprocess.run(call_stop)

if __name__ == "__main__":

    advertise()