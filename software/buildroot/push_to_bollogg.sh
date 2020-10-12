#!/bin/sh

DIR="bollogg:/home/volzotan/buildroot_extree/external_tree/"

rsync -av config_raspberrypi0w/ $DIR --delete --exclude=".DS_Store"

rsync -av ../ccam $DIR"overlay/home/pi"             \
    --delete                                        \
    --exclude=".DS_Store"                           \
    --exclude="README.md"                           \
    --exclude="*.pyc"                               \
    --exclude="*__pycache__*"                           