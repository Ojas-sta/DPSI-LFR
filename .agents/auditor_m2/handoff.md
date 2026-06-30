# Forensic Audit & Handoff Report - Milestone M2 Audit

## Forensic Audit Report

**Work Product**: rbpi_package/cli.py, rbpi_package/hardware.py, rbpi_package/test_hardware.py
**Profile**: General Project
**Verdict**: CLEAN

### Phase Results
- [Source Code Analysis]: PASS — Checked for hardcoded test results, facade implementations, and pre-populated artifacts. Found no cheating patterns.
- [Behavioral Verification - Build & Run]: PASS — Successfully compiled Python source files and successfully ran unit tests with all 6 passing.
- [Dependency Audit]: PASS — Maintained correct standard and third-party library boundaries. No core work delegated to external pre-built solutions.

---

## 1. Observation

- **Target Files**:
  - `rbpi_package/cli.py`
  - `rbpi_package/hardware.py`
  - `rbpi_package/test_hardware.py`
- **Unit Tests Execution**:
  - Command: `python3 -m unittest test_hardware.py` in `rbpi_package`
  - Result:
    ```
    Ran 6 tests in 0.003s

    OK
    ```
- **Compilation Check**:
  - Command: `python3 -m py_compile rbpi_package/cli.py rbpi_package/hardware.py` in repository root
  - Result: Completed successfully with 0 errors (exit code 0).
- **Source Code Inspections**:
  - `rbpi_package/test_hardware.py` uses `unittest.mock.MagicMock` and `patch` to mock `serial` module calls and check method/write calls. For example:
    - Line 50: `mock_port.write.assert_called_with(b"M:0.5123,-0.6789\n")`
    - Line 54: `mock_port.write.assert_called_with(b"M:1.0000,-1.0000\n")`
  - `rbpi_package/hardware.py` features a real serial implementation:
    - Port scanning loop over `/dev/serial0` and `/dev/ttyUSB0` (Lines 37-49).
    - Background thread `run_serial_reader` sending ping `P\n` heartbeats every 1.0 second and reading non-blocking lines (Lines 69-124).
    - Proper synchronization using `serial_lock` and `telemetry_lock` (Lines 16-17, 80, 94, 104, 127, 181, 201, 221, 240).
    - Active connection monitoring: `self.is_connected = (time.time() - self.last_pong_time) < 2.5` (Line 121).
  - `rbpi_package/cli.py` implements a curses TUI:
    - Centered ASCII art display (`load_ascii_art`, Lines 10-21, and drawing at Lines 174-184).
    - Color configuration with `curses.init_pair` for blue-purple theme, speed green/red rendering, and connection status badge (Lines 130-138).
    - Speed cap adjustments via keys `[` and `]` (Lines 379-385).
    - Non-blocking keyboard input loop reading user keypresses (Line 143, Line 347).
    - Port toggling between `/dev/serial0` and `/dev/ttyUSB0` (Lines 425-428).

## 2. Logic Chain

1. **Cheating & Hardcoding Check**: The test code in `test_hardware.py` mocks serial traffic and asserts that correct byte commands are written to the serial interface. The implementation code in `hardware.py` uses math clamping (`max(-1.0, min(1.0, ...))`) and formatting (`:.4f`) to generate command strings dynamically. No hardcoded results or cheats bypass tests.
2. **Correctness & Genuineness of Features**:
   - **TUI & UI Elements**: `cli.py` successfully initializes `curses` settings (color pairs 1-6 for blue/magenta theme, green/red speed text, etc.) and draws a responsive chassis visualization via `draw_chassis`.
   - **Locks**: Lock objects `serial_lock` and `telemetry_lock` wrap all concurrent serial and logging operations across threads.
   - **Thread Reads**: The background daemon reader thread executes non-blocking `readline()` reads and manages the 10-line telemetry buffer.
   - **Heartbeats**: The background loop issues `P\n` and updates connection flags based on `P_ACK` responses.
   - **Port Switching**: Toggling switches the active device name and closes/re-opens serial ports dynamically.
3. **Test Passing & Compilation**: Empirical execution of `unittest` and `py_compile` confirmed zero failures and compilation errors.

## 3. Caveats

- Testing was performed on a machine simulating the serial interface (using mock modes built into `hardware.py` and mocks in tests). Physical UART hardware execution (e.g. raw gpiozero LED outputs and `/dev/serial0` hardware ports) was mocked or bypassed via fallback modes when running the tests.

## 4. Conclusion

The work products (`cli.py`, `hardware.py`, `test_hardware.py`) are **CLEAN** of any integrity violations under Development, Demo, and Benchmark modes. The implementation is genuine, and all verification checks (compilation, unit testing) passed successfully.

## 5. Verification Method

- To verify compilation:
  `python3 -m py_compile rbpi_package/cli.py rbpi_package/hardware.py`
- To verify unit tests:
  `python3 -m unittest test_hardware.py` (executed from within the `rbpi_package` directory)
