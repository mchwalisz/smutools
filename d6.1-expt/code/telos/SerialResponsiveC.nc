#include "spectrummonitor.h"

configuration SerialResponsiveC
{
  provides {
    interface Packet as TracePacket;
  } uses {
    interface Receive as TraceReceive;
  }
} implementation {

  components SerialResponsiveP as Dump;
  components MainC, LedsC;
  components new PoolC(message_t, SERIAL_BUFFER_SIZE);
  components new QueueC(message_t*, SERIAL_BUFFER_SIZE);

  TraceReceive = Dump;
  TracePacket = Dump; 
  
  Dump.Boot -> MainC;
  Dump.MessagePool -> PoolC;
  Dump.MessageOutQueue -> QueueC;
  Dump.Leds -> LedsC;

  components new Msp430Usart1C() as UsartC;
  Dump.UartResource -> UsartC.Resource;
  Dump.Usart -> UsartC.HplMsp430Usart;
  Dump.UsartInterrupts -> UsartC.HplMsp430UsartInterrupts;
}

