# Tool Shed Revision Mismatch - Fix Guide

## Error Message
```
The change log does not include revision d84537b60153.
```

## What This Means

The Tool Shed is tracking a git revision (d84537b60153) that doesn't exist in your current local repository. This happens when:
- Repository history was rewritten (git rebase, reset, etc.)
- Working with a different clone of the repository
- Previous uploads used different git commits

## 🔧 Solutions

---

### Solution 1: Force Update (Recommended)

This resets the Tool Shed to match your current git state.

```bash
# 1. Commit all current changes
cd cryoEM_particle_picker
git add -A
git commit -m "Version 2.1.0: Real crYOLO model, fixed conda dependencies"

# 2. Navigate to tool directory
cd planemo/tools/ml_particle_picker

# 3. Force update Tool Shed
planemo shed_update --shed_target toolshed \
    --force_repository_creation \
    --message "Version 2.1.0: Force update to resolve revision mismatch"
```

**Or use the automated script:**
```bash
chmod +x fix_toolshed_revision.sh
./fix_toolshed_revision.sh
```

---

### Solution 2: Manual Upload via Web Interface

If planemo force update doesn't work:

1. **Go to Tool Shed**: https://toolshed.g2.bx.psu.edu/
2. **Login** to your account
3. **Navigate** to your repository: `cryoem_particle_picker`
4. **Click** "Upload files to repository"
5. **Select** "Upload a tar archive"
6. **Create tar archive**:
   ```bash
   cd cryoEM_particle_picker/planemo/tools/ml_particle_picker
   tar -czf cryoem_tool_v2.1.0.tar.gz \
       ml_particle_picker.xml \
       ml_picker_production.py \
       ml_picker_batch.py \
       ml_picker_wrapper.sh \
       datatypes_conf.xml \
       .shed.yml
   ```
7. **Upload** the tar file
8. **Add commit message**: "Version 2.1.0: Real crYOLO model integration"

---

### Solution 3: Create New Repository

If the above don't work, create a fresh repository:

1. **On Tool Shed website**, create new repository:
   - Name: `cryoem_particle_picker_v2`
   - Description: "CryoEM Particle Picker with crYOLO model"
   - Categories: Imaging, Machine Learning

2. **Update .shed.yml**:
   ```yaml
   name: cryoem_particle_picker_v2
   owner: jatin_bioinformatics
   description: crYOLO-based particle detection for CryoEM
   ```

3. **Upload to new repository**:
   ```bash
   cd planemo/tools/ml_particle_picker
   planemo shed_upload --shed_target toolshed \
       --message "Initial release v2.1.0"
   ```

---

### Solution 4: Reset Tool Shed Repository

**Warning**: This deletes all previous versions!

1. **On Tool Shed website**:
   - Go to your repository
   - Click "Repository Actions"
   - Select "Reset metadata"
   - Confirm reset

2. **Re-upload**:
   ```bash
   cd planemo/tools/ml_particle_picker
   planemo shed_upload --shed_target toolshed \
       --message "Version 2.1.0: Fresh upload after reset"
   ```

---

## 🎯 Recommended Approach

**For your situation**, I recommend:

1. ✅ **Commit current changes** (preserve your work)
2. ✅ **Use force update** (Solution 1)
3. ✅ **If that fails**, use manual upload (Solution 2)

---

## 📋 Step-by-Step: Force Update

### 1. Commit Your Changes

```bash
cd cryoEM_particle_picker

# Check what needs to be committed
git status

# Add all changes
git add -A

# Commit with descriptive message
git commit -m "Version 2.1.0: Real crYOLO PhosNet model integration
- Integrated authentic crYOLO PhosNet model (193.3 MB)
- Fixed confidence scoring (0.3-0.99 range)
- Resolved conda dependency conflicts
- Simplified requirements for better compatibility
- Added comprehensive troubleshooting documentation"

# Verify commit
git log -1
```

### 2. Force Update Tool Shed

```bash
# Navigate to tool directory
cd planemo/tools/ml_particle_picker

# Force update
planemo shed_update --shed_target toolshed \
    --force_repository_creation \
    --message "Version 2.1.0: Force update - Real crYOLO model, fixed conda issues"
```

### 3. Verify Update

1. Visit: https://toolshed.g2.bx.psu.edu/
2. Navigate to: `cryoem_particle_picker`
3. Check:
   - New revision is present
   - Version shows 2.1.0+galaxy0
   - Files are updated
   - No error messages

---

## 🔍 Understanding the Issue

### Why This Happens

The Tool Shed uses git revisions to track changes. When you:
- Rewrite git history (rebase, reset)
- Work from a different clone
- Delete and recreate the repository

The Tool Shed still expects the old revision (d84537b60153) to exist in your git history.

### The Fix

Force update tells the Tool Shed: "Ignore the old revision, use my current git state as the new baseline."

---

## ⚠️ Important Notes

1. **Backup First**: Make sure all your changes are committed
2. **Force Update**: May affect users who have the tool installed
3. **Version Bump**: Always increment version number (2.1.0 → 2.1.1 if needed)
4. **Test After**: Install in test Galaxy to verify everything works

---

## 🆘 If Nothing Works

Contact Tool Shed support:
- **Email**: galaxy-dev@lists.galaxyproject.org
- **Help Forum**: https://help.galaxyproject.org/
- **Provide**:
  - Repository name: cryoem_particle_picker
  - Owner: jatin_bioinformatics
  - Error message: "changelog does not include revision d84537b60153"
  - What you've tried

---

## ✅ Success Indicators

After successful fix:
- ✅ No revision error messages
- ✅ Tool Shed shows version 2.1.0+galaxy0
- ✅ All files present and updated
- ✅ Can install in Galaxy without errors
- ✅ Tool runs successfully with test data

---

## 📝 Prevention for Future

To avoid this issue:
1. **Don't rewrite git history** after uploading to Tool Shed
2. **Use version bumps** instead of force updates when possible
3. **Keep git history linear** (avoid rebasing published commits)
4. **Test locally first** before uploading to Tool Shed

---

## Quick Reference

```bash
# Quick fix (one command)
cd cryoEM_particle_picker && \
git add -A && \
git commit -m "Version 2.1.0: crYOLO model integration" && \
cd planemo/tools/ml_particle_picker && \
planemo shed_update --shed_target toolshed --force_repository_creation \
    --message "Version 2.1.0: Force update to resolve revision mismatch"
```

---

Your tool is ready - this is just a git housekeeping issue that's easily resolved! 🚀
