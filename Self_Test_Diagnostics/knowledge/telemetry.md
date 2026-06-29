# Technical Blueprint: IR Sensor Array Telemetry & Data Serialization Architecture

## 1. Subsystem Overview

The telemetry subsystem collects digital reflectance data from a 10-sensor TCRT5000 infrared (IR) array positioned at the front of the robot chassis. This data provides the core perception stream needed to evaluate line tracking precision, sensor calibration, and surface contrast. 

To transmit this raw sensor state over Wi-Fi to the diagnostic web dashboard without exceeding network bandwidth or causing memory allocation overhead on the ESP32-S3, the telemetry pipeline packages sensor readings into compact 10-bit bitmasks and structured JSON frames broadcast at a rate of 20 Hz ($50\text{ ms}$ sample period).

---

## 2. Hardware Mapping & IR Sensor Array Architecture

### 2.1 TCRT5000 Sensor Topology
The TCRT5000 sensor module integrates an infrared emitting diode and a phototransistor. When positioned over a reflective surface (e.g., white floor), IR light is reflected back, pulling the comparator output LOW (`0`). When positioned over a non-reflective surface (e.g., black track line), IR light is absorbed, driving the digital output HIGH (`1`).

```
Physical Layout (Front View, Facing Motion):
+-----------------------------------------------------------------------------------+
| [IR1]  [IR2]  [IR3]  [IR4]  [IR5]  [IR6]  [IR7]  [IR8]  [IR9]  [IR10]             |
| FarL    <---      Left Center       --->       Right Center     --->   FarR       |
+-----------------------------------------------------------------------------------+
```

### 2.2 Microcontroller GPIO Allocation
The 10 TCRT5000 digital signals are routed directly to high-speed GPIO pins on the ESP32-S3:

| Sensor Label | Spatial Position | ESP32-S3 Pin | Bit Mask Index | Bit Value (2^N) |
| :--- | :--- | :---: | :---: | :---: |
| **`PIN_IR_1`** | Far Left | GPIO 1 | Bit 0 | 1 |
| **`PIN_IR_2`** | Left Outer | GPIO 2 | Bit 1 | 2 |
| **`PIN_IR_3`** | Left Mid-Outer | GPIO 4 | Bit 2 | 4 |
| **`PIN_IR_4`** | Left Mid-Inner | GPIO 5 | Bit 3 | 8 |
| **`PIN_IR_5`** | Center Left | GPIO 6 | Bit 4 | 16 |
| **`PIN_IR_6`** | Center Right | GPIO 7 | Bit 5 | 32 |
| **`PIN_IR_7`** | Right Mid-Inner | GPIO 15 | Bit 6 | 64 |
| **`PIN_IR_8`** | Right Mid-Outer | GPIO 16 | Bit 7 | 128 |
| **`PIN_IR_9`** | Right Outer | GPIO 17 | Bit 8 | 256 |
| **`PIN_IR_10`**| Far Right | GPIO 18 | Bit 9 | 512 |

---

## 3. Sampling Scheme & Bitmask Construction

### 3.1 10-Bit Bitmask Assembly Logic
Rather than processing 10 separate boolean variables, the digital state of the entire array is sampled simultaneously and consolidated into a single unsigned 16-bit integer (`uint16_t`). 

#### Bitmask Mathematical Formula
$$\text{Bitmask} = \sum_{n=0}^{9} \left( D_n \ll n \right)$$
Where $D_n \in \{0, 1\}$ represents the digital read state of sensor $n+1$.

#### Explicit Assembly Operation
```c
uint16_t bitmask = 0;
bitmask |= (digitalRead(PIN_IR_1)  << 0);
bitmask |= (digitalRead(PIN_IR_2)  << 1);
bitmask |= (digitalRead(PIN_IR_3)  << 2);
bitmask |= (digitalRead(PIN_IR_4)  << 3);
bitmask |= (digitalRead(PIN_IR_5)  << 4);
bitmask |= (digitalRead(PIN_IR_6)  << 5);
bitmask |= (digitalRead(PIN_IR_7)  << 6);
bitmask |= (digitalRead(PIN_IR_8)  << 7);
bitmask |= (digitalRead(PIN_IR_9)  << 8);
bitmask |= (digitalRead(PIN_IR_10) << 9);
```

### 3.2 Boolean Array Conversion Strategy
On the receiving client side (or for localized diagnostic evaluation), the 10-bit integer bitmask is rapidly unpacked into a 10-element boolean array using bitwise extraction mask operations (`(bitmask >> n) & 0x01`):

```
Bitmask (e.g., 768 / 0x0300 in Binary):
+---+---+---+---+---+---+---+---+---+---+
| 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |  <-- 10-bit binary representation
+---+---+---+---+---+---+---+---+---+---+
 Bit9 Bit8 Bit7 Bit6 Bit5 Bit4 Bit3 Bit2 Bit1 Bit0
 (IR10)(IR9)(IR8)(IR7)(IR6)(IR5)(IR4)(IR3)(IR2)(IR1)
```

---

## 4. JSON Payload Specification & Protocol Framing

### 4.1 Telemetry Broadcast Payload Structure
Telemetry updates are formatted as lightweight JSON objects transmitted over the active WebSocket channel (`ws://192.168.4.1/ws`).

#### JSON Schema
```json
{
  "type": "telemetry",
  "bitmask": 768,
  "sensors": [0, 0, 1, 1, 0, 0, 0, 0, 0, 0]
}
```

#### Field Specifications
- **`type`** (`string`): Identifies packet class (`"telemetry"`). Allows frontend event handlers to route data efficiently.
- **`bitmask`** (`integer`): 10-bit unsigned integer value ($0$ to $1023$). Facilitates low-bandwidth logging and raw bit parsing.
- **`sensors`** (`array of integers`): 10-element explicit array containing binary states (`0` or `1`) ordered strictly from Far Left (`IR1`) to Far Right (`IR10`).

---

## 5. Telemetry Loop Scheduling & Performance Optimization

### 5.1 FreeRTOS Task Scheduling ($20\text{ Hz}$)
The telemetry loop runs inside `TelemetryTask` on Core 1, synchronized by FreeRTOS task delays to achieve a consistent $20\text{ Hz}$ sampling cadence ($50\text{ ms}$ interval):

```
  Time (ms) 0          50         100        150        200
            |----------|----------|----------|----------|
  Execution [Sample+TX] [Sample+TX] [Sample+TX] [Sample+TX]
            <-- 50ms -->
```

### 5.2 Serialization Overhead & Memory Protection
1. **Static Buffer Allocation**: To avoid dynamic memory allocation overhead during high-frequency string formatting, the JSON string generation utilizes static character buffers (`char tele_buf[128]`) or `StaticJsonDocument<256>`.
2. **Non-Blocking WebSocket Broadcast**: Serialization completes on Core 1, and the resulting string is passed to `ws.textAll()` on Core 0. If no clients are connected (`ws.count() == 0`), sampling and serialization execution is bypassed entirely to preserve CPU resources.
