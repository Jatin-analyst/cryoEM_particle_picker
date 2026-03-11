# Deployment Instructions - v3.0.0+galaxy12

## Changes Made

### Version Update
- Updated from v3.0.0+galaxy11 to v3.0.0+galaxy12

### Bug Fixes
1. **Fixed path resolution for Galaxy deployment**
   - Added flexible path detection (tries 3 different locations)
   - Handles different directory structures in Tool Shed vs local
   - Better error messages showing which paths were tried

2. **Enhanced error logging**
   - Added script location and working directory logging
   - Better error handling at each step
   - More detailed error messages for debugging

3. **Cleaned up repository**
   - Removed 26+ old documentation files
   - Removed test data (archive/, batch_output/)
   - Removed development files (.kiro/, .pytest_cache/)
   - Removed old scripts and notebooks
   - Removed duplicate .shed.yml
   - Removed old model file (yolov8n.pt)

### Files to Commit

```bash
# Modified files
planemo/tools/ml_particle_picker/ml_particle_picker.xml  # Version bump to galaxy12
planemo/tools/ml_particle_picker/run_cryotransformer.py  # Path fixes and logging

# New documentation
CRYOPPP_USER_GUIDE.md                    # Comprehensive user guide
CLEANUP_AND_DEPLOYMENT_SUMMARY.md        # Deployment summary
DEPLOYMENT_INSTRUCTIONS.md               # This file

# Deleted files (26+ old docs, test data, dev files)
```

## Git Commands

```bash
cd cryoEM_particle_picker

# Stage all changes
git add -A

# Commit with descriptive message
git commit -m "v3.0.0+galaxy12: Fix Galaxy path resolution, enhance logging, cleanup repo

- Fixed path resolution to work in Galaxy Tool Shed deployment
- Added flexible path detection (tries 3 locations)
- Enhanced error logging with script location and working directory
- Cleaned up 26+ old documentation files
- Removed test data and development files
- Added comprehensive user guide for CryoPPP dataset usage"

# Push to repository
git push origin tree
```

## Planemo Deployment

After committing and pushing:

```bash
cd planemo/tools/ml_particle_picker

# Validate tool
planemo lint ml_particle_picker.xml

# Check diff with Tool Shed
planemo shed_update --shed_target toolshed --check_diff .

# Upload to Tool Shed
planemo shed_update --shed_target toolshed .
```

## Verification

After deployment:

1. **Check Tool Shed**
   - Visit: https://toolshed.g2.bx.psu.edu/view/jatin_bioinformatics/particle_picker_bharat
   - Verify version shows: 3.0.0+galaxy12
   - Check that files are uploaded correctly

2. **Test in Galaxy**
   - Install tool from Tool Shed
   - Upload a test MRC file
   - Run particle picker
   - Verify it completes successfully
   - Check output STAR file

3. **Monitor Logs**
   - Check Galaxy logs for any errors
   - Verify path resolution works correctly
   - Confirm model loads successfully

## Expected Behavior

The tool should now:
- ✅ Find model and lib directories in Galaxy deployment
- ✅ Provide clear error messages if paths not found
- ✅ Log script location and working directory for debugging
- ✅ Work with any Galaxy directory structure
- ✅ Process micrographs successfully
- ✅ Generate valid STAR files

## Troubleshooting

If the tool still fails in Galaxy:

1. **Check the logs** - Look for the detailed path information:
   ```
   Script location: /path/to/script
   Working directory: /path/to/workdir
   Tried locations:
     1. /path1/pretrained_model / /path1/lib
     2. /path2/pretrained_model / /path2/lib
     3. /path3/pretrained_model / /path3/lib
   ```

2. **Verify file structure** - Ensure these exist in Tool Shed:
   - `pretrained_model/CryoTransformer_pretrained_model.pth`
   - `pretrained_model/detr_r101_dc5.pth`
   - `lib/model_imp_file/` (with all source files)

3. **Check dependencies** - Verify conda packages installed:
   - pytorch 2.0+
   - torchvision 0.14+
   - numpy, scipy, mrcfile, etc.

## Summary

**Version**: 3.0.0+galaxy12  
**Status**: Ready for deployment  
**Changes**: Path fixes, enhanced logging, repository cleanup  
**Testing**: Tested locally, ready for Galaxy testing

---

**Date**: March 11, 2026  
**Author**: Kiro AI Assistant  
**Repository**: https://github.com/jatinchd115/cryoEM_particle_picker
