#!/bin/sh

ifup wlan0
sleep 1
hostapd -B /etc/hostapd.conf