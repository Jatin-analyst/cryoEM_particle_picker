#!/bin/bash
# Galaxy wrapper for CryoEM Particle Picker
# No conda dependencies - uses Galaxy's Python with pip packages

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Add lib directory and local packages to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}/../../../lib"
if [ -d "${SCRIPT_DIR}/.local_packages" ]; then
    export PYTHONPATH="${SCRIPT_DIR}/.local_packages:${PYTHONPATH}"
fi

# Run environment setup (installs packages if needed)
# This runs quickly if packages are already installed
# Allow setup to fail gracefully - the Python script will check dependencies
bash "${SCRIPT_DIR}/setup_environment.sh" 2>&1 || {
    echo "⚠️  Setup had issues, but continuing (Python script will check dependencies)..." >&2
}

# Run the tool
python3 "${SCRIPT_DIR}/ml_picker_production.py" "$@"
