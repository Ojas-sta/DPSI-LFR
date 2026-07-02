#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(ROOT_DIR="${ROOT_DIR}" python3 - <<'PY'
import os
import tomllib
with open(os.path.join(os.environ["ROOT_DIR"], "pyproject.toml"), "rb") as handle:
    print(tomllib.load(handle)["project"]["version"])
PY
)"
RELEASE_NAME="dpsi-lfr-pi-only-${VERSION}"
BUILD_DIR="${ROOT_DIR}/dist/${RELEASE_NAME}"
ARCHIVE="${ROOT_DIR}/dist/${RELEASE_NAME}.tar.gz"

echo "Building ${RELEASE_NAME}"
rm -rf "${BUILD_DIR}" "${ARCHIVE}"
mkdir -p "${BUILD_DIR}/wheelhouse" "${BUILD_DIR}/scripts" "${BUILD_DIR}/tests" "${BUILD_DIR}/data"

python3 -m pip wheel --no-deps --wheel-dir "${BUILD_DIR}/wheelhouse" "${ROOT_DIR}"

cp "${ROOT_DIR}/scripts/install_release.sh" "${BUILD_DIR}/scripts/install_release.sh"
cp "${ROOT_DIR}/scripts/install_user_service.sh" "${BUILD_DIR}/scripts/install_user_service.sh"
cp "${ROOT_DIR}/scripts/bootstrap_pi_from_git.sh" "${BUILD_DIR}/scripts/bootstrap_pi_from_git.sh"
cp "${ROOT_DIR}/requirements_pi_only.txt" "${BUILD_DIR}/requirements_pi_only.txt"
cp "${ROOT_DIR}/pyproject.toml" "${BUILD_DIR}/pyproject.toml"
cp "${ROOT_DIR}/rpi_line_follower/README.md" "${BUILD_DIR}/README.md"
cp "${ROOT_DIR}/data/master_pinout.md" "${BUILD_DIR}/data/master_pinout.md"
cp "${ROOT_DIR}/tests/smoke_pi_only.py" "${BUILD_DIR}/tests/smoke_pi_only.py"
chmod +x "${BUILD_DIR}/scripts/install_release.sh" "${BUILD_DIR}/scripts/install_user_service.sh" "${BUILD_DIR}/scripts/bootstrap_pi_from_git.sh"

cat > "${BUILD_DIR}/INSTALL.txt" <<EOF
DPSI-LFR Pi-only release ${VERSION}

Copy this folder or ${RELEASE_NAME}.tar.gz to the Raspberry Pi.

Install:
  tar -xzf ${RELEASE_NAME}.tar.gz
  cd ${RELEASE_NAME}
  ./scripts/install_release.sh

After install:
  source ~/.venvs/dpsi-lfr/bin/activate
  dpsi-cli --help
  python3 tests/smoke_pi_only.py
  dpsi-cli --benchmark --benchmark-frames 1000
  dpsi-cli --self-test --no-imu

Pinout:
  data/master_pinout.md

Before motor testing:
  Lift the robot so the wheels cannot touch the mat.
  dpsi-cli --self-test --motor-pulse-test

Optional service install:
  ./scripts/install_user_service.sh
  systemctl --user start dpsi-lfr.service
  journalctl --user -u dpsi-lfr.service -f
EOF

(cd "${BUILD_DIR}" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS)
(cd "${ROOT_DIR}/dist" && tar -czf "${ARCHIVE}" "${RELEASE_NAME}")
(cd "${ROOT_DIR}/dist" && shasum -a 256 "${RELEASE_NAME}.tar.gz" > "${RELEASE_NAME}.tar.gz.sha256")

echo "Release folder: ${BUILD_DIR}"
echo "Release archive: ${ARCHIVE}"
echo "Archive checksum: ${ARCHIVE}.sha256"
