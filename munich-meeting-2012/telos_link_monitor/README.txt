Author/Contact: Jan Hauer <hauer@tkn.tu-berlin.de>

Description:

This directory contains TinyOS measurement code to perform link measurements
between one sender node and N receiver nodes. There are two variants:

(a) The sender continuously broadcasts packets and all receivers listen for the
packets. Receivers do not send acknowledgements.

(b) The sender continuously sends unicast packets to all N receivers round
robin (one after another) and whenever a receiver has received a packet
destined to itself it sends an acknowledgement packet.

Both variants have in common that packets are sent on one pre-defined IEEE
802.15.4 channel. Also, in both variants several other things that can be
configured at compile time (the addresses, CC2420 output power, transmission
frequency etc.); they are all listed and explained in the "config.h" file.
Whenever a sender or receiver has received a packet it ouputs the details
(statistics) over the USB interface via the TinyOS printf library; the
PC/laptop should be ready capture these statistics (see below). Once started,
the sender node will toggle its blue LED once per second. A receiver will
toggle its blue LED if it receives at least one packet per second.


Installation:

[note: below you may need to replace the "ttyUSB0" with the correct file that
 your telosb has been assigned by your OS]

  1. Install the sender:
      (a) broadcast variant:
      $ make telosb install sender broadcast bsl,/dev/ttyUSB0

      (b) unicast variant:
      $ make telosb install sender unicast.10,11,12 bsl,/dev/ttyUSB0
      -> Sends packets round-robin to 3 receiver nodes with IDs 10,11 and 12

  2. Install one or more receivers:
      (a) broadcast variant:
      $ make telosb install receiver broadcast bsl,/dev/ttyUSB0

      (b) unicast variant:
      $ make telosb install receiver unicast.10 bsl,/dev/ttyUSB0
      -> Assigns node ID 10 to this receiver

ATTENTION: if you chose the unicast variant you must make sure that the IDs of
the receivers match the list of IDs passed to the make system when compiling
the sender!


Traces:

  To get the traces of a node (sender/receiver) you need to start the
  TinyOS java PrintfClient:

  $ java net.tinyos.tools.PrintfClient -comm serial@/dev/ttyUSB0:115200

  Trace format: the sender will print one line per transmitted packets, each
  line looks similar to this one: 

            "406 731909 65535 0 1 0 0 -89 0"

  the fields have the following meaning:

  406   : is the sequence number of the transmitted packet
  731909: is the local timestamp of the transmitted packet
  65535 : is the destination address (65535 == BROADCAST)
  0     : is set to 0 if no ACK was received or 1 if an ACK was received
  1     : is set to 0 if the channel was clear just before transmitting 
          the packet (or 0 if it was not clear)
  0     : is the RSSI (in dBm)of the received ACK (if any)
  0     : is the LQI of the received ACK (if any)
  -89   : is the ambient RF noise level (in dBm)
  0     : is an error code which should always be 0


  A receiver will print one line per received packets, each line looks 
  similar to this one: 

            "473 720 840802 -27 106 -94 0

  the fields have the following meaning:

  473   : is a sequence number incremented for every message sent over USB 
          (this should start at 0 and there should be no "gaps", otherwise
           we are losing packets over the USB line!)
  720   : is the sequence number copied from the received packet
  840802: is the local timestamp of the received packet
  -27   : is the RSSI (in dBm) of the received packet
  106   : is the LQI of the received packet
  -94   : is the ambient RF noise level (in dBm)
  0     : is an error code which should always be 0

