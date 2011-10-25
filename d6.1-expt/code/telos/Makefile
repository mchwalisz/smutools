COMPONENT=SpectrumMonitorAppC
# CFLAGS += -I$(TOSDIR)/lib/printf
CFLAGS +=  -I./cc2420/
C_INCLUDE = $(TOSDIR)/../support/sdk/c/sf
BUILD_EXTRA_DEPS += twist_trace_parser

ifdef FREQUENCY_VECTOR
CFLAGS += -DFREQUENCY_VECTOR=$(FREQUENCY_VECTOR)
endif

include $(MAKERULES)

twist_trace_parser: twist_trace_parser.c $(MSGS)
	gcc $(GCCFLAGS) -I$(C_INCLUDE) -g -O2 twist_trace_parser.c -c -o twist_trace_parser.o
	gcc $(GCCFLAGS) -I$(C_INCLUDE) -g -O2 -o twist_trace_parser  twist_trace_parser.o $(C_INCLUDE)/libmote.a

clean: clean-twist

clean-twist:
	-rm -f twist_trace_parser

.PHONY: clean clean-twist
