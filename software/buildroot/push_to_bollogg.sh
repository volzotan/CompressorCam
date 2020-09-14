#!/bin/sh

DIR="bollogg:/home/volzotan/buildroot_extree/external_tree/"

rsync -av config_raspberrypi0w/ bollogg:/home/volzotan/buildroot_extree/external_tree/ --delete --exclude=".DS_Store"