// ==========================================
// ESP32 Single Encoder Test
// Isolates Motor 1 (Front Left) for verification
// ==========================================

const int ENC_A = 25; // Phase A (Interrupt Pin)
const int ENC_B = 26; // Phase B (Direction Pin)

volatile long count = 0;

void IRAM_ATTR handleEncoder() {
    // Standard Quadrature Phase A vs B Logic
    if (digitalRead(ENC_A) == digitalRead(ENC_B)) {
        count++;
    } else {
        count--;
    }
}

void setup() {
    Serial.begin(115200);
    
    // Setup pins with internal pull-up (Essential for open-drain encoders)
    pinMode(ENC_A, INPUT_PULLUP);
    pinMode(ENC_B, INPUT_PULLUP);
    
    // Attach interrupt to Phase A for every state change
    attachInterrupt(digitalPinToInterrupt(ENC_A), handleEncoder, CHANGE);
    
    Serial.println("--- Single Encoder Test Started ---");
    Serial.println("Spin Motor 1 manually to see counts...");
}

void loop() {
    // Print the absolute count every 100ms
    Serial.print("Encoder Ticks: ");
    Serial.println(count);
    
    delay(100);
}
