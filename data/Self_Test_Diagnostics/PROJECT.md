# Project: ESP32 Diagnostics Firmware Hardware Migration

## Architecture
- **PlatformIO**: Embedded development environment targeting the ESP32 platform.
- **Config**: Core hardware pin mapping and configuration settings.
- **Motors**: Control interface for the L298N motor driver.
- **Sensors**: Reads analog/digital inputs (previously handled MPU6050 and IR sensors, now deprecated/removed).
- **WebDiagnostics/Dashboard**: Wi-Fi AP and web server hosting the dashboard for remote control.

## Code Layout
- `platformio.ini` - Project configuration file.
- `src/Config.h` - Pin mapping and system-wide configuration definitions.
- `src/main.cpp` - Firmware entry point, setup, and main loop.
- `src/Motors.h` / `src/Motors.cpp` - Motor driver initialization and speed/direction control.
- `src/Sensors.h` / `src/Sensors.cpp` - Sensor interface functions.
- `src/Dashboard.h` - Web page HTML/JS content.
- `src/WebDiagnostics.h` / `src/WebDiagnostics.cpp` - Web server and dashboard backend.
- `src/Display.h` / `src/Display.cpp` - I2C display interface functions.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | Analysis & Strategy | Spawn Explorer to locate and map all MPU6050, IR sensor, and motor pin usages in the codebase. | None | DONE (c8120de9-a146-47cd-b235-e1a08c0e05f8) |
| 2 | PlatformIO & Pin Migration | Update board configuration and assign the new motor and analog pins in Config.h. | M1 | DONE (fb16d1d9-2677-4439-ad0d-7ff5fa5829c7) |
| 3 | Sensor Deprecation & Code Cleanups | Completely remove MPU6050 and IR sensor drivers, tasks, and references from main, WebDiagnostics, Display, etc. | M2 | DONE (29a64d02-a69e-46db-be14-d6a901d0fa3d) |
| 4 | Verification & Compilation | Compile the code using PlatformIO (`pio run`) and run verification checks via worker, reviewer, and auditor. | M3 | DONE (5a069843-2889-4709-9dd4-a54ce5ab34f7, fb9f1399-90ed-48b5-904c-3da01501cdf0) |

## Interface Contracts
- **Motors ↔ WebDiagnostics**: Motors must provide initialization and direction/speed control APIs that are independent of any sensor feedback.
- **WebDiagnostics ↔ Sensors**: Web dashboard endpoints must not refer to MPU6050 or IR sensors.
