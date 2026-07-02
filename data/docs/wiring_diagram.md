# Line Following Robot - Wiring Diagram

## Components List
- **Main Controller**: Raspberry Pi (with Camera)
- **Secondary Controller**: ESP32-S3
- **Motor Driver**: L298N
- **Motors**: 2x N20 DC Motors
- **Power**: 11.1V 2200mAh LiPo Battery (3S)
- **Buck Converter**: LM2596 (HW-411) - for voltage regulation
- **Cooling**: Fan

## Power Distribution

### Battery (11.1V LiPo 3S 2200mAh)
```
Battery (+) ────┬──> L298N (12V input)
                │
                └──> LM2596 Buck Converter Input (+)

Battery (-) ────┴──> Common Ground (GND)
```

### Buck Converter Configuration
**LM2596 Output Settings:**
- **Output 1**: 5V @ 3A → Raspberry Pi + Fan
- **Output 2**: 5V @ 1A → ESP32-S3 (if needed, otherwise use USB)

## Detailed Wiring Connections

### 1. Power Connections

#### LM2596 Buck Converter
```
IN+  ← Battery (+) 11.1V
IN-  ← Battery (-) GND
OUT+ → 5V Rail
OUT- → GND Rail
```

**Adjust the potentiometer on LM2596 to output exactly 5V before connecting components!**

#### L298N Motor Driver
```
+12V  ← Battery (+) 11.1V
GND   ← Battery (-) GND
+5V   ← Do NOT use (keep jumper removed if present)
```

### 2. Raspberry Pi Connections

#### Power
```
Pin 2 (5V)  ← LM2596 OUT+ (5V)
Pin 6 (GND) ← LM2596 OUT- (GND)
```

#### GPIO to L298N Motor Driver
```
Raspberry Pi          L298N
────────────          ─────
GPIO 17 (Pin 11) ──> IN1 (Motor A Direction)
GPIO 27 (Pin 13) ──> IN2 (Motor A Direction)
GPIO 22 (Pin 15) ──> IN3 (Motor B Direction)
GPIO 23 (Pin 16) ──> IN4 (Motor B Direction)

GPIO 12 (Pin 32) ──> ENA (Motor A Speed - PWM)
GPIO 13 (Pin 33) ──> ENB (Motor B Speed - PWM)

Pin 9 (GND)      ──> GND
```

#### Camera Connection
```
Raspberry Pi CSI Camera Port ← Camera Ribbon Cable
```

#### Communication with ESP32-S3 (UART)
```
Raspberry Pi          ESP32-S3
────────────          ────────
GPIO 14 (Pin 8)  ──> RX (GPIO 44)
GPIO 15 (Pin 10) ──> TX (GPIO 43)
Pin 14 (GND)     ──> GND
```

### 3. ESP32-S3 Connections

#### Power
```
5V  ← LM2596 OUT+ (5V) or USB-C
GND ← LM2596 OUT- (GND)
```

#### UART to Raspberry Pi
```
ESP32-S3          Raspberry Pi
────────          ────────────
GPIO 43 (TX) ──> GPIO 14 (RX)
GPIO 44 (RX) ──> GPIO 15 (TX)
GND          ──> GND
```

### 4. L298N Motor Driver to N20 Motors

#### Motor A (Left Motor)
```
L298N          N20 Motor A
─────          ───────────
OUT1      ──> Motor A (+)
OUT2      ──> Motor A (-)
```

#### Motor B (Right Motor)
```
L298N          N20 Motor B
─────          ───────────
OUT3      ──> Motor B (+)
OUT4      ──> Motor B (-)
```

### 5. Fan Connection

```
Fan (+) ← LM2596 OUT+ (5V)
Fan (-) ← LM2596 OUT- (GND)
```

**Note**: If fan draws >500mA, consider adding a MOSFET switch controlled by GPIO

## Complete Wiring Table

