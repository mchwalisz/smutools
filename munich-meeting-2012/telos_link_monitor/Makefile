COMPONENT=./src/LQMC
CFLAGS += -I./src -I./src/cc2420
CFLAGS += -I$(TOSDIR)/lib/printf
CFLAGS += -DPRINTF_BUFFER_SIZE=3000
TOSMAKE_PATH += ./extras
CFLAGS += -DCOMPILE_TIME='"$(shell date)"'


# here we retrieve the FTDI chip ID of the telosb as
# returned by the "motelist" script and pass it as
# preprocessor define to the compiler ...
TMP1 := [,.]
TMP2 := $(shell perl -e 'print join " ", map {s{^(.*?)$(TMP1)}{\U$$1=};$$_} grep /$(TMP1)/, split /\s+/, "$(MAKECMDGOALS)";')
BSLSTR := ($(findstring BSL=/dev/ttyUSB,$(TMP2)),)
ifeq ($(BSLSTR),(,))
$(error You must pass the 'bsl,...' option )
endif
TTYUSB = $(shell perl -e 'print substr("$(TMP2)",4,14);')
FTDI_CHIP_ID=$(shell motelist | grep /dev/ttyUSB0 | awk '{print $$1}')
CFLAGS += -DFTDI_CHIP_ID='"$(FTDI_CHIP_ID)"'

include $(MAKERULES)



