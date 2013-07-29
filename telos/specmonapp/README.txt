README for SpectrumMonitorApp

Description:

This application periodically samples RF noise power in the 2.4 GHz band on a
set of user-defined frequencies (FREQUENCY_VECTOR in spectrummonitor.h) and
continuously outputs the result over the USB interface.  Each sample represents
RF power averaged over a 192 microsec interval on a given frequency. By default
the sampling period is 128/32768 sec (roughly 4 ms), the bandwidth (IEEE
802.15.4 channel width) is 2 MHz (fixed). This app is only available for the
TelosB (Tmote Sky) platform. During operation, all LEDs should remain off. The
RED LED will indicate an error; also, in case of an error the resulting RSSI
sampling will be set to a value of 100 dBm. 

Timing example: if FREQUENCY_VECTOR is defined as {2400, 2410, 2415} (in
spectrummonitor.h), then the radio will continously, round robin sweep over the
frequencies 2400->2410->2415->2400->2410->etc. Because there are 3 center
frequencies each frequency is sampled once every ~12ms (assuming default
SAMPLING_PERIOD of 128 jiffies in spectrummonitor.h). This includes the time for
streaming the results over the USB interface.


Usage: 

1. Install the image on a telosb node:
   $ make telosb install
   
   Note: if you have more than one telosb attached to your laptop and want to 
   install the app to a specific one, first run the "motelist" command and then

   $ make telosb install bsl,/dev/ttyUSB1
   
   where "/dev/ttyUSB1" can be replaced by a device file returned by "motelist"

2. Start a serialforwarder:
   $ CLASSPATH=.:./tinyos.jar:$CLASSPATH java net.tinyos.sf.SerialForwarder -comm serial@/dev/ttyUSB0:115200 -no-gui -port 9002

   ... and display the results:
   $ CLASSPATH=.:./tinyos.jar:$CLASSPATH java net.tinyos.tools.PrintfClient -comm sf@localhost:9002
   (this will run a local/patched version of the printf library)  

   Format: one column per channel in the order defined by FREQUENCY_VECTOR, 
           RF power is given in dBm


Parsing data from a TWIST experiment:

1. Create the image
   $ make telosb

2. Install build/telosb/main.exe on some (all) TWIST tmote nodes via
   TWIST webinterface https://www.twist.tu-berlin.de:8000

3. Start TWIST automatic tracing function

4. After experiment download the trace file and extract the data to text files:
   -> run the "./twist_trace_parser" script. It creates one file per node with 
   the samples incl. a NTP timestamp taken on the slug for each sweep.
   

