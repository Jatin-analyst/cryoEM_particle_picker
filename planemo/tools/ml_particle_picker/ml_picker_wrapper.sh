#!/bin/bash
# Wrapper script to set up Python path for Galaxy tool

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Add lib directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}/../../../lib"

# Run the Python script with all arguments
python3 "${SCRIPT_DIR}/ml_picker.py" "$@"
