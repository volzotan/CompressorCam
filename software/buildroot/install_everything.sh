
# remount main partition as RW
ssh buildroot 'mount -o remount,rw /dev/root /'

# create /boot dir so fstab can mount the boot partition
ssh buildroot 'mkdir /boot'
ssh buildroot 'mkdir /media/storage'
# ssh buildroot 'mkdir /media/external_storage'

# ------------------------------------------

# echo "resize partition and reboot"
# scp resize_fs.sh buildroot:/root
# ssh buildroot 'sh /root/resize_fs.sh'

# echo "sleep 20s"
# sleep 20

# echo "finishing resizing partitions"
# ssh buildroot 'resize2fs /dev/mmcblk0p2'

# ------------------------------------------

echo "creating new partition and reboot"
scp create_fs.sh buildroot:/root
scp remount_rw.sh buildroot:/root
ssh buildroot 'sh /root/create_fs.sh'

echo "sleep 20s"
sleep 20

echo "format new partition"
ssh buildroot 'mke2fs -t ext4 /dev/mmcblk0p3'

ssh buildroot 'reboot'

echo "sleep 20s"
sleep 20

# ------------------------------------------

echo "\n---"
echo "setting current time and date on the pi"
sh set_date.sh

# upload_zerobox.sh takes care of RW-remount
echo "\n---"
echo "uploading zerobox files"
sh upload_zerobox.sh

echo "\n---"
echo "deleting files"
sh buildroot_clean.sh

# install script need to access /boot/config.txt and cmdline.txt 
# so boot partition needs to be mounted for this

echo "\n---"
echo "download pip packages"
ssh buildroot 'sh /home/pi/zerobox/buildroot_install.sh'

echo "DONE! reboot..."
ssh buildroot 'reboot'