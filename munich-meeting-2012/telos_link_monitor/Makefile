COMPONENT=./src/LQMC
CFLAGS += -I./src -I./src/cc2420
CFLAGS += -I$(TOSDIR)/lib/printf
CFLAGS += -DPRINTF_BUFFER_SIZE=3000
TOSMAKE_PATH += ./extras
CFLAGS += -DCOMPILE_TIME='"$(shell date)"'

include $(MAKERULES)


