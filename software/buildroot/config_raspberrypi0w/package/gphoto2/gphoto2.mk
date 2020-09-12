GPHOTO2_VERSION = 2.5.23
GPHOTO2_SOURCE = gphoto2-$(GPHOTO2_VERSION).tar.bz2
GPHOTO2_SITE = https://downloads.sourceforge.net/project/gphoto/gphoto/$(GPHOTO2_VERSION)

GPHOTO2_LICENSE_FILES = COPYING
GPHOTO2_INSTALL_STAGING = YES

GPHOTO2_DEPENDENCIES = libgphoto2 popt

GPHOTO2_CONF_ENV = POPT_CFLAGS="-I$(STAGING_DIR)/usr/include" POPT_LIBS="-L$(STAGING_DIR)/usr -lpopt"
# GPHOTO2_CONF_OPTS += --oldincludedir=$(STAGING_DIR)

# POPT_CFLAGS = "-I=$(STAGING_DIR)/usr/include"
# GPHOTO"_POPT_CFLAGS = "-I=$(STAGING_DIR)/usr/include"

$(eval $(autotools-package))

