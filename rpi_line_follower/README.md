# DPSI-LFR Pi-Only Line Follower

This package drives the robot directly from the Raspberry Pi 4B:

* Picamera2/OpenCV detects the black line, green markers, red stop marker, intersections, and gaps.
* RPi.GPIO drives the L298N ENA/ENB pins with PWM for dynamic speed.
* MPU6050 yaw is used only as a secondary fallback during gaps and timed turns.
* A threaded TUI/CLI lets you tune PID and speed constants live.
* The camera is configured at 320x240 and targets 120 FPS for a fast control loop.
* Optional human/person masking removes detected people from the vision ROI before line detection.

## Run

```bash
./dpsi-cli
```

Useful options:

```bash
./dpsi-cli --dry-run --no-imu --no-tui
./dpsi-cli --preview
./dpsi-cli --camera-index 0
./dpsi-cli --mode final
./dpsi-cli --no-human-filter
./dpsi-cli --tuning-file ~/.config/dpsi-lfr/tunables.json
./dpsi-cli --self-test --no-imu
./dpsi-cli --benchmark --benchmark-frames 1000
./dpsi-cli --benchmark --report-file reports/benchmark.json
./dpsi-cli --world-model --world-display
```

Default mode is `prelim`, matching the annexure: green dot blinks the green LED and continues movement; red dot stops completely and blinks/beeps red feedback. `--mode final` enables deterministic green-marker turn decisions.

Human masking uses OpenCV's built-in HOG person detector when available. Detected person boxes are padded and removed from the ROI before black-line, green-marker, and red-marker masks are calculated. If it causes false positives or lowers FPS on the Pi, run with `--no-human-filter`.

## Top-Down World Model

Run the alternate bird's-eye navigator:

```bash
dpsi-cli --world-model --world-display
```

This mode maps the camera image into a top-down world view, displays that warped view live during inference, detects the black path and red horizontal lines in that warped map, waits at the first red line, drives after the start line clears, then stops at the next different red line.

Useful options:

```bash
dpsi-cli --world-model --dry-run --world-display
dpsi-cli --world-model --preview
dpsi-cli --world-model --world-size 320
```

Use `--world-display` for only the live top-down inference window. Use `--preview` when you also want the line and red-line mask debug windows. The default perspective source points assume the camera sees a trapezoid of mat in front of the robot. If the top-down view looks skewed, tune `TopDownMapper.src_ratios` in [pi_only_follower.py](pi_only_follower.py) using `--preview` until tape lines look roughly parallel in the warped window.

## Raspberry Pi Installation

Use this on the Raspberry Pi 4B that will run the robot.

### One-Command Git Install

After this branch is pushed to GitHub, run this on the Raspberry Pi:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Ojas-sta/DPSI-LFR/DPSI_LFR_RBPI_DISCRETE/scripts/bootstrap_pi_from_git.sh)"
```

The script installs `git`, clones or pulls `~/DPSI-LFR`, runs `scripts/install_pi_only.sh`, and leaves `dpsi-cli` available inside `~/DPSI-LFR/.venv`.

Use a custom target folder or branch:

```bash
DPSI_DIR=~/robot-code DPSI_BRANCH=DPSI_LFR_RBPI_DISCRETE bash -c "$(curl -fsSL https://raw.githubusercontent.com/Ojas-sta/DPSI-LFR/DPSI_LFR_RBPI_DISCRETE/scripts/bootstrap_pi_from_git.sh)"
```

### No-Clone Release Install

Build a release bundle on your laptop:

```bash
./scripts/build_pi_release.sh
```

Copy the generated archive from `dist/` to the Raspberry Pi, then install without cloning the repo:

```bash
tar -xzf dpsi-lfr-pi-only-0.1.0.tar.gz
cd dpsi-lfr-pi-only-0.1.0
./scripts/install_release.sh
source ~/.venvs/dpsi-lfr/bin/activate
dpsi-cli --help
```

The archive also includes `SHA256SUMS` and [data/master_pinout.md](../data/master_pinout.md). The release installer verifies the staged files before installing when a SHA-256 tool is available.

Then run:

```bash
python3 tests/smoke_pi_only.py
dpsi-cli --benchmark --benchmark-frames 1000
dpsi-cli --self-test --no-imu
```

Use `dpsi-cli --self-test` after I2C is enabled and the MPU6050 is connected.

### Editable Repo Install

Fast path from the project folder:

```bash
cd ~/DPSI-LFR
./scripts/install_pi_only.sh
```

The helper installs Raspberry Pi OS packages, creates `.venv` with system site packages, and installs `dpsi-cli` in editable mode. It does not start the robot or pulse the motors.

Manual path:

1. Update the Pi and install system packages:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-opencv python3-picamera2 python3-rpi.gpio python3-smbus i2c-tools git
```

