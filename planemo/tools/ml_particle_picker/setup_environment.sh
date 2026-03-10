#!/bin/bash
# Complete environment setup for CryoEM Particle Picker
# Bypasses conda entirely - uses pip in Galaxy's Python environment

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="${SCRIPT_DIR}/setup.log"

echo "🔧 Setting up CryoEM Particle Picker environment..." | tee "$LOG_FILE"
echo "Timestamp: $(date)" | tee -a "$LOG_FILE"

# Function to install package with pip
install_package() {
    local package=$1
    local import_name=${2:-$1}
    
    if python3 -c "import ${import_name}" 2>/dev/null; then
        echo "✅ ${package} already installed" | tee -a "$LOG_FILE"
        return 0
    fi
    
    echo "📦 Installing ${package}..." | tee -a "$LOG_FILE"
    
    # Try different installation methods in order
    # 1. Try --user install first
    if pip3 install --user "${package}" --quiet 2>&1 | tee -a "$LOG_FILE"; then
        echo "✅ ${package} installed successfully (--user)" | tee -a "$LOG_FILE"
        return 0
    fi
    
    # 2. Try without --user (system install if permissions allow)
    if pip3 install "${package}" --quiet 2>&1 | tee -a "$LOG_FILE"; then
        echo "✅ ${package} installed successfully (system)" | tee -a "$LOG_FILE"
        return 0
    fi
    
    # 3. Try with --target to local directory
    local target_dir="${SCRIPT_DIR}/.local_packages"
    mkdir -p "$target_dir"
    if pip3 install --target="$target_dir" "${package}" --quiet 2>&1 | tee -a "$LOG_FILE"; then
        export PYTHONPATH="${target_dir}:${PYTHONPATH}"
        echo "✅ ${package} installed successfully (--target)" | tee -a "$LOG_FILE"
        return 0
    fi
    
    echo "⚠️  Failed to install ${package}, will try to continue" | tee -a "$LOG_FILE"
    return 1
}

# Install all required packages
echo "" | tee -a "$LOG_FILE"
echo "Installing Python packages..." | tee -a "$LOG_FILE"

install_package "numpy" "numpy"
install_package "scipy" "scipy"
install_package "mrcfile" "mrcfile"
install_package "scikit-image" "skimage"
install_package "matplotlib" "matplotlib"
install_package "h5py" "h5py"
install_package "pandas" "pandas"

echo "" | tee -a "$LOG_FILE"
echo "✅ Environment setup complete!" | tee -a "$LOG_FILE"

# Download crYOLO model if needed
MODEL_DIR="${SCRIPT_DIR}/../../../lib/ml_model/models/cryolo"
MODEL_FILE="${MODEL_DIR}/gmodel_phosnet_202005_N63_c17.h5"

if [ ! -f "$MODEL_FILE" ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "📥 Downloading crYOLO model (193 MB, one-time download)..." | tee -a "$LOG_FILE"
    mkdir -p "$MODEL_DIR"
    
    MODEL_URL="https://zenodo.org/record/3576630/files/gmodel_phosnet_202005_N63_c17.h5"
    
    if command -v wget &> /dev/null; then
        wget -q --show-progress -O "$MODEL_FILE" "$MODEL_URL" 2>&1 | tee -a "$LOG_FILE" || {
            echo "⚠️  Model download failed, using fallback detection" | tee -a "$LOG_FILE"
            rm -f "$MODEL_FILE"
        }
    elif command -v curl &> /dev/null; then
        curl -L -o "$MODEL_FILE" "$MODEL_URL" 2>&1 | tee -a "$LOG_FILE" || {
            echo "⚠️  Model download failed, using fallback detection" | tee -a "$LOG_FILE"
            rm -f "$MODEL_FILE"
        }
    else
        echo "⚠️  wget/curl not available, using fallback detection" | tee -a "$LOG_FILE"
    fi
    
    if [ -f "$MODEL_FILE" ]; then
        echo "✅ crYOLO model downloaded successfully" | tee -a "$LOG_FILE"
    fi
else
    echo "✅ crYOLO model already present" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "🎉 Setup complete! Tool is ready to use." | tee -a "$LOG_FILE"
