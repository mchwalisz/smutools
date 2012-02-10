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
 * $Date: 2009/11/18 18:23:06 $
 * @author: Jan Hauer <hauer@tkn.tu-berlin.de>
 * ========================================================================
 */

#include "lqm.h"
#include "CC2420IEEE802154.h"
#define NEW_PRINTF_SEMANTICS
#include "printf.h"

#if !defined(PLATFORM_TELOSB)
#error "The only supported platform is: TelosB!"
#endif

#if !defined(_LQM_SENDER) && !defined(_LQM_RECEIVER)
#error "You must pass either 'sender' or 'receiver' as a make option"
#endif

#if defined(_LQM_SENDER) && defined(_LQM_RECEIVER)
#error "You must pass either 'sender' or 'receiver' as a make option (not both!)"
#endif

#if defined(_LQM_SENDER) && (!defined(_LQM_UNICAST) && !defined(_LQM_BROADCAST))
#error "For a sender you must pass either 'unicast' or 'broadcast' as a make option"
#endif

#if defined(_LQM_SENDER) && (defined(_LQM_UNICAST) && defined(_LQM_BROADCAST))
#error "For a sender you must pass either 'unicast' or 'broadcast' as a make option (not both!)"
#endif


configuration LQMC {

} implementation {

#if defined(_LQM_UNICAST) 
  #if defined(_LQM_SENDER)
    components new LQMP(LQM_UNICAST, LQM_SENDER);
  #elif defined(_LQM_RECEIVER)
    components new LQMP(LQM_UNICAST, LQM_RECEIVER);
  #else
    #error Unknown LQM-role!
  #endif
#elif defined(_LQM_BROADCAST)
  #if defined(_LQM_SENDER)
    components new LQMP(LQM_BROADCAST, LQM_SENDER);
  #elif defined(_LQM_RECEIVER)
    components new LQMP(LQM_BROADCAST, LQM_RECEIVER);
  #else
    #error Unknown LQM-role!
  #endif
#else
#error Unknown LQM-variant!
#endif

  components PrintfC;
  components SerialStartC;

  components MainC, LedsC;
  MainC.Boot <- LQMP.Boot;
  LQMP.Leds -> LedsC;

/*  components SerialSenderC;*/
/*  LQMP.SerialSend -> SerialSenderC.SerialSend;*/
/*  LQMP.SerialPacket -> SerialSenderC;*/

  components CC2420ControlC;
  LQMP.SpiResource -> CC2420ControlC;
  LQMP.CC2420Power -> CC2420ControlC;

  components CC2420TransmitC;
  LQMP.TxControl -> CC2420TransmitC;
  LQMP.CC2420Tx -> CC2420TransmitC;

  components CC2420ReceiveC;
  LQMP.RxControl -> CC2420ReceiveC;
  LQMP.CC2420Rx -> CC2420ReceiveC.CC2420Rx;

  components UserButtonC;
  LQMP.GetButtonState -> UserButtonC;
  LQMP.ButtonPressed -> UserButtonC;

  components McuSleepC;
  McuSleepC.McuPowerOverride -> LQMP;

  components Msp430ClockC;
  LQMP.Msp430ClockInit -> Msp430ClockC;

  components Msp430TimerC;
  LQMP.TimerA -> Msp430TimerC.TimerA;
/*  LQMP.TimerB -> Msp430TimerC.TimerB;*/

  components new Alarm32khz32C() as Alarm;
  LQMP.Alarm -> Alarm;

}

