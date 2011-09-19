#include "spectrummonitor.h"
#include <stdio.h>

module SpectrumMonitorC {
  provides interface Receive as TraceReceive;
  uses {
    interface Boot;
    interface Leds;
    interface Resource as SpiResource;
    interface CC2420Power;
    interface StdControl as TxControl;
    interface AsyncSplitControl as RxControl;
    interface Alarm<T32khz,uint32_t>;
    interface Packet as TracePacket;
  }
}
implementation {

  message_t m_traceMsg;
  message_t *m_traceMsgPtr;
  norace printf_msg_t* m_currentTrace;
  uint16_t m_traceIndex;
  uint16_t fvector[] = FREQUENCY_VECTOR;
  uint16_t findex;

#define NUM_FREQUENCIES (sizeof(fvector) / sizeof(uint16_t))

  norace uint32_t tlast;

  task void startRxControlTask();
  task void sendDataOverSerialTask();
  inline int8_t readRssiFast();

  event void Boot.booted() 
  {
    call Leds.led2On();
    m_traceMsgPtr = &m_traceMsg;
    m_currentTrace = (printf_msg_t*) call TracePacket.getPayload(m_traceMsgPtr, sizeof(printf_msg_t));
    if (call TracePacket.maxPayloadLength() < sizeof(printf_msg_t)){
      call Leds.led1On();
      return;
    }
    call SpiResource.request();
  }

  event void SpiResource.granted() 
  {
    call CC2420Power.startVReg(); 
  }

  async event void CC2420Power.startVRegDone()
  {
    call CC2420Power.startOscillator();
  }

  async event void CC2420Power.startOscillatorDone()
  {
/*    call CC2420Power.setChannel(fvector[0]);*/
    call CC2420Power.setFrequency(fvector[0]);
    post startRxControlTask();
  }

  task void startRxControlTask()
  {
    error_t error;
    call TxControl.start();
    call SpiResource.release(); // need to be available for RxControl... 
    error = call RxControl.start();
    if (error != SUCCESS)
      call Leds.led0On();
  }

  async event void RxControl.startDone(error_t error)
  {
    // RadioRx component is ready for Rx in unbuffered mode!
    if (error != SUCCESS)
      call Leds.led0On();
    if (call SpiResource.immediateRequest() != SUCCESS)
      call Leds.led0On();

    call CC2420Power.flushRxFifo();
    call CC2420Power.rxOn();
    call Leds.led2Off();


    tlast = call Alarm.getNow();
    call Alarm.startAt(tlast, SAMPLING_PERIOD);
  }

  async event void Alarm.fired()
  {
    int numwritten;
    int16_t remaining;
    int8_t rssi;
    uint32_t now = call Alarm.getNow();

    atomic {
      if (now > tlast + SAMPLING_PERIOD + 1)
        call Leds.led0On();

      rssi = readRssiFast() - 45;

      call CC2420Power.rfOff();
/*      call CC2420Power.setChannel(fvector[findex++]);*/
      call CC2420Power.setFrequency(fvector[findex++]);
      call CC2420Power.rxOn();

      if (findex == NUM_FREQUENCIES)
        numwritten = snprintf((char*) &m_currentTrace->buffer[m_traceIndex], MAX_STRLEN, "%d\n", rssi);
      else
        numwritten = snprintf((char*) &m_currentTrace->buffer[m_traceIndex], MAX_STRLEN, "%d ", rssi);
      findex = findex % NUM_FREQUENCIES;

      tlast += SAMPLING_PERIOD;
      if (numwritten <= 0 || numwritten > MAX_STRLEN)
        call Leds.led1On();
      else {
        m_traceIndex += numwritten;
        remaining = sizeof(printf_msg_t) - m_traceIndex;
        if (remaining < MAX_STRLEN) {
          memset((char*) &m_currentTrace->buffer[m_traceIndex], 0, remaining);
          post sendDataOverSerialTask();
          return;
        }
      }
      call Alarm.startAt(tlast, SAMPLING_PERIOD);
    }
  }

  task void sendDataOverSerialTask()
  {
    atomic {
      m_traceMsgPtr = signal TraceReceive.receive(m_traceMsgPtr, 
          call TracePacket.getPayload(m_traceMsgPtr, sizeof(printf_msg_t)), sizeof(printf_msg_t));
      m_currentTrace = (printf_msg_t*) call TracePacket.getPayload(m_traceMsgPtr, sizeof(printf_msg_t));
      m_traceIndex = 0;
      call Alarm.startAt(tlast, SAMPLING_PERIOD);
    }
  }

  inline int8_t readRssiFast()
  {
    // for a register read: after writing the address byte, two bytes are
    // read (we provide the clock by sending two dummy bytes)
    // this now takes only 13 us !
    int8_t rssi;
    //return call CC2420Power.rssiFast(); 
    P4OUT &= ~0x04;      // clear CSN, CS low
    // write address 0x53  (0x40 for register read, 0x13 for RSSI register address)
    U0TXBUF = 0x53;
    // wait until data has moved from UxTXBUF to the TX shift register 
    // and UxTXBUF is ready for new data. It doesnot indicate RX/TX completion.
    while (!(IFG1 & UTXIFG0))  
      ;
    U0TXBUF = 0;
    while (!(IFG1 & UTXIFG0))  
      ;
    U0TXBUF = 0;
    while (!(IFG1 & UTXIFG0))  
      ;
    while (!(U0TCTL & TXEPT))
      ;
    rssi = U0RXBUF;
    P4OUT |= 0x04;      // CS high
    return rssi; 
  }

  async event void RxControl.stopDone(error_t error) { call Leds.led0On(); }
}

