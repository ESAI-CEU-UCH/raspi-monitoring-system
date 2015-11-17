/*
  
  emonTxV3 Discrete Sampling with pulse 
  
  If an AC-AC adapter is detected, assume emonTx is also powered from adapter (jumper shorted) and take Real Power Readings and disable sleep mode to keep load on power supply constant.
  If an AC-AC adapter is not detected, assume powering from batteries / USB 5V. AC sample is not present so take Apparent Power Readings and enable sleep mode.
  
  Pulse Input: 
  Many meters have pulse outputs, including electricity meters: single phase, 3-phase, 
  import, export.. Gas meters, Water flow meters etc.

  The pulse output may be a flashing LED or a switching relay (usually solid state) or both.

  In the case of an electricity meter or a gas meter, a pulse output corresponds to a certain amount of 
  energy passing through the meter (kWh/Wh). For single-phase domestic electricity meters
  (eg. Elster A100c) each pulse usually corresponds to 1 Wh (1000 pulses per kWh). For a gas meter
  it might mean 0.001 cu.m of gas, and it is necessary to know the calorific value of the gas in order
  to convert to kWh.

  The Interrupt Service Routine runs when the falling edge of each pulse is detected and increments pulseCount
  
  (Power for display is found by the calculating the time elapsed between pulses.)
  
  Read more about pulse counting here:
  http://openenergymonitor.org/emon/buildingblocks/introduction-to-pulse-counting

  Transmit values via RFM12B radio
  
  
 -----------------------------------------emonTx V3 Hardware Connections-----------------------------
 
 Connect the pulse input into emonTx V3 terminal block port 4 (IRQ 0 / Digital 2)
 A pull-down resistor is already present on the PCB (R31).
 
 If the pulse input can suffer from contact bounce (i.e. it is a mechanical switch of some sort) a HARDWARE debounce circuit must be used 
   between the switch and the pulse input. 
 If you're using an optical counter (e.g TSL256) you should be connecting the power pin direct to the 3.3V or 5V (if running off 5V USB)
 
 emonTx V3 Terminal block: 
 port 1: 5V
 port 2: 3.3V
 port 3: GND
 port 4: IRQ 0 / Dig2
 
 We recommend powering the emonTx V3 from 5V USB when using for pulse counting operation. 
 
 
   -----------------------------------------
  Part of the openenergymonitor.org project
  
  Authors: Glyn Hudson & Trystan Lea
  This sketch merged from the Discrete Sampling & Pulse sketches by Robert Wall.
  
  Builds upon JCW JeeLabs RF12 library and Arduino 
  
  Licence: GNU GPL V3

*/

/*Recommended node ID allocation
------------------------------------------------------------------------------------------------------------
-ID-	-Node Type- 
0	- Special allocation in JeeLib RFM12 driver - reserved for OOK use
1-4     - Control nodes 
5-10	- Energy monitoring nodes
11-14	--Un-assigned --
15-16	- Base Station & logging nodes
17-30	- Environmental sensing nodes (temperature humidity etc.)
31	- Special allocation in JeeLib RFM12 driver - Node31 can communicate with nodes on any network group
-------------------------------------------------------------------------------------------------------------


Change Log:
V1.2 - fix bug which caused Vrms to be returned as zero if CT1 was not connected 
V1.1 - fix bug in startup Vrms calculation, startup Vrms startup calculation is now more accuratre
*/

#define emonTxV3                                                      // Tell emonLib this is the emonTx V3 - don't read Vcc assume Vcc = 3.3V as is always the case on emonTx V3 eliminates bandgap error and need for calibration http://harizanov.com/2013/09/thoughts-on-avr-adc-accuracy/

#include <RFu_JeeLib.h>                                               // Special modified version of the JeeJib library to work with the RFu328 https://github.com/openenergymonitor/RFu_jeelib        
ISR(WDT_vect) { Sleepy::watchdogEvent(); }                            // Attached JeeLib sleep function to Atmega328 watchdog -enables MCU to be put into sleep mode inbetween readings to reduce power consumption 

#include "EmonLib.h"                                                  // Include EmonLib energy monitoring library https://github.com/openenergymonitor/EmonLib
EnergyMonitor ct1, ct2, ct3, ct4;       

