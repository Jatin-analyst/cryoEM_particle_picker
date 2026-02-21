#!/bin/bash
# Wrapper script to run the particle picker with correct Python path

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Add lib directory to Python path
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Run the picker with all arguments passed to this script
python "${SCRIPT_DIR}/planemo/tools/ml_particle_picker/ml_picker.py" "$@"
