#define emonTxV3                                                                   // Tell emonLib this is the emonTx V3 - don't read Vcc assume Vcc = 3.3V as is always the case on emonTx V3 eliminates bandgap error and need for calibration http://harizanov.com/2013/09/thoughts-on-avr-adc-accuracy/
#define RF69_COMPAT 1                                                              // Set to 1 if using RFM69CW or 0 is using RFM12B

#include <JeeLib.h>                                                                      //https://github.com/jcw/jeelib - Tested with JeeLib 3/11/14
ISR(WDT_vect) { Sleepy::watchdogEvent(); }                            // Attached JeeLib sleep function to Atmega328 watchdog -enables MCU to be put into sleep mode inbetween readings to reduce power consumption 

#include "EmonLib.h"                                                                    // Include EmonLib energy monitoring library https://github.com/openenergymonitor/EmonLib
EnergyMonitor ct1, ct2, ct3, ct4;       

#include <OneWire.h>                                                  //http://www.pjrc.com/teensy/td_libs_OneWire.html

// All CTs are considered as enabled
const byte version = 10;

float Vcal1=276.9; // (230V x 13) / (9V x 1.2) = 276.9 Calibration for EU AC-AC adapter 77DB-06-09 
float Vcal2=276.9; // (230V x 13) / (9V x 1.2) = 276.9 Calibration for EU AC-AC adapter 77DB-06-09 
float Vcal3=276.9; // (230V x 13) / (9V x 1.2) = 276.9 Calibration for EU AC-AC adapter 77DB-06-09 
float Vcal4=276.9; // (230V x 13) / (9V x 1.2) = 276.9 Calibration for EU AC-AC adapter 77DB-06-09 

const float Ical1=                87.60;                               // (2000 turns / 22 Ohm burden) = 90.9
const float Ical2=                87.70;                               // (2000 turns / 22 Ohm burden) = 90.9
const float Ical3=                87.50;                               // (2000 turns / 22 Ohm burden) = 90.9
const float Ical4=                16.67;                               // (2000 turns / 120 Ohm burden) = 16.67

const float phase_shift1=          1.7;
const float phase_shift2=          1.7;
const float phase_shift3=          1.7;
const float phase_shift4=          1.7;

//----------------------------emonTx V3 hard-wired connections--------------------------------------------------------------------------------------------------------------- 
const byte LEDpin=                 6;                              // emonTx V3 LED
const byte battery_voltage_pin=    7;                              // Battery Voltage sample from 3 x AA
#define ONE_WIRE_BUS               5                               // DS18B20 Data                     
//-------------------------------------------------------------------------------------------------------------------------------------------

//-----------------------RFM12B / RFM69CW SETTINGS----------------------------------------------------------------------------------------------------
#define RF_freq RF12_433MHZ                                              // Frequency of RF69CW module can be RF12_433MHZ, RF12_868MHZ or RF12_915MHZ. You should use the one matching the module you have.
byte nodeID = 10;                                                        // emonTx RFM12B node ID
const int networkGroup = 210;
//-------------------------------------------------------------------------------------------------------------------------------------------

bool ACAC;
const int no_of_half_wavelengths = 20;
const int timeout = 400;

void setup() 
{
  pinMode(LEDpin, OUTPUT); 
  digitalWrite(LEDpin,HIGH); 

  Serial.begin(9600);
  Serial.print("raspimon - Voltage V"); Serial.print(version*0.1);
  #if (RF69_COMPAT)
    Serial.println(" RFM69CW");
  #else
    Serial.println(" RFM12B");
  #endif
  Serial.println("POST.....wait 10s");  
  
  Serial.print("Node: "); 
  Serial.print(nodeID); 
  Serial.print(" Freq: "); 
  if (RF_freq == RF12_433MHZ) Serial.print("433Mhz");
  if (RF_freq == RF12_868MHZ) Serial.print("868Mhz");
  if (RF_freq == RF12_915MHZ) Serial.print("915Mhz"); 
  Serial.print(" Network: "); 
  Serial.println(networkGroup);
  
  // Calculate if there is an ACAC adapter on analog input 0
  double vrms = calc_rms(0,1780) * 0.87;
  if (vrms>90) ACAC = 1; else ACAC=0;
 
  if (ACAC) 
  {
    Serial.println("ACAC found");
    for (int i=0; i<10; i++)                                              // indicate AC has been detected by flashing LED 10 times
    { 
      digitalWrite(LEDpin, HIGH); delay(200);
      digitalWrite(LEDpin, LOW); delay(300);
    }
  }
  else {
    Serial.println("THIS SCHEME NEEDS ACAC ADAPTOR");
    return;
  }

  ct1.current(1, Ical1);
  ct2.current(2, Ical2);
  ct3.current(3, Ical3);
  ct4.current(4, Ical4);
 
  ct1.voltage(0, Vcal1, phase_shift1);          // ADC pin, Calibration, phase_shift
  ct2.voltage(0, Vcal2, phase_shift2);          // ADC pin, Calibration, phase_shift
  ct3.voltage(0, Vcal3, phase_shift3);          // ADC pin, Calibration, phase_shift
  ct4.voltage(0, Vcal4, phase_shift4);          // ADC pin, Calibration, phase_shift

  pinMode(LEDpin, OUTPUT);                                              // Setup indicator LED
  digitalWrite(LEDpin, HIGH);
  delay(200);
  digitalWrite(LEDpin, LOW);
}

void loop() 
{
  if (!ACAC) {
    Serial.println("THIS SCHEME NEEDS ACAC ADAPTOR");
    delay(1000);
    return;
  }
  
  ct1.calcVI(no_of_half_wavelengths,timeout); 
  ct2.calcVI(no_of_half_wavelengths,timeout); 
  ct3.calcVI(no_of_half_wavelengths,timeout); 
  ct4.calcVI(no_of_half_wavelengths,timeout); 
  
  Serial.print("CT1: "); ct1.serialprint();
  Serial.print("CT2: "); ct2.serialprint();
  Serial.print("CT3: "); ct3.serialprint();
  Serial.print("CT4: "); ct4.serialprint();

  if (ACAC) {digitalWrite(LEDpin, HIGH); delay(200); digitalWrite(LEDpin, LOW);}    // flash LED if powe  
  delay(10);
}

double calc_rms(int pin, int samples)
{
  unsigned long sum = 0;
  for (int i=0; i<samples; i++) // 178 samples takes about 20ms
  {
    int raw = (analogRead(0)-512);
    sum += (unsigned long)raw * raw;
  }
  double rms = sqrt((double)sum / samples);
  return rms;
}

