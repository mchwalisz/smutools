/*
 * Copyright (c) 2007, Technische Universitaet Berlin
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * - Redistributions of source code must retain the above copyright notice,
 *   this list of conditions and the following disclaimer.
 * - Redistributions in binary form must reproduce the above copyright
 *   notice, this list of conditions and the following disclaimer in the
 *   documentation and/or other materials provided with the distribution.
 * - Neither the name of the Technische Universitaet Berlin nor the names
 *   of its contributors may be used to endorse or promote products derived
 *   from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
 * TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
 * OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
 * OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
 * USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * - Revision -------------------------------------------------------------
 * $Revision: 1.4 $
 * $Date: 2006/12/12 18:23:06 $
 * @author: Jan Hauer <hauer@tkn.tu-berlin.de>
 * ========================================================================
 */

#include "spectrummonitor.h"
#include <Serial.h>
#include "crc.h"
module SerialResponsiveP
{
  provides {
    interface Packet as TracePacket;
  } uses {
    interface Boot;
    interface Receive as TraceReceive;
    interface Pool<message_t> as MessagePool;
    interface Queue<message_t*> as MessageOutQueue;

    interface Resource as UartResource;
    interface HplMsp430Usart as Usart;
    interface HplMsp430UsartInterrupts as UsartInterrupts;
  
    interface Leds;
  }
} implementation {

  typedef enum {
    S_INIT_1,
    S_INIT_2,
    S_INIT_3,
    S_INIT_4,
    S_INIT_5,
    S_CONVERTING,
    S_CRC1,
    S_CRC2,
    S_END,
    S_DONE,

    NUM_CONVERSION_BYTES = 1,
  } sd_state_t;

  bool m_started;
  norace bool m_busySending;
  uint8_t m_hdlcData[sizeof(message_t)*10];
  uint16_t m_hdlcDataIndx;
  uint16_t m_txCRC;
  sd_state_t m_state;
  serial_header_t* m_serialHeader;
  uint8_t *m_msgPtr;
  uint8_t m_msgPtrIndx;
  uint8_t m_data;

  task void sendSerialTask();
  task void txNextByteTask();
  task void uartSendTask();
  void uartSend(uint8_t data);
  task void uartSendRawTask();
  void uartSendRaw(uint8_t data);

  enum {
    // Assumption SMCL runs at binary 4MHZ, i.e. where 1MHZ = 1048576 Hz
    UBR_8MHZ_57600=0x008E,  UMCTL_8MHZ_57600=0x44, 
    UBR_4MHZ_57600=0x0048,  UMCTL_4MHZ_57600=0x7B, 
    UBR_2MHZ_57600=0x0024,  UMCTL_2MHZ_57600=0x29, 
    UBR_1MHZ_57600=0x0012,  UMCTL_1MHZ_57600=0x84, 

    UBR_1MHZ_115200=0x0009, UMCTL_1MHZ_115200=0x10,
  };

  msp430_uart_union_config_t msp430_uart_telos_config = { {ubr: UBR_1MHZ_115200, umctl: UMCTL_1MHZ_115200, ssel: 0x02, pena: 0, pev: 0, spb: 0, clen: 1, listen: 0, mm: 0, ckpl: 0, urxse: 0, urxeie: 1, urxwie: 0, utxe : 1, urxe : 1} };

/*  msp430_uart_union_config_t msp430_uart_telos_config = { {ubr: UBR_8MHZ_57600, umctl: UMCTL_8MHZ_57600, ssel: 0x02, pena: 0, pev: 0, spb: 0, clen: 1, listen: 0, mm: 0, ckpl: 0, urxse: 0, urxeie: 1, urxwie: 0, utxe : 1, urxe : 1} };*/

  event void Boot.booted() {
    m_busySending = FALSE;
    m_started = FALSE;
    call UartResource.request();
  }

  event void UartResource.granted(){
    call Usart.setModeUart(&msp430_uart_telos_config);
    call Usart.disableRxIntr();
    call Usart.disableTxIntr();
    call Usart.disableIntr();
    IFG2 |= UTXIFG1; // for internal state, means that uart tx register is ready
    m_started = TRUE;
  }

  event message_t* TraceReceive.receive(message_t* msg, void* payload, uint8_t len)
  {
    message_t* emptyMessage = call MessagePool.get();
    if (emptyMessage != NULL && len == sizeof(printf_msg_t) && m_started){
      call MessageOutQueue.enqueue(msg);
      post sendSerialTask();
      return emptyMessage;
    } else {
      call Leds.led0On();
      return msg;
    }
  }

  task void sendSerialTask()
  {
    message_t* msg;
    if (!call MessageOutQueue.empty() &&  !m_busySending){
      m_busySending = TRUE;
      m_state = S_INIT_1;
      msg = call MessageOutQueue.head();
      m_serialHeader = (serial_header_t*)(msg->data - sizeof(serial_header_t));
      post txNextByteTask();
    }
  }

  task void txNextByteTask()
  {
    // the HDLC conversion takes a lot of time (~3ms) - in order to keep 
    // the system responsive we spin tasks (we don't care about energy). it 
    // creates some overhead for posting the tasks but overall we're much faster.
    uint8_t data;
    switch (m_state)
    {
      case S_INIT_1:
        m_serialHeader->dest = AM_BROADCAST_ADDR;
        m_serialHeader->type = AM_PRINTF_MSG;
        m_serialHeader->length = sizeof(printf_msg_t);
        // make HDLC conversion, create the header as described in TEP113 (but w/o seqno!)
        m_txCRC = 0;
        m_state = S_INIT_2;
        uartSendRaw(HDLC_FLAG_BYTE);
        break;
      case S_INIT_2:
        m_txCRC = crcByte(m_txCRC,SERIAL_PROTO_PACKET_NOACK);
        m_state = S_INIT_3;
        uartSend(SERIAL_PROTO_PACKET_NOACK);
        break;
      case S_INIT_3:
        m_txCRC = crcByte(m_txCRC,TOS_SERIAL_ACTIVE_MESSAGE_ID);
        m_msgPtr = (uint8_t*) m_serialHeader;
        m_msgPtrIndx = 0;
        m_state = S_CONVERTING;
        uartSend(TOS_SERIAL_ACTIVE_MESSAGE_ID);
        break;
      case S_CONVERTING:
        data = m_msgPtr[m_msgPtrIndx++];
        m_txCRC = crcByte(m_txCRC, data);
        if (m_msgPtrIndx == sizeof(serial_header_t) + sizeof(printf_msg_t))
          m_state = S_CRC1;
        uartSend(data);
        break;
      case S_CRC1:
        m_state = S_CRC2;
        uartSend((m_txCRC & 0xff));
        break;
      case S_CRC2:
        m_state = S_END;
        uartSend((m_txCRC >> 8) & 0xff);
        break;
      case S_END:
        m_state = S_DONE;
        uartSendRaw(HDLC_FLAG_BYTE);
        break;
      case S_DONE: 
        call MessagePool.put(call MessageOutQueue.dequeue());
        m_busySending = FALSE;
        post sendSerialTask();
      default:
        break;
    }
  }

  void uartSend(uint8_t data)
  {
    if( !call Usart.isTxIntrPending() ){
      m_data = data;
      post uartSendTask(); // spin
    } else {
      call Usart.clrTxIntr();
      // hdlc conversion
      if (data == HDLC_FLAG_BYTE || data == HDLC_CTLESC_BYTE){
        call Usart.tx(HDLC_CTLESC_BYTE);
        m_data = data ^ 0x20;
        post uartSendTask();
      } else {
        call Usart.tx(data);
        post txNextByteTask();
      }
    }
  }

  task void uartSendTask()
  {
    uartSend(m_data);
  }

  void uartSendRaw(uint8_t data)
  {
    if( !call Usart.isTxIntrPending() ){
      m_data = data;
      post uartSendRawTask(); // spin
    } else {
      call Usart.clrTxIntr();
      // no hdlc conversion
      call Usart.tx(data);
      post txNextByteTask();
    }
  }

  task void uartSendRawTask()
  {
    uartSendRaw(m_data);
  }

  async event void UsartInterrupts.txDone(){}
  async event void UsartInterrupts.rxDone(uint8_t data){}

  command void TracePacket.clear(message_t* msg){ memset(msg->data, 0, TOSH_DATA_LENGTH);}
  command uint8_t TracePacket.payloadLength(message_t* msg){ 
    return ((serial_header_t*)(msg->data - sizeof(serial_header_t)))->length;}
  command void TracePacket.setPayloadLength(message_t* msg, uint8_t len){
    ((serial_header_t*)(msg->data - sizeof(serial_header_t)))->length = len;}
  command uint8_t TracePacket.maxPayloadLength(){ return TOSH_DATA_LENGTH;}
  command void* TracePacket.getPayload(message_t* msg, uint8_t len){ return msg->data;}
}

