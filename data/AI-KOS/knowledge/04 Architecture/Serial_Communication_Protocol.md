# Serial Communication Protocol Specification

## 1. System Overview
The DPSI-LFR V2 robotics platform utilizes a bi-directional asynchronous full-duplex serial communication link between the primary computer vision processor (Raspberry Pi 4B) and the real-time microcontroller (ESP32-S3). The physical interface operates over USB Serial (`/dev/ttyUSB0` on Raspberry Pi 4B mapped to UART0 `GPIO43/GPIO44` on ESP32-S3) at a baud rate of **115,200 baud**, 8 data bits, no parity, and 1 stop bit (8N1).

---

## 2. Packet Framing Architecture

All transmission units are formatted as binary structured frames. Binary encoding ensures minimal latency, zero string parsing overhead, and high-frequency deterministic throughput.

### 2.1 Binary Packet Frame Layout

| Byte Offset | Field Name | Data Type | Size (Bytes) | Description / Valid Values |
| :--- | :--- | :--- | :--- | :--- |
| `0x00` | **Header Byte 1** | `uint8_t` | 1 | Fixed Synchronization Byte 1: `0xAA` |
| `0x01` | **Header Byte 2** | `uint8_t` | 1 | Fixed Synchronization Byte 2: `0x55` |
| `0x02` | **Sequence ID** | `uint8_t` | 1 | Rolling packet counter (`0x00` to `0xFF`) for drop detection |
| `0x03` | **Opcode** | `uint8_t` | 1 | Command or Telemetry Identifier (See Opcode Table) |
| `0x04` | **Payload Length ($N$)**| `uint8_t` | 1 | Length of following payload field in bytes ($0 \le N \le 32$) |
| `0x05` to `0x05+N-1`| **Payload Data** | `uint8_t[]` | $N$ | Command-specific parameter bytes (Little-Endian) |
| `0x05+N` | **CRC16 Low Byte** | `uint8_t` | 1 | CRC-16-CCITT lower byte computed over bytes `0x02` to `0x04+N` |
| `0x06+N` | **CRC16 High Byte**| `uint8_t` | 1 | CRC-16-CCITT upper byte |

---

### 2.2 Frame Verification & CRC-16 Algorithm
The frame integrity is validated using the standard **CRC-16-CCITT** polynomial ($X^{16} + X^{12} + X^5 + 1$, seed `0xFFFF`). The calculation includes the Sequence ID, Opcode, Payload Length, and all Payload bytes.

```
Example Frame Representation (SET_MOTOR_SPEEDS: Left=150, Right=150):
[ 0xAA | 0x55 | 0x12 | 0x01 | 0x04 | 0x96 0x00 0x96 0x00 | 0x4B 0xA2 ]
  Header       Seq    Op    Len    Payload (16-bit int)   CRC16
```

---

## 3. Comprehensive Opcodes & Payload Register Table

### 3.1 Commands (Raspberry Pi 4B $\to$ ESP32-S3)

| Opcode (Hex) | Opcode Name | Direction | Payload Length ($N$) | Payload Breakdown / Structure | Description / Functionality |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `0x01` | `SET_MOTOR_SPEEDS` | Pi $\to$ ESP | 4 Bytes | `int16_t left_pwm`<br>`int16_t right_pwm` | Direct manual override of wheel PWM duty cycles ($-255$ to $+255$). Suspends line-following PID. |
| `0x02` | `EXECUTE_TURN_90` | Pi $\to$ ESP | 1 Byte | `uint8_t direction`<br>(`0x01`=Left, `0x02`=Right) | Triggers precision IMU-guided 90-degree closed-loop pivot turn on ESP32 Core 0/1. |
| `0x03` | `EXECUTE_TURN_180` | Pi $\to$ ESP | 0 Bytes | None | Triggers 180-degree U-turn maneuver using MPU6050 feedback. |
| `0x04` | `SET_PID_GAINS` | Pi $\to$ ESP | 12 Bytes | `float kp`<br>`float ki`<br>`float kd` | Dynamically updates line-following PID gain parameters in ESP32 Flash/RAM. |
| `0x05` | `SET_MODE` | Pi $\to$ ESP | 1 Byte | `uint8_t mode`<br>(`0`=Standby, `1`=LineFollow, `2`=Manual) | Changes executive operational state on ESP32 firmware. |
| `0x0A` | `HEARTBEAT_PING` | Pi $\to$ ESP | 1 Byte | `uint8_t status_flags` | Sent periodically (every 200ms) to reset hardware safety watchdog. |
| `0xFF` | `EMERGENCY_STOP` | Pi $\to$ ESP | 0 Bytes | None | High-priority immediate override. Cuts power to L298N outputs ($PWM=0$). |

---

