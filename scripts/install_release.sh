#!/usr/bin/env bash
set -euo pipefail

RELEASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-${HOME}/.venvs/dpsi-lfr}"

echo "DPSI-LFR release installer"
echo "Release: ${RELEASE_DIR}"
echo "Virtualenv: ${VENV_DIR}"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This release installer is intended for Raspberry Pi OS/Linux."
  exit 1
fi

if command -v apt >/dev/null 2>&1; then
  echo "Installing Raspberry Pi OS runtime packages..."
  sudo apt update
  sudo apt install -y \
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

if [[ -f "${RELEASE_DIR}/SHA256SUMS" ]]; then
  echo "Verifying release file checksums..."
  if command -v sha256sum >/dev/null 2>&1; then
    (cd "${RELEASE_DIR}" && sha256sum -c SHA256SUMS)
  elif command -v shasum >/dev/null 2>&1; then
    (cd "${RELEASE_DIR}" && shasum -a 256 -c SHA256SUMS)
  else
    echo "No SHA-256 verifier found; skipping checksum verification."
  fi
fi

python3 -m venv --system-site-packages "${VENV_DIR}"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

WHEEL="$(find "${RELEASE_DIR}/wheelhouse" -maxdepth 1 -name 'dpsi_lfr-*.whl' | sort | tail -n 1)"
if [[ -z "${WHEEL}" ]]; then
  echo "No dpsi_lfr wheel found in ${RELEASE_DIR}/wheelhouse"
  exit 1
fi

python3 -m pip install --upgrade pip
python3 -m pip install --no-deps --force-reinstall "${WHEEL}"

echo
echo "Install complete."
echo "Activate with:"
echo "  source ${VENV_DIR}/bin/activate"
echo
echo "Next checks:"
echo "  dpsi-cli --help"
echo "  python3 ${RELEASE_DIR}/tests/smoke_pi_only.py"
echo "  dpsi-cli --benchmark --benchmark-frames 1000"
echo "  dpsi-cli --self-test --no-imu"
