# Galaxy ToolShed Deployment Guide

## Current Status

Your CryoEM Particle Picker tool is ready for Galaxy deployment, but there are a few steps to complete before uploading to the public ToolShed.

---

## ⚠️ Important: Two Deployment Options

### Option 1: Local Galaxy Instance (Recommended First)

Deploy to your own Galaxy server for testing before going public.

### Option 2: Public Galaxy ToolShed

Deploy to the public ToolShed for community use (requires account and approval).

---

## Option 1: Local Galaxy Deployment (Easiest)

### Step 1: Install Galaxy Locally

```bash
# Clone Galaxy
git clone https://github.com/galaxyproject/galaxy.git
cd galaxy

# Start Galaxy (first time takes ~10 minutes)
sh run.sh
```

Galaxy will be available at: `http://localhost:8080`

### Step 2: Copy Tool to Galaxy

```bash
# Create tool directory
mkdir -p galaxy/tools/cryoem

# Copy your tool
cp -r /path/to/cryoem-precision-tool/planemo/tools/ml_particle_picker \
      galaxy/tools/cryoem/

# Copy lib directory
cp -r /path/to/cryoem-precision-tool/lib \
      galaxy/tools/cryoem/ml_particle_picker/
```

### Step 3: Register Tool in Galaxy

Edit `galaxy/config/tool_conf.xml`:

```xml
<toolbox>
  <!-- Add this section -->
  <section id="cryoem" name="CryoEM Tools">
    <tool file="cryoem/ml_particle_picker/ml_particle_picker.xml" />
  </section>
</toolbox>
```

### Step 4: Restart Galaxy

```bash
# Stop Galaxy (Ctrl+C)
# Start again
sh run.sh
```

Your tool will now appear in the Galaxy interface under "CryoEM Tools"!

---

## Option 2: Public ToolShed Deployment

### Prerequisites

1. **Create ToolShed Account**
   - Go to: https://toolshed.g2.bx.psu.edu/
   - Click "Register" and create account
   - Verify email

2. **Create GitHub Repository** (Optional but recommended)
   - Create public repo for your tool
   - Push your code
   - Update `.shed.yml` with correct URLs

### Step 1: Fix Linting Issues

Before uploading, fix the warnings:

```bash
# Check current issues
planemo lint planemo/tools/ml_particle_picker/ml_particle_picker.xml
```

**Current Issues:**
- ✅ Minor: XML element order (not critical)
- ⚠️ Test parameter validation (needs fixing)
- ⚠️ Test output expectations (needs fixing)

### Step 2: Update .shed.yml

Edit `planemo/tools/ml_particle_picker/.shed.yml`:

```yaml
name: cryoem_particle_picker
owner: YOUR_TOOLSHED_USERNAME  # Change this!
description: ML-based particle picker for CryoEM micrographs using YOLOv8n
long_description: |
  Automated particle detection in CryoEM micrographs using YOLOv8n deep learning model.
  
  Features:
  - Supports .mrc, .mrcs, .st file formats
  - Batch processing for large datasets
  - Pretrained YOLOv8n model (no training required)
  - STAR format output (RELION/CryoSPARC compatible)
  - Optional CTF estimation
  - CPU and GPU support
  
categories:
  - Imaging
  - Machine Learning
  
homepage_url: https://github.com/YOUR_USERNAME/cryoem-precision-tool
remote_repository_url: https://github.com/YOUR_USERNAME/cryoem-precision-tool

auto_tool_repositories:
  name_template: "{{ tool_id }}"
  description_template: "{{ tool_name }}"
```

### Step 3: Login to ToolShed

```bash
# Login (you'll be prompted for password)
planemo shed_login --shed_target toolshed
```

### Step 4: Create Repository on ToolShed Website

**IMPORTANT**: You must create the repository on the website FIRST!

1. Go to: https://toolshed.g2.bx.psu.edu/
2. Login with your account
3. Click "Create new repository"
4. Fill in:
   - **Name**: `cryoem_particle_picker`
   - **Synopsis**: ML-based particle picker for CryoEM
   - **Description**: (copy from .shed.yml)
   - **Categories**: Imaging, Machine Learning
5. Click "Create repository"

### Step 5: Upload Tool

