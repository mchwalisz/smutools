#ifndef SPECTRUMMONITOR_H
#define SPECTRUMMONITOR_H

#ifndef FREQUENCY_VECTOR

// The center frequencies of the IEEE 802.15.4 channels in the 2.4 GHz band
//#define FREQUENCY_VECTOR {2405, 2410, 2415, 2420, 2425, 2430, 2435, 2440, 2445, 2450, 2455, 2460, 2465, 2470, 2475, 2480}

#define FREQUENCY_VECTOR {2400, 2402, 2404, 2406, 2408, 2410, 2412, 2414, 2416, 2418, 2420, 2422, 2424, 2426, 2428, 2430, 2432, 2434, 2436, 2438, 2440, 2442, 2444, 2446, 2448, 2450, 2452, 2454, 2456, 2458, 2460, 2462, 2464, 2466, 2468, 2470, 2472, 2474, 2476, 2478, 2480}

#endif

enum {
  SAMPLING_PERIOD = 128, // ticks of ACLK, which runs at 32768 Hz, use values below 64 at your own risk!
};

/*** no need to change anything below ***/

#define TOSH_DATA_LENGTH 250

#ifndef PRINTF_MSG_LENGTH
#define PRINTF_MSG_LENGTH 220
#endif

typedef nx_struct printf_msg {
  nx_uint8_t buffer[PRINTF_MSG_LENGTH];
} printf_msg_t;

enum {
  MAX_STRLEN = 6,
  SERIAL_BUFFER_SIZE = 5,
  AM_PRINTF_MSG = 100,
};

#endif 

