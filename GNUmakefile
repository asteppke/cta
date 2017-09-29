include /ioc/tools/driver.makefile

BUILDCLASSES = Linux

MODULE = cta

EXCLUDE_VERSIONS = 3.13 3.14.8

ARCH_FILTER = SL6-x86_64 eldk52-e500v2

SOURCES += seqCtrl/devSeqCtrl.c
SOURCES += seqCtrl/seqCtrl.c

DBDS += seqCtrl/seqCtrl.dbd

TEMPLATES += seqCtrl/seqCtrl.db

ifeq (spy, $(CONF))
	CFLAGS += -DQ_SPY
  qpc_VERSION = spy
else
  qpc_VERSION = dbg
endif

