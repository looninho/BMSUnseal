/**********************************
 * USE ARDUINO FOR SMBUS ADAPTATOR FOR CHANGING MANUFACTURER PARAMETERS OF 3DR SOLO BATTERY
 * LOONINHO 
 * Code Version 0.01 beta
 * 
 * Use serial port to send hex command to Arduino.
 * Then Arduino convert this command to i2c_smbus to communicate with the battery.
 * 
 * Format of the hex command by serial port: TODO! 
 * 0x00: send byte
 * 0x10: read word
 * 0xF0: read block
 * 0x1F: write word
 * 0xFF: write block
 * 
 **********************************/


/**********************************
 * SMBus FOR 3DR SOLO with Arduino UNO R3
 * STAVROPOULOS
 * Code Version 0.02 beta
 * 
 * MUCH OF THIS CODE WAS COPIED FROM
 * https://github.com/PowerCartel/PackProbe/blob/master/PackProbe/PackProbe.ino
 * https://github.com/ArduPilot/PX4Firmware/blob/master/src/drivers/batt_smbus/batt_smbus.cpp
 * 
 **********************************/

/**********************************
 * Configured for Arduino UNO R3
 * you will need to use external pull up resistors of 
 * 4.7k-ohm to pull the SDA and SCL lines up to 3.3v
 **********************************/

/**********************************
 * CONFIGURE I2C/SERIAL ON ARDUINO
 **********************************/
 
//DEFINE SDA AND SCL PINS
#define SCL_PIN 5                 //COMMUNICATION PIN 5 ON MEGA
#define SCL_PORT PORTC

#define SDA_PIN 4                 //COMMUNICATION PIN 6 ON MEGA
#define SDA_PORT PORTC


//CONFIGURE I2C MODES
#define I2C_TIMEOUT 100           //PREVENT SLAVE DEVICES FROM STRETCHING LOW PERIOD OF THE CLOCK INDEFINITELY AND LOCKING UP MCU BY DEFINING TIMEOUT
  //#define I2C_NOINTERRUPT 1       //SET TO 1 IF SMBus DEVICE CAN TIMEOUT
  //#define I2C_FASTMODE 1          //THE STANDARD I2C FREQ IS 100kHz.  USE THIS TO PERMIT FASTER UP TO 400kHz.
  //#define I2C_SLOWMODE 1            //THE STANDARD I2C FREQ IS 100kHz.  USE THIS TO PERMIT SLOWER, DOWN TO 25kHz.
#define BAUD_RATE 115200
#include <SoftI2CMaster.h>

/**********************************
 * CONFIGURE SERIAL LIBRARY
 **********************************/
  //#include <SoftwareSerial.h>
  //#include <Serial.h>
#include <Wire.h>
#define bufferLen 32
uint8_t i2cBuffer[bufferLen];
byte deviceAddress = 0x0b;
String inputString = "";         // a String to hold incoming data
boolean stringComplete = false;  // whether the string is complete

/**********************************
 * CONFIGURE SMBUS FUNCTIONS
 **********************************/
#define SEND_BYTE   0x00
#define READ_WORD   0x10
#define WRITE_WORD  0x1F
#define READ_BLOCK  0xF0
#define WRITE_BLOCK 0xFF

void setup() {
  // initialize serial:
  Serial.begin(BAUD_RATE);
  // reserve 200 bytes for the inputString:
  inputString.reserve(200);
  //SETUP I2C INPUT PINS
  pinMode(27,INPUT_PULLUP);                             //use external pull up resistor instead
  pinMode(28,INPUT_PULLUP);                             //use external pull up resistor instead
  Serial.flush();

  while (!Serial) {    
  ;                                                       //wait for Console port to connect.
  }

  i2c_init();                                             //i2c_start initialized the I2C system.  will return false if bus is locked.
}

void loop() {
  // print the string when a newline arrives:
  if (stringComplete) {
    uint8_t instrlen=inputString.length();
    if (instrlen >= 2) {
      uint8_t length_read = 0;
      char buf1[3];
      inputString.substring(0,2).toCharArray(buf1,3);
      unsigned long smbus_fct = strtoul(buf1,NULL,16);
      if (instrlen == 2 && smbus_fct == SEND_BYTE) {//find address (for debug)
        i2c_smbus_scan_address();
      }
      else if (instrlen >=4) {
        char buf2[3];
        inputString.substring(2,4).toCharArray(buf2,3);
        unsigned long smbus_cmd = strtoul(buf2,NULL,16);
        switch(smbus_fct) {
          case SEND_BYTE: // send byte (for debug)
            if (instrlen == 4) { //send byte
              Serial.println(i2c_smbus_send_byte(smbus_cmd));
            }
            // below is other cond for futur use i.e. scan for pwd:...
            break;
          case READ_WORD : //read word
            if (instrlen == 4) {
              Serial.println(i2c_smbus_read_word(smbus_cmd));
            }
            break;
          case READ_BLOCK: //read block
            length_read = i2c_smbus_read_block(smbus_cmd, i2cBuffer, bufferLen);
            Serial.write(i2cBuffer, length_read);
            //Serial.println(length_read);  // for debug
            break;
          case WRITE_WORD: //write word
            if (instrlen == 8) {
              char nbyte[3];
              uint8_t datalen=instrlen/2 - 2;
              uint8_t databuff[datalen];
              for (uint8_t x=0; x<datalen; x++) {
                inputString.substring(2*x+4,2*x+6).toCharArray(nbyte,3);
                databuff[x]=strtoul(nbyte,NULL,16);
                Serial.print(databuff[x]);
                Serial.print(" ");
              }
              i2c_smbus_write_word(smbus_cmd, databuff);
            }
            break;
          case WRITE_BLOCK: //write block
            if (instrlen % 2 == 0 && instrlen >= 12 ) {
              char nbyte[3];
              inputString.substring(4,6).toCharArray(nbyte,3);
              uint8_t counts = strtoul(nbyte,NULL,16);
              uint8_t datalen=instrlen/2 - 3;
              uint8_t databuff[datalen];
              for (uint8_t x=0; x<datalen; x++) {
                inputString.substring(2*x+6,2*x+8).toCharArray(nbyte,3);
                databuff[x]=strtoul(nbyte,NULL,16);
                Serial.print(databuff[x]);
                Serial.print(" ");
              }
              i2c_smbus_write_block(smbus_cmd, databuff, counts);
            }
            break;
          default:
            break;
        }
      }
      // clear the string:
      inputString = "";
      stringComplete = false;
    }
  }
}
/*
  SerialEvent occurs whenever a new data comes in the hardware serial RX. This
  routine is run between each time loop() runs, so using delay inside loop can
  delay response. Multiple bytes of data may be available.
*/
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    if (inChar != '\n' && inChar != '\r') { // start or end of inputString
      inputString += inChar;
    }
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\r') { // end of inputString
      stringComplete = true;
    }
  }
}

