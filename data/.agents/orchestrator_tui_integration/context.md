# Context: TUI and Firmware Integration

## Requirements Summary (from 2026-06-30T20:08:11+05:30)
- **R1 (TUI Overhaul)**: Implement blue/purple themed `curses` interface in `rbpi_package/cli.py`. Display centered `ascii-art.txt` at the top. 3-wheel differential ASCII chassis visualization (2 rear wheels + 1 front caster). Real-time motor speeds next to wheels (color-coded: green for forward, red for reverse). Key binds for speed caps, toggling LEDs/Buzzer, switching serial ports.
- **R2 (UART Connectivity & Monitor)**: Background thread to read non-blocking serial lines in `cli.py` / `hardware.py` and display in scrolling "Serial Monitor" box (last 10 lines). Default serial connection to `/dev/serial0` (UART), but toggleable to `/dev/ttyUSB0` via UI. Continuous `P\n` pinging to ESP with status badge (`CONNECTED` / `DISCONNECTED`).
- **R3 (Motor Node Firmware Update)**: In `Self_Test_Diagnostics/src/main.cpp`, add parsing for `P\n` command and immediately reply with `P_ACK\n` over Serial.

## Codebase Locations
- Raspberry Pi CLI: `rbpi_package/cli.py`
- Raspberry Pi Hardware: `rbpi_package/hardware.py`
- ESP8266 Main source: `Self_Test_Diagnostics/src/main.cpp`
- ASCII Art: `ascii-art.txt`

## Verification Commands
- Python compilation check: `python3 -m py_compile rbpi_package/cli.py`
- ESP8266 compilation check: `pio run` in `Self_Test_Diagnostics`
