# setup buildroot with basic defconfig

make BR2_EXTERNAL=../external_tree zeroroot_defconfig
make menuconfig

# the init.d scripts require execute permissions
# permissions from the host system will be used on buildroot too

chmod 755 overlay/etc/init.d/S34compressorcam

# the picamera-python package requires (to date) an env var set for successful building:

export READTHEDOCS=True

# start build

make

# after flashing and booting:

sh install_everything.sh