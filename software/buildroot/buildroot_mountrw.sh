#!/bin/sh

ssh buildroot 'mount -o remount,rw /dev/root /'

echo "RE-MOUNTED MAIN PARTITION RW\n"