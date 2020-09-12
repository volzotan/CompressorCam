################################################################################
#
# python-exifread
#
################################################################################

PYTHON_EXIFREAD_VERSION = 2.1.2
PYTHON_EXIFREAD_SOURCE = ExifRead-$(PYTHON_EXIFREAD_VERSION).tar.gz
PYTHON_EXIFREAD_SITE = https://files.pythonhosted.org/packages/7b/cb/92b644626830115910cf2b36d3dfa600adbec86dff3207a7de3bfd6c6a60
PYTHON_EXIFREAD_SETUP_TYPE = setuptools
PYTHON_EXIFREAD_LICENSE = BSD
PYTHON_EXIFREAD_LICENSE_FILES = LICENSE.txt

$(eval $(python-package))
