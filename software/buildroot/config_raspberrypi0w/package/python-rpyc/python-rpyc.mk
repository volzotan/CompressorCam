################################################################################
#
# python-rpyc
#
################################################################################

PYTHON_RPYC_VERSION = 4.1.2
PYTHON_RPYC_SOURCE = rpyc-$(PYTHON_RPYC_VERSION).tar.gz
PYTHON_RPYC_SITE = https://files.pythonhosted.org/packages/0e/36/3d8c7ba73535aa0df1319b55af882d0d8b87d5297c016d4991970d4e7999
PYTHON_RPYC_SETUP_TYPE = setuptools
PYTHON_RPYC_LICENSE = MIT
PYTHON_RPYC_LICENSE_FILES = LICENSE

$(eval $(python-package))