| Component | Pin/Terminal | Connects To | Component | Pin/Terminal |
|-----------|--------------|-------------|-----------|--------------|
| **Battery** | (+) | → | **L298N** | +12V |
| **Battery** | (+) | → | **LM2596** | IN+ |
| **Battery** | (-) | → | **All** | GND (Common) |
| | | | | |
| **LM2596** | OUT+ (5V) | → | **Raspberry Pi** | Pin 2 (5V) |
| **LM2596** | OUT+ (5V) | → | **ESP32-S3** | 5V |
| **LM2596** | OUT+ (5V) | → | **Fan** | (+) |
| **LM2596** | OUT- (GND) | → | **All** | GND (Common) |
| | | | | |
| **Raspberry Pi** | GPIO 17 | → | **L298N** | IN1 |
| **Raspberry Pi** | GPIO 27 | → | **L298N** | IN2 |
| **Raspberry Pi** | GPIO 22 | → | **L298N** | IN3 |
| **Raspberry Pi** | GPIO 23 | → | **L298N** | IN4 |
| **Raspberry Pi** | GPIO 12 (PWM) | → | **L298N** | ENA |
| **Raspberry Pi** | GPIO 13 (PWM) | → | **L298N** | ENB |
| **Raspberry Pi** | GPIO 14 (TX) | → | **ESP32-S3** | GPIO 44 (RX) |
| **Raspberry Pi** | GPIO 15 (RX) | → | **ESP32-S3** | GPIO 43 (TX) |
| | | | | |
| **L298N** | OUT1 | → | **Motor A** | (+) |
| **L298N** | OUT2 | → | **Motor A** | (-) |
| **L298N** | OUT3 | → | **Motor B** | (+) |
| **L298N** | OUT4 | → | **Motor B** | (-) |

## Important Notes

### ⚠️ Safety Precautions
1. **Voltage Check**: Always verify LM2596 output is 5V before connecting to Raspberry Pi/ESP32
2. **Polarity**: Double-check battery polarity - reversed connection will damage components
3. **Common Ground**: Ensure all components share a common ground
4. **Battery Protection**: Use a LiPo battery with built-in protection circuit or add a separate BMS
5. **Fuse**: Consider adding a 5A fuse between battery and system

### 🔧 Configuration Steps
1. **Before connecting anything**:
   - Connect LM2596 to battery
   - Adjust output to exactly 5.0V using multimeter
   - Disconnect battery

2. **Assembly order**:
   - Connect all grounds first (common ground)
   - Connect LM2596 and verify 5V output again
   - Connect Raspberry Pi power
   - Connect motor driver power
   - Connect signal wires last

3. **L298N Jumper Settings**:
   - Remove 5V enable jumper if present
   - Keep ENA/ENB jumpers IN for PWM control

### 💡 Power Consumption Estimates
- Raspberry Pi: ~700-900mA (idle), up to 1.5A (peak with camera)
- ESP32-S3: ~80-260mA
- Motors (2x N20): ~300-800mA total (depends on load)
- Fan: ~100-200mA
- **Total**: ~2-3A (ensure LM2596 is rated for 3A)

### 🔋 Battery Runtime
- Battery capacity: 2200mAh
- Average current draw: ~2.5A
- Estimated runtime: ~45-50 minutes

## Testing Procedure

1. **Power Test** (without motors):
   - Connect battery to LM2596 only
   - Verify 5V output
   - Connect Raspberry Pi
   - Verify boot and camera function

2. **Motor Test**:
   - Connect one motor at a time
   - Test direction and speed control
   - Check for overheating

3. **Full System Test**:
   - Run line following algorithm
   - Monitor temperature
   - Check battery voltage regularly

## Troubleshooting

| Problem | Possible Cause | Solution |
|---------|---------------|----------|
| Pi won't boot | Insufficient voltage | Check LM2596 output, verify 5V |
| Motors don't move | No PWM signal | Check GPIO connections and code |
| Motors run backward | Reversed polarity | Swap motor wires or change code |
| System resets randomly | Voltage drop from motors | Add capacitor (1000µF) across motor driver input |
| Overheating | Insufficient cooling | Reposition fan, add heatsinks |

## Optional Improvements

1. **Add voltage monitoring**: Connect battery voltage divider to ESP32-S3 ADC
2. **Emergency stop**: Add physical button to GPIO with pull-up resistor
3. **Status LEDs**: Add RGB LED for system status indication
4. **Capacitor**: 1000µF capacitor across battery terminals for current spike protection