#include <OneWire.h>                                                  //http://www.pjrc.com/teensy/td_libs_OneWire.html
#include <DallasTemperature.h>                                        //http://download.milesburton.com/Arduino/MaximTemperature/DallasTemperature_LATEST.zip




//----------------------------emonTx V3 Settings----------------------------------------------------------------------------------------------
const byte Vrms=                  230;                             // Vrms for apparent power readings (when no AC-AC voltage sample is present)
const byte TIME_BETWEEN_READINGS= 10;                              //Time between readings   

const float Ical1=                90.9;                            // (2000 turns / 22 Ohm burden) = 90.9
const float Ical2=                90.9;                            // (2000 turns / 22 Ohm burden) = 90.9
const float Ical3=                90.9;                            // (2000 turns / 22 Ohm burden) = 90.9
const float Ical4=                16.6;                            // (2000 turns / 120 Ohm burden) = 16.6

const float Vcal=                 276.9;                           // (230V x 13) / (9V x 1.2) = 276.9

const float phase_shift=          1.7;
const int no_of_samples=          1480; 
const int no_of_half_wavelengths= 20;
const int timeout=                2000;                            //emonLib timeout 
const int ACAC_DETECTION_LEVEL=   3000;
const int TEMPERATURE_PRECISION=  11;                              //9 (93.8ms),10 (187.5ms) ,11 (375ms) or 12 (750ms) bits equal to resolution of 0.5C, 0.25C, 0.125C and 0.0625C
#define FILTERSETTLETIME          10                               // Time (ms) to allow the filters to settle before sending data
#define ASYNC_DELAY 375                                            // DS18B20 conversion delay - 9bit requires 95ms, 10bit 187ms, 11bit 375ms and 12bit resolution takes 750ms
//-------------------------------------------------------------------------------------------------------------------------------------------
//-------------------------------------------------------------------------------------------------------------------------------------------


//----------------------------emonTx V3 hard-wired connections------------------------------------------------------------------------------- 
const byte LEDpin=                6;                               // emonTx V3 LED
const byte DS18B20_PWR=           19;                              // DS18B20 Power
#define ONE_WIRE_BUS              5                                // DS18B20 Data                     
//-------------------------------------------------------------------------------------------------------------------------------------------

// Pulse counting settings 
volatile long pulseCount = 0;                                      // Number of pulses, used to measure energy.
int ppwh = 1;                                                      // 1000 pulses/kWh = 1 pulse per Wh
                                                                   //   - Number of pulses per Wh - found or set on the meter.

//-------------------------------------------------------------------------------------------------------------------------------------------

//Setup DS128B20
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

//-------------------------------------------------------------------------------------------------------------------------------------------

//-----------------------RFM12B SETTINGS----------------------------------------------------------------------------------------------------
#define RF_freq RF12_868MHZ                                        // Frequency of RF12B module can be RF12_433MHZ, RF12_868MHZ or RF12_915MHZ. You should use the one matching the module you have.
const int nodeID = 10;                                             // emonTx RFM12B node ID
const int networkGroup = 210;  
typedef struct { int power1, power2, power3, power4, Vrms, temp, pulses; } PayloadTX;     // create structure - a neat way of packaging data for RF comms
  PayloadTX emontx; 
//-------------------------------------------------------------------------------------------------------------------------------------------
//-------------------------------------------------------------------------------------------------------------------------------------------


//Random Variables 
boolean settled = false;
boolean CT1, CT2, CT3, CT4, ACAC, debug, DS18B20_STATUS; 
byte CT_count=0;
int numSensors;
//addresses of sensors, MAX 4!!  
byte allAddress [4][8];  // 8 bytes per address

