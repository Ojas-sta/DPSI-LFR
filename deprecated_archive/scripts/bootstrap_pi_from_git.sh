#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${DPSI_REPO_URL:-https://github.com/Ojas-sta/DPSI-LFR.git}"
BRANCH="${DPSI_BRANCH:-DPSI_LFR_RBPI_DISCRETE}"
TARGET_DIR="${DPSI_DIR:-${HOME}/DPSI-LFR}"

echo "DPSI-LFR one-command Pi setup"
echo "Repo: ${REPO_URL}"
echo "Branch: ${BRANCH}"
echo "Target: ${TARGET_DIR}"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This setup is intended for Raspberry Pi OS/Linux."
  exit 1
fi

if command -v apt >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y git ca-certificates
fi

if [[ -d "${TARGET_DIR}/.git" ]]; then
  echo "Existing checkout found; pulling latest code..."
  git -C "${TARGET_DIR}" fetch origin "${BRANCH}"
  git -C "${TARGET_DIR}" checkout "${BRANCH}"
  git -C "${TARGET_DIR}" pull --ff-only origin "${BRANCH}"
else
  echo "Cloning repository..."
  rm -rf "${TARGET_DIR}"
  git clone --branch "${BRANCH}" --single-branch "${REPO_URL}" "${TARGET_DIR}"
fi

chmod +x "${TARGET_DIR}/scripts/install_pi_only.sh"
"${TARGET_DIR}/scripts/install_pi_only.sh"

echo
echo "One-command setup complete."
echo "Use:"
echo "  source ${TARGET_DIR}/.venv/bin/activate"
echo "  dpsi-cli --help"
echo "  python3 ${TARGET_DIR}/tests/smoke_pi_only.py"
echo "  dpsi-cli --benchmark --benchmark-frames 1000"
echo "  dpsi-cli --self-test --no-imu"
