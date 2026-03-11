# Portability Guide - Cross-Platform Deployment

## Will This Tool Work on Different Computers/Galaxy Accounts?

**Short Answer:** Yes, with proper dependency installation.

**Long Answer:** The tool is designed to be portable, but requires Python dependencies to be installed in each Galaxy environment.

---

## Portability Status

### ✅ What Works Out-of-the-Box

1. **Tool Shed Installation**
   - Tool XML files are portable
   - Scripts are pure Python (no compiled code)
   - No OS-specific dependencies
   - Works on Linux, macOS, Windows (with Python)

2. **File Format Support**
   - MRC, MRCS, ST formats work everywhere
   - Uses standard mrcfile library
   - No proprietary formats

3. **Galaxy Integration**
   - Standard Galaxy tool XML format
   - Compatible with all Galaxy versions 16.01+
   - Works with Docker Galaxy, cloud Galaxy, local Galaxy

### ⚠️ What Requires Setup

1. **Python Dependencies**
   - Must be installed in Galaxy's Python environment
   - Not automatically installed by Tool Shed
   - Requires admin access to Galaxy server

2. **crYOLO Model Download**
   - 193 MB model downloads on first run
   - Requires internet connection
   - Can be pre-downloaded for offline use

---

## Deployment Checklist

### For Galaxy Administrators

#### Step 1: Install Tool from Tool Shed ✅
```
1. Login as Galaxy admin
2. Go to: Admin → Search Tool Shed
3. Search: "particle_picker_bharat"
4. Click: Install
5. Confirm installation
```

**Status:** ✅ Works on any Galaxy instance

#### Step 2: Install Python Dependencies ⚠️

**This is the CRITICAL step that must be done on each Galaxy instance!**

##### For Standard Galaxy:
```bash
# Activate Galaxy's virtual environment
source /path/to/galaxy/.venv/bin/activate

# Install dependencies
pip install numpy scipy mrcfile scikit-image matplotlib h5py pandas plotly
```

##### For Docker Galaxy:
```bash
# Find container name
docker ps

# Install in container
docker exec CONTAINER_NAME bash -c \
  "source /galaxy_venv/bin/activate && \
   pip install numpy scipy mrcfile scikit-image matplotlib h5py pandas plotly"
```

##### For Kubernetes Galaxy:
```bash
# Get pod name
kubectl get pods

# Install in pod
kubectl exec POD_NAME -- bash -c \
  "source /galaxy_venv/bin/activate && \
   pip install numpy scipy mrcfile scikit-image matplotlib h5py pandas plotly"
```

**Status:** ⚠️ Must be done manually on each Galaxy instance

#### Step 3: Verify Installation ✅
```bash
# Test that packages are available
docker exec CONTAINER_NAME bash -c \
  "source /galaxy_venv/bin/activate && python -c 'import mrcfile, plotly; print(\"OK\")'"
```

**Expected Output:** `OK`

---

## Common Deployment Scenarios

### Scenario 1: Public Galaxy Server (usegalaxy.org)

**Can you use it?** ⚠️ Only if admins install dependencies

**Steps:**
1. Tool is available from Tool Shed
2. Contact Galaxy admins to install Python dependencies
3. Once installed, works for all users

**Likelihood:** Low (public servers rarely install custom dependencies)

### Scenario 2: Institutional Galaxy Server

**Can you use it?** ✅ Yes, with admin cooperation

**Steps:**
1. Request admin to install tool from Tool Shed
2. Request admin to install Python dependencies
3. Works for all users in institution

**Likelihood:** High (institutional admins usually accommodate)

### Scenario 3: Personal Docker Galaxy

**Can you use it?** ✅ Yes, full control

**Steps:**
1. Install tool from Tool Shed
2. Install dependencies yourself (you have docker access)
3. Works immediately

**Likelihood:** Very High (you control everything)

### Scenario 4: Cloud Galaxy (AWS, GCP, Azure)

**Can you use it?** ✅ Yes, with configuration

**Steps:**
1. Install tool from Tool Shed
2. Add dependency installation to cloud init script
3. Dependencies persist across restarts

**Likelihood:** High (cloud deployments are configurable)

---

## Potential Issues and Solutions