2. Enable the required Pi interfaces:

```bash
sudo raspi-config
```

In `Interface Options`, enable:

* Camera
* I2C

Then reboot:

```bash
sudo reboot
```

3. From the project folder, create a virtual environment and install the controller:

```bash
cd ~/DPSI-LFR
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[pi]"
```

`--system-site-packages` is recommended because Raspberry Pi OS often provides `picamera2`, `RPi.GPIO`, and OpenCV through apt packages.

4. Check the MPU6050 is visible on I2C:

```bash
i2cdetect -y 1
```

Look for address `0x68`. If it is missing, the robot can still run with:

```bash
dpsi-cli --no-imu
```

5. Run the no-hardware smoke test before powering the motors:

```bash
python3 tests/smoke_pi_only.py
```

Expected final line:

```text
SMOKE PASS
```

Optional: measure no-GPIO vision/navigation loop speed:

```bash
dpsi-cli --benchmark --benchmark-frames 1000
```

On the Pi, run this with preview off. Add `--benchmark-require-100hz` when you want the command to fail if synthetic processing drops below the control-loop target.

Save benchmark evidence:

```bash
mkdir -p reports
dpsi-cli --benchmark --benchmark-frames 1000 --report-file reports/benchmark.json
```

6. Start safely with motors disabled or raised off the mat:

```bash
dpsi-cli --dry-run --no-imu
```

7. Run a hardware self-test before the first real drive:

```bash
dpsi-cli --self-test
```

This checks GPIO setup, LED/buzzer feedback, camera frames, vision processing, and MPU6050 availability without starting autonomous line following. If the MPU6050 is disconnected or noisy, use:

```bash
dpsi-cli --self-test --no-imu
```

Only after lifting the robot so the wheels cannot touch the mat, run the optional motor pulse check:

```bash
dpsi-cli --self-test --motor-pulse-test
```

If every other subsystem works but the motors do not move, skip camera/IMU checks and drive only the L298N pins from the README pinout:

```bash
dpsi-cli --motor-only-test --motor-test-duty 0.75 --motor-test-seconds 1.0
```

This pulses left, right, both forward, then both reverse, and stops the motors after each step.

Save self-test evidence:

```bash
mkdir -p reports
dpsi-cli --self-test --report-file reports/self-test.json
```

8. Start the real robot:

```bash
dpsi-cli
```

For the annexure preliminary round, keep the default mode. Green markers blink the green LED and continue movement; red markers stop completely. For final-round green-marker turn behavior:

```bash
dpsi-cli --mode final
```

Tune on the mat, then press `w` in the TUI or type `save` in command mode to store the current PID and speed values. On the next run, `dpsi-cli` automatically loads:

```text
~/.config/dpsi-lfr/tunables.json
```

Use a different profile when testing:

```bash
dpsi-cli --tuning-file ~/fast-track-tuning.json
```

## Preserved Node 1 Pins

Do not move these unless you rewire the robot:

| Function | BCM GPIO |
| :--- | :---: |
| Red LED | 5 |
| Green LED | 6 |
| Buzzer PWM | 13 |
| I2C SDA | 2 |
| I2C SCL | 3 |
| Legacy UART TX | 14 |
| Legacy UART RX | 15 |

## Direct L298N Pins

| L298N Signal | BCM GPIO |
| :--- | :---: |
| ENA left PWM | 12 |
| IN1 left direction | 16 |
| IN2 left direction | 20 |
| IN3 right direction | 21 |
| IN4 right direction | 26 |
| ENB right PWM | 18 |

## TUI Controls

| Key | Action |
| :--- | :--- |
| Space | Pause/run |
| `q` | Quit and stop motors |
| `w` | Save PID/speed tuning profile |
| `l` | Load PID/speed tuning profile |
| `z` / `x` | Decrease/increase Kp |
| `a` / `s` | Decrease/increase Ki |
| `c` / `v` | Decrease/increase Kd |
| `[` / `]` | Decrease/increase base speed |
| `-` / `+` | Decrease/increase max speed cap |
| `g` | Toggle green-marker turns |
| `r` | Toggle red-stop behavior |
| `m` | Toggle preliminary/final marker mode |

Non-curses CLI commands also work:

```text
kp 0.90
ki 0.0
kd 0.18
base 0.42
max 0.82
save
load
pause
run
q
mode final
mode prelim
```

## Camera Mount

Start with the Raspberry Pi camera 85-120 mm above the mat, pitched 18-25 degrees downward from horizontal. For this chassis, begin around 22 degrees and aim the lower third of the frame roughly 60-90 mm in front of the drive axle.
