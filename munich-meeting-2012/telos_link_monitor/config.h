

#ifndef __LQM_CONFIG_H
#define __LQM_CONFIG_H

enum {
  /* INIT_DELAY defines (roughly) the number of seconds the nodes wait
   * after booting, before they start exchanging packets. In order 
   * not miss the first packets the receiver will start listening
   * already at (INIT_DELAY / 2) seconds after it has booted.
   *
   * If INIT_DELAY = 0 then the measurement is started by pressing the
   * user buttons (-> make sure you first press the button on the receiver)
   */
  INIT_DELAY = 1, // in seconds (roughly)

  /* The time interval between sending two consecutive packets in 
   * milliseconds, i.e. transmission frequency = 1/PACKET_TX_PERIOD */
  PACKET_TX_PERIOD = 50,

  /* IEEE 802.15.4 channel (11..26) */
  RADIO_CHANNEL = 11,

  /* Transmission power (PA_LEVEL register, see CC2420 Datasheet):
   *
   *  31 -> 0 dBm
   *  27 -> -1 dBm
   *  23 -> -3 dBm
   *  19 -> -5 dBm
   *  15 -> -7 dBm
   *  11 -> -10 dBm
   *  7 -> -15 dBm
   *  3 -> -25 dBm
   **/
  PA_LEVEL = 31,     // 0 dBm

  /* By default DATA packets are as small as possible (13 byte MPDU),
   * but you  can "artificially" increase the payload (-> just make sure 
   * that the MPDU is no more than 127 byte in total)
   **/
  ADDITIONAL_PAYLOAD = 0, // in byte

  /* Total number of DATA packets transmitted by the sender to *every*
   * receiver (if you choose the broadcast option then this is the total
   * number of pacjkets transmitted). 
   * If NUM_PACKETS = 0 then the sender will send infinitely many.
   */
  NUM_PACKETS = 0,
};

#endif
