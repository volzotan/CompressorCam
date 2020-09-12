################################################################################
#
# python-plumbum
#
################################################################################

PYTHON_PLUMBUM_VERSION = 1.6.8
PYTHON_PLUMBUM_SOURCE = plumbum-$(PYTHON_PLUMBUM_VERSION).tar.gz
PYTHON_PLUMBUM_SITE = https://files.pythonhosted.org/packages/dd/fa/dd1cbfe75006c7ffc3c4f89612fd8b6c7391754cb2ea72e8737d4f048e61
PYTHON_PLUMBUM_SETUP_TYPE = setuptools
PYTHON_PLUMBUM_LICENSE = MIT
PYTHON_PLUMBUM_LICENSE_FILES = LICENSE

$(eval $(python-package))
