/*
 * Copyright (c) 2005-2006 Arch Rock Corporation
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * - Redistributions of source code must retain the above copyright
 *   notice, this list of conditions and the following disclaimer.
 * - Redistributions in binary form must reproduce the above copyright
 *   notice, this list of conditions and the following disclaimer in the
 *   documentation and/or other materials provided with the
 *   distribution.
 * - Neither the name of the Arch Rock Corporation nor the names of
 *   its contributors may be used to endorse or promote products derived
 *   from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE
 * ARCHED ROCK OR ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE
 */

/**
 * @author Jonathan Hui <jhui@archrock.com>
 * @author David Moss
 * @author Jung Il Choi
 * @author Jan Hauer <hauer@tkn.tu-berlin.de>
 * @version $Revision: 1.2 $ $Date: 2007/07/06 18:09:44 $
 */
/*#include "IeeeEui64.h"*/
module CC2420ReceiveP {

  provides interface Init;
  provides interface AsyncSplitControl; 
  provides interface CC2420Receive;
  provides interface CC2420Rx;
  provides interface ReceiveIndicator as PacketIndicator;

  uses interface GeneralIO as SFD;
  uses interface GeneralIO as CSN;
  uses interface GeneralIO as FIFO;
  uses interface GeneralIO as FIFOP;
  uses interface GpioInterrupt as InterruptFIFOP;

  uses interface Resource as SpiResource;
  uses interface CC2420Fifo as RXFIFO;
  uses interface CC2420Strobe as SACK;
  uses interface CC2420Strobe as SFLUSHRX;
  uses interface CC2420Strobe as SRXON;
  uses interface CC2420Strobe as SRFOFF;
  uses interface CC2420Register as MDMCTRL1;
/*  uses interface CC2420Packet;*/
/*  uses interface CC2420PacketBody;*/
  uses interface CC2420Config;
/*  uses interface CaptureTime;*/
  
  uses interface Leds;
}

