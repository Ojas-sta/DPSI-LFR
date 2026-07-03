#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

echo "DPSI-LFR Pi-only installer"
echo "Project: ${ROOT_DIR}"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This installer is intended for Raspberry Pi OS/Linux."
  echo "On this machine, use the README commands manually if needed."
  exit 1
fi

if command -v apt >/dev/null 2>&1; then
  echo "Installing Raspberry Pi OS packages..."
  sudo apt update
  sudo apt install -y \
    git \
    i2c-tools \
    python3-opencv \
    python3-picamera2 \
    python3-pip \
    python3-rpi.gpio \
    python3-smbus \
    python3-venv
else
  echo "apt not found; skipping system package install."
fi

echo "Creating virtual environment with system site packages..."
python3 -m venv --system-site-packages "${VENV_DIR}"

echo "Installing dpsi-cli in editable mode..."
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
python3 -m pip install --upgrade pip
python3 -m pip install -e "${ROOT_DIR}[pi]"

USER_BIN_DIR="${HOME}/.local/bin"
mkdir -p "${USER_BIN_DIR}"
cat > "${USER_BIN_DIR}/dpsi-cli" <<EOF
#!/usr/bin/env bash
set -euo pipefail
source "${VENV_DIR}/bin/activate"
exec "${VENV_DIR}/bin/dpsi-cli" "\$@"
EOF
chmod +x "${USER_BIN_DIR}/dpsi-cli"

echo
echo "Install complete."
echo "Next commands on the Pi:"
echo "  export PATH=\"${USER_BIN_DIR}:\$PATH\""
echo "  python3 tests/smoke_pi_only.py"
echo "  dpsi-cli --self-test --no-imu"
echo "  dpsi-cli --self-test"
echo
echo "Enable Camera and I2C in raspi-config if they are not already enabled:"
echo "  sudo raspi-config"
