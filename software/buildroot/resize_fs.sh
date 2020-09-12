#!/bin/sh

# copy resize_fs.sh to pi and run it
# after reboot: resize2fs /dev/mmcblk0p2

echo "RESIZING PARTITIONS!"

# ROOT_PART=mmcblk0p2
PART_NUM=2

# Get the starting offset of the root partition
PART_START=$(parted /dev/mmcblk0 -ms unit s p | grep "^${PART_NUM}" | cut -f 2 -d: | sed 's/[^0-9]//g')
[ "$PART_START" ] || return 1

# Return value will likely be error for fdisk as it fails to reload the
# partition table because the root fs is mounted
fdisk -u /dev/mmcblk0 <<EOF
p
d
$PART_NUM
n
p
$PART_NUM
$PART_START

p
w
EOF

sleep 5

echo "\n\n"
echo "REBOOT!"

sleep 5

reboot