### 3.2 Telemetry & Acknowledgments (ESP32-S3 $\to$ Raspberry Pi 4B)

| Opcode (Hex) | Opcode Name | Direction | Payload Length ($N$) | Payload Breakdown / Structure | Description / Functionality |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `0x81` | `REPORT_TELEMETRY` | ESP $\to$ Pi | 10 Bytes | `uint16_t ir_raw_bitmask`<br>`float integrated_yaw`<br>`int16_t current_error` | Continuous telemetry packet broadcast by ESP32 at 20 Hz. |
| `0x82` | `TURN_COMPLETE` | ESP $\to$ Pi | 2 Bytes | `uint8_t turn_type`<br>`uint8_t status_code` | Dispatched when closed-loop IMU turn reaches within $\pm 0.5^\circ$ deadband. |
| `0x8A` | `HEARTBEAT_PONG` | ESP $\to$ Pi | 2 Bytes | `uint16_t system_uptime_sec` | Echo response confirming ESP32 health and core task activity. |
| `0xFE` | `ACK_COMMAND` | ESP $\to$ Pi | 2 Bytes | `uint8_t rx_seq_id`<br>`uint8_t rx_opcode` | Acknowledges valid receipt and queuing of a command packet. |
| `0xFF` | `ERROR_REPORT` | ESP $\to$ Pi | 2 Bytes | `uint8_t error_code`<br>`uint8_t detail_code` | Sent on CRC failure (`0x01`), watchdog timeout (`0x02`), or I2C bus stall (`0x03`). |

---

## 4. Handshake, Heartbeat, and Error Recovery Protocols

### 4.1 Connection Handshake Sequence
Upon bootup or serial port reconnect, the Raspberry Pi 4B and ESP32-S3 execute a 3-way handshake to synchronize state registers before motor movement is permitted.

```
Raspberry Pi 4B                                              ESP32-S3
      |                                                          |
      | -------- OP_SET_MODE(Standby, Seq=0x01) ------------->   |  (Verify CRC)
      |                                                          |
      | <------- OP_ACK_COMMAND(Seq=0x01) --------------------   |  (State = Standby)
      |                                                          |
      | -------- OP_HEARTBEAT_PING(Seq=0x02) ---------------->   |
      |                                                          |
      | <------- OP_HEARTBEAT_PONG(Seq=0x02) -----------------   |  (Connection Synchronized)
      |                                                          |
      | -------- OP_SET_MODE(LineFollow, Seq=0x03) ------------>   |
      |                                                          |
      | <------- OP_ACK_COMMAND(Seq=0x03) --------------------   |  (Engage Control Loop)
```

---

### 4.2 Watchdog Heartbeat & Safety Timeout Mechanism

To guarantee physical safety in autonomous operation, the ESP32-S3 firmware implements a hardware safety watchdog within `Task_LineFollow_PID`.

```
                    +--------------------------------+
                    | Serial Packet Received by ESP32|
                    +---------------+----------------+
                                    |
                                    v
                    Reset g_last_packet_timer = millis()
                                    |
                                    v
                 +--------------------------------------+
                 | Every 10ms Loop Check:               |
                 | (millis() - g_last_packet_timer) > 500ms? |
                 +------------------+-------------------+
                                    |
                          +---------+---------+
                          | Yes               | No
                          v                   v
              +-----------------------+   Continue Normal
              | Trigger Safety Halt!  |   Execution Loop
              | Set PWM_L=0, PWM_R=0  |
              | Transmit ERROR_REPORT |
              +-----------------------+
```

1. **Ping Frequency**: The Raspberry Pi 4B transmits an `OP_HEARTBEAT_PING` packet every **200 ms**.
2. **Watchdog Threshold**: If the ESP32-S3 does not receive a valid CRC-verified serial packet for **500 ms** (due to Pi program crash, cable disconnection, or OS freeze), the system automatically aborts active navigation, disables motor drivers ($PWM = 0$), and flashes `EMERGENCY_STOP` on the OLED telemetry display.

---

### 4.3 Frame Corruption & Error Recovery Protocol
1. **Header Byte Alignment**: If the receiver byte parser encounters a byte other than `0xAA` while searching for frame start, the byte is discarded. If `0xAA` is found but the next byte is not `0x55`, the parser resets to header-search state.
2. **CRC Verification Failure**: If a received frame fails CRC validation, the receiving node discards the frame, increments an internal `corrupt_packet_counter`, and transmits an `ERROR_REPORT` packet (`error_code = 0x01`) back to the sender containing the rejected Sequence ID.
3. **Retransmission**: The sender maintains a 1-element unacknowledged packet buffer. If no `ACK_COMMAND` is received within **50 ms** for critical control packets (`EXECUTE_TURN_90`), the packet is retransmitted up to 3 times before declaring a link failure.
