## 2026-06-30T14:43:25Z
/goal

Investigate and propose changes for Milestone 2: Curses TUI and Serial Connection.

Active Requirements:
1. TUI Overhaul (`rbpi_package/cli.py`):
   - Implement a blue/purple themed curses interface.
   - Read and render the contents of `ascii-art.txt` at the top (centered).
   - Display a detailed 3-wheel differential ASCII chassis (2 rear wheels + 1 front caster).
   - Show real-time motor speeds directly next to the rear wheels, color-coded in green (forward, positive values) and red (reverse, negative values).
   - Keyboard controls:
     - Setting speed caps using `[` and `]` keys (10% steps, from 10% to 100%).
     - Toggling LEDs/Buzzer.
     - Switching/toggling serial ports between `/dev/serial0` and `/dev/ttyUSB0`.
2. UART Connectivity & Monitor (`rbpi_package/hardware.py` & `cli.py`):
   - Background thread to read non-blocking serial lines from the ESP motor node and display them in a live scrolling "Serial Monitor" box (last 10 lines of incoming Serial telemetry) inside the TUI.
   - Serial connection must default to UART (`/dev/serial0`) but allow toggling to USB Serial (`/dev/ttyUSB0`) from the UI.
   - Python code must continually send `P\n` to ping the ESP and check for replies (`P_ACK\n`) to update a live "CONNECTED/DISCONNECTED" status badge (green `[ CONNECTED ]` or red `[ DISCONNECTED ]`).

Please look at the existing `cli.py` and `hardware.py` in `/Users/roopalisingh/DPSI-LFR/rbpi_package`. Propose code changes to implement these requirements cleanly, preventing races on serial or curses, handling mock modes when physical devices are missing, and ensuring it builds cleanly.

Write a detailed analysis report in `/Users/roopalisingh/DPSI-LFR/.agents/explorer_m2/analysis.md`.