void i2c_smbus_scan_address()
{
    byte i = 0;
    bool ack = false;
    while (!ack && i < 127)
    {
      bool ack = i2c_start(i<<1 | I2C_WRITE); 
      if ( ack ) {
        //Serial.println(": OK");
        Serial.println(i);
        Serial.flush();        
      }
      i2c_stop();
      i++;
    }
}

byte i2c_smbus_send_byte(byte cmd)
{
  byte rsp = 0;
  bool ack = i2c_start_wait(deviceAddress<<1 | I2C_WRITE);
  if ( ack ) {
    rsp = 1;
  }
  i2c_stop();
  return rsp;
}

int i2c_smbus_read_word(byte func)
{
    i2c_start(deviceAddress<<1 | I2C_WRITE);                //Initiates a transfer to the slave device with the (8-bit) I2C address addr.
                                                            //Alternatively, use i2c_start_wait which tries repeatedly to start transfer until acknowledgment received
    //i2c_start_wait(deviceAddress<<1 | I2C_WRITE);
    i2c_write(func);                                        //Sends a byte to the previously addressed device. Returns true if the device replies with an ACK.
    i2c_rep_start(deviceAddress<<1 | I2C_READ);             //Sends a repeated start condition, i.e., it starts a new transfer without sending first a stop condition.
    byte b1 = i2c_read(false);                              //i2c_read Requests to receive a byte from the slave device. If last is true, 
                                                            //then a NAK is sent after receiving the byte finishing the read transfer sequence.
    byte b2 = i2c_read(true);
    i2c_stop();                                             //Sends a stop condition and thereby releases the bus.
    return (int)b1|((( int)b2)<<8);
}

uint8_t i2c_smbus_read_block ( uint8_t command, uint8_t* blockBuffer, uint8_t blockBufferLen ) 
{
    uint8_t x, num_bytes;
    i2c_start((deviceAddress<<1) + I2C_WRITE);
    i2c_write(command);
    i2c_rep_start((deviceAddress<<1) + I2C_READ);             
    num_bytes = i2c_read(false);                              //num of bytes; 1 byte will be index 0
    num_bytes = constrain(num_bytes,0,blockBufferLen-2);      //Constrains num_bytes to be within 0 and blockBufferLen-2 (=30). room for null at the end
    for (x=0; x<num_bytes-1; x++) {                           //-1 because x=num_bytes-1 if x<y; last byte needs to be "nack"'d, x<y-1
      blockBuffer[x] = i2c_read(false);
    }
    blockBuffer[x++] = i2c_read(true);                        //this will nack the last byte and store it in x's num_bytes-1 address.
    blockBuffer[x] = 0;                                       // and null it at last_byte+1
    i2c_stop();
    return num_bytes;
}

int i2c_smbus_write_word(byte func, uint8_t* wordBuffer)
{
    //i2c_start(deviceAddress<<1 | I2C_WRITE);                //Initiates a transfer to the slave device with the (8-bit) I2C address addr.
                                                            //Alternatively, use i2c_start_wait which tries repeatedly to start transfer until acknowledgment received
    i2c_start_wait(deviceAddress<<1 | I2C_WRITE);
    i2c_write(func);                                        //Sends a byte to the previously addressed device. Returns true if the device replies with an ACK.
    i2c_write(wordBuffer[1]);                                         // MSB is transferred first
    i2c_write(wordBuffer[0]);
    i2c_stop();                                             //Sends a stop condition and thereby releases the bus.
    return 0;
}

uint8_t i2c_smbus_write_block ( uint8_t command, uint8_t* blockBuffer, uint8_t blockBufferLen ) 
{
    uint8_t x;
    i2c_start_wait(deviceAddress<<1 | I2C_WRITE);
    i2c_write(command);
    i2c_write(blockBufferLen);
    for (x=0; x<blockBufferLen; x++) {
      i2c_write(blockBuffer[x]);
    }
    i2c_stop();
    return blockBufferLen;
}

