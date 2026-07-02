#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="${VENV_DIR:-${HOME}/.venvs/dpsi-lfr}"
CONFIG_DIR="${HOME}/.config/dpsi-lfr"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
SERVICE_FILE="${SYSTEMD_USER_DIR}/dpsi-lfr.service"
ENV_FILE="${CONFIG_DIR}/service.env"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This helper is intended for Raspberry Pi OS/Linux."
  exit 1
fi

if [[ ! -x "${VENV_DIR}/bin/dpsi-cli" ]]; then
  echo "dpsi-cli not found at ${VENV_DIR}/bin/dpsi-cli"
  echo "Run scripts/install_release.sh first, or set VENV_DIR to the installed virtualenv."
  exit 1
fi

mkdir -p "${CONFIG_DIR}" "${SYSTEMD_USER_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
  cat > "${ENV_FILE}" <<'EOF'
# Edit this line to change startup behavior.
# Keep --headless for service use. Use --no-imu if MPU6050 is not connected.
DPSI_CLI_ARGS="--headless --save-on-exit"
EOF
fi

cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=DPSI-LFR Pi-only line follower
After=default.target

[Service]
Type=simple
EnvironmentFile=${ENV_FILE}
ExecStart=/bin/bash -lc 'exec "${VENV_DIR}/bin/dpsi-cli" \${DPSI_CLI_ARGS}'
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload

echo "Installed user service: ${SERVICE_FILE}"
echo "Config file: ${ENV_FILE}"
echo
echo "Start now:"
echo "  systemctl --user start dpsi-lfr.service"
echo
echo "Enable at user login:"
echo "  systemctl --user enable dpsi-lfr.service"
echo
echo "View logs:"
echo "  journalctl --user -u dpsi-lfr.service -f"
echo
echo "Stop:"
echo "  systemctl --user stop dpsi-lfr.service"
