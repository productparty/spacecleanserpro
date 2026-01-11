# Space Cleanser Pro v1.1.4

## 🐛 Bug Fixes

### Delete Confirmation Dialog
- **Fixed:** Delete and Cancel buttons were not clickable in the confirmation dialog
- **Root Cause:** Scrollable frame was expanding and pushing buttons below visible area
- **Solution:** 
  - Increased dialog height from 400px to 500px
  - Changed scrollable frame to fixed height (120px) instead of expanding
  - Added explicit button heights (35px) for better clickability
  - Ensured buttons always stay visible at bottom

## 📋 Full Changelog (v1.1.0 → v1.1.4)

### v1.1.4 (Current)
- Fix delete confirmation dialog buttons not clickable

### v1.1.3
- Fix duplicate cards not displaying (root cause: file preview in hidden frame)
- Show first 3 duplicate files immediately without expanding
- Add "Scan Both" button to run duplicate and large file scans simultaneously
- Improve expand/collapse behavior for file lists

### v1.1.2
- Enable concurrent scans (duplicate and large file scans can run simultaneously)
- Improve card display with periodic UI updates
- Limit initial display to 100 items for performance
- Add debug logging for troubleshooting
- Better progress messages when both scans run

### v1.1.1
- Fix duplicate and large file display issues
- Add error handling to card creation with proper exception logging
- Clear scrollable frames before displaying new results
- Update progress label before hiding progress frame
- Fix border_color issue in DuplicateGroupCard
- Add empty state messages when no results found
- Force UI update after displaying cards

### v1.1.0 - Discovery Pack Release
- **New Feature:** Duplicate Finder - Hash-based duplicate file detection across C: drive
- **New Feature:** Large File Detective - Configurable large file finder (100MB, 500MB, 1GB, 2GB, 5GB thresholds)
- **New UI:** Discovery tab with split-pane layout
- **New Components:**
  - DuplicateGroupCard - Shows duplicate file groups with wasted space
  - LargeFileCard - Shows large files with type categorization
  - File action dialogs for delete/move confirmations
- **New Functionality:**
  - File type detection (video, installer, archive, image, document)
  - Batch selection for duplicates
  - "Keep newest" / "Keep oldest" quick actions
  - Move files to external drives
  - Progress indicators with cancel support
  - System folder exclusions

## 🚀 Installation

1. Download `SpaceCleanserPro-v1.1.4.exe` from the assets below
2. Double-click to run
3. If Windows shows a SmartScreen warning, click "More info" → "Run anyway"

## 📝 What's New in Discovery Pack

The Discovery Pack helps you find hidden space hogs beyond standard caches:

- **Duplicate Finder:** Identifies identical files using MD5 hashing (files >1MB)
- **Large File Finder:** Finds files above your chosen threshold
- **Smart Categorization:** Automatically categorizes files by type
- **Batch Operations:** Select multiple files for deletion
- **Move Instead of Delete:** Option to move files to external drives

## 🔧 Technical Details

- Minimum file size for duplicate detection: 1MB
- Hash algorithm: MD5 (fast and sufficient for duplicate detection)
- System folders excluded: Windows, Program Files, ProgramData, Recycle Bin
- Progress updates: Every 25-50 files processed
- Initial display limit: 100 items (scroll to see more)

## 📦 What's Included

- Pre-built Windows executable
- All dependencies bundled
- Configuration files included
- Discovery Pack features fully integrated

## 🐛 Known Issues

None at this time. If you encounter any issues, please report them on GitHub.

---

**For Developers:** See README.md for running from source, or RELEASE.md for release process documentation.
