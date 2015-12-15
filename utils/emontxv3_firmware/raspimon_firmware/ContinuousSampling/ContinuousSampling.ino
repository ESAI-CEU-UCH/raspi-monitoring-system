/*
  Computes an average of all EnergyMonitor object properties for all four CTs.
*/
#define emonTxV3                                                                   // Tell emonLib this is the emonTx V3 - don't read Vcc assume Vcc = 3.3V as is always the case on emonTx V3 eliminates bandgap error and need for calibration http://harizanov.com/2013/09/thoughts-on-avr-adc-accuracy/
#define RF69_COMPAT 1                                                              // Set to 1 if using RFM69CW or 0 is using RFM12B

#include <JeeLib.h>                                                                //https://github.com/jcw/jeelib - Tested with JeeLib 3/11/14
ISR(WDT_vect) { Sleepy::watchdogEvent(); }                                         // Attached JeeLib sleep function to Atmega328 watchdog -enables MCU to be put into sleep mode inbetween readings to reduce power consumption 

#include "EmonLib.h"                                                               // Include EmonLib energy monitoring library https://github.com/openenergymonitor/EmonLib

// All CTs are considered as enabled
const byte version = 10;


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

// In each of this arrays first one is Voltage and second one is Current.

const float cal[] = { 241.0, 88.24,
                      241.0, 85.70,
                      241.0, 87.60,
                      241.0, 16.20 };
const float phase_cal[] = { 1.90, 1.0,
                            1.57, 1.0,
                            1.60, 1.0,
                            1.54, 1.0 };
const int pins[] = { 0, 1,
                     0, 2,
                     0, 3,
                     0, 4 };

const int SIZE=50;
                     
double offsets[8], filtereds[8], shifteds[8], lastFiltereds[8], samples[8];
int lines[SIZE][8];

bool ACAC;

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
  
  if (RF_freq == RF12_433MHZ) Serial.println("433Mhz");
  if (RF_freq == RF12_868MHZ) Serial.println("868Mhz");
  if (RF_freq == RF12_915MHZ) Serial.println("915Mhz"); 
  
  // Calculate if there is an ACAC adapter on analog input 0
  double vrms = calc_rms(0,1780) * 0.87;
  if (vrms>90) ACAC = 1; else ACAC=0;
 
  if (ACAC) 
  {
    Serial.println("ACAC found");
    // indicate AC has been detected by flashing LED 10 times
    for (int i=0; i<10; i++)
    { 
      digitalWrite(LEDpin, HIGH); delay(200);
      digitalWrite(LEDpin, LOW); delay(300);
    }
  }
  else {
    Serial.println("THIS SCHEME NEEDS ACAC ADAPTOR");
    return;
  }

  pinMode(LEDpin, OUTPUT);                      // Setup indicator LED
  digitalWrite(LEDpin, HIGH);
  delay(200);
  digitalWrite(LEDpin, LOW);
  
  for (int j=0; j<8; ++j) offsets[j] = ADC_COUNTS>>1;
  for (int j=0; j<8; ++j) lastFiltereds[j] = 0.0;
}

void loop()
{
  int SupplyVoltage=3300;
  
  if (!ACAC) {
    Serial.println("THIS SCHEME NEEDS ACAC ADAPTOR");
    delay(1000);
    return;
  }
    
  for (int i=0; i<SIZE; ++i) {
    lines[i][0] = analogRead(pins[0]);    
    lines[i][1] = analogRead(pins[1]);
    lines[i][2] = analogRead(pins[2]);
    lines[i][3] = analogRead(pins[3]);
    lines[i][4] = analogRead(pins[4]);
    lines[i][5] = analogRead(pins[5]);
    lines[i][6] = analogRead(pins[6]);
    lines[i][7] = analogRead(pins[7]);
  }
  
  for (int i=0; i<SIZE; ++i) {
    for (int j=0; j<8; ++j) samples[j] = lines[i][j];
    for (int j=0; j<8; ++j) offsets[j] = offsets[j] + ((samples[j] - offsets[j])/1024.0);
    for (int j=0; j<8; ++j) filtereds[j] = samples[j] - offsets[j];
    for (int j=0; j<8; ++j) shifteds[j] = lastFiltereds[j] + phase_cal[j] * (filtereds[j] - lastFiltereds[j]);
    for (int j=0; j<8; ++j) lines[i][j] = cal[j] * (shifteds[j] * ((SupplyVoltage/1000.0)*(ADC_COUNTS)));
    for (int j=0; j<8; ++j) lastFiltereds[j] = filtereds[j];
  }
  
  for (int i=0; i<SIZE; ++i) {
    Serial.print(i); Serial.print(" ");
    for (int j=0; j<8; ++j) {
      Serial.print(lines[i][j]); Serial.print(" ");
    }
    Serial.println("");
  }  
}

double calc_rms(int pin, int samples)
{
  unsigned long sum = 0;
  for (int i=0; i<samples; i++) // 178 samples takes about 20ms
  {
    int raw = (analogRead(pin)-512);
    sum += (unsigned long)raw * raw;
  }
  double rms = sqrt((double)sum / samples);
  return rms;
}

