// ==========================================
// ENCODER HARDWARE DEBUGGER (ALL 4 MOTORS)
// ==========================================

#define E1_A 25
#define E1_B 26

#define E2_A 32
#define E2_B 33

#define E3_A 34
#define E3_B 35

#define E4_A 27
#define E4_B 14

void setup() {
  Serial.begin(115200);
  
  // Configure all pins
  pinMode(E1_A, INPUT_PULLUP); pinMode(E1_B, INPUT_PULLUP);
  pinMode(E2_A, INPUT_PULLUP); pinMode(E2_B, INPUT_PULLUP);
  pinMode(E3_A, INPUT);        pinMode(E3_B, INPUT);        // 34 & 35 do not have internal pullups
  pinMode(E4_A, INPUT_PULLUP); pinMode(E4_B, INPUT_PULLUP);
  
  Serial.println("Turn any motor slowly by hand...");
}

void loop() {
  // Read all 8 pins
  int m1a = digitalRead(E1_A); int m1b = digitalRead(E1_B);
  int m2a = digitalRead(E2_A); int m2b = digitalRead(E2_B);
  int m3a = digitalRead(E3_A); int m3b = digitalRead(E3_B);
  int m4a = digitalRead(E4_A); int m4b = digitalRead(E4_B);
  
  // Print all 8 signals to the Serial Plotter
  Serial.print("M1_A:"); Serial.print(m1a); Serial.print(" ");
  Serial.print("M1_B:"); Serial.print(m1b); Serial.print(" ");
  
  Serial.print("M2_A:"); Serial.print(m2a); Serial.print(" ");
  Serial.print("M2_B:"); Serial.print(m2b); Serial.print(" ");
  
  Serial.print("M3_A:"); Serial.print(m3a); Serial.print(" ");
  Serial.print("M3_B:"); Serial.print(m3b); Serial.print(" ");
  
  Serial.print("M4_A:"); Serial.print(m4a); Serial.print(" ");
  Serial.print("M4_B:"); Serial.println(m4b);
  
  delay(20); // Fast read for smooth plotting
}
