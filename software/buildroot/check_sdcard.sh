#!/bin/sh

DISK="/Volumes/UNTITLED/"

f3write $DISK
f3read $DISK

# ---

# sudo f3probe --destructive --time-ops /dev/sdb