void setup()
{ 
 
  pinMode(LEDpin, OUTPUT); 
  pinMode(DS18B20_PWR, OUTPUT);  
  digitalWrite(LEDpin,HIGH); 

  attachInterrupt(0, onPulse, FALLING);                            // kWh interrupt attached to IRQ 0  = Digital 2
                                                                   //    - hardwired to emonTx V3 terminal block 

  Serial.begin(9600);
  Serial.println("emonTx V3 Discrete Sampling V1.2");
  Serial.println("OpenEnergyMonitor.org");
  Serial.println("Performing power-on tests.....please wait 10s");
  delay(10);
  rf12_initialize(nodeID, RF_freq, networkGroup);                  // initialize RFM12B
   for (int i=0; i<10; i++)                                        //Send RFM12B test sequence (for factory testing)
   {
     emontx.power1=i; 
     rf12_sendNow(0, &emontx, sizeof emontx);
     delay(100);
   }
  rf12_sendWait(2);
  emontx.power1=0;
  rf12_sleep(RF12_SLEEP);   
 
   

  if (analogRead(1) > 0) {CT1 = 1; CT_count++;} else CT1=0;        // check to see if CT is connected to CT1 input, if so enable that channel
  if (analogRead(2) > 0) {CT2 = 1; CT_count++;} else CT2=0;        // check to see if CT is connected to CT2 input, if so enable that channel
  if (analogRead(3) > 0) {CT3 = 1; CT_count++;} else CT3=0;        // check to see if CT is connected to CT3 input, if so enable that channel
  if (analogRead(4) > 0) {CT4 = 1; CT_count++;} else CT4=0;        //  check to see if CT is connected to CT4 input, if so enable that channel
  
  if ( CT_count == 0) CT1=1;                                       // If no CT's are connect ed CT1-4 then by default read from CT1

  // Quick check to see if there is a voltage waveform present on the ACAC Voltage input
  // Check consists of calculating the RMS from 100 samples of the voltage input.
  Sleepy::loseSomeTime(10000);            //wait for settle
  digitalWrite(LEDpin,LOW); 
  
  // Calculate if there is an ACAC adapter on analog input 0
  //double vrms = calc_rms(0,1780) * (Vcal * (3.3/1024) );
  double vrms = calc_rms(0,1780) * 0.87;
  if (vrms>90) ACAC = 1; else ACAC=0;
 
  if (ACAC) 
  {
    for (int i=0; i<10; i++)                                       // indicate AC has been detected by flashing LED 10 times
    { 
      digitalWrite(LEDpin, HIGH); delay(200);
      digitalWrite(LEDpin, LOW); delay(300);
    }
  }
  else 
  {
    delay(1000);
    digitalWrite(LEDpin, HIGH); delay(2000); digitalWrite(LEDpin, LOW);   // indicate DC power has been detected by turing LED on then off
  }
 
 
  //################################################################################################################################
  //Setup and for presence of DS18B20
  //################################################################################################################################
  digitalWrite(DS18B20_PWR, HIGH); delay(50); 
  sensors.begin();
  sensors.setWaitForConversion(false);             //disable automatic temperature conversion to reduce time spent awake, conversion will be implemented manually in sleeping http://harizanov.com/2013/07/optimizing-ds18b20-code-for-low-power-applications/ 
  numSensors=(sensors.getDeviceCount()); 
  
  byte j=0;                                        // search for one wire devices and
                                                   // copy to device address arrays.
  while ((j < numSensors) && (oneWire.search(allAddress[j])))  j++;
  digitalWrite(DS18B20_PWR, LOW);
  
  if (numSensors==0) DS18B20_STATUS=0; 
    else DS18B20_STATUS=1;

  
//################################################################################################################################

  if (Serial) debug = 1; else debug=0;          //if serial UART to USB is connected show debug O/P. If not then disable serial
  if (debug==1)
  {
    Serial.print("CT 1 Calibration: "); Serial.println(Ical1);
    Serial.print("CT 2 Calibration: "); Serial.println(Ical2);
    Serial.print("CT 3 Calibration: "); Serial.println(Ical3);
    Serial.print("CT 4 Calibration: "); Serial.println(Ical4);
    delay(1000);

    Serial.print("RMS Voltage on AC-AC Adapter input is: ~");
    Serial.print(vrms,0); Serial.println("V");
      
    if (ACAC) 
    {
      Serial.println("AC-AC adapter detected - Real Power measurements enabled");
      Serial.println("assuming powering from AC-AC adapter (jumper closed)");
      Serial.print("Vcal: "); Serial.println(Vcal);
      Serial.print("Phase Shift: "); Serial.println(phase_shift);
    }
     else 
     {
       Serial.println("AC-AC adapter NOT detected - Apparent Power measurements enabled");
       Serial.print("Assuming VRMS to be "); Serial.print(Vrms); Serial.println("V");
       Serial.println("Assuming powering from batteries / 5V USB - power saving mode enabled");
     }  

    if (CT_count==0) Serial.println("NO CT's detected, sampling from CT1 by default");
    else   
    {
      if (CT1) Serial.println("CT 1 detected");
      if (CT2) Serial.println("CT 2 detected");
      if (CT3) Serial.println("CT 3 detected");
      if (CT4) Serial.println("CT 4 detected");
    }
    if (DS18B20_STATUS==1) {Serial.print("Detected "); Serial.print(numSensors); Serial.println(" DS18B20..using this for temperature reading");}
      else Serial.println("Unable to detect DS18B20 temperature sensor");
    Serial.println("RFM12B Initiated: ");
    Serial.print("Node: "); Serial.print(nodeID); 
    Serial.print(" Freq: "); 
    if (RF_freq == RF12_433MHZ) Serial.print("433MHz");
    if (RF_freq == RF12_868MHZ) Serial.print("868MHz");
    if (RF_freq == RF12_915MHZ) Serial.print("915MHz"); 
    Serial.print(" Network: "); Serial.println(networkGroup);
   delay(500);  
  }
  else 
    Serial.end();
  
  
    
  if (CT1) ct1.current(1, Ical1);             // CT ADC channel 1, calibration.  calibration (2000 turns / 22 Ohm burden resistor = 90.909)
  if (CT2) ct2.current(2, Ical2);             // CT ADC channel 2, calibration.
  if (CT3) ct3.current(3, Ical3);             // CT ADC channel 3, calibration. 
  //CT 4 is high accuracy @ low power -  4.5kW Max @ 240V 
  if (CT4) ct4.current(4, Ical4);             // CT channel ADC 4, calibration.  calibration (2000 turns / 120 Ohm burden resistor = 16.66)
  
  if (ACAC)
  {
    if (CT1) ct1.voltage(0, Vcal, phase_shift);          // ADC pin, Calibration, phase_shift
    if (CT2) ct2.voltage(0, Vcal, phase_shift);          // ADC pin, Calibration, phase_shift
    if (CT3) ct3.voltage(0, Vcal, phase_shift);          // ADC pin, Calibration, phase_shift
    if (CT4) ct4.voltage(0, Vcal, phase_shift);          // ADC pin, Calibration, phase_shift
  }
 
 // Do measurements to allow the software filter to settle - don't use the result
  if (ACAC)
  {
    if (CT1) for (int j=0; j<5;j++) ct1.calcVI(no_of_half_wavelengths,timeout);
    if (CT2) for (int j=0; j<5;j++) ct2.calcVI(no_of_half_wavelengths,timeout);
    if (CT3) for (int j=0; j<5;j++) ct3.calcVI(no_of_half_wavelengths,timeout);
    if (CT4) for (int j=0; j<5;j++) ct4.calcVI(no_of_half_wavelengths,timeout);
   }
   else
  {
    if (CT1) for (int j=0; j<5;j++) ct1.calcIrms(no_of_samples);
    if (CT2) for (int j=0; j<5;j++) ct2.calcIrms(no_of_samples);
    if (CT3) for (int j=0; j<5;j++) ct3.calcIrms(no_of_samples);
    if (CT4) for (int j=0; j<5;j++) ct4.calcIrms(no_of_samples);
   }
 
 
}

