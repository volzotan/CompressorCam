#/bin/sh

HOSTNAME="compressorcam"

# remount main partition as RW
ssh $HOSTNAME 'mount -o remount,rw /dev/root /'

rsync -av                           \
--delete                            \
--exclude=".DS_Store"               \
--exclude="*.pyc"                   \
--exclude="README.md"               \
~/GIT/CompressorCam/software/ccam $HOSTNAME:/home/pi

# remount main partition as RO
# ssh $HOSTNAME 'mount -o remount,ro /dev/root /'