#!/bin/bash
# Convenience script for batch particle picking
# Automatically sets PYTHONPATH to find lib modules

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to include the project root
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Run the batch picker with all arguments
python "${SCRIPT_DIR}/planemo/tools/ml_particle_picker/ml_picker_batch.py" "$@"
