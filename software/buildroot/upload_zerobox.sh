#/bin/sh

# rsync -av               \
# --exclude="RAW/"        \
# --exclude="captures_1"  \
# --exclude="captures_2"  \
# --exclude="captures_3"  \
# --exclude="*.jpg"       \
# --exclude="*.log"       \
# --exclude="__pycache__" \
# ~/GIT/timebox/zerobox buildroot:/home/pi

# remount main partition as RW
ssh buildroot 'mount -o remount,rw /dev/root /'

rsync -av                           \
--include="/*"                      \
--include="trashcam.py"             \
--include="devices.py"              \
--include="requirements.txt"        \
--include="buildroot_install.sh"    \
--include="mjpg_stream.sh"          \
--exclude="*"                       \
~/GIT/timebox/zerobox buildroot:/home/pi

# remount main partition as RO
# ssh buildroot 'mount -o remount,ro /dev/root /'