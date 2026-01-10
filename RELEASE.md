# Release Process for Space Cleanser Pro

This document outlines the process for creating a new release of Space Cleanser Pro with automated executable builds.

## Prerequisites

- Write access to the repository
- Git installed and configured
- GitHub account with appropriate permissions

## Release Checklist

### 1. Update Version Number

Update the `VERSION` constant in `main.py`:

```python
VERSION = "1.0.0"  # Update to new version (e.g., "1.1.0")
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

### 2. Update Changelog (Optional but Recommended)

Document what changed in this release. You can add this to the release description on GitHub.

Example:
```markdown
## v1.1.0

### Added
- New feature X
- Support for Y

### Fixed
- Bug fix Z

### Changed
- Improved performance
```

### 3. Commit and Push Changes

```bash
git add main.py
git commit -m "Bump version to v1.1.0"
git push origin main
```

### 4. Create GitHub Release

1. Go to the repository on GitHub
2. Click **"Releases"** → **"Draft a new release"**
3. **Tag version:** Enter `v1.1.0` (must match the version in `main.py`, prefixed with `v`)
4. **Release title:** `Space Cleanser Pro v1.1.0`
5. **Description:** Add changelog and release notes
6. **Check:** "Set as the latest release" (if this is the newest version)
7. Click **"Publish release"**

### 5. GitHub Action Build

Once you publish the release:

1. The GitHub Action workflow (`.github/workflows/build-release.yml`) will automatically trigger
2. It will:
   - Checkout the code
   - Set up Python 3.11
   - Install dependencies and PyInstaller
   - Build the executable using PyInstaller
   - Extract the version from the tag
   - Rename the executable to `SpaceCleanserPro-v{version}.exe`
   - Upload it as a release asset

### 6. Verify Release

1. Go to the [Releases page](https://github.com/productparty/spacecleanser/releases)
2. Check that the release appears
3. Wait for the GitHub Action to complete (check the "Actions" tab)
4. Verify that `SpaceCleanserPro-v{version}.exe` appears in the release assets
5. Download and test the executable on a clean Windows machine (without Python installed)

### 7. Announce Release (Optional)

- Update the README if needed
- Post on social media or relevant communities
- Notify users of important updates

## Troubleshooting

### GitHub Action Fails

1. Check the Actions tab for error messages
2. Common issues:
   - Missing dependencies in `requirements.txt`
   - PyInstaller build errors
   - File path issues with `--add-data`

### Executable Not Attached to Release

1. Check that the workflow completed successfully
2. Verify the upload step didn't fail
3. Check that the tag format matches `vX.Y.Z`
4. Re-run the workflow if needed (Actions → Select workflow → Re-run)

### Executable Too Large

- PyInstaller bundles Python and all dependencies
- Target size: under 50 MB
- If larger, consider:
  - Excluding unnecessary modules
  - Using `--exclude-module` flags
  - Checking for large dependencies

### Testing the Build Locally

Before creating a release, test the build process locally:

```bash
build.bat
```

Then test the resulting `dist/SpaceCleanserPro.exe`:
- Run on a machine without Python installed
- Verify `folder_defs.json` loads correctly
- Verify settings save to `AppData/Local/SpaceCleanserPro/`
- Test scanning and cleaning functionality

## Version History

Keep track of releases here or in a separate CHANGELOG.md:

- **v1.0.0** - Initial release with executable distribution