void loop()
{
  
  if (ACAC) {
    delay(200);                                       //if powering from AC-AC allow time for power supply to settle    
    emontx.Vrms=0;                                    //Set Vrms to zero, this will be overwritten by one or more of CT 1-4
  }
  
  if (CT1) 
  {
   if (ACAC) 
   {
     ct1.calcVI(no_of_half_wavelengths,timeout); emontx.power1=ct1.realPower;
     emontx.Vrms=ct1.Vrms*100;
   }
   else
     emontx.power1 = ct1.calcIrms(no_of_samples)*Vrms;                               // Calculate Apparent Power 1  1480 is  number of samples
   if (debug==1) {Serial.print(emontx.power1); Serial.print(" ");} 

  }
  
  if (CT2) 
  {
   if (ACAC) 
   {
     ct2.calcVI(no_of_half_wavelengths,timeout); emontx.power2=ct2.realPower;
     emontx.Vrms=ct2.Vrms*100;
   }
   else
     emontx.power2 = ct2.calcIrms(no_of_samples)*Vrms;                               // Calculate Apparent Power 1  1480 is  number of samples
   if (debug==1) {Serial.print(emontx.power2); Serial.print(" ");}  

  }

  if (CT3) 
  {
   if (ACAC) 
   {
     ct3.calcVI(no_of_half_wavelengths,timeout); emontx.power3=ct3.realPower;
     emontx.Vrms=ct3.Vrms*100;
   }
   else
     emontx.power3 = ct3.calcIrms(no_of_samples)*Vrms;                               // Calculate Apparent Power 1  1480 is  number of samples
   if (debug==1) {Serial.print(emontx.power3); Serial.print(" ");} 

  }
  

  if (CT4) 
  {
   if (ACAC) 
   {
     ct4.calcVI(no_of_half_wavelengths,timeout); emontx.power4=ct4.realPower;
     emontx.Vrms=ct4.Vrms*100;
   }
   else
     emontx.power4 = ct4.calcIrms(no_of_samples)*Vrms;                               // Calculate Apparent Power 1  1480 is  number of samples
   if (debug==1) {Serial.print(emontx.power4); Serial.print(" ");} 

  }
  
  
  if (ACAC) 
  { 
    if ((debug==1) && (!CT_count==0))  Serial.print(emontx.Vrms);
  }

  // Accumulate Pulses 
  noInterrupts();
  emontx.pulses = pulseCount; 
  pulseCount=0; 
  interrupts();
  if (debug==1)
  {
	Serial.print(" ");
    Serial.print(emontx.pulses);                                   // the incremental pulse count
  }
                                                                               
  if ((debug==1) && (!CT_count==0)) {Serial.println(); delay(30);}
  
  // because millis() returns to zero after 50 days ! 
  if (!settled && millis() > FILTERSETTLETIME) settled = true;

  
  if (DS18B20_STATUS==1)
  {
     digitalWrite(DS18B20_PWR, HIGH); Sleepy::loseSomeTime(50); 
     for(int j=0;j<numSensors;j++) sensors.setResolution(allAddress[j], TEMPERATURE_PRECISION);   // and set the a to d conversion resolution of each.
     sensors.requestTemperatures();                                // Send the command to get temperatures
     Sleepy::loseSomeTime(ASYNC_DELAY);                            //Must wait for conversion, since we use ASYNC mode
     float temp=(sensors.getTempC(allAddress[0]));
     digitalWrite(DS18B20_PWR, LOW);
     if ((temp<125.0) && (temp>-40.0)) emontx.temp=(temp*10);      //if reading is within range for the sensor convert float to int ready to send via RF
     if (debug==1) {Serial.print("temperature: "); Serial.println(emontx.temp*0.1); delay(20);}
  }
  
  if (settled)                                                     // send data only after filters have settled
  { 
    send_rf_data();                                                // *SEND RF DATA* - see emontx_lib
    
    if (ACAC)
    {
     delay(TIME_BETWEEN_READINGS*1000);
     digitalWrite(LEDpin, HIGH); delay(200); digitalWrite(LEDpin, LOW);    // flash LED - turn off to save power
    }
    
    else
      emontx_sleep(TIME_BETWEEN_READINGS);                         // sleep or delay in seconds 
  }  
 
}

// The interrupt routine - runs each time a change is detected
void onPulse()                  
{
  static unsigned long changeTime = 0, lastTime = 0;          
  lastTime = changeTime;        
  changeTime = micros();
  pulseCount++;                                                    //pulseCounter     
}



void send_rf_data()
{
  rf12_sleep(RF12_WAKEUP);                                   
  rf12_sendNow(0, &emontx, sizeof emontx);                         //send temperature data via RFM12B using new rf12_sendNow wrapper
  rf12_sendWait(2);
  rf12_sleep(RF12_SLEEP);
}

void emontx_sleep(int seconds) {
  Sleepy::loseSomeTime(seconds*1000);
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

