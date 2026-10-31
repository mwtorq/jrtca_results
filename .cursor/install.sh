#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the jrtca_results Python pipeline.
# Installs system libraries needed to build pyodbc, then creates a virtualenv
# and installs the pinned Python dependencies. Safe to run repeatedly.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Installing system packages"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq \
  python3-venv \
  python3-dev \
  build-essential \
  unixodbc \
  unixodbc-dev

echo "==> Configuring Git LFS (data files are stored in LFS; pull on demand)"
git lfs install --local

echo "==> Fetching the requirements file from Git LFS"
git lfs pull --include="requirements_scraper.txt"

echo "==> Creating the Python virtual environment (.venv)"
if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

echo "==> Installing Python dependencies"
# pywin32 is declared with a win32-only marker and is skipped on Linux.
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements_scraper.txt

echo "==> Done. Activate the environment with: source .venv/bin/activate"