### Issue 1: ModuleNotFoundError

**Error:**
```
ModuleNotFoundError: No module named 'mrcfile'
```

**Cause:** Python dependencies not installed

**Solution:**
```bash
# Install missing package
docker exec CONTAINER bash -c \
  "source /galaxy_venv/bin/activate && pip install mrcfile"
```

**Prevention:** Install all dependencies upfront

### Issue 2: Permission Denied

**Error:**
```
PermissionError: [Errno 13] Permission denied
```

**Cause:** Galaxy user doesn't have write permissions

**Solution:**
```bash
# Fix permissions on Galaxy directories
chown -R galaxy:galaxy /galaxy_data
chmod -R 755 /galaxy_data
```

**Prevention:** Ensure proper Galaxy setup

### Issue 3: Model Download Fails

**Error:**
```
Failed to download crYOLO model
```

**Cause:** No internet connection or firewall blocking

**Solution:**
```bash
# Pre-download model
mkdir -p /galaxy_data/models/cryolo
cd /galaxy_data/models/cryolo
wget https://path/to/model.h5

# Update tool to use local model
```

**Prevention:** Pre-download models for offline environments

### Issue 4: Memory Errors

**Error:**
```
MemoryError: Unable to allocate array
```

**Cause:** Insufficient RAM for large files

**Solution:**
```bash
# Increase Docker memory limit
docker update --memory 16g CONTAINER_NAME

# Or use smaller files
```

**Prevention:** Ensure 8GB+ RAM available

---

## Dependency Installation Script

### Automated Installation

Create this script for easy deployment:

```bash
#!/bin/bash
# install_cryoem_deps.sh

echo "🔧 Installing CryoEM Particle Picker Dependencies"

# Detect Galaxy environment
if [ -f "/galaxy_venv/bin/activate" ]; then
    VENV="/galaxy_venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    VENV=".venv/bin/activate"
else
    echo "❌ Galaxy virtual environment not found"
    exit 1
fi

# Activate environment
source $VENV

# Install dependencies
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install numpy>=1.18.5 \
            scipy>=1.7.3 \
            mrcfile>=1.5.4 \
            scikit-image>=0.19.3 \
            matplotlib>=3.5.3 \
            h5py>=2.10.0 \
            pandas>=1.3.5 \
            plotly>=5.0.0

# Verify installation
echo "✅ Verifying installation..."
python -c "import numpy, scipy, mrcfile, skimage, matplotlib, h5py, pandas, plotly; print('All packages installed successfully!')"

echo "🎉 Installation complete!"
```

**Usage:**
```bash
# For Docker Galaxy
docker cp install_cryoem_deps.sh CONTAINER:/tmp/
docker exec CONTAINER bash /tmp/install_cryoem_deps.sh

# For standard Galaxy
bash install_cryoem_deps.sh
```

---

## Testing Portability

### Test on New Galaxy Instance

1. **Install Tool**
   ```
   Admin → Tool Shed → Install particle_picker_bharat
   ```

2. **Install Dependencies**
   ```bash
   docker exec CONTAINER bash -c \
     "source /galaxy_venv/bin/activate && \
      pip install numpy scipy mrcfile scikit-image matplotlib h5py pandas plotly"
   ```

3. **Upload Test Data**
   - Upload a small MRC file (< 100 MB)
   - Upload a test STAR file

4. **Run Particle Picker**
   - Set particle size: 200
   - Set confidence: 0.3
   - Run tool

5. **Run Interactive Visualization**
   - Input: micrograph from step 3
   - Input: STAR file from step 4
   - Run tool

6. **Verify Output**
   - Download HTML file
   - Open in browser
   - Check interactive features work

**Expected Result:** ✅ All steps work without errors

---

## Docker Galaxy Template

### Pre-configured Docker Image

Create a Dockerfile with dependencies pre-installed:

```dockerfile
FROM bgruening/galaxy-stable:latest

# Switch to galaxy user
USER galaxy

# Install CryoEM dependencies
RUN source /galaxy_venv/bin/activate && \
    pip install --no-cache-dir \
        numpy>=1.18.5 \
        scipy>=1.7.3 \
        mrcfile>=1.5.4 \
        scikit-image>=0.19.3 \
        matplotlib>=3.5.3 \
        h5py>=2.10.0 \
        pandas>=1.3.5 \
        plotly>=5.0.0

# Pre-download crYOLO model (optional)
# RUN mkdir -p /galaxy_data/models && \
#     wget -O /galaxy_data/models/cryolo_model.h5 https://path/to/model

USER root
```

