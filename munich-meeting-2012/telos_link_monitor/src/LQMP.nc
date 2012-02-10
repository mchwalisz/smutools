/*
 * Copyright (c) 2009, Technische Universitaet Berlin
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

#include "IEEE802154.h"
#include <CC2420.h>
#include "lqm.h"
#include "UserButton.h"

generic module LQMP(uint8_t LQM_VARIANT, uint8_t LQM_ROLE) {

  provides {
    interface McuPowerOverride;
  }

  uses {
    interface Boot;
    interface Leds;
    interface Resource as SpiResource;
    interface StdControl as TxControl;        
    interface AsyncSplitControl as RxControl; 
    interface CC2420Power;
    interface CC2420Rx;
    interface CC2420Tx;
    interface Get<button_state_t> as GetButtonState;
    interface Notify<button_state_t> as ButtonPressed;
    interface Msp430ClockInit;
    interface Msp430Timer as TimerA;
    interface Alarm<T32khz,uint32_t>;

/*    interface Msp430Timer as TimerB;*/
/*    interface SerialSend;*/
/*    interface Packet as SerialPacket;*/
  }

} implementation {

  /* module variables */
  uint16_t m_initCounter;
  uint16_t m_initDelay;

  norace uint8_t m_packet[sizeof(header_154_t) + sizeof(payload_154_t)];
  norace uint32_t m_seqno;
  norace uint32_t m_serialSeqno;
  norace uint8_t m_error;
  norace uint16_t m_upperTime;
  norace bool m_wasNoisePostSampled;
  uint16_t m_destId[] = RECEIVER_IDS;
  uint16_t m_destIdIndex;
  noise_pre_entry_t m_noisePreList[NOISE_PRE_LIST_ENTRIES];
  uint16_t m_noisePreListIndex;

  message_t m_serialMsg;
  message_t *m_serialMsgPtr;
  norace lqm_trace_sender_t *m_traceSender;
  norace lqm_trace_receiver_t *m_traceReceiver;
  lqm_trace_info_t *m_traceInfo;


  norace enum {
    S_BOOT,
    S_INIT,
    S_IDLE_OFF,
    S_RX_PREPARE,
    S_LOAD_TXFIFO,
    S_SAMPLE_NOISE,
    S_PACKET_WAIT,
    S_ACK_WAIT,
    S_OFF_PENDING,
    S_SEND_SERIAL,
  } m_state;

  /* task/function prototypes */
  task void startDoneTask();
  task void initBlinkTask();
  task void rxControlStartTask();
  task void serialSendTask();
  task void txDoneTask();
  task void rxSampleNoisePostTask();
  task void txPacketTask();

  void startReceiver();
  void startSender();
/*  uint32_t convertToLocalTime(uint16_t tbr);*/
/*  uint32_t getNow();*/
  void offSpiReserved();
  void clearTrace();
  error_t sampleNoiseNow(uint8_t numSamples, int8_t* noise);
  void enableContinuousNoiseMonitoring();
  void disableContinuousNoiseMonitoring();
  bool isCrcCorrect(uint8_t *packet);


  /* ------------------- Booting ------------------- */

  event void Boot.booted()
  {
    m_state = S_BOOT;
    call SpiResource.request();
  }
  
  void bootSpiReserved()
  {
    call CC2420Power.startVReg();
  }

  async event void CC2420Power.startVRegDone()
  {
    call CC2420Power.startOscillator();
  }

  async event void CC2420Power.startOscillatorDone()
  {
    call CC2420Power.rfOff();
    call CC2420Power.setChannel(RADIO_CHANNEL);
    call CC2420Power.setTxPower(PA_LEVEL);
    call CC2420Tx.lockChipSpi();
    post startDoneTask();
  }

  task void startDoneTask()
  {
    header_154_t *header = (header_154_t*) m_packet;

    m_state = S_INIT;
    m_initDelay = (LQM_ROLE == LQM_SENDER ? INIT_DELAY : ((INIT_DELAY+1) / 2));
    m_seqno = 0;
    m_error = 0;
    m_destIdIndex = 0;

    // prepare MAC header -> length field: substract PHY length field (-1), add MAC footer (+2)
    header->length = sizeof(header_154_t) - 1 + sizeof(payload_154_t) + 2; 
    header->fcf = FRAME_TYPE_DATA | ACK_REQUEST | (DEST_MODE_SHORT << 8);
    if (LQM_VARIANT == LQM_BROADCAST)
      header->fcf &= ~ACK_REQUEST;
    header->destpan = PAN_ID;

    // prepare trace info
    m_serialMsgPtr = &m_serialMsg;
    m_traceInfo = (lqm_trace_info_t*) m_serialMsgPtr;//call SerialPacket.getPayload(m_serialMsgPtr, sizeof(lqm_trace_info_t));
    if (m_traceInfo == NULL) {
      m_error |= E_GENERIC;
      call Leds.led0On(); // error!
      return;
    }
    m_traceInfo->nodeID = TOS_NODE_ID;      
#if defined(_LQM_RECEIVER)
    m_traceInfo->nodeID = m_destId[0];      
#endif
    m_traceInfo->role = LQM_ROLE;
    m_traceInfo->paLevel = PA_LEVEL;
    m_traceInfo->channel = RADIO_CHANNEL;
    m_traceInfo->mpduSize = header->length;
    m_traceInfo->numPackets = NUM_PACKETS;

    call SpiResource.release();
    call ButtonPressed.enable();
    post initBlinkTask();
  }

  task void initBlinkTask()
  {
    if (m_state == S_INIT) {

      if (m_initCounter < 10000) {
        if (LQM_ROLE == LQM_SENDER)
          call Leds.set(0xFF); 
        else if (LQM_ROLE == LQM_RECEIVER)
          call Leds.set(2);
        else
          call Leds.led0On();
      } else 
        call Leds.set(0x00); 

      m_initCounter += 1;

      if (m_initCounter > 20000) {
        m_initCounter = 0;

        if (INIT_DELAY != 0) {
          m_initDelay -= 1;
          if (m_initDelay == 0)
            signal ButtonPressed.notify(BUTTON_PRESSED);
        }
      }
      post initBlinkTask(); // spin
    }
  }

  event void ButtonPressed.notify( button_state_t val )
  {
    lqm_trace_info_t *trace_info = (lqm_trace_info_t *) m_serialMsgPtr;//call SerialPacket.getPayload(m_serialMsgPtr, sizeof(lqm_trace_info_t));

    if (val == BUTTON_PRESSED && m_state == S_INIT) {
      m_state = S_IDLE_OFF;
      disableContinuousNoiseMonitoring();

      // send the trace-info over serial Receive
      /*
      m_serialMsgPtr = call SerialSend.send(m_serialMsgPtr, 
          call SerialPacket.getPayload(m_serialMsgPtr, sizeof(lqm_trace_info_t)), 
          sizeof(lqm_trace_info_t), AM_LQM_TRACE_INFO);
      */
      printf("# COMPILE_TIME: %s\n# NodeId: %u\n# Node FTDI chip ID: %s\n# Role: %s%s\n# PA_LEVEL: %u\n# Channel %u\n# Packet (MPDU) size: %u byte\n# No. packets to be transmitted: %lu\n",
          COMPILE_TIME, trace_info->nodeID, FTDI_CHIP_ID, (trace_info->role==0)?"receiver":"sender", (LQM_VARIANT == LQM_UNICAST)?" (unicast)":" (broadcast)",
          trace_info->paLevel, trace_info->channel, trace_info->mpduSize, trace_info->numPackets);
      printfflush();
      

      if (LQM_ROLE == LQM_SENDER)
        startSender();
      else if (LQM_ROLE == LQM_RECEIVER)
        startReceiver();
      // else (unknown role) -> do nothing ...

    } else if (val == BUTTON_PRESSED) {
      call Leds.set(m_state); // debug: display current state on LEDs
    }
  }

  async command mcu_power_t McuPowerOverride.lowestState()
  {
    return MSP430_POWER_ACTIVE; // never sleep
  }

  /* ------------------- Receiver ------------------- */

  void startReceiver() 
  {
    m_state = S_RX_PREPARE;
    clearTrace();
    call TxControl.start();
    post rxControlStartTask(); // will start the Rx logic and continue in receiverStarted()
  }

  void receiverStarted(error_t error)
  {
    if (error != SUCCESS || call SpiResource.immediateRequest() != SUCCESS) {
      m_error |= E_GENERIC;
      call Leds.led0On(); // error!
    }
    m_state = S_PACKET_WAIT;
    if (call CC2420Power.rxOn() != SUCCESS) {
      m_error |= E_GENERIC;
      call Leds.led0On(); // error!
    }
    call SpiResource.release();
    
    // start the continuous noise sampling in the background
    enableContinuousNoiseMonitoring();

    // we're in Rx mode -> the next event that we expect to happen is that we 
    // receive a packet and it will be signalled through dataPacketReceived() 
  }

  async event void TimerA.overflow()
  {
    atomic {
      if (call CC2420Tx.immediateSpiRequest() == SUCCESS) {
        m_noisePreListIndex = (m_noisePreListIndex + 1) % NOISE_PRE_LIST_ENTRIES;
        call CC2420Tx.rssi(&m_noisePreList[m_noisePreListIndex].noise);
        m_noisePreList[m_noisePreListIndex].noise -= 45; // convert to dBm (see CC2420 datasheet)
        m_noisePreList[m_noisePreListIndex].timestamp = call Alarm.getNow(); //getNow();
        call CC2420Tx.releaseSpi();
      } 
    }
  }

  bool dataPacketReceived(uint8_t *data, uint32_t timestamp, bool overflow)
  {
    uint16_t i;
    uint32_t refTime = 0, refIndex = 0;
    bool correctCrc = isCrcCorrect(data);

    if (overflow)
      m_error |= E_RXFIFO_OVERFLOW;

    // received a packet: is it really the DATA packet that we're expecting?
    if (correctCrc && data[0] == m_packet[0] && data[1] == m_packet[1] && data[2] == m_packet[2])
    {
      // yes! got a packet destined to us with the expected length.
      // (keep in mind that address recognition / ACK transmission is done in CC2420)
      payload_154_t *payload = (payload_154_t*) ((uint8_t*) data + sizeof(header_154_t));
      uint8_t mpduLen = *data; // first byte => PHY length field

      if (m_state != S_PACKET_WAIT) {
        // argh, the serial is too slow ...
        call Leds.led1On();
        m_error |= E_SERIAL_OVERFLOW;
        return FALSE;
      }
      disableContinuousNoiseMonitoring();

      m_state = S_SEND_SERIAL;
      m_traceReceiver->nodeID = TOS_NODE_ID; 
      atomic {
        if (timestamp != 0 && call CC2420Rx.isRxFifoEmpty()) {
          // timestamp represents SFD time -> find last noise value sampled
          // at least 5 byte (=160 us) before the SFD time
          for (i=0; i<NOISE_PRE_LIST_ENTRIES; i++) {
            if (m_noisePreList[i].timestamp + 7 <= timestamp)
              if (m_noisePreList[i].timestamp >= refTime) {
                refTime = m_noisePreList[i].timestamp;
                refIndex = i;
              }
          }
        } 
        if (refTime != 0) {
          m_traceReceiver->noisePre = m_noisePreList[refIndex].noise; 
          m_traceReceiver->noisePreTime = m_noisePreList[refIndex].timestamp; 
        } else {
          m_traceReceiver->noisePre = 127; // invalid
          m_traceReceiver->noisePreTime = 0; // invalid
        } 
      }
      m_traceReceiver->serialSeqno = m_serialSeqno++;
      m_traceReceiver->seqno = payload->seqno;
      m_traceReceiver->rssi = data[mpduLen - 1];
      m_traceReceiver->rssi -= 45; // convert to dBm (see CC2420 datasheet)
      m_traceReceiver->lqi = data[mpduLen] & 0x7F; // clear top bit -> CRC (always set, since we use AUTO_ACK)
      m_traceReceiver->rxTime = timestamp; 
      m_traceReceiver->error = m_error; 
      if (payload->seqno % (1000/PACKET_TX_PERIOD) == 0)
        call Leds.led2Toggle();
      post rxSampleNoisePostTask();

    }
    return FALSE; // keep Rx enabled
  }

  task void rxSampleNoisePostTask()
  {      
    if (call CC2420Tx.immediateSpiRequest() != SUCCESS) {
      post rxSampleNoisePostTask();
      return;
    } else if (sampleNoiseNow(NUM_RECEIVER_NOISE_SAMPLES_POST, (int8_t*) m_traceReceiver->noisePost) != SUCCESS) {
      call CC2420Tx.releaseSpi();
      post rxSampleNoisePostTask();
      return;
    } else {
      call CC2420Tx.releaseSpi();
      printf("%lu %lu %lu %d %u %d %u\n",
          m_traceReceiver->serialSeqno, m_traceReceiver->seqno, m_traceReceiver->rxTime, 
          m_traceReceiver->rssi, m_traceReceiver->lqi, m_traceReceiver->noisePost[0], m_traceReceiver->error);
      printfflush();
      post serialSendTask();
    }
  }

  /* ------------------- Sender ------------------- */

  void startSender()
  {
    header_154_t *header = (header_154_t*) m_packet;
    payload_154_t *payload = (payload_154_t*) ((uint8_t*) m_packet + sizeof(header_154_t));

    clearTrace();
    call TxControl.start();
    m_state = S_LOAD_TXFIFO;
    if (LQM_VARIANT == LQM_UNICAST)
      m_traceSender->destID = header->dest = m_destId[m_destIdIndex];
    else if (LQM_VARIANT == LQM_BROADCAST)
      m_traceSender->destID = header->dest = BROADCAST_ADDRESS;
    
    m_wasNoisePostSampled = FALSE;
    payload->seqno = m_seqno;
    header->dsn = m_seqno; // LSB

    // load the TXFIFO with the DATA packet
    if (call CC2420Tx.loadTXFIFO(m_packet) != SUCCESS) { 
      m_error |= E_GENERIC;
      call Leds.led0On(); // error!
    }
  }

  async event void CC2420Tx.loadTXFIFODone(uint8_t *data, error_t error)
  {
    if (error != SUCCESS) {
      m_error |= E_GENERIC;
      call Leds.led0On(); // error!
    }
    m_state = S_SAMPLE_NOISE;
    // -> make CC2420TransmitP owner of the Spi, so CC2420ReceiveP won't interfere
    if (call CC2420Tx.immediateSpiRequest() != SUCCESS) {
      m_error |= E_GENERIC;
      call Leds.led0On(); // error!
    }
     if (m_seqno == 0)
      call Alarm.start(0);
    else
      call Alarm.startAt(call Alarm.getAlarm(), PACKET_TX_PERIOD*32.768);
  }

  async event void Alarm.fired()
  {
    call CC2420Tx.rxOn();
    post txPacketTask();
  }

  task void txPacketTask()
  {
    // The radio is in Rx mode (but RSSI may not be valid yet), and the
    // SPI is owned by Transmit component. Before we send the packet
    // we take NUM_NOISE_SAMPLES non-overlapping (in time) RSSI samples, 
    // i.e. one sample every 128us.


    atomic {
      if (sampleNoiseNow(NUM_SENDER_NOISE_SAMPLES_PRE, 
            (int8_t*) m_traceSender->noisePre) != SUCCESS) {
        post txPacketTask(); // RSSI not valid -> spin
        return;
      }
      //P6OUT &= ~0x02;     // low
      m_traceSender->cca = call CC2420Tx.cca();
      call CC2420Tx.send(); // go (without CCA)!
      //P6OUT |= 0x02;      // high 

      // we just started sending the first bytes of the packet...
      // if we previously received a packet while we collected the 
      // noise floor samples, then it should be flushed out ...
      if (call CC2420Tx.flushRxFifo() != SUCCESS) {
        m_error |= E_GENERIC;
        call Leds.led0On();
      }
      call CC2420Tx.releaseSpi(); // allow Rx logic to take over for the ACK

      /* Note: the receive logic of the CC2420 driver is not yet  */
      /* started, i.e. we cannot (yet) have received any packets  */

      // start the Rx logic -> will then continue in senderRxEnabled()
      if (LQM_VARIANT == LQM_UNICAST) {
        if (call RxControl.start() != SUCCESS) {
          m_error |= E_GENERIC;
          call Leds.led0On();
        }
      } else {
        // in the BROADCAST variant we do not expect ACKs, i.e. we
        // do not enable the Rx logic and cannot receive packets.
        // still we "pretend" to be in state S_ACK_WAIT to keep the  
        // state machines for the two variants as similar as possible
        m_state = S_ACK_WAIT;
      }
    }
    if (m_seqno % (1000/PACKET_TX_PERIOD) == 0 && m_destIdIndex == 0)
      call Leds.led2Toggle();
  }

  void senderRxEnabled(error_t error)
  {
    // Rx logic is ready to receive the ACK: must happen before sendDone
    atomic {
      if (m_state != S_SAMPLE_NOISE || error != SUCCESS) {
        m_error |= E_RX_TOO_SLOW1;
        call Leds.led0On(); // error!
      }
      m_state = S_ACK_WAIT;
    }
  }

  async event void CC2420Tx.sendDone(uint8_t *data, uint16_t tbr, error_t error)
  {
    uint32_t timestamp = call Alarm.getNow();//convertToLocalTime(tbr);

    if (m_state != S_ACK_WAIT || error != SUCCESS) {
      m_error |= E_RX_TOO_SLOW2;
      call Leds.led0On(); // error!
    }
    m_traceSender->seqno = m_seqno;
    m_traceSender->txTime = timestamp;
    m_traceSender->error = m_error; 
    post txDoneTask();
  }

  bool ackReceived(uint8_t *data, uint32_t timestamp, bool overflow)
  {
    bool correctCrc = isCrcCorrect(data);

    // note: with the default configuration the ACK may arrive up to
    // 3 ms after the SFD of the DATA packet (measured on an oscilloscope)
    // -> this is definitely sufficient, since ACKs are sent automatically
    // by the CC2420 12 symbols after reception of the DATA packet
    if (overflow)
      m_error |= E_RXFIFO_OVERFLOW;

    // received a packet: is it really the ACK that we're expecting?
    atomic {
      if (correctCrc 
          && m_state == S_ACK_WAIT  
          && data[0] == 5                   // length of an ACK MPDU
          && data[1] == FRAME_TYPE_ACK      // FCF1
          && data[2] == 0                   // FCF2
          && data[3] == (m_seqno & 0xFF))            // seqno
      {
        // ... yes!
        uint8_t mpduLen = *data; // first byte => PHY length field
      
        m_state = S_OFF_PENDING; 
        m_traceSender->wasAcked = 1;
        m_traceSender->error = m_error; 
        m_traceSender->rssi = data[mpduLen - 1];
        m_traceSender->rssi -= 45; // now in dBm (see CC2420 datasheet)
        m_traceSender->lqi = data[mpduLen] & 0x7F; // clear top bit -> CRC (always set, since we use AUTO_ACK)
        if (call CC2420Tx.immediateSpiRequest() == SUCCESS) {
          if (sampleNoiseNow(NUM_SENDER_NOISE_SAMPLES_POST, 
                (int8_t*) m_traceSender->noisePost) != SUCCESS)
            call Leds.led0On();
          call CC2420Tx.releaseSpi();
        } else 
          call Leds.led0On();
        m_wasNoisePostSampled = TRUE;
        return TRUE; // switch transceiver off
      }
    }
    return FALSE;
  }

  task void txDoneTask()
  {
    if ((LQM_VARIANT == LQM_UNICAST) && (m_traceSender->txTime + ACK_WAIT_TIME > call Alarm.getNow()) )
      // wait (spin) for the ACK / timeout
      post txDoneTask();
    else {
      // past the time where the ACK must have arrived: we're done!
      //P6OUT &= ~0x02;     // low
      m_state = S_OFF_PENDING;
      if (LQM_VARIANT == LQM_UNICAST) {
        if (call RxControl.stop() != SUCCESS) { 
          m_error |= E_GENERIC;
          call Leds.led0On();
        }
      } else  // BROADCAST variant: never enabled RxControl, fake the stopDone()
        signal RxControl.stopDone(SUCCESS);

      // output the statistics now
      printf("%lu %lu %u %u %u %d %u %d %u\n",
          m_traceSender->seqno, m_traceSender->txTime, m_traceSender->destID, 
          m_traceSender->wasAcked, m_traceSender->cca, m_traceSender->rssi, 
          m_traceSender->lqi, m_traceSender->noisePre[0], m_traceSender->error);
      printfflush();  
    }
  }

  async event void RxControl.stopDone(error_t error)
  {
    if (error != SUCCESS) {
      m_error |= E_GENERIC;
      call Leds.led0On();
    }
    call SpiResource.request(); // we need the SPI to switch the radio off
  
  }

  task void txDoneSpinTask()
  {
    offSpiReserved();
  }

  void offSpiReserved()
  {
    if (!m_wasNoisePostSampled) {
      // we have not received the ACK -> sample noise now
      if (sampleNoiseNow(NUM_SENDER_NOISE_SAMPLES_POST, 
            (int8_t*) m_traceSender->noisePost) != SUCCESS)
        call Leds.led1On();
      m_wasNoisePostSampled = TRUE;
    }
    
/*    if (m_traceSender->txTime + ((PACKET_TX_PERIOD-2) * 32.768) > getNow()) {*/
/*      // spin here to compensate for the time needed to sample*/
/*      // noise after an ACK was not received ...*/
/*      post txDoneSpinTask();*/
/*      return;*/
/*    }*/
    
    call CC2420Power.rfOff();
    call TxControl.stop();
    call SpiResource.release();
    post serialSendTask();
  }

  /* ------------------- Common ------------------- */

  bool isCrcCorrect(uint8_t *packet)
  {
    uint8_t length = packet[0]; // remember: this byte is not counted
    
    if (packet[length] & 0x80) // top bit of last byte denotes result of CRC check
      return TRUE;
    else
      return FALSE;
  }
  
  /* @returns FAIL if RSSI is not (yet) valid, SUCCESS otherwise */
  error_t sampleNoiseNow(uint8_t numSamples, int8_t* noise)
  {
    uint8_t n;
    error_t result;

    atomic {
      if (numSamples > 0) {
        n = 0;
        result = call CC2420Tx.rssi(&noise[n++]);
        if (result != SUCCESS)
          return FAIL;
        //P6OUT |= 0x02;      // high 
        while (n < numSamples) {
          BUSY_WAIT_RSSI(); // busy wait 128 us
          //P6OUT &= ~0x02;     // low
          call CC2420Tx.rssi(&noise[n++]);
          //P6OUT |= 0x02;      // high 
        }
        for (n=0; n<numSamples; n++)
          noise[n] -= 45; // now in dBm (see CC2420 datasheet)
      }   
    }
    return SUCCESS;
  }

  async event bool CC2420Rx.receive(uint8_t *data, uint16_t tbr, bool isTbrValid, bool overflow)
  {
    uint32_t timestamp = call Alarm.getNow();//isTbrValid ? convertToLocalTime(tbr) : 0;

    if (LQM_ROLE == LQM_SENDER)
      return ackReceived(data, timestamp, overflow);
    else
      return dataPacketReceived(data, timestamp, overflow);
  }

  task void rxControlStartTask()
  {
    error_t error = call RxControl.start();
    if (error != SUCCESS) {
      m_error |= E_GENERIC;
      call Leds.led0On();
    }
  }

  async event void RxControl.startDone(error_t error)
  {
    if (LQM_ROLE == LQM_SENDER)
      senderRxEnabled(error);
    else
      receiverStarted(error);
  }

  task void serialSendTask()
  {
/*    message_t *msg = m_serialMsgPtr;*/
/*    uint8_t serialLen = (LQM_ROLE == LQM_RECEIVER ? sizeof(lqm_trace_receiver_t) : sizeof(lqm_trace_sender_t));*/

    // send the trace over the serial line
/*    m_serialMsgPtr = call SerialSend.send(m_serialMsgPtr, */
/*      call SerialPacket.getPayload(m_serialMsgPtr, serialLen), serialLen,*/
/*      LQM_ROLE == LQM_RECEIVER ? AM_LQM_TRACE_RECEIVER : AM_LQM_TRACE_SENDER);*/
/*    if (msg == m_serialMsgPtr) {*/
/*      call Leds.led1On();*/
/*      m_error |= E_SERIAL_OVERFLOW;*/
/*    }*/
/*    if ( LQM_ROLE == LQM_RECEIVER ) {*/
/*      printf("%lu %lu %lu %d %u %d %u\n",*/
/*          m_traceReceiver->serialSeqno, m_traceReceiver->seqno, m_traceReceiver->rxTime, */
/*          m_traceReceiver->rssi, m_traceReceiver->lqi, m_traceReceiver->noisePost[0], m_traceReceiver->error);*/
/*    } else {*/
/*      printf("%lu %lu %u %u %u %d %u %d %u\n",*/
/*          m_traceSender->seqno, m_traceSender->txTime, m_traceSender->destID, */
/*          m_traceSender->wasAcked, m_traceSender->cca, m_traceSender->rssi, */
/*          m_traceSender->lqi, m_traceSender->noisePost[0], m_traceSender->error);*/
/*    }*/
/*    printfflush();*/

    if (LQM_VARIANT == LQM_UNICAST) {
      m_destIdIndex++; // increment the index of the receiver address list
      if (m_destIdIndex == (sizeof(m_destId) / sizeof(TOS_NODE_ID))) {
        m_seqno += 1;
        m_destIdIndex = 0;
      }
    } else 
      m_seqno += 1;

    if (LQM_ROLE == LQM_RECEIVER) {
      clearTrace();
      enableContinuousNoiseMonitoring();
      m_state = S_PACKET_WAIT;
    } else {
      if (NUM_PACKETS == 0 || m_seqno != NUM_PACKETS)
        startSender();
    }
  }

  void enableContinuousNoiseMonitoring()
  {
    atomic TACTL |= (TAIE | MC0); 
  } 

  void disableContinuousNoiseMonitoring()
  {
    atomic TACTL &= ~TAIE; 
  } 

  event void SpiResource.granted() 
  {
    switch (m_state)
    {
      case S_BOOT: bootSpiReserved(); break;
      case S_OFF_PENDING: offSpiReserved(); break;
      default: // huh ?
           call Leds.led1On(); break;
    }
  }

  void clearTrace()
  {
    if (LQM_ROLE == LQM_SENDER) {
      m_traceSender = (lqm_trace_sender_t*)  m_serialMsgPtr;//call SerialPacket.getPayload(m_serialMsgPtr, sizeof(lqm_trace_sender_t));
      if (m_traceSender == NULL) {
        m_error |= E_GENERIC;
        call Leds.led0On(); // error!
        return;
      }
      memset(m_traceSender, 0, sizeof(lqm_trace_sender_t)); // clear
    } else {
      m_traceReceiver = (lqm_trace_receiver_t*)  m_serialMsgPtr;// call SerialPacket.getPayload(m_serialMsgPtr, sizeof(lqm_trace_receiver_t));
      if (m_traceReceiver == NULL) {
        m_error |= E_GENERIC;
        call Leds.led0On(); // error!
        return;
      }
      memset(m_traceReceiver, 0, sizeof(lqm_trace_receiver_t)); // clear
    }
  }

  async event bool CC2420Rx.continueRead(uint8_t length)
  {
    uint8_t expectedLength = 0;

    if (LQM_VARIANT == LQM_BROADCAST) {
      if (LQM_ROLE == LQM_SENDER)
        return FALSE; // we don't expect ACKs
      else 
        expectedLength = sizeof(header_154_t) - 1 + sizeof(payload_154_t) + 2;
    } else if (LQM_VARIANT == LQM_UNICAST) {
      if (LQM_ROLE == LQM_SENDER)
        expectedLength = ACK_LENGTH;
      else 
        expectedLength = sizeof(header_154_t) - 1 + sizeof(payload_154_t) + 2;
    }
    return length == expectedLength;
  }



  event void CC2420Tx.cancelDone(error_t error){}
  async event void CC2420Tx.transmissionStarted ( uint8_t *data ){}
  async event void CC2420Tx.transmittedSFD ( uint32_t time, uint8_t *data ){}

  /* ------------------- Clock / Timer ------------------- */

  event void Msp430ClockInit.setupDcoCalibrate()
  {
    call Msp430ClockInit.defaultSetupDcoCalibrate();
#if defined(MSP430_MCLK_8MHZ) 
    BCSCTL2 = 0x01; // external resistor
#endif
  }

  event void Msp430ClockInit.initClocks()
  {
    call Msp430ClockInit.defaultInitClocks();
    return;
    // BCSCTL1
    // .XT2OFF = 1; disable the external oscillator for SCLK and MCLK
    // .XTS = 0; set low frequency mode for LXFT1
    // .DIVA = 0; set the divisor on ACLK to 1
    // .RSEL, do not modify
    BCSCTL1 = XT2OFF | (BCSCTL1 & (RSEL2|RSEL1|RSEL0));

    // BCSCTL2
    // .SELM = 0; select DCOCLK as source for MCLK
    // .DIVM = 0; set the divisor of MCLK to 1
    // .SELS = 0; select DCOCLK as source for SMCLK
    // .DIVS = 0; set the divisor of SMCLK to 2 
    // .DCOR = 0; select internal resistor for DCO

#ifdef MSP430_MCLK_8MHZ
    BCSCTL2 = 0x01; // SMCLK = DCO = 8MHz, external resistor
#else
    BCSCTL2 = 0x00; // SMCLK = DCO
#endif

    // IE1.OFIE = 0; no interrupt for oscillator fault
    CLR_FLAG( IE1, OFIE );    
  }

  event void Msp430ClockInit.initTimerA(){    
    TAR = 0;
    // TACTL
    // .TACLGRP = 0; each TACL group latched independently
    // .CNTL = 0; 16-bit counter
    // .TASSEL = 1; source ACLK 
    // .ID = 0; input divisor of 1
    // .MC = 1; up mode 
    // .TACLR = 0; reset timer A
    // .TAIE = 1; enable timer A interrupts
    TACTL = TASSEL0 | MC0 | TAIE;
    TACCR0 = NOISE_PRE_UPDATE_PERIOD;
  }

  event void Msp430ClockInit.initTimerB(){call Msp430ClockInit.defaultInitTimerB();}

#if 0
  // writes current TBR value -> tbr, returns TRUE iff
  // at the time TBR was read the IFG was set (overlap)
  // assumption: this functions is called in atomic!
  bool readTBR(uint16_t *tbr)
  {
    uint16_t spins = 0, tbr1, tbr2, tbifg;
    do {
      // CSS 10 Feb 2006: Brano Kusy notes MSP430 User's Guide, Section 12.2.1,
      // Note says reading a counter may return garbage if its clock source is
      // async.  The noted work around is to take a majority vote.
      tbr1 = TBR;
      tbifg = (TBCTL & TBIFG);
      tbr2 = TBR;
      spins++;
    } while (tbr1 != tbr2);
    if (spins > 5) { // something is really wrong !!!
      m_error |= E_GENERIC;
      call Leds.led0On();
    }
    *tbr = tbr1;
    return (tbifg != 0);
  }

  uint32_t getNow()
  {
    uint16_t lower, upper;
    atomic {
      upper = m_upperTime;
      if (readTBR(&lower))
        upper++;
    }
    return (((uint32_t) upper) << 16) + lower;
  }

  // assumption: "convertToLocalTime()" is called no more
  // than 2s after the tbr value was read!
  uint32_t convertToLocalTime(uint16_t tbr)
  {
    atomic {
      uint32_t now = getNow();
      uint32_t before = (((uint32_t) m_upperTime) << 16) + tbr;

      if (before > now) // TODO: 32-bit overlap
        before = (((uint32_t) m_upperTime - 1) << 16) + tbr;
      return before;
    }
  }

  async event void TimerB.overflow()
  {
    atomic m_upperTime += 1;
  }
#endif
}

