# Docker Build Troubleshooting Guide

## 🚨 Error: "no build stage in current context"

This error typically occurs when there are issues with your Dockerfile structure.

### 🔍 Common Causes:

1. **Missing FROM statement** - Every Dockerfile must start with `FROM`
2. **Syntax errors** in Dockerfile
3. **Incorrect file structure** or file not found
4. **Empty or corrupted Dockerfile**

### 🛠️ Quick Fixes:

#### 1. Check Your Dockerfile Structure
Make sure your Dockerfile starts with a `FROM` statement:

```dockerfile
# MUST be first line (after comments)
FROM python:3.11-bookworm

# Then your other commands...
ENV VIRTUAL_ENV=/opt/venv
# ... rest of your Dockerfile
```

#### 2. Verify File Location
Make sure your Dockerfile is in the correct location and named properly:

```bash
# Check if Dockerfile exists
ls -la Dockerfile

# Or if you're using a different name
ls -la Dockerfile.tgservice-bot
```

#### 3. Check docker-compose.yml Configuration
If using docker-compose, verify your service configuration:

```yaml
version: '3.8'
services:
  tgservice-bot:
    build:
      context: .
      dockerfile: Dockerfile  # Make sure this points to the right file
    # ... rest of your service config
```

### 🧪 Test with Minimal Dockerfile

Create a minimal test Dockerfile to verify the setup:

```dockerfile
FROM python:3.11-bookworm

# Test megatools installation
RUN apt-get update && \
    apt-get install -y --no-install-recommends megatools && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Test basic pyobidl installation
RUN pip install requests beautifulsoup4 user-agent pycryptodome tenacity

# Create a simple test
RUN echo 'import shutil; print("megatools available:", shutil.which("megadl"))' > test.py

CMD ["python", "test.py"]
```

### 🔧 Debugging Steps:

#### Step 1: Validate Dockerfile Syntax
```bash
# Check Dockerfile syntax
docker build --dry-run .
```

#### Step 2: Build with Verbose Output
```bash
# Build with detailed output
docker build --no-cache --progress=plain .
```

#### Step 3: Check Build Context
```bash
# Make sure you're in the right directory
pwd
ls -la

# Check what's being sent to Docker daemon
docker build . 2>&1 | head -10
```

### 📁 Expected File Structure

Your project should look like this:

```
your-project/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── src/
    ├── main.py
    └── ... (your source files)
```

### 🚀 Complete Working Dockerfile

Use this complete Dockerfile that includes everything needed for pyobidl:

```dockerfile
FROM python:3.11-bookworm

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

# CRITICAL: Install megatools
RUN apt-get update && \
    apt-get install -y --no-install-recommends megatools && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install setuptools wheel
RUN pip install -r /config/requirements.txt
RUN pip install --upgrade rarfile beautifulsoup4 user-agent pycryptodome

RUN mkdir /src
COPY src /src
WORKDIR /src

CMD ["python", "main.py"]
```

### 🧹 Clean Build (if nothing else works)

```bash
# Clean everything and rebuild
docker system prune -a
docker-compose build --no-cache tgservice-bot
```

### 📋 Checklist Before Building:

- [ ] Dockerfile starts with `FROM`
- [ ] No syntax errors in Dockerfile
- [ ] requirements.txt exists and is accessible
- [ ] src/ directory exists with your source code
- [ ] You're in the correct directory when running build
- [ ] docker-compose.yml points to correct Dockerfile 