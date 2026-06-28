#include "WeOneWire.h"

WeOneWire::WeOneWire(uint8_t pin)
{
  reset(pin);
}

WeOneWire::WeOneWire(void){}

void WeOneWire::reset(uint8_t pin)
{
  WePIN=pin;
}

uint8_t WeOneWire::reset(void)
{
  uint8_t r;
  pinMode(WePIN,OUTPUT);
  digitalWrite(WePIN,LOW);
  delayMicroseconds(480);
  pinMode(WePIN,INPUT);
  delayMicroseconds(50);
  r=digitalRead(WePIN);
  delayMicroseconds(100);
  return r;
}

uint8_t WeOneWire::respond(void)
{ 
  unsigned long time;
  time = millis();
  pinMode(WePIN,INPUT);
  while(digitalRead(WePIN)==1)
  {
  	if((millis()-time)>150)
	return 1;
  }
  time = millis(); // Reset timeout
  while(digitalRead(WePIN)==0)
  {
    if((millis()-time)>150) // 150ms timeout to prevent fatal infinite loop
      return 1;
  }
  pinMode(WePIN,OUTPUT);
  digitalWrite(WePIN,LOW);
  delayMicroseconds(30);
  pinMode(WePIN,INPUT);
  return 0;
}

void WeOneWire::write_bit(uint8_t value)
{
  noInterrupts();
  digitalWrite(WePIN,LOW);
  pinMode(WePIN,OUTPUT);
  delayMicroseconds(5);
  digitalWrite(WePIN, value);
  interrupts();
  delayMicroseconds(30);
  digitalWrite(WePIN,HIGH);
  delayMicroseconds(5);
}

void WeOneWire::write_byte(uint8_t v)
{
  for(int i=0;i<8;i++){
    write_bit((v >> i) & 1);
  }
  pinMode(WePIN,INPUT);
}

uint8_t WeOneWire::read_bit(void)
{
  unsigned long time = millis();
  while(digitalRead(WePIN) == 1 && (millis() - time) <= 3);

  noInterrupts();
  delayMicroseconds(35);
  uint8_t r = digitalRead(WePIN);
  interrupts();
  delayMicroseconds(40);

  return r;
}

uint8_t WeOneWire::read_byte(void)
{
  uint8_t k = 0;
  pinMode(WePIN, INPUT);
  for(int i=0;i<8;i++){
    k |= read_bit() << i;
  }
  return k;
}

bool WeOneWire::send(uint8_t id, uint8_t dataLen, byte* data)
{
  if(reset())return false;
  write_byte(id);
  if(dataLen == 0)return true;
  if(reset())return false;
  for(int i=0; i<dataLen; ++i)
    write_byte(data[i]);
  return true;
}

bool WeOneWire::recv(uint8_t id, uint8_t dataLen, byte* data)
{
  if(reset())return false;
  write_byte(id);
  if(respond())return false;
  for(int i=0; i<dataLen; ++i)
    data[i] = read_byte();
  return true;
}

bool WeOneWire::write(uint8_t id, uint8_t dataLen, byte* data, long time, uint8_t writeDataLen, byte* writeData)
{
  if(reset())return false;
  write_byte(id);
  if(writeDataLen > 0){
    if(reset())return false;
    for(int i=0; i<writeDataLen; ++i)
      write_byte(writeData[i]);
  }
  if(dataLen == 0)return true;
  unsigned long timestamp = millis() + time;
  while(respond())
    if(millis() >= timestamp)
      return false;
  for(int i=0; i<dataLen; ++i)
    data[i] = read_byte();
  return true;
}

bool WeOneWire::send(uint8_t id)
{
  send(id, 0, 0);
}
