#!/bin/bash
# Runtime dependency and model installer for Galaxy
# Installs missing Python packages and downloads crYOLO model if needed

echo "🔧 Checking and installing dependencies..."

# Function to check if a Python package is available
check_package() {
    python -c "import $1" 2>/dev/null
    return $?
}

# Install missing packages using pip
install_if_missing() {
    local package=$1
    local import_name=${2:-$1}
    
    if ! check_package "$import_name"; then
        echo "📦 Installing $package..."
        pip install --user "$package" --quiet
    else
        echo "✅ $package already available"
    fi
}

# Install core dependencies
install_if_missing "numpy" "numpy"
install_if_missing "scipy" "scipy"
install_if_missing "mrcfile" "mrcfile"
install_if_missing "scikit-image" "skimage"
install_if_missing "matplotlib" "matplotlib"
install_if_missing "h5py" "h5py"

echo "✅ All dependencies ready"

# Download crYOLO model if not present
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODEL_DIR="${SCRIPT_DIR}/../../../lib/ml_model/models/cryolo"
MODEL_FILE="${MODEL_DIR}/gmodel_phosnet_202005_N63_c17.h5"

if [ ! -f "$MODEL_FILE" ]; then
    echo "📥 Downloading crYOLO model (193 MB, one-time download)..."
    mkdir -p "$MODEL_DIR"
    
    # Download from Zenodo or GitHub releases
    MODEL_URL="https://zenodo.org/record/3576630/files/gmodel_phosnet_202005_N63_c17.h5"
    
    if command -v wget &> /dev/null; then
        wget -q -O "$MODEL_FILE" "$MODEL_URL" 2>/dev/null || {
            echo "⚠️  Model download failed, using fallback detection"
            rm -f "$MODEL_FILE"
        }
    elif command -v curl &> /dev/null; then
        curl -s -L -o "$MODEL_FILE" "$MODEL_URL" 2>/dev/null || {
            echo "⚠️  Model download failed, using fallback detection"
            rm -f "$MODEL_FILE"
        }
    else
        echo "⚠️  wget/curl not available, using fallback detection"
    fi
    
    if [ -f "$MODEL_FILE" ]; then
        echo "✅ crYOLO model downloaded successfully"
    fi
else
    echo "✅ crYOLO model already present"
fi