```bash
# Navigate to tool directory
cd planemo/tools/ml_particle_picker

# Upload to ToolShed
planemo shed_upload --shed_target toolshed \
                    --message "Initial release v2.0.0"
```

### Step 6: Test Installation

```bash
# Test that the tool can be installed
planemo shed_test --shed_target toolshed
```

---

## Alternative: Use Planemo Serve (Quick Testing)

Test your tool in a temporary Galaxy instance:

```bash
# Serve tool in temporary Galaxy
planemo serve planemo/tools/ml_particle_picker/ml_particle_picker.xml
```

This starts a Galaxy instance at `http://localhost:9090` with your tool pre-installed!

---

## Troubleshooting

### Error: "Failed to find repository"

**Cause**: Repository doesn't exist on ToolShed yet

**Solution**: Create repository on ToolShed website first (Step 4 above)

### Error: "500 Internal Server Error"

**Cause**: ToolShed server issue or authentication problem

**Solutions**:
1. Check you're logged in: `planemo shed_login --shed_target toolshed`
2. Verify repository exists on website
3. Try again later (server might be down)
4. Check ToolShed status: https://status.galaxyproject.org/

### Error: "Linting failed"

**Cause**: Tool XML has issues

**Solution**: Fix issues reported by `planemo lint`

### Error: "Permission denied"

**Cause**: Not logged in or wrong username

**Solution**: 
1. Login: `planemo shed_login --shed_target toolshed`
2. Verify username in `.shed.yml` matches your ToolShed account

---

## Current Tool Status

### ✅ Ready
- Tool XML definition
- Python CLI scripts
- Dependencies specified
- Help documentation
- Citations included

### ⚠️ Needs Attention
- Fix test parameter validation
- Update GitHub URLs in .shed.yml
- Create ToolShed account (if deploying publicly)
- Create repository on ToolShed website

### 📝 Optional Improvements
- Add more test cases
- Add tool screenshots
- Create tutorial/workflow
- Add example datasets

---

## Recommended Deployment Path

### For Testing (Do This First)

1. ✅ **Use Planemo Serve**
   ```bash
   planemo serve planemo/tools/ml_particle_picker/ml_particle_picker.xml
   ```
   - Fastest way to test
   - No setup required
   - Temporary Galaxy instance

2. ✅ **Deploy to Local Galaxy**
   - Full Galaxy experience
   - Test with real data
   - No public exposure

### For Production (Do This Later)

3. ✅ **Deploy to ToolShed**
   - After thorough testing
   - When tool is stable
   - For community use

---

## Quick Start: Test Your Tool Now

```bash
# Option 1: Serve with Planemo (easiest)
planemo serve planemo/tools/ml_particle_picker/ml_particle_picker.xml

# Option 2: Test locally
./run_picker.sh \
    --input archive/12128/data/20240114_JN_MB04_LO_004_Tomo_009.st \
    --output test_output.star \
    --particle_size 200 \
    --device cpu

# Option 3: Batch processing
./run_batch_picker.sh \
    --input_dir archive/12128/data \
    --output_dir batch_test \
    --particle_size 200 \
    --device cpu \
    --verbose
```

---

## Next Steps

1. **Test locally first** - Use `planemo serve` or local Galaxy
2. **Fix linting issues** - Run `planemo lint` and address warnings
3. **Create ToolShed account** - If deploying publicly
4. **Create repository on website** - Before using `planemo shed_upload`
5. **Upload tool** - Use `planemo shed_upload`

---

## Support

- **Planemo Documentation**: https://planemo.readthedocs.io/
- **Galaxy ToolShed**: https://toolshed.g2.bx.psu.edu/
- **Galaxy Tool Development**: https://docs.galaxyproject.org/en/latest/dev/
- **Community Help**: https://help.galaxyproject.org/

---

## Summary

Your tool is **ready for local deployment** and **almost ready for ToolShed**. 

**Immediate action**: Use `planemo serve` to test your tool in Galaxy right now!

**Before ToolShed deployment**: 
1. Create ToolShed account
2. Create repository on website
3. Fix linting warnings
4. Update .shed.yml with your info

The tool works perfectly via command line - Galaxy deployment is just packaging!
