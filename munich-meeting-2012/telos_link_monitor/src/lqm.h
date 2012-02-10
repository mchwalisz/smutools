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
 * $Revision: 1.6 $
 * $Date: 2009/03/22 12:07:16 $
 * @author: Jan Hauer <hauer@tkn.tu-berlin.de>
 * ========================================================================
 */

/* This header file includes constants/typedefs that are assumed to
 * be common to all LQM setups. There should be no reason to change
 * anything here, but if you do, keep in mind that the changes will
 * affect all setups. The parameters that can be configured for a
 * particular setup are located in the setup-specific header file.
 * For example, the parameters for the unicast-setup can be changed
 * in: ../unicast/lqm_unicast.h */

#ifndef __LQM_H
#define __LQM_H

#include "../config.h"

#if defined(_LQM_UNICAST) || defined (_LQM_BROADCAST)

enum {

  /* Number of noise samples collected on the sender node immediately
   * before sending the DATA packet. Keep in mind that every sample 
   * results in an extra 128 us delay. 
   */
  NUM_SENDER_NOISE_SAMPLES_PRE = 3,

  /* Number of noise samples collected on the sender node immediately
   * after receiving the ACK packet or, if an ACK was not received,
   * after the timeout (defined by ACK_WAIT_TIME in lqm.h)
   */
  NUM_SENDER_NOISE_SAMPLES_POST = 2,

  /* Number of noise samples collected on the receiver node immediately
   * after sending the ACK packet.
   */
  NUM_RECEIVER_NOISE_SAMPLES_POST = 3,
};

/* Transmitted over serial by every node once at the start of the measurement.
 * This is basically summarizing the currently selected configuration from the 
 * setup-specific header file (e.g. lqm_unicast.h for the unicast setup). */
typedef nx_struct lqm_trace_info {
  
  /* the 16-bit short address of this node */
  nxle_uint16_t nodeID;         

  /* role of the node: 0 = receiver, 1 = sender */
  nxle_uint8_t role;         

  /* the PA_LEVEL  */
  nxle_uint8_t paLevel;      

  /* the RADIO_CHANNEL */
  nxle_uint8_t channel;      

  /* size of MAC header + MAC payload + MAC footer (CRC) */
  nxle_uint8_t mpduSize;     

  /* the NUM_PACKETS */
  nxle_uint32_t numPackets;  

} lqm_trace_info_t;


/* Transmitted over serial for every sent DATA packet (by the sender node) */
typedef nx_struct lqm_trace_sender {

  /* Sequence number of the 802.15.4 DATA packet, starting 
   * at 0 and incremented for every broadcast DATA packet 
   * or after sending it to all receivers (unicast).
   * -> holes in the sequence number would indicate that the 
   * sender is dropping packets on the serial line! */
  nxle_uint32_t seqno;    

  /* Signal strength sampled immediately before sending the DATA 
   * packet, one sample is taken every 128 us (which is the time 
   * RSSI is averaged over) */
  nxle_int8_t noisePre[NUM_SENDER_NOISE_SAMPLES_PRE];  

  /* 
   * Packets are sent without CCA, still we inspect the CCA
   * just before sending the packet. We use the CCA-Mode = 2, 
   * which means: 
   *
   *   cca=1 when not receiving valid IEEE 802.15.4 data, 
   *   cca=0 otherwise 
   * 
   * IEEE 802.15.4-2006 Std:
   * "CCA Mode 2: Carrier sense only. CCA shall report a 
   *  busy medium only upon the detection of a signal compliant 
   *  with this standard with the same modulation and spreading 
   *  characteristics of the PHY that is currently in use by 
   *  the device. This signal may be above or below the ED 
   *  threshold."
   *  
   * -> In this CCA mode the signal strength is irrelevant. 
   * Note that we already have the signal strength info as 
   * the "noisePre" parameter.
   **/
  nxle_uint8_t cca;     

  /* Transmission time of the DATA packet 
   * expressed in local time (32768 Hz clock) */
  nxle_uint32_t txTime;   

  /* the 16-bit short address of the receiver that the DATA packet 
   * was sent to and from which we expected to get the ACK back. */
  nxle_uint16_t destID;     

  /* 0 = didn't receive an ACK, 1 = received an ACK */
  nxle_uint8_t wasAcked;     

  /* RSSI of the ACK packet (invalid if wasAcked = 0) */
  nxle_int8_t rssi;               

  /* LQI of the ACK packet (invalid if wasAcked = 0) */
  nxle_uint8_t lqi;              

  /* Signal strength sampled immediately after receiving the ACK
   * or timeout, one sample is taken every 128 us. */
  nxle_int8_t noisePost[NUM_SENDER_NOISE_SAMPLES_POST];  

  /* Error bit mask -> should always be 0 (see E_xxx codes below) */
  nxle_uint8_t error;                    

} lqm_trace_sender_t;


