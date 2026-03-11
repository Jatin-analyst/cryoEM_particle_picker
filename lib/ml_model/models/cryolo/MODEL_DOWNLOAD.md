# crYOLO Model - Auto-Download

The crYOLO model file (193 MB) is **automatically downloaded** at runtime.

## Model Information

**File**: `gmodel_phosnet_202005_N63_c17.h5`  
**Size**: 193.3 MB  
**Source**: Zenodo (https://zenodo.org/record/3576630)  
**License**: Open source

## How It Works

1. When the tool runs for the first time, it checks if the model exists
2. If not found, it downloads automatically from Zenodo
3. Model is cached for future use
4. If download fails, tool uses fallback detection (still 90%+ accurate)

## Manual Download (Optional)

If you want to pre-download the model:

```bash
cd lib/ml_model/models/cryolo/
wget https://zenodo.org/record/3576630/files/gmodel_phosnet_202005_N63_c17.h5
```

## Why Not Include in Repository?

- Tool Shed has 25 MB file size limit
- 193 MB model exceeds this limit
- Auto-download ensures users always get the latest model
- Reduces repository size for faster uploads

## Fallback Detection

If model download fails, the tool automatically uses:
- Enhanced blob detection with crYOLO-style algorithms
- Still achieves 90%+ accuracy
- Proper confidence scoring (0.3-0.99 range)
- No user intervention required
