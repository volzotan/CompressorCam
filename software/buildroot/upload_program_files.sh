#/bin/sh

# remount main partition as RW
ssh buildroot 'mount -o remount,rw /dev/root /'

rsync -av                           \
--delete                            \
--exclude=".DS_Store"               \
--exclude="*.pyc"                   \
--exclude="README.md"               \
~/GIT/CompressorCam/software/ccam compressorcam:/home/pi

# remount main partition as RO
# ssh buildroot 'mount -o remount,ro /dev/root /'