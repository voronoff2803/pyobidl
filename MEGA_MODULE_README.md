# Recreated Mega Module for PyObidl

This document describes the recreated and improved mega module that integrates the functionality from your original `mega_downloader.py` with the existing PyObidl infrastructure.

## Overview

The mega module has been enhanced with:
- **Improved URL parsing** from your original code
- **Megatools integration** with automatic installation on macOS
- **Simplified download interface** while maintaining full API compatibility
- **Better error handling** and logging
- **Universal downloader** supporting multiple platforms

## Key Features

### 1. Enhanced Mega.py Class

The `Mega` class now includes new methods from your original code:

- `parse_mega_url(url)` - Parse Mega.nz URLs to extract file ID and decryption key
- `download_with_megatools(url, output_dir)` - Download using megatools (megadl command)
- `install_megatools_macos()` - Automatically install megatools on macOS via Homebrew
- `simple_download(url, output_dir)` - Simplified download with fallback methods

### 2. Universal Downloader

The improved `downloader.py` now supports:
- **Mega.nz** files
- **YouTube** videos
- **MediaFire** files
- **Google Drive** files

### 3. Enhanced Platform Support

All platform downloaders now have consistent interfaces:
- `YoutubeDownloader` class
- `MediaFireDownloader` class
- `GoogleDriveDownloader` class

## Usage Examples

### 1. Simple Mega.nz Download

```python
from pyobidl.megacli.mega import Mega

# Create Mega instance
mega = Mega()

# Simple download (tries megatools first, then provides instructions)
success = mega.simple_download(
    "https://mega.nz/file/B3kg2ZqC#aEOZ5e6OJYV-H8aKFY8nWhX-wxwZQL21hlWV1Sj9jg4",
    "./downloads"
)

if success:
    print("✅ Download completed!")
else:
    print("❌ Download failed!")
```

### 2. Universal Downloader (Any Platform)

```python
from pyobidl.downloader import UniversalDownloader

downloader = UniversalDownloader()

# Automatically detects platform and downloads
urls = [
    "https://mega.nz/file/B3kg2ZqC#aEOZ5e6OJYV-H8aKFY8nWhX-wxwZQL21hlWV1Sj9jg4",
    "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "https://mediafire.com/file/abc123/example.zip",
    "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
]

for url in urls:
    success = downloader.download(url, "./downloads")
    print(f"{'✅' if success else '❌'} {url}")
```

### 3. Traditional Mega API (Full Features)

```python
from pyobidl.megacli.mega import Mega

# Create and login to Mega
mega = Mega()
mega.login("email@example.com", "password")  # or mega.login() for anonymous

# Get all files
files = mega.get_files()

# Download specific file
mega.download_url(
    "https://mega.nz/file/B3kg2ZqC#aEOZ5e6OJYV-H8aKFY8nWhX-wxwZQL21hlWV1Sj9jg4",
    dest_path="./downloads/"
)

# Upload file
mega.upload("local_file.txt")

# Create folder
mega.create_folder("My Folder")
```

## Command Line Usage

### 1. Mega-specific CLI (like your original script)

```bash
# Basic download
python mega_downloader_cli.py "https://mega.nz/file/B3kg2ZqC#aEOZ5e6OJYV-H8aKFY8nWhX-wxwZQL21hlWV1Sj9jg4"

# Download to specific directory
python mega_downloader_cli.py "https://mega.nz/file/B3kg2ZqC#aEOZ5e6OJYV-H8aKFY8nWhX-wxwZQL21hlWV1Sj9jg4" ./downloads

# Verbose logging
python mega_downloader_cli.py "https://mega.nz/file/B3kg2ZqC#aEOZ5e6OJYV-H8aKFY8nWhX-wxwZQL21hlWV1Sj9jg4" -v

# With authentication
MEGA_EMAIL=your@email.com MEGA_PASSWORD=yourpassword python mega_downloader_cli.py --login "https://mega.nz/file/..."
```

### 2. Universal CLI (all platforms)

```bash
# Download from any supported platform
python -m pyobidl.downloader "https://mega.nz/file/B3kg2ZqC#aEOZ5e6OJYV-H8aKFY8nWhX-wxwZQL21hlWV1Sj9jg4"
python -m pyobidl.downloader "https://youtube.com/watch?v=dQw4w9WgXcQ" ./downloads
python -m pyobidl.downloader "https://mediafire.com/file/abc123/example.zip" -v
```

## Installation Requirements

### For Mega.nz (Recommended)

The module will try to use megatools for better reliability:

```bash
# macOS (automatic via the script)
brew install megatools

# Ubuntu/Debian
sudo apt install megatools

# Or download from: https://megatools.megous.com/
```

### For YouTube

```bash
pip install youtube-dl
```

### For web scraping (MediaFire, Google Drive)

```bash
pip install beautifulsoup4 user-agent
```

## Error Handling

The recreated module includes comprehensive error handling:

- **Network errors** with retry logic
- **Authentication failures** with clear error messages
- **Rate limiting** with exponential backoff
- **Invalid URLs** with format validation
- **Missing dependencies** with installation instructions

## Logging

Enhanced logging system with different levels:

```python
from pyobidl.utils import setup_logging

# Basic logging
setup_logging()

# Verbose logging
setup_logging(verbose=True)
```

## Migration from Original Code

Your original `mega_downloader.py` functionality is now integrated:

| Original Function | New Location | Notes |
|-------------------|--------------|-------|
| `parse_mega_url()` | `Mega.parse_mega_url()` | Same functionality |
| `download_with_megatools()` | `Mega.download_with_megatools()` | Enhanced error handling |
| `download_from_mega()` | `Mega.simple_download()` | Improved interface |
| Auto-install megatools | `Mega.install_megatools_macos()` | Same functionality |

## Advanced Features

### 1. Progress Callbacks

```python
def progress_callback(filename, bytes_downloaded, total_bytes, speed, eta):
    percent = (bytes_downloaded / total_bytes) * 100
    print(f"Downloading {filename}: {percent:.1f}% ({speed/1024:.1f} KB/s)")

mega.download_url(url, progressfunc=progress_callback)
```

### 2. Proxy Support

```python
mega = Mega(options={
    'proxies': {
        'http': 'http://proxy.example.com:8080',
        'https': 'https://proxy.example.com:8080'
    }
})
```

### 3. Async Downloads

```python
import asyncio
from pyobidl.downloader import AsyncDownloader

async def download_multiple():
    downloader = AsyncDownloader()
    tasks = [
        downloader.download_url(url1),
        downloader.download_url(url2),
        downloader.download_url(url3)
    ]
    results = await asyncio.gather(*tasks)
    return results
```

## Troubleshooting

### Common Issues

1. **"megatools not found"**
   - Install megatools: `brew install megatools` (macOS) or `sudo apt install megatools` (Ubuntu)

2. **"Invalid Mega.nz URL format"**
   - Ensure URL format: `https://mega.nz/file/[file_id]#[decryption_key]`

3. **"Login failed"**
   - Check credentials or use anonymous login: `mega.login()`

4. **"Rate limit exceeded"**
   - Wait a few minutes and try again

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all operations will show detailed debug info
```

This recreated mega module maintains full compatibility with your existing code while adding the improved functionality from your original `mega_downloader.py` script. 