# Milestone M1 Analysis: ESP8266 Ping-Pong Command

## 1. Executive Summary
This document analyzes the requirements for Milestone M1 of the project, details the current serial communication logic in the ESP8266 diagnostics firmware, and proposes the concrete design changes and verification tests necessary to implement a ping-pong serial command.

- **Milestone**: M1 (ESP8266 Ping-Pong Command)
- **Goal**: Update the ESP8266 firmware to parse the command `P\n` over Serial and immediately respond with `P_ACK\n`.
- **Primary Files Affected**: 
  - `Self_Test_Diagnostics/src/main.cpp` (Main firmware entry and serial parsing loop)
  - `Self_Test_Diagnostics/test/test_firmware.cpp` (Unit tests verifying firmware features)
- **Dependencies & Inter-component Impact**: No other hardware or software dependencies are negatively affected. Raspberry Pi-side files (`rbpi_package/hardware.py` and `rbpi_package/cli.py`) do not currently refer to `P\n` or `P_ACK\n`, meaning adding this parser case is backward-compatible. This serves as a prerequisite for Milestone M3 (UART Connection Status tracking on Pi).

---

## 2. Technical Findings

### 2.1 Current Serial Command Handling
In `Self_Test_Diagnostics/src/main.cpp`, the `handleSerialInput()` function processes serial data:
- **Loop**: It runs inside a non-blocking `while (Serial.available() > 0)` loop inside `loop()`.
- **Buffer**: Characters are read one-by-one and placed into `static char rx_buffer[32]`. Index tracking is managed via `static int rx_index`.
- **Overflow Prevention**: Characters are only appended if `rx_index < 31` (leaving 1 slot for null termination).
- **Line Ending Handling**: The parser triggers parsing when a newline character `\n` or carriage return `\r` is encountered.
  - If a terminator is received and `rx_index > 0`, the buffer is null-terminated: `rx_buffer[rx_index] = '\0'`.
  - Crucially, the terminator characters `\n` and `\r` themselves are **never** stored in `rx_buffer`.
  - After processing, `rx_index` is reset to `0`.
- **Matching Protocol**: Prefix matching is used via `strncmp()` for commands with arguments:
  - `"M:"` (Motor control speed scaling)
  - `"A:"` (Arm/Disarm state)
  - `"C:"` (Auto/Manual mode select)

### 2.2 Ping-Pong Design Analysis
- **Input representation**: Because the line end delimiters (`\n` and `\r`) are stripped and never added to the buffer, when the Raspberry Pi sends `P\n`, the buffer `rx_buffer` will contain precisely the string `"P"` with null terminator `\0` at index `1`.
- **Parsing logic**: To detect this command, we perform an exact string match using `strcmp(rx_buffer, "P") == 0`.
- **Mode Independence**: Unlike motor commands, the Ping command is system-wide and does not depend on the auto/manual mode `g_auto_mode` or the armed state `g_armed`. The ESP8266 should always reply, indicating connection status.
- **Output response**: On receipt of `P`, the firmware must transmit `P_ACK\n` immediately. We can print this using the standard Arduino output method `Serial.println("P_ACK");`, which appends the line delimiter.

---

## 3. Proposed Modifications

### 3.1 Modification to `Self_Test_Diagnostics/src/main.cpp`
Add an `else if` branch to match `"P"` exactly and reply with `"P_ACK"`.

#### Snippet Match
**Before:**
```cpp
                } else if (strncmp(rx_buffer, "C:", 2) == 0) {
                    int mode_val = 0;
                    if (sscanf(rx_buffer + 2, "%d", &mode_val) == 1) {
                        g_auto_mode = (mode_val != 0);
                    }
                }
                rx_index = 0;
```

**After:**
```cpp
                } else if (strncmp(rx_buffer, "C:", 2) == 0) {
                    int mode_val = 0;
                    if (sscanf(rx_buffer + 2, "%d", &mode_val) == 1) {
                        g_auto_mode = (mode_val != 0);
                    }
                } else if (strcmp(rx_buffer, "P") == 0) {
                    Serial.println("P_ACK");
                }
                rx_index = 0;
```

---

### 3.2 Modification to `Self_Test_Diagnostics/test/test_firmware.cpp`
Introduce a test function `run_test_ping_pong()` and invoke it from `main()`.

#### Snippet Match
**Before `main` (around line 156):**
```cpp
int main() {
    std::cout << "=== ESP8266 FIRMWARE VERIFICATION START ===" << std::endl;
    run_test_safety_overrides();
    run_test_auto_mode();
    run_test_uart_scaling_constraints();
    std::cout << "=== ALL TESTS PASSED SUCCESSFULLY ===" << std::endl;
    return 0;
}
```

**After:**
```cpp
void run_test_ping_pong() {
    std::cout << "[TEST] Running Ping-Pong Command Tests..." << std::endl;

    // Reset mock serial state
    Serial.clear();

    // Feed "P\n" over the mock serial interface
    Serial.feed("P\n");
    handleSerialInput();

    // Verify response written to Serial Tx
    std::string output = Serial.tx_buffer.str();
    if (output != "P_ACK\n") {
        std::cerr << "  FAIL: Expected \"P_ACK\\n\", got \"" << output << "\"" << std::endl;
        exit(1);
    }
    std::cout << "  PASS: Serial ping 'P\\n' responded with 'P_ACK\\n'." << std::endl;
}

int main() {
    std::cout << "=== ESP8266 FIRMWARE VERIFICATION START ===" << std::endl;
    run_test_safety_overrides();
    run_test_auto_mode();
    run_test_uart_scaling_constraints();
    run_test_ping_pong();
    std::cout << "=== ALL TESTS PASSED SUCCESSFULLY ===" << std::endl;
    return 0;
}
```

---

## 4. Verification and Validation Plan
1. **Compilation**: Compile the firmware tests using `g++ -std=c++17 -Isrc -Itest test/test_firmware.cpp test/mock_arduino.cpp src/Motors.cpp src/WebDiagnostics.cpp src/main.cpp -o test_firmware`.
2. **Execution**: Run `./test_firmware` and ensure it outputs `PASS: Serial ping 'P\n' responded with 'P_ACK\n'.` alongside the other passes.
3. **PlatformIO Integration**: Build target via platformio tool chain (if hardware is attached) to verify it compiles under the `esp8266_diagnostics` PlatformIO configuration.
