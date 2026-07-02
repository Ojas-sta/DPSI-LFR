# Handoff Report — Milestone M1 Exploration

This handoff contains the observation, logic chain, caveats, conclusion, and verification method for Milestone M1 (ESP8266 Ping-Pong Command).

---

## 1. Observation
- **Project Scope (from `PROJECT.md`)**:
  - Line 10: `- Ping Command: P\n`
  - Line 11: `- Pong Command: P_ACK\n`
  - Line 42: `- P\n: Connection ping, no arguments.`
  - Line 43: `- P_ACK\n: Connection acknowledgement, sent by ESP8266 immediately on receipt of P\n.`
- **Serial Input Processing (from `Self_Test_Diagnostics/src/main.cpp`)**:
  - `handleSerialInput()` uses a static buffer `rx_buffer` of size 32:
    ```cpp
    10: void handleSerialInput() {
    11:     static char rx_buffer[32];
    12:     static int rx_index = 0;
    ```
  - Trailing `\n` and `\r` are stripped by termination:
    ```cpp
    16:         if (c == '\n' || c == '\r') {
    17:             if (rx_index > 0) {
    18:                 rx_buffer[rx_index] = '\0';
    ```
  - Command branching is performed via:
    ```cpp
    21:                 if (strncmp(rx_buffer, "M:", 2) == 0) {
    ...
    40:                 } else if (strncmp(rx_buffer, "A:", 2) == 0) {
    ...
    49:                 } else if (strncmp(rx_buffer, "C:", 2) == 0) {
    ```
- **Firmware Mock Testing (from `Self_Test_Diagnostics/test/mock_arduino.h`)**:
  - The `Serial` class is mocked to expose a `tx_buffer` and allow feeding input:
    ```cpp
    64: class SerialMock {
    ...
    80:     void print(const char* s) { tx_buffer << s; }
    ...
    105:     void feed(const std::string& data) {
    106:         rx_buffer += data;
    107:     }
    ```
- **Compiling and Running Unit Tests**:
  - In `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics/test`, the test command:
    `g++ -O3 -Wall -std=c++17 -o test_runner_bin test_firmware.cpp mock_arduino.cpp ../src/Motors.cpp ../src/WebDiagnostics.cpp ../src/main.cpp -I../src -I. && ./test_runner_bin`
  - Runs successfully with output:
    ```
    === ESP8266 FIRMWARE VERIFICATION START ===
    [TEST] Running Safety Override (g_armed = false) Tests...
      PASS: Direct speed commands forced to 0 when disarmed.
      PASS: UART commands forced to 0 when disarmed.
      PASS: WebSocket commands forced to 0 when disarmed.
    [TEST] Running Auto/Manual Mode Toggling Tests...
      PASS: UART commands ignored in MANUAL mode.
      PASS: WebSocket commands processed in MANUAL mode.
      PASS: UART commands processed in AUTO mode.
      PASS: WebSocket commands ignored in AUTO mode.
    [TEST] Running UART Scaling & Constraint Clamping Tests...
      PASS: Float commands correctly scaled by 255.0f and clamped to [-255, 255].
    === ALL TESTS PASSED SUCCESSFULLY ===
    ```

---

## 2. Logic Chain
1. Based on the serial parser behavior (Observation, `Self_Test_Diagnostics/src/main.cpp:16-18`), sending `P\n` results in the delimiter `\n` being stripped.
2. Therefore, when the newline or return character triggers evaluation, the null-terminated `rx_buffer` will contain precisely the characters before `\n`, which is the string `"P"`.
3. To match `"P"` exactly, we cannot use prefix matching like `strncmp(rx_buffer, "P:", 2) == 0` because there is no `:` parameter delimiter. Instead, we should check for exact equality using `strcmp(rx_buffer, "P") == 0`.
4. Once matched, the ESP8266 must write the `P_ACK\n` response back (Observation, `PROJECT.md:43`).
5. Writing `Serial.print("P_ACK\n")` is selected instead of `Serial.println("P_ACK")` because `Serial.println` appends a carriage return `\r` on ESP8266 (`\r\n`), whereas the interface contract specifies exactly `P_ACK\n`.
6. To test this command, a corresponding test case `run_test_ping_pong()` should be defined in `Self_Test_Diagnostics/test/test_firmware.cpp` feeding `P\n` and asserting that `Serial.tx_buffer` receives exactly `P_ACK\n`.

---

## 3. Caveats
- No physical hardware testing was done as this is a read-only investigation.
- It is assumed that the serial sender on the Raspberry Pi uses standard serial encoding and parses lines terminated with `\n` correctly (this is standard in PySerial).

---

## 4. Conclusion
To implement Milestone M1:
1. Modify `Self_Test_Diagnostics/src/main.cpp` by adding a string match for `"P"` using `strcmp` in the `handleSerialInput()` control block, immediately printing `"P_ACK\n"` using `Serial.print`.
2. Add a verification case to `Self_Test_Diagnostics/test/test_firmware.cpp` within the unit tests to mock-feed `"P\n"` and confirm that `"P_ACK\n"` is outputted in the mock serial transmitter buffer.

---

## 5. Verification Method
After implementation, the implementer can run the following sequence to compile and run tests:
1. Navigate to `/Users/roopalisingh/DPSI-LFR/Self_Test_Diagnostics/test`.
2. Run the compilation and test command:
   ```bash
   g++ -O3 -Wall -std=c++17 -o test_runner_bin test_firmware.cpp mock_arduino.cpp ../src/Motors.cpp ../src/WebDiagnostics.cpp ../src/main.cpp -I../src -I. && ./test_runner_bin
   ```
3. Check the command output to ensure `PASS: Ping-Pong command responded with P_ACK\n.` is printed and the program exits with code `0`.
