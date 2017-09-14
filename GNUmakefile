include /ioc/tools/driver.makefile

BUILDCLASSES = Linux

MODULE = cta

EXCLUDE_VERSIONS = 3.13 3.14.8

ARCH_FILTER = SL6-x86_64 eldk52-e500v2

qpc_VERSION = biffiger_r

ifeq (spy, $(CONF))
	CFLAGS += -DQ_SPY
endif

