# Analysis and Design Proposal: ESP8266 Ping-Pong Command (Milestone M1)

## Executive Summary
This document presents the design and proposed changes to support the new `P\n` Ping command and `P_ACK\n` Pong response protocol in the ESP8266 firmware (`Self_Test_Diagnostics/src/main.cpp`). It reviews the current serial parser, outlines the code additions, specifies the exact line insertions, proposes corresponding unit test updates, and discusses potential dependencies.

---

## 1. Review of Current Serial Command Parser
In `Self_Test_Diagnostics/src/main.cpp`, serial commands are read non-blockingly from `Serial` in the `handleSerialInput()` function:

1. **Buffering**: 
   - A static buffer `rx_buffer[32]` and index `rx_index` accumulate incoming characters.
   - Buffer overflow protection is implemented: `rx_index < (int)sizeof(rx_buffer) - 1`.

2. **Newline Handling**:
   - The parser checks for delimiter characters `\n` or `\r`.
   - When a delimiter is encountered, the trailing character is replaced with a null byte `\0` if `rx_index > 0`, transforming the buffer into a standard null-terminated C-string.
   - The index is reset: `rx_index = 0`.

3. **Command Matching**:
   - Currently, commands are matched by checking the command header prefix using `strncmp()`:
     - Motor control: `strncmp(rx_buffer, "M:", 2) == 0` (e.g., `M:<left>,<right>\n`)
     - Arm/Disarm: `strncmp(rx_buffer, "A:", 2) == 0` (e.g., `A:<val>\n`)
     - Mode Control: `strncmp(rx_buffer, "C:", 2) == 0` (e.g., `C:<val>\n`)

---

## 2. Proposed Changes for `P\n` Command parsing
When the Raspberry Pi sends `P\n`, the serial parser processes `P` and then `\n`.
The trailing `\n` is stripped, meaning `rx_buffer` will contain exactly `"P"` (length 1).

### A. Match Logic
Since `"P"` is a exact 1-character string command, we will use `strcmp()` to perform an exact string match rather than a prefix match:
```cpp
} else if (strcmp(rx_buffer, "P") == 0) {
    // Handle Ping
}
```

### B. Response Logic
The interface contract requires printing `P_ACK\n` immediately back to Serial.
We will print this exactly by writing:
```cpp
Serial.print("P_ACK\n");
```
Using `Serial.print("P_ACK\n")` is preferred over `Serial.println("P_ACK")` because `Serial.println()` appends `\r\n` (carriage return + newline) on ESP8266, whereas the protocol explicitly requests a single `\n` termination character.

### C. Placement in Code
The change will be added as a new branch in the `if/else if` chain inside `handleSerialInput()` in `Self_Test_Diagnostics/src/main.cpp`.

**Proposed Firmware Diff:**
```diff
--- Self_Test_Diagnostics/src/main.cpp
+++ Self_Test_Diagnostics/src/main.cpp
@@ -52,2 +52,4 @@
                         g_auto_mode = (mode_val != 0);
                     }
+                } else if (strcmp(rx_buffer, "P") == 0) {
+                    Serial.print("P_ACK\n");
                 }
```

---

## 3. Unit Test Additions
To verify that the Ping-Pong command functions correctly, a unit test function `run_test_ping_pong()` will be added to the test suite in `Self_Test_Diagnostics/test/test_firmware.cpp`.

**Proposed Test Suite Diff:**
```diff
--- Self_Test_Diagnostics/test/test_firmware.cpp
+++ Self_Test_Diagnostics/test/test_firmware.cpp
@@ -154,2 +154,16 @@
 }
 
+void run_test_ping_pong() {
+    std::cout << "[TEST] Running Ping-Pong Command Tests..." << std::endl;
+
+    Serial.clear();
+    Serial.feed("P\n");
+    handleSerialInput();
+
+    if (Serial.tx_buffer.str() != "P_ACK\n") {
+        std::cerr << "  FAIL: Ping-Pong command failed! Expected P_ACK\\n, got: " 
+                  << Serial.tx_buffer.str() << std::endl;
+        exit(1);
+    }
+    std::cout << "  PASS: Ping-Pong command responded with P_ACK\\n." << std::endl;
+}
+
 int main() {
@@ -159,2 +173,3 @@
     run_test_uart_scaling_constraints();
+    run_test_ping_pong();
     std::cout << "=== ALL TESTS PASSED SUCCESSFULLY ===" << std::endl;
```

---

## 4. Dependencies and Impact Analysis
- **Firmware Dependencies**: Standard Arduino libraries (specifically `Serial` interface). No external header files or external library additions are required. `strcmp` is a standard built-in C/C++ function available from compiler headers.
- **Affected Files**:
  1. `Self_Test_Diagnostics/src/main.cpp` (firmware entry point and serial handler)
  2. `Self_Test_Diagnostics/test/test_firmware.cpp` (firmware unit tests)
- **Downstream Impact**:
  - The Raspberry Pi TUI dashboard (`rbpi_package/cli.py` and `rbpi_package/hardware.py`) currently operates in mock/static mode without active status validation. Once this change is implemented, Milestone M3 (UART Connection Status) can be built to periodically transmit `P\n` from a background thread every 1s and update the dashboard status badge dynamically based on receipt of `P_ACK\n` within a 500ms timeout window.
