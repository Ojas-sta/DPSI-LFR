// ==========================================
// ESP32-S3 + 4 Encoder Motors + 2x L298N
// High-Performance PWM & Encoder Version
// ==========================================

// ---------- MOTOR 1 & 2 (L298N #1) ----------
const int M1_PWM = 1;
const int M1_IN1 = 2;
const int M1_IN2 = 4;

const int M2_PWM = 5;
const int M2_IN1 = 6;
const int M2_IN2 = 7;

// ---------- MOTOR 3 & 4 (L298N #2) ----------
const int M3_PWM = 8;
const int M3_IN1 = 9;
const int M3_IN2 = 10;

const int M4_PWM = 11;
const int M4_IN1 = 12;
const int M4_IN2 = 13;

// ---------- ENCODER PINS ----------
const int ENC1_A = 14; const int ENC1_B = 15;
const int ENC2_A = 16; const int ENC2_B = 17;
const int ENC3_A = 18; const int ENC3_B = 21;
const int ENC4_A = 38; const int ENC4_B = 39;

// ---------- ENCODER COUNTS ----------
volatile long encCount[4] = {0, 0, 0, 0};

// ---------- INTERRUPTS ----------
void IRAM_ATTR readEnc1() { (digitalRead(ENC1_A) == digitalRead(ENC1_B)) ? encCount[0]++ : encCount[0]--; }
void IRAM_ATTR readEnc2() { (digitalRead(ENC2_A) == digitalRead(ENC2_B)) ? encCount[1]++ : encCount[1]--; }
void IRAM_ATTR readEnc3() { (digitalRead(ENC3_A) == digitalRead(ENC3_B)) ? encCount[2]++ : encCount[2]--; }
void IRAM_ATTR readEnc4() { (digitalRead(ENC4_A) == digitalRead(ENC4_B)) ? encCount[3]++ : encCount[3]--; }

void setup() {
  Serial.begin(115200);

  // Motor Pins Setup
  int outPins[] = {M1_PWM, M1_IN1, M1_IN2, M2_PWM, M2_IN1, M2_IN2, 
                   M3_PWM, M3_IN1, M3_IN2, M4_PWM, M4_IN1, M4_IN2};
  for(int p : outPins) pinMode(p, OUTPUT);

  // Encoder Pins Setup
  int inPins[] = {ENC1_A, ENC1_B, ENC2_A, ENC2_B, ENC3_A, ENC3_B, ENC4_A, ENC4_B};
  for(int p : inPins) pinMode(p, INPUT_PULLUP);

  // Attach Interrupts
  attachInterrupt(digitalPinToInterrupt(ENC1_A), readEnc1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC2_A), readEnc2, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC3_A), readEnc3, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC4_A), readEnc4, CHANGE);

  Serial.println("ESP32-S3 4-Motor System: INITIALIZED");
}

void setMotor(int m, int speed) {
  int pwm, in1, in2;
  if(m==0) { pwm=M1_PWM; in1=M1_IN1; in2=M1_IN2; }
  else if(m==1) { pwm=M2_PWM; in1=M2_IN1; in2=M2_IN2; }
  else if(m==2) { pwm=M3_PWM; in1=M3_IN1; in2=M3_IN2; }
  else { pwm=M4_PWM; in1=M4_IN1; in2=M4_IN2; }

  analogWrite(pwm, abs(speed));
  digitalWrite(in1, speed > 0);
  digitalWrite(in2, speed < 0);
}

void loop() {
  // Test: All motors forward at medium speed
  for(int i=0; i<4; i++) setMotor(i, 150);

  // Debug Print
  Serial.printf("M1:%ld | M2:%ld | M3:%ld | M4:%ld\n", encCount[0], encCount[1], encCount[2], encCount[3]);
  delay(100);
}
