################################################################################
#
# python-hid
#
################################################################################

PYTHON_HID_VERSION = 1.0.4
PYTHON_HID_SOURCE = hid-$(PYTHON_HID_VERSION).tar.gz
PYTHON_HID_SITE = https://files.pythonhosted.org/packages/96/ba/e1923a3f7f865cd9f3c388bf6a42b4ed149ae1a00e68f71eec49ea3d3da4
PYTHON_HID_SETUP_TYPE = setuptools
PYTHON_HID_LICENSE = MIT

$(eval $(python-package))