implementation {

  typedef enum {
    S_STOPPED,
    S_STARTING,
    S_STARTING_FLUSHRX,
    S_STARTED,
    S_RX_LENGTH,
    S_RX_FCF,
    S_RX_HEADER,
    S_RX_PAYLOAD,
  } cc2420_receive_state_t;

  enum {
    RXFIFO_SIZE = 128,
    TIMESTAMP_QUEUE_SIZE = 8,
    //SACK_HEADER_LENGTH = 7,
    SACK_HEADER_LENGTH = 3,
  };

  uint16_t m_timestamp_queue[ TIMESTAMP_QUEUE_SIZE ];
  
  uint8_t m_timestamp_head;
  
  bool m_timestampLoaded;

  typedef enum {
    TS_IDLE,
    TS_LOADED,
    TS_INVALID,
  } timestamp_state_t;

  uint16_t m_timestamp;
  
  /** Number of packets we missed because we were doing something else */
  uint8_t m_missed_packets;
  
  /** TRUE if we are receiving a valid packet into the stack */
  norace bool receivingPacket;
  
  norace uint8_t m_bytes_left;

  // norace message_t* m_p_rx_buf;

  // message_t m_rx_buf;
  
  cc2420_receive_state_t m_state;
  
  // new packet format:
  uint8_t m_rxBuf[300]; // we have enough RAM...

  message_t m_frame;
  norace message_t *m_rxFramePtr;
  norace uint8_t m_mhrLen;
  uint8_t m_dummy;
  norace bool m_stop;
  norace bool m_overflow;
  norace bool m_timestampInvalid;
  
  /***************** Prototypes ****************/
  void reset_state();
  void beginReceive();
  void receive();
  void waitForNextPacket();
  void flush();
  void switchToUnbufferedMode();
  void switchToBufferedMode();
  void startingSpiReserved();
  void continueStart();
  void continueStop();
  task void stopContinueTask();
  
/*  task void receiveDone_task();*/
  
  /***************** Init Commands ****************/
  command error_t Init.init() {
    m_rxFramePtr = &m_frame;
    atomic m_state = S_STOPPED;
    return SUCCESS;
  }

  /***************** AsyncSplitControl ****************/
  // ASSUMPTION: when AsyncSplitControl.start is called, 
  // a FIFOP must not be pending...
  async command error_t AsyncSplitControl.start()
  {
    atomic {
      if (m_state != S_STOPPED){
        call Leds.led0On();
        return FAIL;
      } else {
        m_state = S_STARTING;
        if (call SpiResource.isOwner()){ 
          call Leds.led0On(); // internal error (debug) !
          startingSpiReserved();
        }
        if (call SpiResource.immediateRequest() == SUCCESS)
          startingSpiReserved();
        else
          call SpiResource.request();        
      }
    }
    return SUCCESS;
  }

  void startingSpiReserved()
  {
    atomic {
      if (!call FIFOP.get() || call FIFO.get()){ // FIFOP is inverted
        // there is something in RXFIFO: flush it out 
        m_overflow = 1; // this should not happen at all ...
        m_state = S_STARTING_FLUSHRX;
        call CSN.clr();
        call RXFIFO.beginRead( &m_dummy, 1 ); // will continue in continueFlushStart()
        return;
      }
    }
    continueStart();
  }

  void continueFlushStart()
  {
    atomic {
      call CSN.set();
      call CSN.clr();
      call SFLUSHRX.strobe();
      call SFLUSHRX.strobe();
      call CSN.set();
    }
    continueStart();
  }
  
  void continueStart()
  {
    // RXFIFO is empty
    if (!call FIFOP.get() || call FIFO.get()){
      call Leds.led0On();
    }
    atomic {
      reset_state();
      m_state = S_STARTED;
      m_overflow = 0;
    }
    call SpiResource.release();
    call InterruptFIFOP.enableFallingEdge();
    signal AsyncSplitControl.startDone(SUCCESS);
  }

  // ASSUMPTION: when AsyncSplitControl.stop is called, 
  // the radio MUST NOT be off !!
  async command error_t AsyncSplitControl.stop()
  {
    atomic {
      if (m_state == S_STOPPED)
        return EALREADY;
      else {
        m_stop = TRUE;
        call InterruptFIFOP.disable();
        if (!receivingPacket)
          continueStop();
        // else stopContinueTask will be posted after 
        // current Rx operation is finished, because m_stop is set
      }
    }
    return SUCCESS;
  }

  void continueStop()
  {
    atomic {
      m_stop = FALSE;
      m_state = S_STOPPED;
    }
    post stopContinueTask();
  }

  task void stopContinueTask()
  {
    if (receivingPacket){
      call Leds.led0On();
    }
    call SpiResource.release(); // may fail
    atomic m_state = S_STOPPED;
    signal AsyncSplitControl.stopDone(SUCCESS);
  }


  /***************** CC2420Receive Commands ****************/
  
  async command void CC2420Receive.efd( uint16_t sfdTime ) { }

  /**
   * Start frame delimiter signifies the beginning/end of a packet
   * See the CC2420 datasheet for details.
   */
  async command void CC2420Receive.sfd( uint16_t time ) 
  {
    atomic {
      m_timestamp = time;
      if ( m_timestampLoaded )
        m_timestampInvalid = TRUE;
      m_timestampLoaded = TRUE;
    }
  }

  async command void CC2420Receive.sfd_dropped() {
    atomic {
      if ( m_timestampLoaded ) {
        m_timestampLoaded = FALSE;
      } else 
        m_timestampInvalid = TRUE;
    }
  }

  /***************** PacketIndicator Commands ****************/
  command bool PacketIndicator.isReceiving() {
    bool receiving;
    atomic {
      receiving = receivingPacket;
    }
    return receiving;
  }

  async command bool CC2420Rx.isRxFifoEmpty() {
    return (call FIFO.get() == 0);
  }  
  
/*  async command bool CC2420Rx.isReceiving() { return (receivingPacket || !call FIFOP.get()); }*/

  /***************** InterruptFIFOP Events ****************/
  async event void InterruptFIFOP.fired() {
    atomic {
      if ( m_state == S_STARTED ) {
        beginReceive();

      } else {
        m_missed_packets++;
      }
    }
  }
  
  
  /***************** SpiResource Events ****************/
  event void SpiResource.granted() {
    atomic {
      switch (m_state)
      {
        case S_STARTING: startingSpiReserved(); break;
        case S_STARTING_FLUSHRX: // fall through
        case S_STOPPED: call Leds.led0On(); 
                        call SpiResource.release(); break;
        default: receive();
      }
    }
  }
  
  /***************** RXFIFO Events ****************/
  /**
   * We received some bytes from the SPI bus.  Process them in the context
   * of the state we're in.  Remember the length byte is not part of the length
   */
  async event void RXFIFO.readDone( uint8_t* rx_buf, uint8_t rx_len, error_t error ) 
  {
    // Jan Hauer: be conservative about errors -> if there is the 
    // slightest chance that something is fishy, we
    // set the m_overflow flag. This way the application knows that as long
    // as an overflow is not signalled we're on the safe side ...
    // Remember, a FIFOP interrupt means:
    //  - (at least one) full packet was received 
    //  - the dest. addresses (if present) match our address
    //  - if the ACK request flag was set, the CC2420 is sending an ACK automatically  

    uint8_t frameLength;
    atomic {
      frameLength = m_rxBuf[0];

      switch( m_state ) {

        case S_RX_LENGTH:
          // we have read the PHY length field (one byte)
          m_state = S_RX_FCF;
          if ( frameLength > RXFIFO_SIZE ) {
            // Length of this packet is bigger than the maximum (128 byte), 
            // -> this packet must be corrupt, the complete content of the
            // RXFIFO is useless! -> flush it
            flush();
          } else {
            if ( !call FIFO.get() && !call FIFOP.get() ) {
              // this is serious: RXFIFO overflow !!!
              m_overflow = 1;
              flush();
            }
            if (signal CC2420Rx.continueRead(frameLength)) {
              m_state = S_RX_PAYLOAD;
              call RXFIFO.continueRead(m_rxBuf + 1, frameLength);
            } else {
              // the client doesn't want this packet, we will simply
              // flush the RXFIFO, but the issue is:
              // we may already be receiving the next packet, so if we
              // flush the RXFIFO we will lose this next packet as well
              // -> be conservative, mark this as a potential error
              if (call SFD.get()) // are we receiving the next packet?
                // TODO: we might want to "manually" spool out the 
                // bytes of the first packet intead?
                m_overflow = 1;
              flush(); // -> flush RXFIFO.
            }
          }
          break;

        case S_RX_PAYLOAD:
          call CSN.set();

          if (m_timestampLoaded)
            m_timestampLoaded = FALSE;
          else 
            m_timestampInvalid = TRUE;

          call SpiResource.release();
          if (signal CC2420Rx.receive(m_rxBuf, m_timestamp, !m_timestampInvalid, m_overflow)) {
            call CSN.clr();
            call SRFOFF.strobe();
            call CSN.set();      
          }
          if (call CC2420Rx.isRxFifoEmpty()) {
            m_timestampLoaded = FALSE;
            m_timestampInvalid = FALSE;
          }

          waitForNextPacket();
          break;

        case S_STARTING_FLUSHRX: continueFlushStart(); break;

        default:
                                 atomic receivingPacket = FALSE;
                                 call CSN.set();
                                 call SpiResource.release();
                                 if (m_stop){
                                   continueStop();
                                   return;
                                 }
                                 break;

      }
      }

    }

    async event void RXFIFO.writeDone( uint8_t* tx_buf, uint8_t tx_len, error_t error ) {
    }  

    /***************** Tasks *****************/
    /**
   * Fill in metadata details, pass the packet up the stack, and
   * get the next packet.
   */
/*  task void receiveDone_task() {*/
  
  /****************** CC2420Config Events ****************/
  event void CC2420Config.syncDone( error_t error ) {
  }
  
  /****************** Functions ****************/
  /**
   * Attempt to acquire the SPI bus to receive a packet.
   */
  void beginReceive() { 
    atomic {
      if ( m_state == S_STOPPED){
        call Leds.led0On();
        return;
      }
      m_state = S_RX_LENGTH;
      receivingPacket = TRUE;
    
      if(call SpiResource.isOwner()) {
        receive();

      } else if (call SpiResource.immediateRequest() == SUCCESS) {
        receive();

      } else {
        call SpiResource.request();
      }
    }
  }
  
  /**
   * Flush out the Rx FIFO
   */
  void flush() {
    reset_state();
    call CSN.set();
    call CSN.clr();
    call SFLUSHRX.strobe();
    call SFLUSHRX.strobe();
    call CSN.set();
    call SpiResource.release();
    waitForNextPacket();
  }
  
  /**
   * The first byte of each packet is the length byte.  Read in that single
   * byte, and then read in the rest of the packet.  The CC2420 could contain
   * multiple packets that have been buffered up, so if something goes wrong, 
   * we necessarily want to flush out the FIFO unless we have to.
   */
  void receive() {
    call CSN.clr();
    //call RXFIFO.beginRead( (uint8_t*)(call CC2420PacketBody.getHeader( m_p_rx_buf )), 1 );
    call RXFIFO.beginRead( m_rxBuf, 1 );
  }


  /**
   * Determine if there's a packet ready to go, or if we should do nothing
   * until the next packet arrives
   */
  void waitForNextPacket() {
    atomic {
      receivingPacket = FALSE;
      if ( m_state == S_STOPPED) {
        call SpiResource.release();
        return;
      }
      if (m_stop){
        continueStop();
        return;
      }
      
      if ( ( m_missed_packets && call FIFO.get() ) || !call FIFOP.get() ) {
        // A new packet is buffered up and ready to go
        if ( m_missed_packets ) {
          m_missed_packets--;
        }
        
        beginReceive();
        
      } else {
        // Wait for the next packet to arrive
        m_state = S_STARTED;
        m_missed_packets = 0;
        call SpiResource.release();
      }
    }
  }
  
  /**
   * Reset this component
   */
  void reset_state() {
    m_bytes_left = RXFIFO_SIZE;
    atomic receivingPacket = FALSE;
    m_timestamp_head = 0;
    m_timestampLoaded = FALSE;
    m_missed_packets = 0;
  }

}
