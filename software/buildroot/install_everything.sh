#!/bin/sh

HOSTNAME="compressorcam"

# remount main partition as RW
ssh $HOSTNAME 'mount -o remount,rw /dev/root /'

# create /boot dir so fstab can mount the boot partition
ssh $HOSTNAME 'mkdir /boot'
ssh $HOSTNAME 'mkdir /media/storage'
# ssh $HOSTNAME 'mkdir /media/external_storage'

# ------------------------------------------

# echo "resize partition and reboot"
# scp resize_fs.sh $HOSTNAME:/root
# ssh $HOSTNAME 'sh /root/resize_fs.sh'

# echo "sleep 20s"
# sleep 20

# echo "finishing resizing partitions"
# ssh $HOSTNAME 'resize2fs /dev/mmcblk0p2'

# ------------------------------------------

# not required anymore: buildroot does already create the partition

# echo "creating new partition and reboot"
# scp create_fs.sh $HOSTNAME:/root
# scp remount_rw.sh $HOSTNAME:/root
# ssh $HOSTNAME 'sh /root/create_fs.sh'

# echo "sleep 20s"
# sleep 20

# echo "format new partition"
# # ssh $HOSTNAME 'mke2fs -t ext4 /dev/mmcblk0p3'
# # ssh $HOSTNAME 'mkexfatfs -n CCSTORAGE /dev/mmcblk0p3'
# ssh $HOSTNAME 'mkfs.vfat -F 32 -n CCSTORAGE /dev/mmcblk0p3'

# ssh $HOSTNAME 'reboot'

# echo "sleep 20s"
# sleep 20

# ------------------------------------------

ssh $HOSTNAME 'sh /root/resize_fs.sh'

echo "sleep 20s"
sleep 20

# ------------------------------------------

echo "\n---"
echo "setting current time and date on the pi"
sh set_date.sh

# upload script takes care of RW-remount
echo "\n---"
echo "uploading ccam program files"
sh upload_program_files.sh

# echo "\n---"
# echo "deleting files"
# sh buildroot_clean.sh

# install script need to access /boot/config.txt and cmdline.txt 
# so boot partition needs to be mounted for this

echo "\n---"
echo "download pip packages"
ssh $HOSTNAME 'sh /home/pi/ccam/buildroot_install.sh'

echo "DONE! reboot..."
ssh $HOSTNAME 'reboot'