# Milestone M1 Analysis: ESP8266 Ping-Pong Command

## 1. Objectives
The objective of Milestone M1 is to update the ESP8266 C++ firmware so that it parses the connection ping command `P\n` over Serial and immediately sends back a connection acknowledgement `P_ACK\n`.

---

## 2. Serial Parsing Logic Analysis
In `Self_Test_Diagnostics/src/main.cpp`, serial communication from the Raspberry Pi is parsed in the function `handleSerialInput()` (lines 10-61):

- **Buffer and Index**:
  - `static char rx_buffer[32]` acts as the receive buffer.
  - `static int rx_index = 0` tracks the position in the buffer.
- **Reading Loop**:
  - The loop checks `Serial.available() > 0` and reads incoming characters.
- **Delimiter Check**:
  - If a delimiter character `\n` or `\r` is encountered, and `rx_index > 0`, the string is null-terminated:
    `rx_buffer[rx_index] = '\0';`
  - It then attempts to match the command prefix.
  - After processing, `rx_index` is reset to `0` (line 55).
- **Buffering**:
  - Any non-delimiter characters are buffered as long as `rx_index < 31`.

### Command Matching Flow
Currently, the matching is done via prefix matching using `strncmp`:
- `M:<left>,<right>\n` matches `strncmp(rx_buffer, "M:", 2) == 0`.
- `A:<val>\n` matches `strncmp(rx_buffer, "A:", 2) == 0`.
- `C:<val>\n` matches `strncmp(rx_buffer, "C:", 2) == 0`.

---

## 3. Proposed Modification for Ping-Pong (`P\n` -> `P_ACK\n`)
When the Raspberry Pi sends `P\n`, the character `'P'` is placed into `rx_buffer[0]` and `rx_index` becomes `1`. When `\n` is read, the buffer is null-terminated at `rx_buffer[1] = '\0'`. The buffer content to match is exactly `"P"`.

### Design Decisions:
1. **Unconditional Handling**:
   The ping command is a connection status probe used by the TUI to determine if the hardware link is active. It does not control motor speeds or mode changes. Thus, it should be processed **unconditionally**, regardless of the states of `g_auto_mode` and `g_armed`.
2. **Matching Strategy**:
   Using `strcmp(rx_buffer, "P") == 0` is the cleanest and safest matching strategy, avoiding false matches with hypothetical longer commands starting with `P`.
3. **Response Method**:
   Upon matching, we print the response immediately back to Serial using `Serial.print("P_ACK\n");`. Using `print` with explicit newline ensures we output exactly `P_ACK\n`.

---

## 4. Target Files and Modifications

### File 1: `Self_Test_Diagnostics/src/main.cpp`
We propose adding the matching branch in `handleSerialInput()` right after checking for `C:`.

**Before (Lines 49-55)**:
```cpp
                } else if (strncmp(rx_buffer, "C:", 2) == 0) {
                    int mode_val = 0;
                    if (sscanf(rx_buffer + 2, "%d", &mode_val) == 1) {
                        g_auto_mode = (mode_val != 0);
                    }
                }
                rx_index = 0;
```

**After**:
```cpp
                } else if (strncmp(rx_buffer, "C:", 2) == 0) {
                    int mode_val = 0;
                    if (sscanf(rx_buffer + 2, "%d", &mode_val) == 1) {
                        g_auto_mode = (mode_val != 0);
                    }
                } else if (strcmp(rx_buffer, "P") == 0) {
                    Serial.print("P_ACK\n");
                }
                rx_index = 0;
```

---

## 5. Affected Files & Unit Testing
No dependencies are negatively affected. However, to ensure correctness and prevent regressions, we should update the mock unit test suite.

### File 2: `Self_Test_Diagnostics/test/test_firmware.cpp`
We propose adding a unit test function `run_test_ping_pong()` to verify the behavior of `P\n` parsing and response.

**New Test Function**:
```cpp
void run_test_ping_pong() {
    std::cout << "[TEST] Running Ping-Pong Command Tests..." << std::endl;
    
    Serial.clear();
    Serial.feed("P\n");
    handleSerialInput();
    
    if (Serial.tx_buffer.str() != "P_ACK\n") {
        std::cerr << "  FAIL: Ping command did not respond with P_ACK\\n! Got: "
                  << Serial.tx_buffer.str() << std::endl;
        exit(1);
    }
    std::cout << "  PASS: Ping command correctly responded with P_ACK\\n." << std::endl;
}
```

We will call this function in `main()` of `test_firmware.cpp` (inserted around line 161).

---

## 6. Machine-Applyable Patch
A unified diff patch has been written to:
`/Users/roopalisingh/DPSI-LFR/.agents/explorer_m1_3/m1_ping_pong.patch`
