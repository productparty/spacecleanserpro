# Step-by-Step Guide: Creating Your First Release (v1.0.0)

Follow these steps to create the first GitHub release. The GitHub Action will automatically build and attach the executable.

## Prerequisites Checklist

Before creating the release, ensure:
- ✅ `main.py` has `VERSION = "1.0.0"` (already verified)
- ✅ All changes are committed and pushed to GitHub
- ✅ `.github/workflows/build-release.yml` exists (already verified)

## Step 1: Commit and Push Current Changes

If you have uncommitted changes (like the README update), commit them first:

```bash
git add README.md
git commit -m "Update README: Activate download links for v1.0.0 release"
git push origin main
```

## Step 2: Navigate to GitHub Releases

1. Open your browser and go to: `https://github.com/productparty/spacecleanser`
2. Click on the **"Releases"** link (usually on the right sidebar, or find it under the "Code" tab)
3. If this is your first release, you'll see a message like "No releases published". Click **"Create a new release"** or **"Draft a new release"**

## Step 3: Fill in Release Details

Fill in the following fields:

### Tag Version
- **Tag:** `v1.0.0` (must match exactly, including the `v` prefix)
- **Target:** Select `main` branch (or your default branch)

### Release Title
- **Title:** `Space Cleanser Pro v1.0.0`

### Release Description
Copy and paste this template, or customize it:

```markdown
## Space Cleanser Pro v1.0.0

### 🎉 First Release!

This is the initial release of Space Cleanser Pro with executable distribution.

### Features
- Single-file Windows executable (.exe)
- No Python installation required
- Automatic scanning of cache folders
- Safety ratings and clear descriptions
- Batch cleanup support
- Visual dashboard with filters

### Installation
1. Download `SpaceCleanserPro-v1.0.0.exe` from the assets below
2. Double-click to run
3. If Windows shows a SmartScreen warning, click "More info" → "Run anyway"

### What's Included
- Pre-built Windows executable
- All dependencies bundled
- Configuration files included

### For Developers
- See README.md for running from source
- See RELEASE.md for release process documentation
```

### Release Options
- ✅ Check **"Set as the latest release"** (if this option appears)
- ✅ Check **"Set as a pre-release"** should be **UNCHECKED** (unless you want this to be a pre-release)

## Step 4: Publish the Release

1. Click the **"Publish release"** button (green button at the bottom)
2. Wait a few seconds - GitHub will create the release

## Step 5: Monitor the GitHub Action

After publishing, the GitHub Action will automatically start:

1. Go to the **"Actions"** tab in your GitHub repository
2. You should see a workflow run called **"Build Release Executable"** start automatically
3. Click on it to see the build progress
4. The workflow will:
   - Checkout code
   - Set up Python 3.11
   - Install dependencies
   - Build the executable with PyInstaller
   - Extract version from tag
   - Rename executable to `SpaceCleanserPro-v1.0.0.exe`
   - Upload it to the release

### Expected Build Time
- Usually takes 3-5 minutes
- Watch for any errors in the workflow logs

## Step 6: Verify the Release

Once the Action completes successfully:

1. Go back to the **"Releases"** page
2. Click on the **"v1.0.0"** release
3. You should see `SpaceCleanserPro-v1.0.0.exe` listed under **"Assets"**
4. The file size should be under 50 MB (typically 20-40 MB)

## Step 7: Test the Executable

1. **Download the .exe** from the release page
2. **Run it** on your Windows machine
3. **Expected behavior:**
   - Windows may show SmartScreen warning → Click "More info" → "Run anyway"
   - App should launch and show the dashboard
   - Window title should show "Space Cleanser Pro v1.0.0"
   - App should scan folders successfully (folder_defs.json should load)
   - Settings should save to `%LOCALAPPDATA%\SpaceCleanserPro\settings.json`

## Troubleshooting

### GitHub Action Fails

If the workflow fails:
1. Check the error message in the Actions tab
2. Common issues:
   - Missing dependencies in `requirements.txt`
   - PyInstaller build errors
   - File path issues

### Executable Not Attached

If the build completes but no .exe appears:
1. Check the workflow logs for the upload step
2. Verify the version extraction worked correctly
3. Check that the file exists in `dist/` folder in the logs

### Need to Rebuild

If you need to rebuild:
1. Delete the release (go to Releases → Edit → Delete)
2. Create a new release with the same tag `v1.0.0`
3. Or create a new tag like `v1.0.1` if you made fixes

## Next Steps After Release

Once the release is live:
- ✅ The README download links will now work
- ✅ Users can download and run the .exe
- ✅ You can share the release link with users

## Success Criteria

You'll know everything worked when:
- ✅ Release appears on GitHub Releases page
- ✅ GitHub Action completes successfully (green checkmark)
- ✅ `SpaceCleanserPro-v1.0.0.exe` is listed under Assets
- ✅ You can download and run the .exe successfully
- ✅ App shows version "v1.0.0" in window title
- ✅ App scans folders correctly

---

**Ready to create the release?** Follow steps 1-4 above, then monitor the Action in step 5!