**Build and Run:**
```bash
# Build image
docker build -t galaxy-cryoem:latest .

# Run container
docker run -d -p 8080:80 \
  -v /path/to/data:/export \
  --name galaxy-cryoem \
  galaxy-cryoem:latest
```

**Status:** ✅ Works on any computer with Docker

---

## Cloud Deployment

### AWS EC2 / GCP Compute / Azure VM

**Requirements:**
- Ubuntu 20.04+ or similar
- 8GB+ RAM
- 50GB+ disk space
- Docker installed

**Deployment Script:**
```bash
#!/bin/bash
# deploy_galaxy_cryoem.sh

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Pull Galaxy image
docker pull bgruening/galaxy-stable:latest

# Run Galaxy
docker run -d -p 80:80 \
  -v /data:/export \
  --name galaxy \
  bgruening/galaxy-stable:latest

# Wait for Galaxy to start
sleep 60

# Install dependencies
docker exec galaxy bash -c \
  "source /galaxy_venv/bin/activate && \
   pip install numpy scipy mrcfile scikit-image matplotlib h5py pandas plotly"

echo "✅ Galaxy with CryoEM tools ready at http://$(curl -s ifconfig.me)"
```

**Status:** ✅ Works on any cloud provider

---

## Kubernetes Deployment

### Helm Chart Configuration

```yaml
# values.yaml
galaxy:
  image:
    repository: bgruening/galaxy-stable
    tag: latest
  
  persistence:
    enabled: true
    size: 100Gi
  
  resources:
    requests:
      memory: "8Gi"
      cpu: "2"
    limits:
      memory: "16Gi"
      cpu: "4"
  
  initContainers:
    - name: install-cryoem-deps
      image: bgruening/galaxy-stable:latest
      command:
        - /bin/bash
        - -c
        - |
          source /galaxy_venv/bin/activate
          pip install numpy scipy mrcfile scikit-image matplotlib h5py pandas plotly
```

**Deploy:**
```bash
helm install galaxy-cryoem ./galaxy-chart -f values.yaml
```

**Status:** ✅ Works in Kubernetes clusters

---

## Offline Deployment

### For Air-Gapped Environments

1. **Download Dependencies**
   ```bash
   # On internet-connected machine
   pip download -d cryoem-deps \
     numpy scipy mrcfile scikit-image matplotlib h5py pandas plotly
   
   # Transfer cryoem-deps/ to offline machine
   ```

2. **Install Offline**
   ```bash
   # On offline machine
   pip install --no-index --find-links=cryoem-deps \
     numpy scipy mrcfile scikit-image matplotlib h5py pandas plotly
   ```

3. **Pre-download Model**
   ```bash
   # Download model on internet-connected machine
   wget https://path/to/cryolo_model.h5
   
   # Transfer to offline machine
   # Place in accessible location
   ```

**Status:** ✅ Works in offline environments with preparation

---

## Summary

### ✅ Portable Aspects
- Tool XML files
- Python scripts
- File format support
- Galaxy integration
- Cross-platform compatibility

### ⚠️ Requires Setup
- Python dependencies (must install on each Galaxy)
- Model download (one-time, 193 MB)
- Permissions (Galaxy user access)

### 🎯 Recommendation

**For Maximum Portability:**
1. Create Docker image with dependencies pre-installed
2. Document dependency installation clearly
3. Provide automated installation scripts
4. Test on multiple Galaxy instances
5. Create offline installation package

**Bottom Line:** The tool WILL work on different computers/Galaxy accounts, but requires Python dependencies to be installed by the Galaxy administrator on each instance. Once dependencies are installed, it works identically everywhere.

---

**Portability Rating:** ⭐⭐⭐⭐☆ (4/5)
- Deducted 1 star for manual dependency installation requirement
- Would be 5/5 if Galaxy supported automatic dependency installation from Tool Shed
