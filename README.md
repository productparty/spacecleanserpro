# Space Cleanser Pro

A transparent Windows disk space manager that helps you understand and reclaim storage on your C: drive. Unlike Windows' cryptic Storage Settings, Space Cleanser shows you exactly what's eating your disk space with plain English explanations, safety ratings, and smart recommendations.

Whether you're a developer drowning in Gradle caches (31 GB, anyone?) or just wondering where your 237 GB went, Space Cleanser scans dev tool caches, browser data, Windows temp files, old downloads, and system logs - then helps you safely delete what you don't need. Every item includes a clear description of what it is, what happens if you delete it, and color-coded safety badges so you never have to guess.

**Built for anyone who's ever stared at "Other: 72.4 GB" and thought "but what IS that?"**

## Quick Start - No Installation Required

### Download & Run

**[⬇️ Download Latest Release](https://github.com/productparty/spacecleanser/releases/latest)**

1. Go to [Releases](https://github.com/productparty/spacecleanser/releases/latest)
2. Download `SpaceCleanserPro-v*.exe`
3. Double-click to run

**No Python installation needed** - Just download and run!

### Windows SmartScreen Warning

When you first run the downloaded `.exe`, Windows may show a SmartScreen warning saying "Windows protected your PC" or "Unknown publisher". This is normal for unsigned executables.

**Why this happens:**
- The app isn't code-signed (certificates cost $300-500/year)
- Windows shows this warning for any unsigned executable from the internet
- The source code is fully open source and available for security review

**How to proceed:**
1. Click **"More info"** on the warning dialog
2. Click **"Run anyway"**
3. The app will launch normally

This is standard for free, open-source tools. Once you run it once, Windows will remember and won't show the warning again.

### Running from Source (For Developers)

If you want to run from source or contribute:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/productparty/spacecleanser.git
   cd spacecleanser
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

4. **Build executable locally (for testing):**
   ```bash
   build.bat
   ```
   The executable will be in the `dist/` folder.

## Features

### 🔍 Transparent Scanning
- **Automatic detection** of common space-hogging locations
- **Real-time size calculation** with human-readable formats
- **Smart categorization** (Dev Tools, System Files, Browser Caches, User Files)
- **Age tracking** to identify old files that can be safely removed

### 🛡️ Safety First
- **Color-coded safety badges**:
  - 🟢 **Safe** - Safe to delete, will rebuild automatically
  - 🟡 **Caution** - Requires understanding the impact before deletion
  - 🔴 **Keep** - Not recommended to delete (e.g., VS Code extensions)
- **Clear impact descriptions** - Every item explains what happens if you delete it
- **Confirmation dialogs** - Always asks before deleting, with clear warnings
- **Batch cleanup** - Review and clean multiple items at once

### 💡 Smart Recommendations
- **Intelligent suggestions** based on scan results
- **Prioritized cleanup** - Shows the biggest wins first
- **Context-aware warnings** - Highlights items that need extra attention

### 📊 Visual Dashboard
- **Disk space visualization** - See your storage breakdown at a glance
- **Filterable results** - Filter by category, size, or age
- **Detailed folder cards** - Each item shows size, age, item count, and safety rating
- **Persistent settings** - Remembers your preferences and last scan results

### 🔧 Developer-Friendly
Scans and manages caches for:
- **Gradle** (build cache, wrapper downloads)
- **Android** (build cache, virtual devices)
- **Rust/Cargo** (package registry)
- **NPM** (package cache)
- **Python/Pip** (package cache)
- **Maven** (repository cache)
- **VS Code/Cursor** (editor caches)
- And more...

### 🌐 Browser & System Support
- **Browser caches** (Chrome, Edge, Firefox)
- **Windows temp files** (user and system)
- **Windows Update downloads**
- **System logs** (old logs only)
- **Recycle Bin**
- **Old Downloads** (configurable age threshold)

## Requirements

- **Windows 10/11**
- Administrator privileges (optional, for full system scanning)

**Note:** If running from source, you'll need Python 3.8+ and the dependencies listed in `requirements.txt`.

## Usage

### First Launch

1. **Start the app** - It will automatically scan your system on startup
2. **Admin privileges** (optional) - The app will prompt you if you want to run with administrator privileges for full system scanning. You can continue without admin - the app works fine, but some system folders will be skipped.

### Scanning

- **Automatic scan** runs on startup
- Click **"Scan"** to refresh the results at any time
- The scan includes:
  - Your user profile folders (dev caches, temp files)
  - Browser data (if browsers are installed)
  - System folders (if running as admin)
  - Downloads folder (old files only)

### Understanding Results

Each folder/item shows:
- **Size** - How much space it's using
- **Safety badge** - Color-coded safety rating
- **Description** - What this folder is for
- **Impact** - What happens if you delete it
- **Age** - How old the files are
- **Item count** - Number of files/folders

### Cleaning Up

1. **Single item cleanup:**
   - Click on any folder card to see details
   - Click **"Clean"** button
   - Review the confirmation dialog
   - Confirm deletion

2. **Batch cleanup:**
   - Use filters to find items you want to clean
   - Click **"Batch Cleanup"** button
   - Select multiple items
   - Review the summary
   - Confirm deletion

3. **Follow recommendations:**
   - Check the recommendations panel at the top
   - Click on recommendation cards to see details
   - Use the suggested actions

### Filters

Use the filter bar to:
- **Filter by category** - Dev Tools, System Files, Browser Caches, User Files
- **Filter by size** - Show only items above a certain size threshold
- **Filter by age** - Show only items older than X days

## Monitored Locations

### Development Tools
- `.gradle/caches` - Gradle Build Cache
- `.gradle/wrapper` - Gradle Wrapper Downloads
- `.android/build-cache` - Android Build Cache
- `.android/avd` - Android Virtual Devices
- `.cargo/registry/cache` - Rust Package Cache
- `.npm/_cacache` - NPM Package Cache
- `.pip/cache` - Python Pip Cache
- `.m2/repository` - Maven Repository Cache
- `.cache` - Generic Application Cache
- `.cursor/cache` - Cursor Editor Cache
- `.vscode/extensions` - VS Code Extensions (marked as Keep)

### System Files
- `%TEMP%` - User Temp Files
- `C:\Windows\Temp` - Windows Temp Files (requires admin)
- `C:\Windows\SoftwareDistribution\Download` - Windows Update Downloads (requires admin)
- `C:\Windows\Logs` - Windows Log Files, old only (requires admin)
- `C:\ProgramData\Package Cache` - Installer Package Cache (requires admin)
- Recycle Bin

### Browser Caches
- Chrome cache (`%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache`)
- Edge cache (`%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache`)
- Firefox cache (`%LOCALAPPDATA%\Mozilla\Firefox\Profiles\*\cache2`)

### User Files
- Downloads folder (files older than 180 days)

## Configuration

Settings are stored in `settings.json` and include:
- Window size and position
- Filter preferences
- Last scan results (for quick loading)

Folder definitions are in `folder_defs.json` - you can customize which locations are scanned and their descriptions.

## Safety Levels Explained

### 🟢 Safe
These items can be deleted without worry. They will rebuild automatically:
- Build caches (Gradle, Android, Maven)
- Package caches (NPM, Pip, Cargo)
- Browser caches
- Temp files
- Old system logs

### 🟡 Caution
These items require understanding before deletion:
- Gradle wrapper downloads (will re-download on next build)
- Android Virtual Devices (you'll need to recreate them)
- Windows Update downloads (only if system is up to date)
- Old Downloads (permanent deletion)
- Installer Package Cache (may need for repairs)

### 🔴 Keep
These items are not recommended for deletion:
- VS Code Extensions (you'll need to reinstall them)

## Requirements

- Python 3.8+
- `customtkinter >= 5.2.0`
- `winshell >= 0.6` (for Recycle Bin access)

## License

GPL-3.0

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Add support for additional cache locations
- Improve documentation

## Disclaimer

This tool helps you understand and clean up disk space, but **always review what you're deleting**. While the app provides safety ratings and descriptions, you are responsible for your data. The developers are not liable for any data loss.

---

**Made with ❤️ for developers and power users who want transparency in their disk space management.**
