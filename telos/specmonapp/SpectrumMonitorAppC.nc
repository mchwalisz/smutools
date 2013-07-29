
#if !defined(PLATFORM_TELOSB)
#error MUST BE TELOSB PLATFORM!
#endif

configuration SpectrumMonitorAppC{
}
implementation {
  components MainC, SpectrumMonitorC, LedsC;

  SpectrumMonitorC.Boot -> MainC;
  SpectrumMonitorC.Leds -> LedsC;

  components CC2420ControlC;
  SpectrumMonitorC.SpiResource -> CC2420ControlC;
  SpectrumMonitorC.CC2420Power -> CC2420ControlC;  

  components CC2420TransmitC;
  SpectrumMonitorC.TxControl -> CC2420TransmitC;

  components CC2420ReceiveC;
  SpectrumMonitorC.RxControl -> CC2420ReceiveC;  

  components new Alarm32khz32C();
  MainC.SoftwareInit -> Alarm32khz32C;
  SpectrumMonitorC.Alarm -> Alarm32khz32C;
  
  components SerialResponsiveC;
  SerialResponsiveC.TraceReceive -> SpectrumMonitorC.TraceReceive;
  SpectrumMonitorC.TracePacket -> SerialResponsiveC;
}

