# Docker Integration Guide for Recreated PyObidl Mega Module

This guide shows how to integrate the recreated pyobidl mega module into your Docker environment.

## 🐳 Required Dockerfile Changes

### 1. **CRITICAL: Install megatools**
Add this section to your Dockerfile:

```dockerfile
# Install megatools for mega.nz downloads (CRITICAL for recreated mega module)
RUN apt-get update && \
    apt-get install -y --no-install-recommends megatools && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### 2. **Optional: Install additional media tools**
For full universal downloader support:

```dockerfile
# Install youtube-dl and other media tools for universal downloader support
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        youtube-dl \
        ffmpeg \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### 3. **Complete Enhanced Dockerfile**
```dockerfile
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /config
COPY requirements.txt /config/requirements.txt

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gnupg2 ca-certificates wget curl git && \
    echo "deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] http://deb.debian.org/debian bookworm main contrib non-free" > /etc/apt/sources.list.d/non-free.list && \
    apt-get update && \
    apt-get install -y unrar && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# CRITICAL: Install megatools for mega.nz downloads
RUN apt-get update && \
    apt-get install -y --no-install-recommends megatools && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Optional: Install media tools for universal downloader
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        youtube-dl \
        ffmpeg \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install setuptools wheel
RUN pip install -r /config/requirements.txt
RUN pip install --upgrade rarfile

# Install additional PyObidl dependencies
RUN pip install --upgrade \
    beautifulsoup4 \
    user-agent \
    pycryptodome

RUN mkdir /src
COPY src /src
WORKDIR /src
```

## 📦 Updated requirements.txt

**Replace your current requirements.txt with this:**

```txt
requests==2.27.1
urllib3==1.25.11
phonenumbers
tenacity>=8.0.0,<10.0.0
python-telegram-bot
patool
pathlib

# PyObidl with recreated mega module
pyobidl @ git+https://github.com/voronoff2803/pyobidl

# Dependencies for universal downloader functionality
beautifulsoup4>=4.12.0
user-agent>=0.1.10
pycryptodome>=3.18.0
youtube-dl
requests-toolbelt

# Remove or comment out mega.py if it conflicts with recreated module
# mega.py @ git+https://github.com/pgp/mega.py
```

## 💡 Important Changes from Your Current Setup

### ✅ **What to Add:**
1. **`megatools`** - Essential system package for mega downloads
2. **Updated `tenacity`** version (>=8.0.0)
3. **Additional Python packages**: `beautifulsoup4`, `user-agent`, `pycryptodome`

### ❌ **What to Remove/Change:**
1. **Remove `mega.py`** from requirements (conflicts with recreated module)
2. **Update `tenacity`** from `==9.0.0` to `>=8.0.0,<10.0.0`

## 🚀 Usage Examples in Docker

### Simple Mega Download
```python
from pyobidl.megacli.mega import Mega

mega = Mega()
success = mega.simple_download(
    "https://mega.nz/file/5r1nWZwK#DlBpWv2Hc0zLhjuldVF8ZJKepkBfZyNYPh7feSOA7jI",
    "/downloads"
)
```

### Universal Downloader
```python
from pyobidl.downloader import UniversalDownloader

downloader = UniversalDownloader()

# Works with any supported platform
success = downloader.download("https://mega.nz/file/...", "/downloads")
success = downloader.download("https://youtube.com/watch?v=...", "/downloads")
success = downloader.download("https://mediafire.com/file/...", "/downloads")
```

## 🔧 Environment Testing

Add this to your container to test if everything works:

```python
#!/usr/bin/env python3
import shutil
from pyobidl.megacli.mega import Mega
from pyobidl.utils import setup_logging

def test_docker_environment():
    setup_logging()
    
    # Test 1: Check megatools
    if shutil.which('megadl'):
        print("✅ megatools available")
    else:
        print("❌ megatools missing!")
        return False
    
    # Test 2: Test mega module
    try:
        mega = Mega()
        file_id, key = mega.parse_mega_url("https://mega.nz/file/test#key")
        print("✅ Mega module working")
    except Exception as e:
        print(f"❌ Mega module error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if test_docker_environment():
        print("🐳 Docker environment ready!")
    else:
        print("❌ Docker setup incomplete!")
```

## 🐛 Troubleshooting

### Problem: "megadl command not found"
**Solution:** Add megatools installation to Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y megatools
```

### Problem: "ImportError: No module named 'tenacity'"
**Solution:** Update requirements.txt:
```txt
tenacity>=8.0.0,<10.0.0
```

### Problem: "Conflicts with mega.py"
**Solution:** Remove or comment out mega.py from requirements:
```txt
# mega.py @ git+https://github.com/pgp/mega.py
```

### Problem: "Download fails with rate limiting"
**Solution:** The recreated module uses megatools which avoids API rate limits:
```python
# Use simple_download method instead of traditional API
mega = Mega()
success = mega.simple_download(url, output_dir)  # Uses megatools
```

## 🎯 Key Advantages in Docker

✅ **No API Rate Limits** - Uses megatools instead of Mega API  
✅ **Faster Downloads** - Direct tool integration  
✅ **Better Reliability** - Less prone to connection issues  
✅ **Universal Support** - Works with multiple platforms  
✅ **Simple Integration** - Just add megatools to your container  

## 📋 Quick Checklist for Docker Integration

- [ ] Add `megatools` to Dockerfile
- [ ] Update `tenacity` version in requirements.txt
- [ ] Remove `mega.py` from requirements.txt  
- [ ] Add `beautifulsoup4`, `user-agent`, `pycryptodome`
- [ ] Test with the provided test script
- [ ] Verify downloads work with your specific URLs

Your Docker environment will now support the full functionality of the recreated pyobidl mega module! 