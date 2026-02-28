#!/bin/bash

# Fix Tool Shed Revision Mismatch
# This script resolves the "changelog does not include revision" error

set -e

echo "🔧 Fixing Tool Shed Revision Mismatch"
echo "======================================"
echo

# Step 1: Commit all current changes
echo "Step 1: Committing current changes..."
git add -A
git commit -m "Version 2.1.0: Real crYOLO model, fixed conda dependencies, resolved confidence scoring" || echo "Nothing to commit or already committed"

# Step 2: Check current revision
CURRENT_REV=$(git rev-parse HEAD)
echo "Current revision: $CURRENT_REV"
echo

# Step 3: Navigate to tool directory
cd planemo/tools/ml_particle_picker

# Step 4: Force update to Tool Shed
echo "Step 2: Force updating Tool Shed repository..."
echo "This will reset the Tool Shed to match your current git state"
echo

read -p "Do you want to proceed with force update? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled by user"
    exit 0
fi

# Option 1: Update with force flag
echo "Attempting force update..."
planemo shed_update --shed_target toolshed \
    --force_repository_creation \
    --message "Version 2.1.0: Force update to resolve revision mismatch - Real crYOLO model integration, fixed conda dependencies"

echo
echo "✅ Tool Shed update completed!"
echo
echo "Next steps:"
echo "1. Visit https://toolshed.g2.bx.psu.edu/"
echo "2. Check your repository: cryoem_particle_picker"
echo "3. Verify the new revision is present"
echo "4. Test installation in Galaxy"
