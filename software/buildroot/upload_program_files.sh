#/bin/sh

# remount main partition as RW
ssh buildroot 'mount -o remount,rw /dev/root /'

rsync -av                           \
--include="/*"                      \
--include="ccam.py"             \
--include="devices.py"              \
--include="requirements.txt"        \
--include="buildroot_install.sh"    \
--include="mjpg_stream.sh"          \
--include="start_uhttpd.sh"         \
--exclude="*"                       \
~/GIT/CompressorCam/software/ccam compressorcam:/home/pi

# remount main partition as RO
# ssh buildroot 'mount -o remount,ro /dev/root /'