/* Transmitted over serial for every received DATA packet (by a receiver node) */
typedef nx_struct lqm_trace_receiver {

  /* the 16-bit short address of this (receiver) node */
  nxle_uint16_t nodeID;     

  /* Sequence number of the serial packet, starting at 0 
   * and incremented for every packet sent over the serial line 
   * -> holes in the sequence number indicate that the receiver
   * is dropping packets on the serial line!
   **/
  nxle_uint32_t serialSeqno;     

  /* Point in time when the "noisePre" sample was taken
   * (0 = invalid) expressed in local time (32768 Hz clock).
   * This should be not much more than 500 microseconds  
   * before the first symbol of the DATA packet arrived. 
   **/
  nxle_uint32_t noisePreTime;     

  /* Signal strength sampled before receiving the DATA packet,
   * at time "noisePreTime", invalid if noisePreTime = 0 */
  nxle_int8_t noisePre;  

  /* Reception time of the DATA packet (0 = invalid) 
   * expressed in local time (32768 Hz clock). The time
   * represents the reception of the SFD byte, i.e. the
   * first byte of the preamble was received 10 symbols 
   * earlier.
   **/
  nxle_uint32_t rxTime;    

  /* sequence number copied from the DATA packet payload */
  nxle_uint32_t seqno;                   

  /* RSSI of the DATA packet */
  nxle_int8_t rssi;                      

  /* LQI of the DATA packet */
  nxle_uint8_t lqi;                      

  /* Signal strength sampled immediately after transmitting 
   * the ACK, one sample is taken every 128 us. */
  nxle_int8_t noisePost[NUM_RECEIVER_NOISE_SAMPLES_POST];  

  /* Error bit mask -> should always be 0 (see E_xxx codes below) */
  nxle_uint8_t error;       

} lqm_trace_receiver_t;

typedef nx_struct {
  nxle_uint32_t seqno;
  nxle_uint8_t dummy[ADDITIONAL_PAYLOAD];
} payload_154_t;
#endif

typedef nx_struct  {
  nxle_uint8_t length;
  nxle_uint16_t fcf;
  nxle_uint8_t dsn;
  nxle_uint16_t destpan;
  nxle_uint16_t dest;
} header_154_t;


enum {
  LQM_UNICAST,
  LQM_BROADCAST,

  LQM_RECEIVER = 0,
  LQM_SENDER = 1,

#if defined(_LQM_UNICAST) 
  PAN_ID = 0x4827,       // random
#elif defined(_LQM_BROADCAST)
  PAN_ID = 0x4927,       // different (so we cannot mix setups)
#elif defined(_LQR_EVAL)
  PAN_ID = 0x4037,       // different (so we cannot mix setups)
#endif

  SERIAL_QUEUE_SIZE  = 10, // queue size for the serial stack

  /* error codes (bitmask) */
  E_RXFIFO_OVERFLOW = 0x01,
  E_SERIAL_OVERFLOW = 0x02, /* you can solve this error by increasing ACK_WAIT_TIME */
  E_RX_TOO_SLOW1 = 0x04,
  E_RX_TOO_SLOW2 = 0x08,
  E_GENERIC = 0x10,

  // active message IDs (serial)
  AM_LQM_TRACE_SENDER = 100,
  AM_LQM_TRACE_RECEIVER = 101,
  AM_LQM_TRACE_INFO = 102,

#if defined(_LQM_UNICAST) 
  // The time to wait for the ACK after the DATA packet 
  // was transmitted -> airtime of DATA-MPDU + IFS + ACK (in 32768 Hz) + guardtime
  // Note: this should be conservative, because if it's too short the 
  // sender will shut the radio off before the ACK was received!
  ACK_WAIT_TIME = ((sizeof(header_154_t) + sizeof(payload_154_t) + 2) + 6 + 11) * 3 + 15, 
#elif defined(_LQM_BROADCAST)
  // There are no ACKs in the broadcast variant. But we artifically 
  // introduce a delay after packet transmission, because otherwise
  // the serial stack will overflow.
  ACK_WAIT_TIME = 108, 
#endif

  FRAME_TYPE_DATA         = 0x01,
  FRAME_TYPE_ACK          = 0x02,
  DEST_MODE_SHORT         = 0x08,
  ACK_REQUEST             = 0x20,
  BROADCAST_ADDRESS       = 0xFFFF,
  ACK_LENGTH              = 5,

  NOISE_PRE_LIST_ENTRIES = 5,

  // period with which we sample noise concurrently (in the
  // background) on a receiver in ticks of 32768Hz clock
  NOISE_PRE_UPDATE_PERIOD = 9, 
}; 

typedef struct {
  uint32_t timestamp;
  int8_t noise;
} noise_pre_entry_t;

/* The default TinyOS configuration calibrates the CPU clock (MCLK) to
 * 4 MHz, but on most telosb variants (more precisely: the ones that have the
 * external ROSC resistor, like Tmote Sky) the MSP430 can be clocked to 8 MHz.
 * If the following macro is defined the CPU clock is calibrated to 8 MHz,
 * if it's not defined the CPU clock is calibrated to 4 MHz. Note: at 4 MHz
 * the serial stack might not be fast enough to output packets fast enough, 
 * you can solve this by increasing the ACK_WAIT_TIME (in lqm.h), but this
 * also reduces the rate at which 802.15.4 DATA packets are transmitted...
 */
//#define MSP430_MCLK_8MHZ

#ifdef TOSH_DATA_LENGTH
  #undef TOSH_DATA_LENGTH
#endif
#define TOSH_DATA_LENGTH 128

#define TEN_NOPS() nop(); nop(); nop(); nop(); nop(); nop(); nop(); nop(); nop(); nop()
#define FIFTY_NOPS() TEN_NOPS(); TEN_NOPS(); TEN_NOPS(); TEN_NOPS(); TEN_NOPS() 
#define HUNDRED_NOPS() FIFTY_NOPS(); FIFTY_NOPS() 

#ifdef MSP430_MCLK_8MHZ
  // determined by measurements on an oscilloscope
  #define BUSY_WAIT_RSSI() HUNDRED_NOPS(); HUNDRED_NOPS(); HUNDRED_NOPS(); HUNDRED_NOPS(); FIFTY_NOPS(); TEN_NOPS() 
#else
  // note: it is not just the number of nops that defines the time to wait
  // (the time of the Spi strobe has to be taken into consideration as well)
  // at 4 MHz we don't busy wait at all because reading the RSSI already 
  // takes slightly longer than 128 us.
  #define BUSY_WAIT_RSSI() 
#endif

#endif
